package kr.co.mindone.ems.pump;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 군산 5분 제어 판단(TB_CTRL_CMD_RST) → 제어명령 대기열(TB_HMI_CTR_TAG) 연계 서비스.
 *
 * 벤더 계약: *_CMD_YN = 'Y' 이면 PUMP_TGT_HZ / NATIONAL_TGT_OPEN / LOCAL_TGT_OPEN 을 제어값으로 송신한다.
 * 장치는 셋이다: 송수펌프(PUMP, Hz) · 국가산단 분기밸브(NATIONAL, %) · 지방산단 분기밸브(LOCAL, %).
 * 지방산단은 2026-09-30 벤더 드롭에서 나운 고수위 최종(fallback) 제어로 부활했고, 같은 날 제어 대상으로 확정했다.
 * 처리 결과는 벤더 테이블 *_CMD_STATUS 에 되돌려 쓴다(READY → APPLIED/REJECTED/FAILED/EXPIRED).
 * 벤더 13:28 판은 APPLIED 만 "실제 제어"로 보고 다음 5분을 HOLD 한다(get_last_applied_device_command).
 * 그래서 송신 완료 즉시 APPLIED 를 써야 하고, 미처리 명령은 다음 판단 전에 종결한다(추천 무응답은 REJECTED).
 *
 * 설계: docs/gunsan-ctrl-workflow.html
 */
@Slf4j
@Service
public class CtrlCmdService {

    public static final String PUMP = "PUMP";
    public static final String NATIONAL = "NATIONAL";
    public static final String LOCAL = "LOCAL";

    public static final String READY = "READY";
    public static final String APPLIED = "APPLIED";
    public static final String REJECTED = "REJECTED";
    public static final String FAILED = "FAILED";
    public static final String EXPIRED = "EXPIRED";

    /** 대기열 구분 코드: 밸브 개도 설정 */
    public static final String ANLY_VALVE_OPEN = "VOP";
    /** 대기열 구분 코드: 밸브 OPENC 펄스, 개도 상향 (기존 VVK 는 군산에서 FLAG 를 되돌리지 않아 분리) */
    public static final String ANLY_VALVE_PULSE = "VPL";
    /** 대기열 구분 코드: 밸브 CLOSEC 펄스, 개도 하향 */
    public static final String ANLY_VALVE_PULSE_CLOSE = "VPC";

    /**
     * 처리 장치 순서. 펌프 먼저, 밸브 다음(같은 판단 행의 대기열 행은 서로를 막지 않는다).
     * 장치명이 곧 벤더 컬럼 접두({DEVICE}_CMD_YN…)이자 태그 키 접두({DEVICE}_OPEN…)이자 대기열 OPT_IDX 꼬리다.
     */
    public static final List<String> DEVICES = Collections.unmodifiableList(Arrays.asList(PUMP, NATIONAL, LOCAL));

    @Autowired
    private CtrlCmdMapper ctrlCmdMapper;

    @Autowired
    private PumpMapper pumpMapper;

    @Autowired
    private PumpService pumpService;

    /** judgeAll 은 같은 빈 안에서 돌아 @Transactional 프록시를 못 탄다. 잠금이 필요한 구간만 이걸로 감싼다 */
    private TransactionTemplate txTemplate;

    @Autowired
    public void setTransactionManager(PlatformTransactionManager transactionManager) {
        this.txTemplate = new TransactionTemplate(transactionManager);
    }

    /** 소비자 마스터 스위치. gu 에서만 true */
    @Value("${ctrl.cmd.consumer.enabled:false}")
    private boolean consumerEnabled;

    /**
     * 판단 마감 여유(초). 판단은 다음 벤더 판단 이 시간 전에 마감한다(:00 판단 → :04:40).
     * 반영 판정(15·45초)이 Python :05 실행 전에 종결하도록 20초를 둔다.
     */
    @Value("${ctrl.cmd.decision-close-sec:20}")
    private int closeSec;

    /** 대기열에 넣은 뒤 송신이 끝나지 않으면 실패로 보는 시간(분) */
    @Value("${ctrl.cmd.queue-timeout-min:15}")
    private int queueTimeoutMin;

    @Value("${ctrl.cmd.pump.grp:1}")
    private String pumpGrp;

    @Value("${ctrl.cmd.pump.hz-min:35}")
    private double pumpHzMin;

    @Value("${ctrl.cmd.pump.hz-max:50}")
    private double pumpHzMax;

    /** 벤더 판단 주기(분). 판단 마감 시각과 승인 팝업의 "응답 마감까지" 계산에 쓴다 */
    @Value("${ctrl.cmd.cycle-min:5}")
    private int cycleMin;

    /** 국가산단 밸브 개도 계측 태그(APPLIED 시 기록용). Python 이 NATIONAL_CUR_OPEN 으로 읽는 태그와 같다 */
    @Value("${ctrl.cmd.valve.national.readback-tag:891-365-POI-8601}")
    private String nationalReadbackTag;

    /** 지방산단 밸브 개도 계측 태그(APPLIED 시 기록용). Python 이 LOCAL_CUR_OPEN 으로 읽는 태그와 같다 */
    @Value("${ctrl.cmd.valve.local.readback-tag:891-365-POI-8600}")
    private String localReadbackTag;

    @Value("${ctrl.cmd.alarm.interval-min:60}")
    private int alarmIntervalMin;

    /** 같은 사유 알람의 마지막 발생 시각 (시간당 1회 제한) */
    private final Map<String, Long> lastAlarmAt = new ConcurrentHashMap<>();

    // ------------------------------------------------------------------
    // 결과 객체
    // ------------------------------------------------------------------

    /** 처리 결과. code 는 ENQUEUED / PENDING / BUSY / SKIPPED / REJECTED / EXPIRED / CONFLICT */
    public static class Outcome {
        public final String code;
        public final String reason;
        public final String message;

        Outcome(String code, String reason, String message) {
            this.code = code;
            this.reason = reason;
            this.message = message;
        }

        public HashMap<String, Object> toMap() {
            HashMap<String, Object> m = new HashMap<>();
            m.put("result", code);
            m.put("reason", reason);
            m.put("reasonLabel", reason == null ? null : reasonLabel(reason));
            m.put("message", message);
            return m;
        }
    }

