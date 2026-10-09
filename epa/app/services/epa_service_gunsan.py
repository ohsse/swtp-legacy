# /app/services/epa_service_gunsan.py
"""
군산 해석 엔진 어댑터.

epa/epanet_gunsan/ 의 독립 CLI 스크립트를 epa_service 와 같은 이름·같은 시그니처로
감싼다. 스크립트 원본은 한 줄도 고치지 않는다 — 필요한 값이 전부 CLI 인자로
노출돼 있어 argv 만 만들어 main() 에 넘기면 되기 때문이다.

**왜 내부 함수가 아니라 main(argv) 를 부르는가**

1. epanet_si_gs.py 에는 run_once 가 없다. 전 과정이 main() 안에 인라인이라
   (epanet_si_gs.py:1242-1505) 함수를 잘라 쓰려면 원본을 고쳐야 한다.
2. argparse.Namespace 를 손으로 만들면 스크립트가 인자를 추가할 때 조용히 깨진다.
   main(argv) 는 ap.parse_args(argv) 를 거치므로 기본값이 항상 채워진다.

**왜 인자를 전부 명시해서 넘기는가**

스크립트 기본값은 SCRIPT_DIR 상대다. 안 넘기면 이미지 안의
/app/epanet_gunsan/connections.json(개발 덤프 DB)을 보고 잘못된 DB 에 결과를 쓴다.
config 값을 넘기면 운영(maria-ems-db-gu)과 개발서버(maria-ems-db-gu-test)가
스택별로 자동으로 갈린다.
"""

import importlib
import logging
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from flask import current_app, g, has_request_context

from app.models.db import DbManager, get_db_connection
from app.services.engine import EngineBusyError, EngineRequestError

logger = logging.getLogger(__name__)

# epa 루트. 이 파일이 <epa>/app/services/ 에 있으므로 두 단계 위가 <epa> 다.
_EPA_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# 동시 실행 차단
#
# 군산 엔진은 EPANET 에 한글 경로를 숨기려고 os.chdir(결과폴더) 후 run_sim 하고
# 되돌아온다(run_epanet_snapshot). CWD 는 프로세스 전역 상태다.
# 그런데 이 앱은 gunicorn --worker-class gthread --threads 4 로 돈다(Dockerfile).
# 락이 없으면 동시 요청 두 개가 서로의 CWD 를 망가뜨린다.
#
# 고산 epa_service 에는 os.chdir 가 없어 이 제약이 없었다. 군산 엔진을 얹으면서
# 새로 생기는 제약이다.
# ---------------------------------------------------------------------------
_ENGINE_LOCK = threading.Lock()

# 로드한 스크립트 모듈 캐시. import 자체는 INP 를 읽지 않으므로 가볍다.
_MODULE_CACHE = {}
_MODULE_CACHE_LOCK = threading.Lock()


def _engine_dir() -> Path:
    """군산 CLI 스크립트가 있는 폴더."""
    configured = current_app.config.get('GUNSAN_ENGINE_DIR')
    return Path(configured).resolve() if configured else (_EPA_ROOT / 'epanet_gunsan')


def _load(module_name: str):
    """
    epanet_gunsan 의 스크립트를 모듈로 가져온다.

    스크립트가 sys.path 밖 폴더에 있으므로 경로를 한 번 얹는다.
    실행부가 `if __name__ == "__main__"` 안에만 있어 import 부작용이 없다.
    """
    with _MODULE_CACHE_LOCK:
        cached = _MODULE_CACHE.get(module_name)
        if cached is not None:
            return cached

        engine_dir = str(_engine_dir())
        if engine_dir not in sys.path:
            sys.path.insert(0, engine_dir)

        module = importlib.import_module(module_name)
        _MODULE_CACHE[module_name] = module
        logger.info(f"군산 해석 엔진 모듈 로드: {module_name} ({engine_dir})")
        return module


def _resolve(value: str, label: str) -> str:
    """
    config 의 상대경로를 epa 루트 기준 절대경로로 바꾸고 존재를 확인한다.

    스크립트도 자체적으로 CWD → SCRIPT_DIR 순으로 찾지만(resolve_input_path),
    여기서 미리 확인해야 "파일이 없다"가 EPANET 오류가 아니라 설정 오류로 보인다.
    INP 는 .dockerignore·.gitignore·볼륨 마운트 3중으로 빠지기 쉬운 파일이라
    이 확인이 특히 값어치를 한다.
    """
    path = Path(value)
    if not path.is_absolute():
        path = (_EPA_ROOT / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"{label} 파일을 찾을 수 없습니다: {path} (config 값: {value})")
    return str(path)


