package com.mindone.editor.inp.storage;

import com.mindone.editor.common.exception.RestApiException;
import com.mindone.editor.inp.exception.InpFileErrorCode;
import com.mindone.editor.storage.StorageProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;

/**
 * INP 파일의 물리 저장을 담당하는 컴포넌트.
 *
 * <p>파일은 기준 경로 하위의 {@code originals} 디렉터리에 저장 파일명(UUID 기반)으로 기록된다.
 * 기준 경로는 {@link StorageProperties} 가 제공한다.</p>
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class InpFileStorage {

    /** INP 원본 파일 저장 하위 디렉터리. */
    private static final String ORIGINAL_SUBDIR = "originals";

    /** 적용 시 원자적 교체를 위한 임시 파일 접미사. */
    private static final String APPLY_TEMP_SUFFIX = ".tmp";

    private final StorageProperties storageProperties;

    /**
     * 업로드 파일을 저장 파일명으로 스토리지에 기록한다.
     *
     * @param file       업로드된 멀티파트 파일
     * @param storFileNm 저장 파일명({uuid}.{확장자})
     */
    public void store(MultipartFile file, String storFileNm) {
        Path dir = storageProperties.resolve(ORIGINAL_SUBDIR);
        try {
            Files.createDirectories(dir);
            file.transferTo(dir.resolve(storFileNm));
            log.info("INP 파일 저장 완료: {}", dir.resolve(storFileNm).toAbsolutePath());
        } catch (IOException e) {
            log.error("INP 파일 저장 실패: {}", e.getMessage(), e);
            throw new RestApiException(InpFileErrorCode.FILE_UPLOAD_ERROR);
        }
    }

    /**
     * 메모리상의 바이트(편집 후 직렬화된 INP 등)를 저장 파일명으로 스토리지에 기록한다.
     *
     * <p>업로드 멀티파트 대신, "다른 이름으로 저장"처럼 서버가 직접 생성한 INP 바이트를 기록할 때 쓴다.</p>
     *
     * @param content    저장할 파일 바이트(CP949 인코딩 INP 등)
     * @param storFileNm 저장 파일명({uuid}.{확장자})
     */
    public void store(byte[] content, String storFileNm) {
        Path dir = storageProperties.resolve(ORIGINAL_SUBDIR);
        try {
            Files.createDirectories(dir);
            Files.write(dir.resolve(storFileNm), content);
            log.info("INP 파일 저장 완료: {}", dir.resolve(storFileNm).toAbsolutePath());
        } catch (IOException e) {
            log.error("INP 파일 저장 실패: {}", e.getMessage(), e);
            throw new RestApiException(InpFileErrorCode.FILE_UPLOAD_ERROR);
        }
    }

    /**
     * 저장 파일을 다운로드용 리소스로 로드한다.
     *
     * @param storFileNm 저장 파일명({uuid}.{확장자})
     * @return 물리 파일 리소스
     * @throws RestApiException 파일이 존재하지 않으면 {@link InpFileErrorCode#FILE_NOT_FOUND}
     */
    public Resource loadAsResource(String storFileNm) {
        Path path = storageProperties.resolve(ORIGINAL_SUBDIR).resolve(storFileNm);
        if (!Files.exists(path)) {
            log.error("INP 파일을 찾을 수 없음: {}", path.toAbsolutePath());
            throw new RestApiException(InpFileErrorCode.FILE_NOT_FOUND);
        }
        return new FileSystemResource(path);
    }

    /**
     * 저장 파일을 삭제한다.
     *
     * <p>레코드 삭제 트랜잭션 커밋 후 호출되는 best-effort 작업이다. 파일이 없거나 삭제에
     * 실패해도 예외를 던지지 않고(이미 레코드는 삭제됨) 로깅만 한다. 실패 시 고아 파일로 남는다.</p>
     *
     * @param storFileNm 저장 파일명({uuid}.{확장자})
     */
    public void delete(String storFileNm) {
        Path path = storageProperties.resolve(ORIGINAL_SUBDIR).resolve(storFileNm);
        try {
            if (Files.deleteIfExists(path)) {
                log.info("INP 파일 삭제 완료: {}", path.toAbsolutePath());
            } else {
                log.warn("삭제할 INP 파일이 존재하지 않음: {}", path.toAbsolutePath());
            }
        } catch (IOException e) {
            log.error("INP 파일 삭제 실패(고아 파일 가능): {} - {}", path.toAbsolutePath(), e.getMessage());
        }
    }

    /**
     * 원본 저장 파일을 기준 경로 <b>루트</b>의 적용 대상 파일명들로 원자적으로 교체한다.
     *
     * <p>기준 경로 루트는 EPANET 해석엔진(epa 컨테이너)이 {@code /app/inp} 로 함께 보는 디렉터리다.
     * 해석엔진은 매 요청마다 이 파일을 다시 읽으므로, 교체가 끝나면 재기동 없이 반영된다.</p>
     *
     * <p><b>교체 절차</b>: 대상마다 같은 디렉터리에 임시 파일({@code .tmp})로 먼저 전부 복사한 뒤,
     * 복사가 모두 성공했을 때에만 각 임시 파일을 대상 파일명으로 리네임한다. 복사(느리고 실패하기 쉬운 단계)를
     * 앞으로, 리네임(순간적이고 실패하기 어려운 단계)을 뒤로 몰아 두면 도중에 실패해도 실제 적용본은
     * 손대지 않은 상태로 남는다. 리네임 사이의 실패는 구조적으로 막을 수 없어 로그만 남긴다.</p>
     *
     * <p>임시 파일을 대상과 <b>같은 디렉터리</b>에 만드는 것이 중요하다. 다른 파일시스템(시스템 temp 등)에
     * 두면 원자적 이동이 실패하거나 복사+삭제로 격하되어 원자성이 깨진다.</p>
     *
     * @param sourceStorFileNm 원본 저장 파일명({@code originals} 하위, {uuid}_r{rev}.inp)
     * @param targetFileNms    교체 대상 파일명 목록(경로 없는 순수 파일명)
     * @throws RestApiException 원본이 없으면 {@link InpFileErrorCode#FILE_NOT_FOUND},
     *                          복사/리네임에 실패하면 {@link InpFileErrorCode#FILE_APPLY_ERROR}
     */
    public void applyToTargets(String sourceStorFileNm, List<String> targetFileNms) {
        Path source = storageProperties.resolve(ORIGINAL_SUBDIR).resolve(sourceStorFileNm);
        if (!Files.exists(source)) {
            log.error("적용할 INP 원본 파일을 찾을 수 없음: {}", source.toAbsolutePath());
            throw new RestApiException(InpFileErrorCode.FILE_NOT_FOUND);
        }

        Path baseDir = storageProperties.basePath();
        List<Path> tempPaths = new ArrayList<>(targetFileNms.size());
        try {
            Files.createDirectories(baseDir);

            // 1단계: 대상마다 임시 파일로 복사. 하나라도 실패하면 실제 적용본은 건드리지 않은 채 중단된다.
            for (String targetFileNm : targetFileNms) {
                Path temp = baseDir.resolve(targetFileNm + APPLY_TEMP_SUFFIX);
                Files.copy(source, temp, StandardCopyOption.REPLACE_EXISTING);
                tempPaths.add(temp);
            }

            // 2단계: 복사가 모두 성공했을 때만 리네임으로 갈아끼운다.
            for (int i = 0; i < targetFileNms.size(); i++) {
                Path target = baseDir.resolve(targetFileNms.get(i));
                moveAtomicIfPossible(tempPaths.get(i), target);
                log.info("INP 모델 적용 완료: {} -> {}", sourceStorFileNm, target.toAbsolutePath());
            }
        } catch (IOException e) {
            log.error("INP 모델 적용 실패: source={}, targets={} - {}",
                    sourceStorFileNm, targetFileNms, e.getMessage(), e);
            throw new RestApiException(InpFileErrorCode.FILE_APPLY_ERROR);
        } finally {
            cleanUpTempFiles(tempPaths);
        }
    }

    /**
     * 임시 파일을 대상 파일로 리네임한다(가능하면 원자적으로).
     *
     * <p>같은 파일시스템 안에서는 원자적 이동이 동작한다. 일부 환경에서 지원되지 않으면 원자성 없는
     * 이동으로 한 번 더 시도한다 — 교체가 아예 안 되는 것보다 낫다. 이 경우 해석엔진이 쓰다 만 파일을
     * 읽을 수 있는 짧은 창이 생기므로 경고 로그를 남긴다.</p>
     */
    private void moveAtomicIfPossible(Path temp, Path target) throws IOException {
        try {
            Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException e) {
            log.warn("원자적 교체 미지원 파일시스템 - 비원자적 이동으로 대체한다: {}", target.toAbsolutePath());
            Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    /** 남은 임시 파일을 정리한다(best-effort). 성공 경로에서는 이미 리네임돼 없어진 상태다. */
    private void cleanUpTempFiles(List<Path> tempPaths) {
        for (Path temp : tempPaths) {
            try {
                if (Files.deleteIfExists(temp)) {
                    log.warn("적용 임시 파일 정리: {}", temp.toAbsolutePath());
                }
            } catch (IOException e) {
                log.error("적용 임시 파일 정리 실패(고아 파일 가능): {} - {}", temp.toAbsolutePath(), e.getMessage());
            }
        }
    }
}