    /** 게이트 판정. kind 가 null 이면 통과이며 rows 에 적재할 대기열 행이 있다 */
    private static class Gate {
        String kind;      // REJECTED / EXPIRED / null
        String reason;
        List<HashMap<String, Object>> rows = new ArrayList<>();
    }

    // ------------------------------------------------------------------
    // 소비자 · 승인 · 거절
    // ------------------------------------------------------------------

    public boolean isConsumerEnabled() {
        return consumerEnabled;
    }

    /**
     * 펌프 제어가 이 경로로 넘어왔는지. true 면 기존 조합 생성기(pumpAiControlTask)를 건너뛴다.
     * 운전·추천·분석 여부는 AI 운전모드(TB_WPP_TAG_CODE PumpStatus) 하나로 정하므로 여기서는 소비자 스위치만 본다.
     */
    public boolean isPumpControlActive() {
        return consumerEnabled;
    }

    /** 처리 대상 판단 행 (명령 있음 + READY 장치 포함) */
    public List<HashMap<String, Object>> selectReadyCmdList(int lookbackMin) {
        HashMap<String, Object> p = new HashMap<>();
        p.put("LOOKBACK_MIN", lookbackMin);
        return ctrlCmdMapper.selectReadyCmdList(p);
    }

    /** 처리 대상 판단 행 조회 범위(분). 마감은 한 주기 안이므로 두 주기면 충분하다 */
    public int getLookbackMin() {
        return cycleMin * 2;
    }

    /**
     * 판단 행의 한 장치를 처리한다. 스케줄러(approve=false)와 승인 API(approve=true)가 같이 쓴다.
     * 행을 FOR UPDATE 로 잠그므로 둘이 동시에 와도 한쪽만 적재한다.
     */
    @Transactional
    public Outcome processDevice(long ctrlId, String device, boolean approve, String userId) {
        if (!consumerEnabled) {
            return new Outcome("CONFLICT", null, "제어 판단 연계가 꺼져 있습니다. (ctrl.cmd.consumer.enabled)");
        }
        if (!DEVICES.contains(device)) {
            return new Outcome("CONFLICT", null, "알 수 없는 장치입니다: " + device);
        }
        HashMap<String, Object> row = lockRow(ctrlId);
        if (row == null) {
            return new Outcome("CONFLICT", null, "판단 결과를 찾을 수 없습니다.");
        }
        if (!"Y".equals(str(row, device + "_CMD_YN"))) {
            return new Outcome("CONFLICT", null, "이 장치에는 제어 명령이 없습니다.");
        }
        String status = str(row, device + "_CMD_STATUS");
        if (!READY.equals(status)) {
            return new Outcome("CONFLICT", null, "이미 처리된 명령입니다. (" + status + ")");
        }
        String optIdx = optIdx(ctrlId, device);
        if (!ctrlCmdMapper.selectQueueByOptIdx(param("OPT_IDX", optIdx)).isEmpty()) {
            return new Outcome(approve ? "CONFLICT" : "SKIPPED", null, "이미 대기열에 등록된 명령입니다.");
        }

        int mode = pumpService.getAiControlStatus();
        if (approve && mode != PumpService.AI_RECOMMEND) {
            return new Outcome("CONFLICT", null, "AI 추천 모드가 아니어서 승인할 수 없습니다.");
        }

        Gate gate = evaluate(row, device, mode);
        if (gate.kind != null) {
            transition(ctrlId, device, gate.kind, gate.reason, closeAction(gate.kind, gate.reason), userId, row, null);
            if ("TAG_NOT_CONFIGURED".equals(gate.reason)) {
                alarm(device + ":" + gate.reason, "[" + deviceLabel(device) + "] 제어 태그가 설정되지 않아 AI 제어 명령을 보내지 못했습니다.");
            }
            return new Outcome(gate.kind, gate.reason, reasonLabel(gate.reason));
        }

        if (mode == PumpService.AI_RECOMMEND && !approve) {
            return new Outcome("PENDING", null, "승인 대기");
        }

        if (ctrlCmdMapper.countForeignActiveQueue(param("CTRL_ID", ctrlId)) > 0) {
            // READY 를 유지해 다음 주기에 재시도한다. 신선도가 먼저 끝나면 만료된다.
            return new Outcome("BUSY", null, "다른 제어 명령이 진행 중입니다. 잠시 후 다시 시도하세요.");
        }

        String now = pumpService.nowStringDate();
        StringBuilder detail = new StringBuilder();
        for (HashMap<String, Object> q : gate.rows) {
            HashMap<String, Object> item = new HashMap<>(q);
            item.put("OPT_IDX", optIdx);
            item.put("TIME", now);
            item.put("FLAG", 0);
            item.put("AI_STATUS", mode);
            pumpMapper.insertHmiTag(item);
            detail.append(q.get("ANLY_CD")).append(' ').append(q.get("TAG")).append('=').append(q.get("VALUE")).append("; ");
        }
        trace(ctrlId, device, approve ? "APPROVE" : "ENQUEUE", null, tgt(row, device), userId, detail.toString());
        log.info("[CtrlCmd] 적재 CTRL_ID={} {} {}", ctrlId, device, detail);
        return new Outcome("ENQUEUED", null, "제어 명령이 대기열에 등록되었습니다.");
    }

    /** 사용자 거절. 모드와 무관하게 아직 적재되지 않은 READY 만 거절할 수 있다 */
    @Transactional
    public Outcome reject(long ctrlId, String device, String userId) {
        if (!consumerEnabled) {
            return new Outcome("CONFLICT", null, "제어 판단 연계가 꺼져 있습니다. (ctrl.cmd.consumer.enabled)");
        }
        if (!DEVICES.contains(device)) {
            return new Outcome("CONFLICT", null, "알 수 없는 장치입니다: " + device);
        }
        HashMap<String, Object> row = lockRow(ctrlId);
        if (row == null || !"Y".equals(str(row, device + "_CMD_YN")) || !READY.equals(str(row, device + "_CMD_STATUS"))) {
            return new Outcome("CONFLICT", null, "이미 처리되었거나 명령이 없습니다.");
        }
        if (!ctrlCmdMapper.selectQueueByOptIdx(param("OPT_IDX", optIdx(ctrlId, device))).isEmpty()) {
            return new Outcome("CONFLICT", null, "이미 송신 중인 명령은 거절할 수 없습니다.");
        }
        transition(ctrlId, device, REJECTED, "USER_REJECT", "REJECT", userId, row, null);
        return new Outcome(REJECTED, "USER_REJECT", "명령을 거절했습니다.");
    }

