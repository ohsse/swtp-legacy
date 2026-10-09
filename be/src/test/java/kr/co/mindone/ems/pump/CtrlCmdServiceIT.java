package kr.co.mindone.ems.pump;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.mybatis.spring.SqlSessionTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 군산 5분 제어 판단 연계(CtrlCmdService) 드라이 테스트.
 *
 * 개발 덤프 DB 에 붙어 가짜 판단 행을 넣고 게이트·적재·승인·거절·마감·APPLIED 판정을 돌린 뒤
 * 테스트마다 롤백한다. 흔적은 남지 않는다.
 *
 * 안전장치
 * - 프로파일 gu2: SchedulerConfig(@Profile("!gu2"))가 빠져 pumpTask 등 스케줄러가 돌지 않는다.
 *   그래서 대기열에 FLAG=0 으로 들어간 행도 Kafka 로 나가지 않는다. Kafka 컨슈머·프로듀서 빈도 gu2 에서는 뜨지 않는다.
 * - datasource 는 환경변수로만 받는다. 기본 gu2 설정은 운영 DB 를 가리키므로, 변수가 없으면 테스트 자체가 건너뛴다.
 * - 벤더 테이블 TB_CTRL_CMD_RST 에 우리가 넣는 행은 이 테스트 트랜잭션 안에서만 존재한다.
 *
 * 실행 (be/ 에서, JDK 11)
 *   CTRL_CMD_IT_DB_URL='jdbc:mariadb://localhost:3306/ems_db?serverTimezone=Asia/Seoul' \
 *   CTRL_CMD_IT_DB_USER=... CTRL_CMD_IT_DB_PASSWORD=... \
 *   ./gradlew test --tests kr.co.mindone.ems.pump.CtrlCmdServiceIT
 *
 * 검증하지 않는 것: Kafka 송신(pumpTask), SCADA 반영, 컨트롤러 HTTP 계층.
 * 설계: docs/gunsan-ctrl-workflow.html, 결정 기록: docs/gunsan-ctrl-cmd-consumer.md
 */
@EnabledIfEnvironmentVariable(named = "CTRL_CMD_IT_DB_URL", matches = ".+")
@SpringBootTest(properties = {
        "spring.profiles.active=gu2",
        "ctrl.cmd.consumer.enabled=true",
        "ctrl.cmd.cycle-min=5",
        "ctrl.cmd.decision-close-sec=20",
        "ctrl.cmd.pump.grp=1",
        // Kafka 는 쓰지 않지만 혹시 연결을 시도해도 닿지 않게 한다
        "spring.kafka.bootstrap-servers=127.0.0.1:9",
        "spring.kafka.bootstrap-servers-1=127.0.0.1:9",
        "spring.kafka.bootstrap-servers-2=127.0.0.1:9"
})
@Transactional
class CtrlCmdServiceIT {

    /** 판단 시점 운전 조합. Python 펌프 번호 = 펌프 마스터 PUMP_IDX (PMB-4017=1 … PMB-4032=4) */
    private static final String COMB = "2,3";
    private static final String[] PMB_TAGS = {"891-365-PMB-4017", "891-365-PMB-4022", "891-365-PMB-4027", "891-365-PMB-4032"};

    @DynamicPropertySource
    static void datasource(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", () -> System.getenv("CTRL_CMD_IT_DB_URL"));
        r.add("spring.datasource.username", () -> System.getenv("CTRL_CMD_IT_DB_USER"));
        r.add("spring.datasource.password", () -> System.getenv("CTRL_CMD_IT_DB_PASSWORD"));
        r.add("spring.datasource.driver-class-name", () -> "org.mariadb.jdbc.Driver");
    }

    @Autowired
    private CtrlCmdService service;

    @Autowired
    private JdbcTemplate jdbc;

    /** 테스트는 한 트랜잭션이라 MyBatis 1차 캐시가 남는다. JDBC 로 바꾼 값을 서비스가 보게 비운다 */
    @Autowired
    private SqlSessionTemplate sqlSession;

