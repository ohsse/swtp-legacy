-- TB_PUMP_CAL 지표 컬럼 추가 (inp Editor 성능곡선 평가지표 저장용)
--
-- [Flyway 미관리] 이 스크립트는 Flyway 마이그레이션이 아니다. 모든 프로파일이 flyway.enabled: false 이고,
--   군산 운영은 폐쇄망이라 DDL 을 수작업으로 적용한다.
--   적용 순서: 군산 개발(localhost / ems_db) → 검증 → 군산 운영(localhost / EMS_DB)
--
-- [적용 시점] 반드시 애플리케이션 배포 "전"에 적용한다. TB_PUMP_CAL 은 JPA 엔티티가 아니라 네이티브 쿼리
--   대상이라 ddl-auto: validate 가 기동 시 컬럼 부재를 잡아주지 못하고, 사용자가 화면을 여는 시점에
--   Unknown column 으로 실패한다.
--
-- [저장 단위] 지표는 조합(PUMP_GRP, C_IDX) 단위 값이므로 C_ORD=1·2 두 행에 동일한 값이 저장된다.
--
-- [run_minutes] BE 는 이 컬럼을 읽기만 하고 쓰지 않는다(성능곡선 저장 SQL 에 포함되지 않음).
--   적재 주체는 외부 EMS/AI 프로세스이며, 적재 전까지 값은 NULL 이다.
ALTER TABLE TB_PUMP_CAL
    ADD COLUMN IF NOT EXISTS avg_error_rate  DOUBLE DEFAULT NULL COMMENT '평균오차(율)',
    ADD COLUMN IF NOT EXISTS power_unit      DOUBLE DEFAULT NULL COMMENT '전력원단위',
    ADD COLUMN IF NOT EXISTS power_cost_unit DOUBLE DEFAULT NULL COMMENT '전력비원단위',
    ADD COLUMN IF NOT EXISTS data_count      INT    DEFAULT NULL COMMENT '데이터수(성능곡선 회귀에 쓰인 실측 표본 수)',
    ADD COLUMN IF NOT EXISTS run_minutes     BIGINT DEFAULT NULL COMMENT '운영건수(분)';