    // ------------------------------------------------------------------
    // 반영 판정 (30초)
    // ------------------------------------------------------------------

    /**
     * READY 장치의 대기열 상태를 보고 APPLIED / FAILED / EXPIRED 로 종결한다.
     * 상태 UPDATE 는 "READY 일 때만" 조건이 걸려 있어 잠금 없이도 중복 전이가 없다.
     */
    public void judgeAll() {
        int lookback = Math.max(getLookbackMin(), queueTimeoutMin) + 30;
        for (HashMap<String, Object> row : selectReadyCmdList(lookback)) {
            long ctrlId = toLong(row.get("CTRL_ID"));
            for (String device : DEVICES) {
                if (!"Y".equals(str(row, device + "_CMD_YN")) || !READY.equals(str(row, device + "_CMD_STATUS"))) {
                    continue;
                }
                try {
                    judgeDevice(ctrlId, device, row);
                } catch (Exception e) {
                    log.error("[CtrlCmd] 반영 판정 실패 CTRL_ID={} {}: {}", ctrlId, device, e.getMessage(), e);
                }
            }
        }
    }

    private void judgeDevice(long ctrlId, String device, HashMap<String, Object> row) {
        String optIdx = optIdx(ctrlId, device);
        List<HashMap<String, Object>> queue = ctrlCmdMapper.selectQueueByOptIdx(param("OPT_IDX", optIdx));

        if (queue.isEmpty()) {
            // 적재 전(승인 대기 포함) 명령의 만료만 여기서 앞당겨 처리한다.
            // 승인·소비자가 같은 행을 FOR UPDATE 로 잡고 적재 중일 수 있으므로,
            // 행을 잠근 뒤 READY 와 "대기열 없음"을 다시 확인하고 전이한다.
            if (staleReason(row, device) != null) {
                txTemplate.executeWithoutResult(status -> expireIfIdle(ctrlId, device));
            }
            return;
        }

        boolean anyDiscarded = false;
        boolean allDone = true;
        long oldestRgstrAge = 0;
        String sentOpen = null;
        for (HashMap<String, Object> q : queue) {
            String flag = str(q, "FLAG");
            if ("3".equals(flag)) {
                anyDiscarded = true;
            }
            if (!"2".equals(flag)) {
                allDone = false;
            }
            oldestRgstrAge = Math.max(oldestRgstrAge, toLong(q.get("RGSTR_AGE_SEC")));
            if (ANLY_VALVE_OPEN.equals(str(q, "ANLY_CD"))) {
                sentOpen = str(q, "VALUE");
            }
        }

        if (anyDiscarded) {
            ctrlCmdMapper.discardQueueRows(param("OPT_IDX", optIdx));
            transition(ctrlId, device, FAILED, "QUEUE_DISCARDED", "FAIL", null, row, "대기열 폐기(모드 전환 등)");
            return;
        }

        if (!allDone) {
            if (oldestRgstrAge > queueTimeoutMin * 60L) {
                ctrlCmdMapper.discardQueueRows(param("OPT_IDX", optIdx));
                transition(ctrlId, device, FAILED, "QUEUE_TIMEOUT", "FAIL", null, row, "송신 미완료 " + oldestRgstrAge + "초");
            }
            return;
        }

        // 송신 완료(묶음 전부 FLAG=2) 시점에 APPLIED. 벤더는 APPLIED 만 "실제 제어"로 보고
        // 다음 5분 판단에서 HOLD 를 거므로, 되읽기를 기다리면 그 판단보다 늦어 이중 제어가 날 수 있다.
        // 제어 효과(유량·수위 추세) 확인은 벤더 response_ok_* 가 한다.
        String detail = null;
        if (!PUMP.equals(device)) {
            // 밸브 개도 계측은 기록용으로만 남긴다
            HashMap<String, Object> raw = latestRaw(readbackTag(device), 5);
            detail = "목표 " + sentOpen + " / 계측 " + (raw == null ? "-" : str(raw, "VALUE") + " @" + str(raw, "TS"));
        }
        transition(ctrlId, device, APPLIED, null, "APPLY", null, row, detail);
    }

    /**
     * 행을 잠근 뒤 여전히 READY·미적재·마감 경과면 종결한다. 트랜잭션 안에서만 부른다.
     * 추천 모드 무응답은 REJECTED(APPROVE_TIMEOUT), 그 밖은 EXPIRED — 다음 판단(:05) 전에 끝낸다.
     */
    private void expireIfIdle(long ctrlId, String device) {
        HashMap<String, Object> row = lockRow(ctrlId);
        if (row == null || !READY.equals(str(row, device + "_CMD_STATUS"))) {
            return;
        }
        if (!ctrlCmdMapper.selectQueueByOptIdx(param("OPT_IDX", optIdx(ctrlId, device))).isEmpty()) {
            return;
        }
        String stale = staleReason(row, device);
        if (stale != null) {
            Gate g = closeStale(new Gate(), pumpService.getAiControlStatus(), stale);
            transition(ctrlId, device, g.kind, g.reason, closeAction(g.kind, g.reason), null, row, null);
        }
    }

    // ------------------------------------------------------------------
    // 화면 조회
    // ------------------------------------------------------------------

    /** 최신 판단 1건 + 장치별 진행 상태 */
    public HashMap<String, Object> latest() {
        HashMap<String, Object> res = new HashMap<>();
        res.put("mode", pumpService.getAiControlStatus());
        res.put("consumerEnabled", consumerEnabled);
        HashMap<String, Object> row = ctrlCmdMapper.selectLatestCmd();
        res.put("cmd", row == null ? null : decorate(row, true));
        return res;
    }