def _fmt_ts(ts: datetime) -> str:
    """스크립트가 datetime.fromisoformat 로 읽는 형식."""
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_pump_hz(pump_hz: Optional[dict]) -> Optional[str]:
    """
    {1: 55.0, 3: 52.0} 를 스크립트의 --pump-hz 형식 "1:55,3:52" 로 바꾼다.

    이 형식을 아는 곳은 이 모듈뿐이어야 한다. 라우트나 프런트가 문자열을 직접 조립하면
    스크립트가 형식을 바꿀 때 어디를 고쳐야 하는지 알 수 없게 된다.

    정수로 떨어지는 Hz 는 "55.0" 이 아니라 "55" 로 적는다. 스크립트의 parse_pump_hz 는
    둘 다 float() 로 읽지만(epanet_si_gs.py:576), 실행 로그가 사람이 읽는 것이라
    원래 입력한 모양에 가깝게 남긴다.
    """
    if not pump_hz:
        return None
    parts = []
    for num in sorted(pump_hz):
        hz = float(pump_hz[num])
        parts.append(f"{int(num)}:{hz:g}")
    return ",".join(parts)


def _common_argv() -> list:
    """mo·si 가 공통으로 받는 인자. 전부 config 에서 온다."""
    cfg = current_app.config
    return [
        "--inp", _resolve(cfg['GUNSAN_INP_PATH'], "군산 관망 INP"),
        "--conn", _resolve(cfg['CONN_FILE_PATH'], "DB 접속 설정"),
        "--conn-key", cfg['DEFAULT_CONN_KEY'],
        "--valve-model", _resolve(cfg['GUNSAN_VALVE_MODEL_PATH'], "밸브 보정곡선"),
        "--valve-mode", cfg.get('GUNSAN_VALVE_MODE', 'opening'),
        "--pressure-unit", cfg.get('GUNSAN_PRESSURE_UNIT', 'legacy_div10'),
        "--reference-hz", str(cfg.get('GUNSAN_REFERENCE_HZ', 60.0)),
        "--fallback-sec", str(cfg.get('GUNSAN_FALLBACK_SEC', cfg.get('FALLBACK_SEC', 600))),
    ]


def _run_engine(module_name: str, argv: list, label: str) -> float:
    """
    락을 잡고 스크립트 main(argv) 를 실행한다. 경과 초를 돌려준다.
    실패는 예외로 올린다 — 라우트가 변환한다.
    """
    timeout = float(current_app.config.get('GUNSAN_LOCK_TIMEOUT_SEC', 600))
    module = _load(module_name)

    if not _ENGINE_LOCK.acquire(timeout=timeout):
        raise EngineBusyError(
            f"{label}: 다른 해석이 실행 중이라 {timeout:.0f}초 안에 시작하지 못했습니다. "
            "잠시 후 다시 시도하세요."
        )

    started = time.perf_counter()
    try:
        logger.info(f"{label} 실행: {' '.join(argv)}")
        try:
            rc = module.main(argv)
        except SystemExit as exc:
            # argparse 의 ap.error() 가 SystemExit 를 던진다.
            # except Exception 에 안 잡히므로 여기서 따로 받아 메시지를 살린다.
            raise RuntimeError(f"{label}: 엔진 인자 오류 (exit={exc.code})") from exc

        if rc != 0:
            raise RuntimeError(f"{label}: 엔진이 실패 코드 {rc} 로 종료했습니다.")

        elapsed = time.perf_counter() - started
        logger.info(f"{label} 완료 ({elapsed:.3f}s)")
        return elapsed
    finally:
        _ENGINE_LOCK.release()


def _db() -> DbManager:
    """요청 중이면 g.db 를, 아니면 풀에서 꺼낸 임시 세션을 쓴다."""
    if has_request_context() and 'db' in g:
        return g.db
    return DbManager(get_db_connection(current_app.config['DEFAULT_CONN_KEY']))


def _latest_si_ts() -> Optional[datetime]:
    """
    TB_EPA_SIM_RESV_FLOW 의 최신 UPDT_TIME.

    스크립트의 pick_latest_si_ts(epanet_si_gs.py:498)와 같은 규칙이다.
    스크립트에 맡기지 않고 여기서 구하는 이유: 응답의 target_ts 를 채워야 하는데
    스크립트가 고른 시각을 되받을 방법이 없기 때문이다.
    """
    own_session = not (has_request_context() and 'db' in g)
    db = _db()
    try:
        row = db.fetchone(
            "SELECT MAX(UPDT_TIME) AS UPDT_TIME FROM TB_EPA_SIM_RESV_FLOW WHERE UPDT_TIME <= %s",
            (datetime.now(),),
        )
        return row.get("UPDT_TIME") if row and row.get("UPDT_TIME") else None
    finally:
        if own_session:
            db.close()


# ---------------------------------------------------------------------------
# epa_service 와 같은 시그니처를 갖는 공개 함수 3종
# ---------------------------------------------------------------------------

