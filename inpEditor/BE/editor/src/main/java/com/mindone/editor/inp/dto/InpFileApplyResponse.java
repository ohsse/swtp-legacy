package com.mindone.editor.inp.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

/**
 * INP 파일 적용 결과.
 *
 * <p>적용은 현재 적용 리비전의 물리 파일을 스토리지 기준 경로 루트의 고정 대상 파일명들로 교체하는 작업이다.
 * 대상 파일명은 {@code editor.apply.target-file-names} 설정에서 온다.</p>
 *
 * @param inpFileId        INP 파일 ID
 * @param revNo            적용한 현재 리비전 번호
 * @param sourceStorFileNm originals 하위 원본 저장 파일명
 * @param targetFileNms    EPA 가 읽는 고정 대상 파일명 목록
 * @param fileSz           적용 후 파일 크기
 */
public record InpFileApplyResponse(
        @Schema(description = "INP 파일 ID") String inpFileId,
        @Schema(description = "적용한 현재 리비전 번호") int revNo,
        @Schema(description = "originals 하위 원본 저장 파일명") String sourceStorFileNm,
        @Schema(description = "EPA 고정 대상 파일명 목록") List<String> targetFileNms,
        @Schema(description = "적용 후 파일 크기") long fileSz
) {
}