    /** 승인 대기 목록 + 모드 전환 확인창에 쓸 개수 */
    public HashMap<String, Object> pending() {
        int mode = pumpService.getAiControlStatus();
        List<HashMap<String, Object>> items = new ArrayList<>();
        for (HashMap<String, Object> row : selectReadyCmdList(getLookbackMin())) {
            long ctrlId = toLong(row.get("CTRL_ID"));
            for (String device : DEVICES) {
                if (!"Y".equals(str(row, device + "_CMD_YN")) || !READY.equals(str(row, device + "_CMD_STATUS"))) {
                    continue;
                }
                if (!ctrlCmdMapper.selectQueueByOptIdx(param("OPT_IDX", optIdx(ctrlId, device))).isEmpty()) {
                    continue;
                }
                // 화면 폴링은 원시데이터 조회(운전 펌프 확인)를 건너뛴다. 승인 시 전체 게이트를 다시 돈다
                Gate gate = evaluate(row, device, mode, false);
                // 마감된 명령은 곧 판정이 종결하므로 팝업에 올리지 않는다
                if (EXPIRED.equals(gate.kind) || "APPROVE_TIMEOUT".equals(gate.reason)) {
                    continue;
                }
                HashMap<String, Object> item = new HashMap<>();
                item.put("CTRL_ID", ctrlId);
                item.put("CTRL_TS", row.get("CTRL_TS"));
                item.put("DEVICE", device);
                item.put("DEVICE_NM", deviceLabel(device));
                item.put("PUMP_COMB", row.get("PUMP_COMB"));
                item.put("CUR", cur(row, device));
                item.put("TGT", tgt(row, device));
                item.put("REMAIN_SEC", remainSec(toLong(row.get("AGE_SEC"))));
                item.put("BLOCK_REASON", gate.kind == null ? null : gate.reason);
                item.put("BLOCK_REASON_LABEL", gate.kind == null ? null : reasonLabel(gate.reason));
                item.put("REASONS", reasonList(str(row, "REASON_CODE")));
                items.add(item);
            }
        }
        HashMap<String, Object> map = new HashMap<>();
        HashMap<String, Object> res = new HashMap<>();
        res.put("mode", mode);
        res.put("items", items);
        res.put("consumerEnabled", consumerEnabled);
        // 화면은 이 값이 true 일 때 군산의 기존 10분 예측비교 팝업(조합 변경 승인)을 띄우지 않는다
        res.put("pumpControlActive", isPumpControlActive());
        map.put("FLAG", 0);
        int waiting = pumpMapper.selectCtrTagList(map).size();
        map.put("FLAG", 1);
        int running = pumpMapper.selectCtrTagList(map).size();
        res.put("queueActiveCount", waiting + running);
        return res;
    }

    /** 승인 응답 마감까지 남은 시간(초). 마감은 다음 벤더 판단 closeSec 초 전이다 */
    private long remainSec(long ageSec) {
        return Math.max(0, decisionCloseAgeSec() - ageSec);
    }

    /** 판단 이력 (기간) + 처리 추적 */
    public List<HashMap<String, Object>> history(String from, String to, boolean cmdOnly) {
        HashMap<String, Object> p = new HashMap<>();
        p.put("FROM", from);
        p.put("TO", to);
        p.put("CMD_ONLY", cmdOnly ? "Y" : "N");
        List<HashMap<String, Object>> rows = ctrlCmdMapper.selectCmdHistory(p);
        Map<Long, List<HashMap<String, Object>>> traces = loadTraces(rows);
        List<HashMap<String, Object>> out = new ArrayList<>();
        for (HashMap<String, Object> row : rows) {
            HashMap<String, Object> d = decorate(row, false);
            d.put("TRACE", traces.getOrDefault(toLong(row.get("CTRL_ID")), Collections.emptyList()));
            out.add(d);
        }
        return out;
    }

    // ------------------------------------------------------------------
    // 게이트
    // ------------------------------------------------------------------

    /**
     * 모드·신선도·테스트모드·값 범위·스위치·태그·운전펌프를 순서대로 검사한다.
     * 대기열 혼잡(BUSY)은 여기서 보지 않는다 — 재시도 대상이지 판정이 아니다.
     */
    private Gate evaluate(HashMap<String, Object> row, String device, int mode) {
        return evaluate(row, device, mode, true);
    }

    /**
     * 게이트 순서는 docs/gunsan-ctrl-workflow.html 6장과 같다:
     * 모드 → 테스트모드 → 신선도 → 값 범위 → 태그 → 운전 펌프 일치.
     * 모드는 AI 운전모드(PumpStatus) 하나로 정한다. 장치별 별도 스위치는 두지 않는다.
     * checkPumpState=false 면 원시데이터를 읽는 마지막 검사를 건너뛴다(화면 폴링용 사전검사).
     */
    private Gate evaluate(HashMap<String, Object> row, String device, int mode, boolean checkPumpState) {
        Gate g = new Gate();
        if (mode == PumpService.AI_ANALYZE) {
            return fail(g, REJECTED, "ANALYZE_MODE");
        }
        if (!pumpService.checkTestMode() || !pumpService.checkCtrTestMode()) {
            return fail(g, REJECTED, "TESTMODE_OFF");
        }
        String stale = staleReason(row, device);
        if (stale != null) {
            return closeStale(g, mode, stale);
        }
        Double target = tgt(row, device);
        if (target == null) {
            return fail(g, REJECTED, "OUT_OF_RANGE");
        }
        if (PUMP.equals(device)) {
            long hz = Math.round(target);
            // 기존 발행 조건(value >= 25, PumpService.pumpCommandTask)과 자동제어 범위를 함께 본다
            if (hz < Math.max(25, pumpHzMin) || hz > pumpHzMax) {
                return fail(g, REJECTED, "OUT_OF_RANGE");
            }
        } else {
            long open = Math.round(target);
            if (open < 0 || open > 100) {
                return fail(g, REJECTED, "OUT_OF_RANGE");
            }
        }
        return PUMP.equals(device) ? evaluatePump(g, row, target, checkPumpState) : evaluateValve(g, loadTagConfig(), device, target, cur(row, device));
    }