    @BeforeEach
    void setUp() {
        // 개발 덤프 DB 를 확인한다. 운영 DB 로 잘못 붙으면 여기서 멈춘다
        String db = jdbc.queryForObject("SELECT DATABASE()", String.class);
        assertTrue(db != null && db.contains("dump"), "개발 덤프 DB 에서만 실행한다: " + db);

        // 추적 테이블: DDL 은 docs/sql/gunsan_ctrl_cmd.sql 과 같다. TEMPORARY 라 커밋 없이 이 연결에만 생긴다
        jdbc.execute("CREATE TEMPORARY TABLE IF NOT EXISTS TB_CTRL_CMD_TRACE ("
                + " TRACE_ID BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,"
                + " CTRL_ID BIGINT UNSIGNED NOT NULL, DEVICE VARCHAR(20) NOT NULL, ACTION VARCHAR(20) NOT NULL,"
                + " REASON VARCHAR(50) DEFAULT NULL, TGT_VALUE DECIMAL(6,2) DEFAULT NULL,"
                + " USER_ID VARCHAR(50) DEFAULT NULL, DETAIL VARCHAR(500) DEFAULT NULL,"
                + " TS DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)");

        // 송신 차단 스위치는 켜 둔다(꺼지면 모든 명령이 TESTMODE_OFF)
        jdbc.update("UPDATE TB_WPP_TAG_CODE SET DEFAULT_VALUE = '1' WHERE FUNC_TYP IN ('TestMode', 'CtrTestMode')");

        // 덤프에는 2024년 원시값뿐이라, 지금 운전 상태를 넣는다: 2·3번 운전, 1·4번 정지
        for (int i = 0; i < PMB_TAGS.length; i++) {
            String value = (i == 1 || i == 2) ? "1" : "0";
            jdbc.update("INSERT INTO TB_RAWDATA (TS, TAGNAME, VALUE) VALUES (NOW(), ?, ?)", PMB_TAGS[i], value);
        }
    }

    @AfterEach
    void tearDown() {
        // 풀로 돌아간 연결에 임시 테이블이 남지 않게 한다
        jdbc.execute("DROP TEMPORARY TABLE IF EXISTS TB_CTRL_CMD_TRACE");
    }

    // ------------------------------------------------------------------
    // AI 운전(0)
    // ------------------------------------------------------------------

    @Test
    void 운전모드_펌프는_적재되고_송신완료시_APPLIED() {
        setMode(0);
        long id = insertCmd(30, true, false);

        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.PUMP, false, null);
        assertEquals("ENQUEUED", o.code, o.message);

        List<Map<String, Object>> q = queue(id, "PUMP");
        assertEquals(2, q.size(), "운전 중인 펌프 2대(2·3번)마다 FREQ 행");
        assertEquals("891-365-PMC-4001", q.get(0).get("TAG"));
        assertEquals("891-365-PMC-4002", q.get(1).get("TAG"));
        for (Map<String, Object> r : q) {
            assertEquals("FREQ", r.get("ANLY_CD"));
            assertEquals("45", r.get("VALUE").toString(), "PUMP_TGT_HZ 45.0 을 정수로 보낸다");
            assertEquals("0", r.get("FLAG").toString());
            assertEquals("0", r.get("AI_STATUS").toString());
        }
        assertEquals("READY", status(id, "PUMP"), "송신 전에는 READY 유지");

        // 송신 중(FLAG 1) 이면 아직 종결하지 않는다
        setQueueFlag(id, "PUMP", "1");
        service.judgeAll();
        assertEquals("READY", status(id, "PUMP"));

