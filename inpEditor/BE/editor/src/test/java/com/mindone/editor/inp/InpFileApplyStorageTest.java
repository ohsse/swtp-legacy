package com.mindone.editor.inp;

import com.mindone.editor.common.exception.RestApiException;
import com.mindone.editor.inp.exception.InpFileErrorCode;
import com.mindone.editor.inp.storage.InpFileStorage;
import com.mindone.editor.storage.StorageProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 모델 적용 시 물리 파일 교체({@link InpFileStorage#applyToTargets}) 단위 테스트.
 *
 * <p>Spring 컨텍스트 없이 컴포넌트를 직접 {@code new} 해서 검증한다(파싱 테스트들과 같은 방식).
 * 검증 포인트는 대상 전부가 원본과 동일한 바이트가 되는지, 기존 적용본을 덮어쓰는지,
 * 임시 파일이 남지 않는지, 원본 결손 시 예외 종류다.</p>
 *
 * <p>이 계층은 <b>대상 목록의 원소가 서로 다르다</b>는 것을 계약으로 삼는다. 중복을 접는 책임은
 * 호출자({@code InpFileService.requireApplyTargets})에 있으며, 그 보장은
 * {@code InpFileApplyServiceTest} 가 검증한다. 여기서는 계약이 깨졌을 때의 동작만 못박아 둔다.</p>
 */
class InpFileApplyStorageTest {

    /** epa 가 읽는 대상 파일명(운영 기본값과 동일하게 si/mo 두 슬롯). */
    private static final List<String> TARGETS = List.of("gs_inp_si.inp", "gs_inp_mo.inp");

    private static final String SOURCE_STOR_FILE_NM = "11111111-2222-3333-4444-555555555555_r3.inp";
    private static final String SOURCE_CONTENT = "[TITLE]\n적용 테스트 모델\n\n[END]\n";

    @TempDir
    Path baseDir;

    private InpFileStorage storage;

    @BeforeEach
    void setUp() {
        storage = new InpFileStorage(new StorageProperties(baseDir));
    }

    /** originals 하위에 원본 리비전 파일을 만들어 둔다. */
    private void givenSourceRevision() throws IOException {
        Path originals = baseDir.resolve("originals");
        Files.createDirectories(originals);
        Files.writeString(originals.resolve(SOURCE_STOR_FILE_NM), SOURCE_CONTENT, StandardCharsets.UTF_8);
    }

    /** 기준 경로 루트에 남아 있는 임시 파일 목록. */
    private List<Path> leftOverTempFiles() throws IOException {
        try (Stream<Path> entries = Files.list(baseDir)) {
            return entries.filter(path -> path.getFileName().toString().endsWith(".tmp")).toList();
        }
    }

    @Test
    @DisplayName("대상 두 슬롯이 모두 원본과 동일한 바이트로 교체되고 임시 파일은 남지 않는다")
    void appliesSourceToAllTargets() throws IOException {
        givenSourceRevision();

        storage.applyToTargets(SOURCE_STOR_FILE_NM, TARGETS);

        for (String target : TARGETS) {
            assertThat(baseDir.resolve(target))
                    .as("대상 파일 %s", target)
                    .exists()
                    .hasContent(SOURCE_CONTENT);
        }
        // si 와 mo 는 언제나 같은 모델이어야 한다.
        assertThat(baseDir.resolve(TARGETS.get(0))).hasSameTextualContentAs(baseDir.resolve(TARGETS.get(1)));
        assertThat(leftOverTempFiles()).isEmpty();
    }

    @Test
    @DisplayName("이미 적용본이 있어도 덮어쓴다")
    void overwritesExistingTargets() throws IOException {
        givenSourceRevision();
        for (String target : TARGETS) {
            Files.writeString(baseDir.resolve(target), "[TITLE]\n예전 모델\n", StandardCharsets.UTF_8);
        }

        storage.applyToTargets(SOURCE_STOR_FILE_NM, TARGETS);

        for (String target : TARGETS) {
            assertThat(baseDir.resolve(target)).hasContent(SOURCE_CONTENT);
        }
        assertThat(leftOverTempFiles()).isEmpty();
    }

    @Test
    @DisplayName("연속 적용해도 임시 파일이 누적되지 않는다")
    void repeatedApplyLeavesNoTempFiles() throws IOException {
        givenSourceRevision();

        storage.applyToTargets(SOURCE_STOR_FILE_NM, TARGETS);
        storage.applyToTargets(SOURCE_STOR_FILE_NM, TARGETS);

        assertThat(leftOverTempFiles()).isEmpty();
    }

    @Test
    @DisplayName("대상 이름이 중복이면 FILE_APPLY_ERROR 다 - 중복을 접는 책임은 호출자에 있다")
    void duplicateTargetsAreNotHandledHere() throws IOException {
        givenSourceRevision();
        List<String> duplicated = List.of("gs_inp.inp", "gs_inp.inp");

        // 1단계 복사는 멱등이라 통과하지만, 2단계는 임시 파일을 리네임으로 소비하므로
        // 두 번째 이동에서 NoSuchFileException 이 나 FILE_APPLY_ERROR 로 바뀐다.
        assertThatThrownBy(() -> storage.applyToTargets(SOURCE_STOR_FILE_NM, duplicated))
                .isInstanceOf(RestApiException.class)
                .extracting(e -> ((RestApiException) e).getErrorCode())
                .isEqualTo(InpFileErrorCode.FILE_APPLY_ERROR);

        // 첫 대상 교체는 이미 디스크에 반영된 뒤라 되돌려지지 않는다(트랜잭션 롤백과 어긋나는 지점).
        // 서비스가 중복을 접어야 하는 이유를 여기서 못박아 둔다.
        assertThat(baseDir.resolve("gs_inp.inp")).exists().hasContent(SOURCE_CONTENT);
        assertThat(leftOverTempFiles()).isEmpty();
    }

    @Test
    @DisplayName("원본 리비전 파일이 없으면 FILE_NOT_FOUND 이고 기존 적용본은 그대로 남는다")
    void throwsWhenSourceMissing() throws IOException {
        Files.writeString(baseDir.resolve(TARGETS.get(0)), "[TITLE]\n예전 모델\n", StandardCharsets.UTF_8);

        assertThatThrownBy(() -> storage.applyToTargets(SOURCE_STOR_FILE_NM, TARGETS))
                .isInstanceOf(RestApiException.class)
                .extracting(e -> ((RestApiException) e).getErrorCode())
                .isEqualTo(InpFileErrorCode.FILE_NOT_FOUND);

        // 원본을 못 찾으면 아무것도 건드리지 않아야 한다.
        assertThat(baseDir.resolve(TARGETS.get(0))).hasContent("[TITLE]\n예전 모델\n");
        assertThat(leftOverTempFiles()).isEmpty();
    }
}