    private Gate evaluatePump(Gate g, HashMap<String, Object> row, double target, boolean checkPumpState) {
        long hz = Math.round(target);
        List<HashMap<String, Object>> masters = ctrlCmdMapper.selectPumpMaster(param("PUMP_GRP", pumpGrp));
        if (!checkPumpState) {
            // 사전검사: 판단 시점 조합(PUMP_COMB)의 펌프에 쓰기 태그가 있는지만 본다
            TreeSet<Integer> comb = parseComb(str(row, "PUMP_COMB"));
            for (HashMap<String, Object> m : masters) {
                String tag = str(m, "CTR_AUTO_FREQ_TAG");
                if (comb.contains((int) toLong(m.get("PUMP_IDX"))) && (tag == null || tag.trim().isEmpty())) {
                    return fail(g, REJECTED, "TAG_NOT_CONFIGURED");
                }
            }
            return g;
        }
        TreeSet<Integer> running = new TreeSet<>();
        List<HashMap<String, Object>> runningMasters = new ArrayList<>();
        for (HashMap<String, Object> m : masters) {
            HashMap<String, Object> raw = latestRaw(str(m, "PMB_TAG"), 10);
            if (raw == null) {
                return fail(g, REJECTED, "PUMP_STATE_UNKNOWN");
            }
            Double v = parseDouble(str(raw, "VALUE"));
            if (v != null && v > 0) {
                running.add((int) toLong(m.get("PUMP_IDX")));
                runningMasters.add(m);
            }
        }
        // 태그 검사를 조합 비교보다 먼저 한다(문서 게이트 순서, 태그 누락 알람이 묻히지 않게)
        for (HashMap<String, Object> m : runningMasters) {
            String tag = str(m, "CTR_AUTO_FREQ_TAG");
            if (tag == null || tag.trim().isEmpty()) {
                return fail(g, REJECTED, "TAG_NOT_CONFIGURED");
            }
            g.rows.add(queueRow(str(m, "PUMP_NM"), tag.trim(), "FREQ", hz));
        }
        // PUMP_COMB 는 Python 의 펌프 번호(PMB-4017=1 … PMB-4032=4). 펌프 마스터 PUMP_IDX 와 같다.
        if (running.isEmpty() || !running.equals(parseComb(str(row, "PUMP_COMB")))) {
            return fail(g, REJECTED, "PUMP_STATE_CHANGED");
        }
        return g;
    }

    /**
     * 분기밸브(국가산단·지방산단 공통): 목표 개도 전송 → 방향별 펄스(1 → 펄스 폭 → 0). 순서는 고정이다.
     * 상향(목표 > 현재)은 OPENC({DEVICE}_PULSE), 하향은 CLOSEC({DEVICE}_CLOSE_PULSE) 태그에 펄스를 준다.
     * 현재 개도는 판단 행의 {DEVICE}_CUR_OPEN 이다. Python 이 목표를 이 값 ± STEP 으로 만들므로
     * 방향이 Python 판단(NATIONAL_OPEN/CLOSE, LOCAL_FALLBACK_CLOSE/LOCAL_RECOVERY_OPEN)과 일치한다.
     * 태그 키: NATIONAL_OPEN/PULSE/CLOSE_PULSE, LOCAL_OPEN/PULSE/CLOSE_PULSE (docs/sql/gunsan_ctrl_cmd.sql 2절).
     */
    private Gate evaluateValve(Gate g, Map<String, HashMap<String, Object>> cfg, String device, double target, Double current) {
        long open = Math.round(target);
        if (open < 0 || open > 100) {
            return fail(g, REJECTED, "OUT_OF_RANGE");
        }
        if (current == null) {
            return fail(g, REJECTED, "CUR_OPEN_UNKNOWN");
        }
        if (target == current) {
            return fail(g, REJECTED, "NO_CHANGE");
        }
        boolean up = target > current;
        String openTag = configTag(cfg, device + "_OPEN");
        String pulseTag = configTag(cfg, up ? device + "_PULSE" : device + "_CLOSE_PULSE");
        if (openTag == null || pulseTag == null) {
            return fail(g, REJECTED, "TAG_NOT_CONFIGURED");
        }
        // 대기열은 CTR_IDX 순으로 한 사이클에 한 행씩 송신되므로 넣는 순서가 곧 송신 순서다
        String ctrNm = valveCtrName(device);
        g.rows.add(queueRow(ctrNm, openTag, ANLY_VALVE_OPEN, open));
        g.rows.add(queueRow(ctrNm, pulseTag, up ? ANLY_VALVE_PULSE : ANLY_VALVE_PULSE_CLOSE, 1));
        return g;
    }

    /** 대기열 CTR_NM(제어이력 화면의 설비명). 기존 국가산단 표기 "국가산단밸브"를 그대로 따른다 */
    private static String valveCtrName(String device) {
        return LOCAL.equals(device) ? "지방산단밸브" : "국가산단밸브";
    }

    /** 밸브 개도 되읽기 태그(APPLIED 상세 기록용) */
    private String readbackTag(String device) {
        return LOCAL.equals(device) ? localReadbackTag : nationalReadbackTag;
    }

    /**
     * 판단 마감 시각(초, CTRL_TS 기준). 다음 벤더 판단 closeSec 초 전이다.
     * 한 판단은 그 주기 안에서만 유효하다. 다음 판단이 "제어 불필요"여도 이전 판단을 승인·송신하지 않게 한다.
     */
    private long decisionCloseAgeSec() {
        return Math.max(1, cycleMin) * 60L - closeSec;
    }

    /** 신선도: 판단 마감 시각 경과 또는 같은 장치의 새 명령 등장 */
    private String staleReason(HashMap<String, Object> row, String device) {
        if (toLong(row.get("AGE_SEC")) >= decisionCloseAgeSec()) {
            return "STALE";
        }
        HashMap<String, Object> p = new HashMap<>();
        p.put("CTRL_TS", row.get("CTRL_TS"));
        p.put("DEVICE", device);
        return ctrlCmdMapper.countNewerDeviceCmd(p) > 0 ? "SUPERSEDED" : null;
    }

    /**
     * 마감된 명령의 종결 상태. 추천 모드는 사용자가 응답하지 않은 것이므로 REJECTED(APPROVE_TIMEOUT),
     * 그 밖(운전 모드에서 대기열 혼잡으로 끝내 적재 못 함 등)은 EXPIRED. Python 에게는 둘 다 "제어 없음"이다.
     */
    private static Gate closeStale(Gate g, int mode, String stale) {
        if (mode == PumpService.AI_RECOMMEND) {
            return fail(g, REJECTED, "APPROVE_TIMEOUT");
        }
        return fail(g, EXPIRED, stale);
    }

