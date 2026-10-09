package com.mindone.editor.inp.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

/**
 * 모델 적용(에디터 → EPANET 해석엔진) 설정 프로퍼티.
 *
 * <p>{@code editor.apply.*} 프로퍼티를 바인딩한다. 적용 시 현재 리비전의 물리 파일을
 * {@code editor.storage.base-path} <b>루트</b>에 여기 지정된 파일명들로 덮어쓴다.
 * epa 컨테이너가 같은 디렉터리를 {@code /app/inp} 로 마운트하고 있어, 파일만 교체하면
 * 재기동 없이 관망해석에 반영된다.</p>
 *
 * <p>따라서 이 값들은 epa 의 {@code config.py} 에 있는 {@code INP_SI_FILE_PATH} /
 * {@code INP_MO_FILE_PATH} 의 파일명과 반드시 일치해야 한다. 어긋나면 적용은 성공하지만
 * 해석엔진은 예전 파일을 계속 읽는다(조용한 무효화).</p>
 *
 * <p>si/mo 를 <b>한 파일</b>로 운영하는 현장(군산)은 두 슬롯에 같은 파일명을 넣으면 된다. 중복은
 * {@code InpFileService.requireApplyTargets} 에서 하나로 접혀 그 파일 하나만 교체된다.</p>
 *
 * @param targetFileNames 교체 대상 파일명 목록 (경로 없는 순수 파일명, 예: gs_inp_si.inp)
 */
@ConfigurationProperties(prefix = "editor.apply")
public record ApplyProperties(List<String> targetFileNames) {
}