def run_si_simulation(
    ts: Optional[datetime] = None,
    db_session: Optional[DbManager] = None,
    pump_comb: Optional[str] = None,
    flow_min=None,
    flow_max=None,
    rule_pipe_id=None,
    rule_priority=None,
    pump_hz: Optional[dict] = None,
) -> dict:
    """
    군산 SI(운영자 시나리오) 해석 한 시점.

    인자 목록과 순서를 epa_service.run_si_simulation 과 똑같이 맞춰 두었다.
    호출부가 위치인자로 부르든 키워드로 부르든 양쪽이 같게 동작해야 하기 때문이다.
    아래 넷은 고산 전용이라 군산 경로에서는 받기만 하고 쓰지 않는다.

    - flow_min / flow_max / rule_pipe_id / rule_priority
      고산은 펌프 조합을 INP 의 [RULES] 에 주입해 표현한다(inject_rule_to_inp).
      군산 엔진은 --pump-comb 로 펌프를 직접 지정하므로 RULE 자체가 없다.
    - db_session
      군산 엔진은 자기 pymysql 연결을 직접 열고 트랜잭션도 스스로 관리한다
      (conn.begin()/commit()/rollback()). 앱 커넥션 풀을 쓰지 않는다.

    pump_hz 는 반대로 **군산에서만 의미가 있는** 인자다({펌프번호: Hz}).
    주면 --pump-hz 로 넘어가 그 값이 그대로 적용되고(HZ_SOURCE=argument),
    안 주면 스크립트가 같은 기준시각의 TB_RAWDATA 실측 Hz(891-365-SPI-400x)를 쓴다
    (epanet_si_gs.py:781-786).
    """
    if not pump_comb:
        raise ValueError("pump_comb 가 필요합니다.")

    target_ts = ts or _latest_si_ts()
    if target_ts is None:
        raise ValueError(
            "TB_EPA_SIM_RESV_FLOW 에 기준 시각이 없습니다. "
            "관망해석 화면에서 배수지 유량을 먼저 저장하세요."
        )

    argv = _common_argv() + [
        "--ts", _fmt_ts(target_ts),
        "--pump-comb", str(pump_comb),
    ]
    # 값이 있을 때만 붙인다. 빈 문자열을 넘기면 스크립트가 형식 오류로 죽는다
    # (parse_pump_hz 는 None/빈값만 "미지정"으로 본다, epanet_si_gs.py:566-567).
    pump_hz_arg = _fmt_pump_hz(pump_hz)
    if pump_hz_arg:
        argv += ["--pump-hz", pump_hz_arg]

    elapsed = _run_engine("epanet_si_gs", argv, "군산 SI")

    return {
        "status": "completed",
        "target_ts": target_ts.isoformat(),
        "pump_comb": pump_comb,
        "pump_hz": pump_hz_arg,
        "elapsed_sec": round(elapsed, 3),
    }


def run_mo_simulation(
    ts: Optional[datetime] = None,
    db_session: Optional[DbManager] = None,
) -> dict:
    """
    군산 MO(계측 기반 모니터링) 해석 한 시점.

    ts 를 안 주면 5분 경계로 내림한 현재 시각을 쓴다. 스크립트의 --snapshot 은
    --ts 를 함께 요구하므로(epanet_mo_gs.py:1202) 여기서 항상 확정해 넘긴다.
    """
    target_ts = ts or datetime.now().replace(second=0, microsecond=0)
    target_ts = target_ts.replace(minute=(target_ts.minute // 5) * 5, second=0, microsecond=0)

    argv = _common_argv() + ["--snapshot", "--ts", _fmt_ts(target_ts)]
    elapsed = _run_engine("epanet_mo_gs", argv, f"군산 MO [{target_ts}]")

    return {
        "status": "completed",
        "target_ts": target_ts.isoformat(),
        "elapsed_sec": round(elapsed, 3),
    }


def run_mo_simulation_for_range(
    start_ts: datetime,
    end_ts: datetime,
    db_session: Optional[DbManager] = None,
) -> dict:
    """
    start_ts ~ end_ts 를 5분 간격으로 반복 실행한다. 고산 구현과 결과 형식이 같다.

    군산 엔진은 매 호출마다 3.9MB INP 를 다시 파싱하고 wntr 모델을 다시 만든다.
    gunicorn --timeout 900 을 넘기기 쉬우므로 스텝 수에 상한을 둔다.
    (이 엔드포인트는 프런트가 호출하지 않는다 — 파리티용이다.)
    """
    max_steps = int(current_app.config.get('GUNSAN_MO_BATCH_MAX_STEPS', 24))
    steps = int((end_ts - start_ts).total_seconds() // 300) + 1
    if steps > max_steps:
        raise EngineRequestError(
            f"요청 구간이 너무 깁니다: {steps}스텝 (상한 {max_steps}). "
            "군산 엔진은 매 스텝마다 관망 모델을 다시 읽어 요청 제한시간을 넘깁니다. "
            "구간을 나눠 요청하세요."
        )

    success = fail = total = 0
    current_ts = start_ts
    logger.info(f"군산 MO 배치 시작: {start_ts} ~ {end_ts} ({steps}스텝)")

    while current_ts <= end_ts:
        total += 1
        try:
            run_mo_simulation(ts=current_ts)
            success += 1
        except Exception as e:
            logger.error(f"[FAILURE] [{current_ts}] 군산 MO 실패: {e}")
            logger.error(traceback.format_exc())
            fail += 1
        current_ts += timedelta(minutes=5)

    logger.info(f"군산 MO 배치 완료. 총 {total}건 중 성공 {success}, 실패 {fail}")
    return {
        "status": "completed",
        "total": total,
        "success": success,
        "failed": fail,
    }