    /** 추적 ACTION: 사람의 거절(REJECT)과 무응답 마감·만료(EXPIRE)를 구분한다 */
    private static String closeAction(String kind, String reason) {
        return EXPIRED.equals(kind) || "APPROVE_TIMEOUT".equals(reason) ? "EXPIRE" : "REJECT";
    }

    private static Gate fail(Gate g, String kind, String reason) {
        g.kind = kind;
        g.reason = reason;
        g.rows.clear();
        return g;
    }

    private static HashMap<String, Object> queueRow(String ctrNm, String tag, String anlyCd, long value) {
        HashMap<String, Object> q = new HashMap<>();
        q.put("CTR_NM", ctrNm);
        q.put("TAG", tag);
        q.put("ANLY_CD", anlyCd);
        q.put("VALUE", value);
        return q;
    }

    // ------------------------------------------------------------------
    // 공통
    // ------------------------------------------------------------------

    private HashMap<String, Object> lockRow(long ctrlId) {
        return ctrlCmdMapper.selectCmdForUpdate(param("CTRL_ID", ctrlId));
    }

    /** READY → toStatus 비교 후 교체. 바뀐 경우에만 추적을 남긴다 */
    private void transition(long ctrlId, String device, String toStatus, String reason, String action,
                            String userId, HashMap<String, Object> row, String detail) {
        HashMap<String, Object> p = new HashMap<>();
        p.put("CTRL_ID", ctrlId);
        p.put("DEVICE", device);
        p.put("FROM_STATUS", READY);
        p.put("TO_STATUS", toStatus);
        int n = ctrlCmdMapper.updateDeviceStatus(p);
        if (n > 0) {
            trace(ctrlId, device, action, reason, tgt(row, device), userId, detail);
            log.info("[CtrlCmd] CTRL_ID={} {} READY → {} ({})", ctrlId, device, toStatus, reason);
        }
    }

    /** 추적 기록. 테이블이 아직 없더라도 제어 흐름은 멈추지 않는다 */
    private void trace(long ctrlId, String device, String action, String reason, Double tgt, String userId, String detail) {
        try {
            HashMap<String, Object> t = new HashMap<>();
            t.put("CTRL_ID", ctrlId);
            t.put("DEVICE", device);
            t.put("ACTION", action);
            t.put("REASON", reason);
            t.put("TGT_VALUE", tgt);
            t.put("USER_ID", userId);
            t.put("DETAIL", detail == null ? null : (detail.length() > 500 ? detail.substring(0, 500) : detail));
            ctrlCmdMapper.insertTrace(t);
        } catch (Exception e) {
            log.warn("[CtrlCmd] 추적 기록 실패(TB_CTRL_CMD_TRACE 확인): {}", e.getMessage());
        }
    }

    /** 같은 사유 알람은 alarmIntervalMin 에 한 번만 */
    private void alarm(String key, String msg) {
        long now = System.currentTimeMillis();
        Long last = lastAlarmAt.get(key);
        if (last != null && now - last < alarmIntervalMin * 60_000L) {
            return;
        }
        lastAlarmAt.put(key, now);
        try {
            HashMap<String, Object> a = new HashMap<>();
            a.put("alr_typ", "PUMP");
            a.put("nowDate", pumpService.nowStringDate());
            a.put("msg", msg + "|");
            a.put("link", "");
            pumpService.emsPumpAlarmInsert(a);
        } catch (Exception e) {
            log.warn("[CtrlCmd] 알람 기록 실패: {}", e.getMessage());
        }
    }

    private Map<String, HashMap<String, Object>> loadTagConfig() {
        Map<String, HashMap<String, Object>> cfg = new HashMap<>();
        for (HashMap<String, Object> r : ctrlCmdMapper.selectCtrlCmdTagConfig()) {
            String key = str(r, "TAG_DSC");
            if (key != null) {
                cfg.put(key.trim(), r);
            }
        }
        return cfg;
    }

    private static String configTag(Map<String, HashMap<String, Object>> cfg, String key) {
        HashMap<String, Object> r = cfg.get(key);
        String v = r == null ? null : str(r, "TAG");
        return v == null || v.trim().isEmpty() ? null : v.trim();
    }

    private HashMap<String, Object> latestRaw(String tag, int freshMin) {
        if (tag == null || tag.isEmpty()) {
            return null;
        }
        HashMap<String, Object> p = new HashMap<>();
        p.put("TAG", tag);
        p.put("FRESH_MIN", freshMin);
        return ctrlCmdMapper.selectLatestRaw(p);
    }

    /** 화면용: 장치별 상태 + 진행 중 파생 + 사유 한글 */
    private HashMap<String, Object> decorate(HashMap<String, Object> row, boolean withQueue) {
        HashMap<String, Object> d = new HashMap<>(row);
        long ctrlId = toLong(row.get("CTRL_ID"));
        List<HashMap<String, Object>> queue = withQueue
                ? ctrlCmdMapper.selectQueueByCtrlId(param("CTRL_ID", ctrlId))
                : Collections.emptyList();
        for (String device : DEVICES) {
            String status = str(row, device + "_CMD_STATUS");
            String view = status;
            if ("Y".equals(str(row, device + "_CMD_YN")) && READY.equals(status) && withQueue) {
                String prefix = optIdx(ctrlId, device);
                boolean inQueue = queue.stream().anyMatch(q -> prefix.equals(str(q, "OPT_IDX")));
                view = inQueue ? "IN_PROGRESS" : "WAITING";
            }
            d.put(device + "_VIEW_STATUS", view);
        }
        d.put("REASONS", reasonList(str(row, "REASON_CODE")));
        if (withQueue) {
            d.put("QUEUE", queue);
        }
        return d;
    }

    private Map<Long, List<HashMap<String, Object>>> loadTraces(List<HashMap<String, Object>> rows) {
        Map<Long, List<HashMap<String, Object>>> map = new HashMap<>();
        if (rows.isEmpty()) {
            return map;
        }
        List<Long> ids = new ArrayList<>();
        for (HashMap<String, Object> r : rows) {
            ids.add(toLong(r.get("CTRL_ID")));
        }
        try {
            HashMap<String, Object> p = new HashMap<>();
            p.put("CTRL_IDS", ids);
            for (HashMap<String, Object> t : ctrlCmdMapper.selectTraceByCtrlIds(p)) {
                t.put("REASON_LABEL", str(t, "REASON") == null ? null : reasonLabel(str(t, "REASON")));
                map.computeIfAbsent(toLong(t.get("CTRL_ID")), k -> new ArrayList<>()).add(t);
            }
        } catch (Exception e) {
            log.warn("[CtrlCmd] 추적 조회 실패(TB_CTRL_CMD_TRACE 확인): {}", e.getMessage());
        }
        return map;
    }

