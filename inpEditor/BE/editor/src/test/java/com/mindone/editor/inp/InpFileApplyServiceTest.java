package com.mindone.editor.inp;

import com.mindone.editor.common.domain.YesOrNo;
import com.mindone.editor.inp.config.ApplyProperties;
import com.mindone.editor.inp.domain.InpFile;
import com.mindone.editor.inp.domain.InpFileRevision;
import com.mindone.editor.inp.domain.RevisionWorkType;
import com.mindone.editor.inp.dto.InpFileApplyResponse;
import com.mindone.editor.inp.repository.InpFileRepository;
import com.mindone.editor.inp.repository.InpFileRevisionRepository;
import com.mindone.editor.inp.service.InpFileService;
import com.mindone.editor.inp.storage.InpFileStorage;
import com.mindone.editor.storage.StorageProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * 모델 적용(에디터 → EPANET 해석엔진)의 서비스 계층 단위 검증.
 *
 * <p>관심사는 {@code editor.apply.target-file-names} 설정이 물리 교체로 이어지는 경로다. 특히
 * 시뮬레이션(si)과 모니터링(mo)을 <b>한 파일</b>로 운영하는 현장(군산)이 두 슬롯에 같은 이름을
 * 넣었을 때 정상 동작하는지를 고정한다. 물리 교체의 2단계 리네임은 임시 파일을 소비하므로
 * 중복이 그대로 내려가면 실패한다({@link InpFileApplyStorageTest} 가 그 동작을 문서화).</p>
 *
 * <p>DB 없이 리포지토리를 목으로 대체하고 물리 저장만 임시 디렉터리에 수행한다
 * ({@code InpFileRevisionServiceTest} 와 같은 방식).</p>
 */
class InpFileApplyServiceTest {

    private static final Charset MS949 = Charset.forName("MS949");
    private static final String CONTENT = "[TITLE]\n적용 테스트 모델\n\n[END]\n";
    /** 저장은 운영과 같이 CP949(MS949) 로 한다 - 단정은 디코딩 없이 바이트로 비교한다. */
    private static final byte[] CONTENT_BYTES = CONTENT.getBytes(MS949);

    @TempDir
    Path storageRoot;

    private InpFileRepository repository;
    private InpFileRevisionRepository revisionRepository;
    private InpFileStorage storage;

    @BeforeEach
    void setUp() {
        storage = new InpFileStorage(new StorageProperties(storageRoot));
        repository = mock(InpFileRepository.class);
        revisionRepository = mock(InpFileRevisionRepository.class);
        when(repository.findByMonitoringYn(YesOrNo.Y)).thenReturn(List.of());
    }

    /** 주어진 적용 대상 설정으로 서비스를 만든다. */
    private InpFileService serviceWithTargets(List<String> targetFileNms) {
        return new InpFileService(repository, revisionRepository, storage, new ApplyProperties(targetFileNms));
    }

    /**
     * 현재 적용 리비전(rev1)을 가진 마스터를 만들고 물리 파일까지 준비한 뒤 그 ID 를 돌려준다.
     */
    private InpFile givenAppliableMaster() {
        InpFile master = InpFile.create("관망도.inp", "inp");
        master.applyRevision(1);
        byte[] bytes = CONTENT_BYTES;
        InpFileRevision rev1 = InpFileRevision.create(
                master.getInpFileId(), 1, master.storFileNmForRev(1), bytes.length, null, RevisionWorkType.EDIT);
        storage.store(bytes, rev1.getStorFileNm());
        when(repository.findById(master.getInpFileId())).thenReturn(Optional.of(master));
        when(revisionRepository.findByInpFileIdAndRevNo(master.getInpFileId(), 1)).thenReturn(Optional.of(rev1));
        return master;
    }

    /** 기준 경로 루트에 남아 있는 임시 파일 목록. */
    private List<Path> leftOverTempFiles() throws IOException {
        try (Stream<Path> entries = Files.list(storageRoot)) {
            return entries.filter(path -> path.getFileName().toString().endsWith(".tmp")).toList();
        }
    }

    @Test
    @DisplayName("si/mo 에 같은 파일명을 주면 하나로 접혀 한 파일만 교체되고 적용이 성공한다")
    void duplicateTargetNamesAreFoldedIntoOne() throws IOException {
        InpFile master = givenAppliableMaster();
        // 군산처럼 si/mo 를 한 파일로 운영하는 설정
        InpFileService service = serviceWithTargets(List.of("gs_inp.inp", "gs_inp.inp"));

        InpFileApplyResponse res = service.applyCurrentRevision(master.getInpFileId());

        // 응답과 실제 교체 모두 1건이어야 한다
        assertThat(res.targetFileNms()).containsExactly("gs_inp.inp");
        assertThat(storageRoot.resolve("gs_inp.inp")).exists().hasBinaryContent(CONTENT_BYTES);
        assertThat(leftOverTempFiles()).isEmpty();
        // 적용중 플래그가 대상으로 옮겨진다
        assertThat(master.getMonitoringYn()).isEqualTo(YesOrNo.Y);
    }

    @Test
    @DisplayName("si/mo 파일명이 서로 다르면 둘 다 같은 내용으로 교체된다(고산 회귀)")
    void distinctTargetNamesAreBothReplaced() throws IOException {
        InpFile master = givenAppliableMaster();
        InpFileService service = serviceWithTargets(List.of("gs_inp_si.inp", "gs_inp_mo.inp"));

        InpFileApplyResponse res = service.applyCurrentRevision(master.getInpFileId());

        assertThat(res.targetFileNms()).containsExactly("gs_inp_si.inp", "gs_inp_mo.inp");
        assertThat(storageRoot.resolve("gs_inp_si.inp")).exists().hasBinaryContent(CONTENT_BYTES);
        // si 와 mo 는 언제나 같은 모델이어야 한다
        assertThat(storageRoot.resolve("gs_inp_mo.inp")).exists().hasBinaryContent(CONTENT_BYTES);
        assertThat(leftOverTempFiles()).isEmpty();
    }
}