        // 송신 완료(FLAG 2) → APPLIED
        setQueueFlag(id, "PUMP", "2");
        service.judgeAll();
        assertEquals("APPLIED", status(id, "PUMP"));
        assertEquals(List.of("ENQUEUE", "APPLY"), traceActions(id));
    }

    @Test
    void 운전모드_대기열에_다른_명령이_있으면_재시도하고_마감되면_EXPIRED() {
        setMode(0);
        write("INSERT INTO TB_HMI_CTR_TAG (CTR_NM, OPT_IDX, TAG, TIME, VALUE, ANLY_CD, FLAG) "
                + "VALUES ('다른명령', 'OTHER', 'X', NOW(), '1', 'FREQ', '0')");
        long id = insertCmd(30, true, false);

        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.PUMP, false, null);
        assertEquals("BUSY", o.code);
        assertEquals("READY", status(id, "PUMP"), "혼잡은 판정이 아니라 재시도");

        // 마감(다음 판단 20초 전)까지 적재하지 못하면 EXPIRED STALE
        ageCmd(id, 290);
        service.judgeAll();
        assertEquals("EXPIRED", status(id, "PUMP"));
        assertEquals("STALE", lastTrace(id).get("REASON"));
    }

    @Test
    void 운전모드_모드전환으로_대기열이_폐기되면_FAILED() {
        setMode(0);
        long id = insertCmd(30, true, false);
        assertEquals("ENQUEUED", service.processDevice(id, CtrlCmdService.PUMP, false, null).code);

        // 모드 전환 시 기존 initCtrTag 가 FLAG 0/1 → 3
        setQueueFlag(id, "PUMP", "3");
        service.judgeAll();
        assertEquals("FAILED", status(id, "PUMP"));
        assertEquals("QUEUE_DISCARDED", lastTrace(id).get("REASON"));
    }

    @Test
    void 운전모드_판단_이후_운전조합이_바뀌면_REJECTED() {
        setMode(0);
        long id = insertCmd(30, true, false);
        write("UPDATE TB_CTRL_CMD_RST SET PUMP_COMB = '1,2' WHERE CTRL_ID = ?", id);

        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.PUMP, false, null);
        assertEquals("REJECTED", o.code);
        assertEquals("PUMP_STATE_CHANGED", o.reason);
        assertTrue(queue(id, "PUMP").isEmpty());
    }

    @Test
    void 운전모드_밸브는_태그가_없으면_REJECTED_있으면_개도_후_하향_CLOSEC_펄스_순서로_적재() {
        setMode(0);
        long noTag = insertCmd(40, false, true);
        CtrlCmdService.Outcome o = service.processDevice(noTag, CtrlCmdService.NATIONAL, false, null);
        assertEquals("REJECTED", o.code);
        assertEquals("TAG_NOT_CONFIGURED", o.reason);

        insertValveTags();
        // insertCmd 는 현재 45 → 목표 40 이므로 하향이다
        long id = insertCmd(30, false, true);
        assertEquals("ENQUEUED", service.processDevice(id, CtrlCmdService.NATIONAL, false, null).code);

        List<Map<String, Object>> q = queue(id, "NATIONAL");
        assertEquals(2, q.size());
        assertEquals("VOP", q.get(0).get("ANLY_CD"));
        assertEquals("TEST-POC-8603", q.get(0).get("TAG"));
        assertEquals("40", q.get(0).get("VALUE").toString(), "NATIONAL_TGT_OPEN 40");
        assertEquals("VPC", q.get(1).get("ANLY_CD"));
        assertEquals("TEST-VVK-8607", q.get(1).get("TAG"), "하향은 CLOSEC");
        assertEquals("1", q.get(1).get("VALUE").toString());

        // 밸브도 송신 완료 시점에 APPLIED (되읽기 대기 없음)
        setQueueFlag(id, "NATIONAL", "2");
        service.judgeAll();
        assertEquals("APPLIED", status(id, "NATIONAL"));
        assertTrue(String.valueOf(lastTrace(id).get("DETAIL")).startsWith("목표 40"), "개도 계측은 기록만");
    }

    @Test
    void 운전모드_밸브_상향은_개도_후_OPENC_펄스() {
        setMode(0);
        insertValveTags();
        long id = insertCmd(30, false, true);
        write("UPDATE TB_CTRL_CMD_RST SET NATIONAL_CUR_OPEN = 35.00 WHERE CTRL_ID = ?", id);
        assertEquals("ENQUEUED", service.processDevice(id, CtrlCmdService.NATIONAL, false, null).code);

        List<Map<String, Object>> q = queue(id, "NATIONAL");
        assertEquals(2, q.size());
        assertEquals("VOP", q.get(0).get("ANLY_CD"));
        assertEquals("40", q.get(0).get("VALUE").toString());
        assertEquals("VPL", q.get(1).get("ANLY_CD"));
        assertEquals("TEST-VVK-8606", q.get(1).get("TAG"), "상향은 OPENC");
    }

    @Test
    void 운전모드_밸브_현재개도가_없으면_REJECTED() {
        setMode(0);
        insertValveTags();
        long id = insertCmd(30, false, true);
        write("UPDATE TB_CTRL_CMD_RST SET NATIONAL_CUR_OPEN = NULL WHERE CTRL_ID = ?", id);
        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.NATIONAL, false, null);
        assertEquals("REJECTED", o.code);
        assertEquals("CUR_OPEN_UNKNOWN", o.reason);
        assertTrue(queue(id, "NATIONAL").isEmpty());
    }

    // ------------------------------------------------------------------
    // 지방산단 밸브 (LOCAL) — 2026-09-30 벤더 드롭으로 부활, 국가산단과 같은 송신 방식
    // ------------------------------------------------------------------

    @Test
    void 운전모드_지방산단은_태그가_없으면_REJECTED_있으면_개도_후_하향_CLOSEC_펄스_순서로_적재() {
        setMode(0);
        long noTag = insertCmd(40, false, false, true);
        CtrlCmdService.Outcome o = service.processDevice(noTag, CtrlCmdService.LOCAL, false, null);
        assertEquals("REJECTED", o.code);
        assertEquals("TAG_NOT_CONFIGURED", o.reason);
        assertEquals("REJECTED", status(noTag, "LOCAL"), "LOCAL_CMD_STATUS 로 되돌려 쓴다");

        insertLocalValveTags();
        // insertCmd 는 현재 98 → 목표 93 이므로 하향이다
        long id = insertCmd(30, false, false, true);
        assertEquals("ENQUEUED", service.processDevice(id, CtrlCmdService.LOCAL, false, null).code);

        List<Map<String, Object>> q = queue(id, "LOCAL");
        assertEquals(2, q.size());
        assertEquals("VOP", q.get(0).get("ANLY_CD"));
        assertEquals("TEST-POC-8602", q.get(0).get("TAG"));
        assertEquals("93", q.get(0).get("VALUE").toString(), "LOCAL_TGT_OPEN 93");
        assertEquals("VPC", q.get(1).get("ANLY_CD"));
        assertEquals("TEST-VVK-8602", q.get(1).get("TAG"), "하향은 CLOSEC");
        assertEquals("1", q.get(1).get("VALUE").toString());
        assertTrue(queue(id, "NATIONAL").isEmpty(), "국가산단 대기열에는 섞이지 않는다");

        setQueueFlag(id, "LOCAL", "2");
        service.judgeAll();
        assertEquals("APPLIED", status(id, "LOCAL"));
        assertTrue(String.valueOf(lastTrace(id).get("DETAIL")).startsWith("목표 93"), "개도 계측은 기록만");
    }

    @Test
    void 운전모드_지방산단_상향은_개도_후_OPENC_펄스() {
        setMode(0);
        insertLocalValveTags();
        long id = insertCmd(30, false, false, true);
        write("UPDATE TB_CTRL_CMD_RST SET LOCAL_CUR_OPEN = 88.00 WHERE CTRL_ID = ?", id);
        assertEquals("ENQUEUED", service.processDevice(id, CtrlCmdService.LOCAL, false, null).code);

        List<Map<String, Object>> q = queue(id, "LOCAL");
        assertEquals(2, q.size());
        assertEquals("VOP", q.get(0).get("ANLY_CD"));
        assertEquals("93", q.get(0).get("VALUE").toString());
        assertEquals("VPL", q.get(1).get("ANLY_CD"));
        assertEquals("TEST-VVK-8601", q.get(1).get("TAG"), "상향은 OPENC");
    }

    @Test
    void 운전모드_지방산단_현재개도가_없으면_REJECTED() {
        setMode(0);
        insertLocalValveTags();
        long id = insertCmd(30, false, false, true);
        write("UPDATE TB_CTRL_CMD_RST SET LOCAL_CUR_OPEN = NULL WHERE CTRL_ID = ?", id);
        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.LOCAL, false, null);
        assertEquals("REJECTED", o.code);
        assertEquals("CUR_OPEN_UNKNOWN", o.reason);
        assertTrue(queue(id, "LOCAL").isEmpty());
    }

    @Test
    void 추천모드_지방산단도_승인대기_목록에_뜬다() {
        setMode(1);
        insertLocalValveTags();
        long id = insertCmd(30, false, false, true);
        assertEquals("PENDING", service.processDevice(id, CtrlCmdService.LOCAL, false, null).code);
        Map<String, Object> item = pendingItem(id, "LOCAL");
        assertNotNull(item, "승인 팝업 목록에 뜬다");
        assertEquals("지방산단 밸브", item.get("DEVICE_NM"));
        assertEquals(98.0, ((Number) item.get("CUR")).doubleValue(), 0.001);
        assertEquals(93.0, ((Number) item.get("TGT")).doubleValue(), 0.001);
    }

    // ------------------------------------------------------------------
    // AI 추천(1)
    // ------------------------------------------------------------------

    @Test
    void 추천모드_소비자는_적재하지_않고_승인대기_승인하면_적재() {
        setMode(1);
        long id = insertCmd(30, true, false);

        assertEquals("PENDING", service.processDevice(id, CtrlCmdService.PUMP, false, null).code);
        assertTrue(queue(id, "PUMP").isEmpty());
        assertEquals("READY", status(id, "PUMP"));

        Map<String, Object> item = pendingItem(id, "PUMP");
        assertNotNull(item, "승인 팝업 목록에 뜬다");
        long remain = ((Number) item.get("REMAIN_SEC")).longValue();
        assertTrue(remain > 240 && remain <= 250, "응답 마감까지 = 280 − 30초 전후: " + remain);

        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.PUMP, true, "tester");
        assertEquals("ENQUEUED", o.code, o.message);
        assertEquals(2, queue(id, "PUMP").size());
        Map<String, Object> t = lastTrace(id);
        assertEquals("APPROVE", t.get("ACTION"));
        assertEquals("tester", t.get("USER_ID"));

        setQueueFlag(id, "PUMP", "2");
        service.judgeAll();
        assertEquals("APPLIED", status(id, "PUMP"));
    }

    @Test
    void 추천모드_거절하면_REJECTED_USER_REJECT() {
        setMode(1);
        long id = insertCmd(30, true, false);

        CtrlCmdService.Outcome o = service.reject(id, CtrlCmdService.PUMP, "tester");
        assertEquals("REJECTED", o.code);
        assertEquals("REJECTED", status(id, "PUMP"));
        Map<String, Object> t = lastTrace(id);
        assertEquals("REJECT", t.get("ACTION"));
        assertEquals("USER_REJECT", t.get("REASON"));
        assertEquals("tester", t.get("USER_ID"));
        assertTrue(queue(id, "PUMP").isEmpty(), "거절은 대기열·송신 로그에 남지 않는다");
    }

    @Test
    void 추천모드_마감_전에는_그대로_마감되면_REJECTED_APPROVE_TIMEOUT() {
        setMode(1);
        long open = insertCmd(270, true, false);
        service.judgeAll();
        assertEquals("READY", status(open, "PUMP"), "270초는 마감(280초) 전");

        ageCmd(open, 290);
        assertNull(pendingItem(open, "PUMP"), "마감된 명령은 팝업에 올리지 않는다");
        service.judgeAll();
        assertEquals("REJECTED", status(open, "PUMP"));
        Map<String, Object> t = lastTrace(open);
        assertEquals("EXPIRE", t.get("ACTION"));
        assertEquals("APPROVE_TIMEOUT", t.get("REASON"));
        assertNull(t.get("USER_ID"), "사람이 한 거절과 구분: 처리자 없음");
    }

    @Test
    void 추천모드_마감_뒤_승인은_거부되고_REJECTED_APPROVE_TIMEOUT() {
        setMode(1);
        long id = insertCmd(285, true, false);

        CtrlCmdService.Outcome o = service.processDevice(id, CtrlCmdService.PUMP, true, "tester");
        assertEquals("REJECTED", o.code);
        assertEquals("APPROVE_TIMEOUT", o.reason);
        assertEquals("REJECTED", status(id, "PUMP"));
        assertTrue(queue(id, "PUMP").isEmpty(), "송신하지 않는다");
    }

    @Test
    void 추천모드가_아니면_승인할_수_없다() {
        setMode(0);
        long id = insertCmd(30, true, false);
        assertEquals("CONFLICT", service.processDevice(id, CtrlCmdService.PUMP, true, "tester").code);
        assertEquals("READY", status(id, "PUMP"));
    }

    // ------------------------------------------------------------------
    // AI 분석(2)
    // ------------------------------------------------------------------

    @Test
    void 분석모드는_보내지_않고_REJECTED_ANALYZE_MODE() {
        setMode(2);
        long id = insertCmd(30, true, true);

        assertEquals("REJECTED", service.processDevice(id, CtrlCmdService.PUMP, false, null).code);
        assertEquals("REJECTED", service.processDevice(id, CtrlCmdService.NATIONAL, false, null).code);
        assertEquals("REJECTED", status(id, "PUMP"));
        assertEquals("REJECTED", status(id, "NATIONAL"));
        assertEquals("ANALYZE_MODE", lastTrace(id).get("REASON"));
        assertTrue(queue(id, "PUMP").isEmpty());
        assertTrue(queue(id, "NATIONAL").isEmpty());
    }

    // ------------------------------------------------------------------
    // 도우미
    // ------------------------------------------------------------------

    /** JDBC 로 쓰고 MyBatis 1차 캐시를 비운다 */
    private void write(String sql, Object... args) {
        jdbc.update(sql, args);
        sqlSession.clearCache();
    }

    /** 현장에서 넣을 밸브 태그 행 (docs/sql/gunsan_ctrl_cmd.sql 2·3절과 같은 모양) */
    private void insertValveTags() {
        write("INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, TAG_GRP, TAG, TAG_KOR_NM, TAG_DSC) "
                + "VALUES ('GSSCADA', 'CtrlCmdTag', '1', 'TEST-POC-8603', '국가산단 밸브 개도 설정', 'NATIONAL_OPEN')");
        write("INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, TAG_GRP, TAG, TAG_KOR_NM, TAG_DSC) "
                + "VALUES ('GSSCADA', 'CtrlCmdTag', '1', 'TEST-VVK-8606', '국가산단 밸브 OPENC 펄스(상향)', 'NATIONAL_PULSE')");
        write("INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, TAG_GRP, TAG, TAG_KOR_NM, TAG_DSC) "
                + "VALUES ('GSSCADA', 'CtrlCmdTag', '1', 'TEST-VVK-8607', '국가산단 밸브 CLOSEC 펄스(하향)', 'NATIONAL_CLOSE_PULSE')");
    }

    /** 지방산단 밸브 태그 행 (2026-09-30 확정 태그 POC-8602 / VVK-8601 / VVK-8602 와 같은 모양) */
    private void insertLocalValveTags() {
        write("INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, TAG_GRP, TAG, TAG_KOR_NM, TAG_DSC) "
                + "VALUES ('GSSCADA', 'CtrlCmdTag', '1', 'TEST-POC-8602', '지방산단 밸브 개도 설정', 'LOCAL_OPEN')");
        write("INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, TAG_GRP, TAG, TAG_KOR_NM, TAG_DSC) "
                + "VALUES ('GSSCADA', 'CtrlCmdTag', '1', 'TEST-VVK-8601', '지방산단 밸브 OPENC 펄스(상향)', 'LOCAL_PULSE')");
        write("INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, TAG_GRP, TAG, TAG_KOR_NM, TAG_DSC) "
                + "VALUES ('GSSCADA', 'CtrlCmdTag', '1', 'TEST-VVK-8602', '지방산단 밸브 CLOSEC 펄스(하향)', 'LOCAL_CLOSE_PULSE')");
    }

    /** AI 운전모드(PumpStatus) 설정: 0 AI / 1 AI 추천 / 2 AI 분석 */
    private void setMode(int mode) {
        write("UPDATE TB_WPP_TAG_CODE SET DEFAULT_VALUE = ? WHERE FUNC_TYP = 'PumpStatus'", String.valueOf(mode));
    }

    /** Python 이 쓰는 모양의 판단 행. 펌프 44 → 45 Hz, 국가산단 45 → 40 %, 지방산단 없음 */
    private long insertCmd(int ageSec, boolean pump, boolean national) {
        return insertCmd(ageSec, pump, national, false);
    }

    /** 지방산단까지 포함한 판단 행. 지방산단은 98 → 93 % (LOCAL_FALLBACK_CLOSE, 5%p 하향) */
    private long insertCmd(int ageSec, boolean pump, boolean national, boolean local) {
        write("INSERT INTO TB_CTRL_CMD_RST (CTRL_TS, CMD_YN, PUMP_COMB,"
                        + " PUMP_CMD_YN, PUMP_CMD_STATUS, PUMP_CUR_HZ, PUMP_TGT_HZ,"
                        + " NATIONAL_CMD_YN, NATIONAL_CMD_STATUS, NATIONAL_CUR_OPEN, NATIONAL_TGT_OPEN,"
                        + " LOCAL_CMD_YN, LOCAL_CMD_STATUS, LOCAL_CUR_OPEN, LOCAL_TGT_OPEN, REASON_CODE)"
                        + " VALUES (NOW() - INTERVAL ? SECOND, 'Y', ?, ?, ?, 44.00, 45.00, ?, ?, 45.00, 40.00, ?, ?, 98.00, 93.00, 'TEST')",
                ageSec, COMB,
                pump ? "Y" : "N", pump ? "READY" : "NO_COMMAND",
                national ? "Y" : "N", national ? "READY" : "NO_COMMAND",
                local ? "Y" : "N", local ? "READY" : "NO_COMMAND");
        return jdbc.queryForObject("SELECT LAST_INSERT_ID()", Long.class);
    }

    private void ageCmd(long id, int ageSec) {
        write("UPDATE TB_CTRL_CMD_RST SET CTRL_TS = NOW() - INTERVAL ? SECOND WHERE CTRL_ID = ?", ageSec, id);
    }

    private String status(long id, String device) {
        return jdbc.queryForObject("SELECT " + device + "_CMD_STATUS FROM TB_CTRL_CMD_RST WHERE CTRL_ID = ?", String.class, id);
    }

    private List<Map<String, Object>> queue(long id, String device) {
        return jdbc.queryForList("SELECT TAG, VALUE, ANLY_CD, FLAG, AI_STATUS FROM TB_HMI_CTR_TAG WHERE OPT_IDX = ? ORDER BY CTR_IDX",
                "CTRL:" + id + ":" + device);
    }

    private void setQueueFlag(long id, String device, String flag) {
        write("UPDATE TB_HMI_CTR_TAG SET FLAG = ? WHERE OPT_IDX = ?", flag, "CTRL:" + id + ":" + device);
    }

    private List<String> traceActions(long id) {
        return jdbc.queryForList("SELECT ACTION FROM TB_CTRL_CMD_TRACE WHERE CTRL_ID = ? ORDER BY TRACE_ID", String.class, id);
    }

    private Map<String, Object> lastTrace(long id) {
        return jdbc.queryForMap("SELECT ACTION, REASON, USER_ID, DETAIL FROM TB_CTRL_CMD_TRACE WHERE CTRL_ID = ? ORDER BY TRACE_ID DESC LIMIT 1", id);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> pendingItem(long id, String device) {
        HashMap<String, Object> res = service.pending();
        for (HashMap<String, Object> item : (List<HashMap<String, Object>>) res.get("items")) {
            if (((Number) item.get("CTRL_ID")).longValue() == id && device.equals(item.get("DEVICE"))) {
                return item;
            }
        }
        return null;
    }
}