    private static String optIdx(long ctrlId, String device) {
        return "CTRL:" + ctrlId + ":" + device;
    }

    /** 목표값 컬럼: 펌프는 {PUMP}_TGT_HZ, 밸브는 {DEVICE}_TGT_OPEN */
    private static Double tgt(HashMap<String, Object> row, String device) {
        return parseDouble(str(row, PUMP.equals(device) ? "PUMP_TGT_HZ" : device + "_TGT_OPEN"));
    }

    /** 현재값 컬럼: 펌프는 {PUMP}_CUR_HZ, 밸브는 {DEVICE}_CUR_OPEN */
    private static Double cur(HashMap<String, Object> row, String device) {
        return parseDouble(str(row, PUMP.equals(device) ? "PUMP_CUR_HZ" : device + "_CUR_OPEN"));
    }

    static String deviceLabel(String device) {
        if (PUMP.equals(device)) {
            return "송수펌프";
        }
        return LOCAL.equals(device) ? "지방산단 밸브" : "국가산단 밸브";
    }

    private static TreeSet<Integer> parseComb(String comb) {
        TreeSet<Integer> set = new TreeSet<>();
        if (comb == null) {
            return set;
        }
        for (String s : comb.split(",")) {
            try {
                set.add(Integer.parseInt(s.trim()));
            } catch (NumberFormatException ignore) {
                // 형식이 다르면 비교에서 불일치로 걸린다
            }
        }
        return set;
    }

    private static HashMap<String, Object> param(String key, Object value) {
        HashMap<String, Object> p = new HashMap<>();
        p.put(key, value);
        return p;
    }

    private static String str(Map<String, Object> m, String key) {
        Object v = m == null ? null : m.get(key);
        return v == null ? null : v.toString();
    }

    private static long toLong(Object v) {
        if (v == null) {
            return 0L;
        }
        if (v instanceof Number) {
            return ((Number) v).longValue();
        }
        try {
            return Long.parseLong(v.toString().trim());
        } catch (NumberFormatException e) {
            return 0L;
        }
    }

