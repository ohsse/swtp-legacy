package kr.co.mindone.ems.pump;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Profile;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;

/**
 * 군산 5분 제어 판단 소비자.
 *
 * - consume: 매분 40초. 벤더 스크립트가 5분마다 쓴 판단 행을 게이트에 통과시켜 대기열에 적재한다.
 *   40초는 Python 이 INSERT 를 끝낼 여유다. 매분 도는 이유: 벤더 계산이 늦거나 대기열이 붐벼도
 *   다음 5분 판단 전에 송신·APPLIED 를 끝내야 벤더 HOLD 가 제대로 걸린다. 행 잠금으로 중복 처리는 없다.
 * - judge: 30초마다. 대기열 FLAG 로 APPLIED(송신 완료) / FAILED / EXPIRED 를 되돌려 쓴다.
 *
 * 송신 자체는 기존 PumpScheduler.pumpTask(1분)가 맡는다.
 * gu 프로파일 전용이며 ctrl.cmd.consumer.enabled=false 면 아무것도 하지 않는다.
 * gu2(섀도우)는 SchedulerConfig 가 스케줄링 자체를 끄므로 여기까지 오지 않는다.
 */
@Slf4j
@Component
@Profile("gu")
public class CtrlCmdScheduler {

    @Autowired
    private CtrlCmdService ctrlCmdService;

    @Scheduled(cron = "${ctrl.cmd.consumer.cron:40 * * * * *}")
    public void consume() {
        if (!ctrlCmdService.isConsumerEnabled()) {
            return;
        }
        List<HashMap<String, Object>> rows = ctrlCmdService.selectReadyCmdList(ctrlCmdService.getLookbackMin());
        for (HashMap<String, Object> row : rows) {
            long ctrlId = ((Number) row.get("CTRL_ID")).longValue();
            // 펌프 → 국가산단 → 지방산단 순(CtrlCmdService.DEVICES). 같은 판단 행의 대기열 행은 서로를 막지 않는다.
            for (String device : CtrlCmdService.DEVICES) {
                if (!"Y".equals(String.valueOf(row.get(device + "_CMD_YN")))
                        || !CtrlCmdService.READY.equals(String.valueOf(row.get(device + "_CMD_STATUS")))) {
                    continue;
                }
                try {
                    CtrlCmdService.Outcome o = ctrlCmdService.processDevice(ctrlId, device, false, null);
                    // 매분 돌므로 승인 대기·적재 완료·대기열 혼잡은 반복된다. 상태가 바뀐 결과만 info 로 남긴다
                    if ("PENDING".equals(o.code) || "SKIPPED".equals(o.code) || "BUSY".equals(o.code)) {
                        log.debug("[CtrlCmd] consume CTRL_ID={} {} → {}", ctrlId, device, o.code);
                    } else {
                        log.info("[CtrlCmd] consume CTRL_ID={} {} → {} {}", ctrlId, device, o.code,
                                o.reason == null ? "" : o.reason);
                    }
                } catch (Exception e) {
                    log.error("[CtrlCmd] consume 실패 CTRL_ID={} {}: {}", ctrlId, device, e.getMessage(), e);
                }
            }
        }
    }

    @Scheduled(cron = "${ctrl.cmd.judge.cron:15,45 * * * * *}")
    public void judge() {
        if (!ctrlCmdService.isConsumerEnabled()) {
            return;
        }
        try {
            ctrlCmdService.judgeAll();
        } catch (Exception e) {
            log.error("[CtrlCmd] judge 실패: {}", e.getMessage(), e);
        }
    }
}