    private static Double parseDouble(String s) {
        if (s == null) {
            return null;
        }
        try {
            double d = Double.parseDouble(s.trim());
            return Double.isFinite(d) ? d : null;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    // ------------------------------------------------------------------
    // 사유코드 한글 사전
    // ------------------------------------------------------------------

    private static final Map<String, String> REASON_LABELS = new LinkedHashMap<>();

    static {
        // Python 판단 사유
        REASON_LABELS.put("NORMAL_HOLD", "정상 범위, 조치 없음");
        REASON_LABELS.put("PUMP_UP", "펌프 주파수 상승");
        REASON_LABELS.put("PUMP_DOWN", "펌프 주파수 하강");
        REASON_LABELS.put("PUMP_DANGER_UP", "위험수위 펌프 즉시 상승");
        REASON_LABELS.put("PUMP_DANGER_DOWN", "위험수위 펌프 즉시 하강");
        REASON_LABELS.put("NATIONAL_OPEN", "국가산단 밸브 열기");
        REASON_LABELS.put("NATIONAL_CLOSE", "국가산단 밸브 닫기");
        REASON_LABELS.put("NATIONAL_DANGER_OPEN", "위험수위 국가산단 밸브 즉시 열기");
        REASON_LABELS.put("NATIONAL_DANGER_CLOSE", "위험수위 국가산단 밸브 즉시 닫기");
        // 지방산단 밸브(2026-09-30 벤더 드롭): 나운 고수위 최종(fallback) 제어
        REASON_LABELS.put("LOCAL_FALLBACK_CLOSE", "나운 고수위 지속, 지방산단 밸브 닫기(최종 제어)");
        REASON_LABELS.put("LOCAL_FORCE_CLOSE", "나운 강제 상한 초과, 지방산단 밸브 즉시 닫기");
        REASON_LABELS.put("LOCAL_RECOVERY_OPEN", "나운 안정 확인, 지방산단 밸브 원복 열기");
        REASON_LABELS.put("LOCAL_POST_CONTROL_HOLD", "지방산단 밸브 제어 직후 대기");
        REASON_LABELS.put("LOCAL_DIRECTION_CHANGED", "지방산단 밸브 판단 방향 바뀜, 재확인 대기");
        REASON_LABELS.put("LOCAL_NO_RESPONSE", "직전 지방산단 밸브 제어 효과 없음");
        REASON_LABELS.put("LOCAL_RESPONSE_CHECK", "지방산단 밸브 반응 판단 불가");
        REASON_LABELS.put("LOCAL_RANGE_CHECK", "지방산단 밸브 개도가 자동제어 범위 밖");
        REASON_LABELS.put("LOCAL_LIMIT", "지방산단 밸브 개도 한계 도달");
        REASON_LABELS.put("LOCAL_DATA_CHECK", "지방산단 밸브 개도 계측 결측");
        REASON_LABELS.put("LOCAL_OBSERVE", "지방산단 밸브 제어 관찰 중");
        REASON_LABELS.put("LOCAL_FORCE_OBSERVE", "지방산단 밸브 강제 닫기 관찰 중");
        REASON_LABELS.put("DIST_NAUN_DOWN_OSIK_UP", "배분 불균형(나운 하강·오식도 상승)");
        REASON_LABELS.put("DIST_NAUN_UP_OSIK_DOWN", "배분 불균형(나운 상승·오식도 하강)");
        // 오식도 유입(FRI-8652)-유출(FRI-8653) 유량수지 보조지표(2026-09-30 벤더 드롭)
        REASON_LABELS.put("OSIK_BALANCE_SURPLUS", "오식도 유입 > 유출(배분 과다 보조 근거)");
        REASON_LABELS.put("OSIK_BALANCE_DEFICIT", "오식도 유입 < 유출(배분 부족 보조 근거)");
        REASON_LABELS.put("OSIK_OUTFLOW_MISSING", "오식도 유출유량 계측 결측(유입유량으로 대체)");
        REASON_LABELS.put("MORNING_FILL", "경부하 충수 구간");
        REASON_LABELS.put("PUMP_POST_CONTROL_HOLD", "펌프 제어 직후 대기");
        REASON_LABELS.put("NATIONAL_POST_CONTROL_HOLD", "밸브 제어 직후 대기");
        REASON_LABELS.put("PUMP_DIRECTION_CHANGED", "펌프 판단 방향 바뀜, 재확인 대기");
        REASON_LABELS.put("NATIONAL_DIRECTION_CHANGED", "밸브 판단 방향 바뀜, 재확인 대기");
        REASON_LABELS.put("PUMP_NO_RESPONSE", "직전 펌프 제어 효과 없음");
        REASON_LABELS.put("NATIONAL_NO_RESPONSE", "직전 밸브 제어 효과 없음");
        REASON_LABELS.put("PUMP_RESPONSE_CHECK", "펌프 반응 판단 불가");
        REASON_LABELS.put("NATIONAL_RESPONSE_CHECK", "밸브 반응 판단 불가");
        REASON_LABELS.put("PUMP_STATE_CHECK", "운전 중 펌프 또는 주파수 없음");
        REASON_LABELS.put("PUMP_RANGE_CHECK", "펌프 주파수가 자동제어 범위 밖");
        REASON_LABELS.put("NATIONAL_RANGE_CHECK", "밸브 개도가 자동제어 범위 밖");
        REASON_LABELS.put("PUMP_LIMIT", "펌프 주파수 한계 도달");
        REASON_LABELS.put("NATIONAL_LIMIT", "밸브 개도 한계 도달");
        REASON_LABELS.put("CLEARWELL_LOW", "정수지 수위 하한");
        REASON_LABELS.put("CLEARWELL_HIGH", "정수지 수위 상한");
        REASON_LABELS.put("RAW_DATA_MISSING", "계측 결측");
        REASON_LABELS.put("CLEARWELL_DATA_MISSING", "정수지 계측 결측");
        REASON_LABELS.put("LEVEL_DATA_INVALID", "배수지 수위 계측 이상");
        REASON_LABELS.put("NATIONAL_DATA_CHECK", "밸브 개도 계측 결측");
        REASON_LABELS.put("LEVEL_SENSOR_CHECK_NAUN", "나운 수위 센서 편차 초과");
        REASON_LABELS.put("LEVEL_SENSOR_CHECK_OSIK", "오식도 수위 센서 편차 초과");
        REASON_LABELS.put("NAUN_SINGLE_SENSOR", "나운 센서 1개로 판단");
        REASON_LABELS.put("OSIK_SINGLE_SENSOR", "오식도 센서 1개로 판단");
        REASON_LABELS.put("PRED_STALE", "예측값 지연");
        REASON_LABELS.put("RATE_TIME_CHECK", "요금 시간대 계산 실패");
        REASON_LABELS.put("GLOBAL_HOLD", "전체 보류");
        // Java 게이트·처리 사유
        REASON_LABELS.put("ANALYZE_MODE", "AI 분석 모드 — 송신하지 않음");
        REASON_LABELS.put("TESTMODE_OFF", "테스트모드·제어테스트모드 꺼짐");
        REASON_LABELS.put("OUT_OF_RANGE", "제어값이 허용 범위 밖");
        REASON_LABELS.put("TAG_NOT_CONFIGURED", "제어 태그 미설정");
        REASON_LABELS.put("CUR_OPEN_UNKNOWN", "현재 개도 없음 — 상향·하향 판단 불가");
        REASON_LABELS.put("NO_CHANGE", "목표 개도가 현재와 같음");
        REASON_LABELS.put("PUMP_STATE_UNKNOWN", "펌프 운전상태 계측 없음");
        REASON_LABELS.put("PUMP_STATE_CHANGED", "판단 이후 운전 펌프 조합 변경");
        REASON_LABELS.put("STALE", "판단 마감 경과(미적재)");
        REASON_LABELS.put("SUPERSEDED", "새 판단으로 대체");
        REASON_LABELS.put("USER_REJECT", "사용자 거절");
        REASON_LABELS.put("APPROVE_TIMEOUT", "승인 응답 없음 — 다음 판단 전 마감");
        REASON_LABELS.put("QUEUE_DISCARDED", "대기열 폐기(모드 전환 등)");
        REASON_LABELS.put("QUEUE_TIMEOUT", "송신 미완료 시간 초과");
    }

    private static final Map<String, String> STATE_LABELS = new HashMap<>();

    static {
        STATE_LABELS.put("DANGER_LOW", "위험 저수위");
        STATE_LABELS.put("DANGER_HIGH", "위험 고수위");
        STATE_LABELS.put("PRE_LOW", "선제 부족");
        STATE_LABELS.put("PRE_HIGH", "선제 과다");
        STATE_LABELS.put("BEHIND", "충수 지연");
        STATE_LABELS.put("AHEAD", "충수 초과");
        STATE_LABELS.put("NORMAL", "정상");
    }

    public static String reasonLabel(String code) {
        if (code == null) {
            return null;
        }
        String label = REASON_LABELS.get(code);
        if (label != null) {
            return label;
        }
        if (code.startsWith("NAUN_") && STATE_LABELS.containsKey(code.substring(5))) {
            return "나운 " + STATE_LABELS.get(code.substring(5));
        }
        if (code.startsWith("OSIK_") && STATE_LABELS.containsKey(code.substring(5))) {
            return "오식도 " + STATE_LABELS.get(code.substring(5));
        }
        return code;
    }

    /** 사유코드 문자열 → [{code,label}]. 다음 판단용 내부 토큰(*_WAIT_*)은 숨긴다 */
    private static List<HashMap<String, Object>> reasonList(String reasonCode) {
        List<HashMap<String, Object>> list = new ArrayList<>();
        if (reasonCode == null || reasonCode.isEmpty()) {
            return list;
        }
        for (String c : reasonCode.split("\\|")) {
            String code = c.trim();
            if (code.isEmpty() || code.contains("_WAIT_")) {
                continue;
            }
            HashMap<String, Object> m = new HashMap<>();
            m.put("code", code);
            m.put("label", reasonLabel(code));
            list.add(m);
        }
        return list;
    }
}
