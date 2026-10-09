from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

import config_path as config_path_module
import pump_curve_engine
from config_path import load_config, resolve_config_path


BASE_DIR = Path(__file__).resolve().parent
RUNNER_PATH = BASE_DIR / "run_optimizer.py"
MONITOR_RUNNER_PATH = BASE_DIR / "run_monitor.py"
OUTPUT_DIR = BASE_DIR / "outputs"


# =============================================================================
# 로깅 설정
# =============================================================================
# waitress 는 액세스 로그를 남기지 않는다. 이 서버가 스스로 기록하지 않으면
# 요청이 도달했는지조차 docker logs 로 알 수 없다. 그래서 stdout(docker logs)과
# 파일(outputs/api_server.log) 양쪽에 남긴다. 파일 쪽은 compose 의
# inp-opt-outputs 볼륨에 실려 컨테이너를 다시 만들어도 남는다.
#
# 예측 모듈 MAIN_2026.py 의 RotatingFileHandler 규약을 그대로 따르되,
# 거기 빠져 있는 encoding="utf-8" 을 명시한다.
# (미지정 시 Windows 기본 인코딩으로 기록돼 한글이 깨진다.)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

_file_handler = RotatingFileHandler(
    str(OUTPUT_DIR / "api_server.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setFormatter(_log_formatter)

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_log_formatter)

# 지정 이름 로거가 아니라 root 에 붙인다. 성능곡선 엔진처럼 import 된 모듈이
# logging.getLogger(__name__) 을 쓰더라도 propagate 를 타고 함께 잡히게 하려는 것이다.
# (지정 로거에만 붙이면 그 모듈들의 로그는 핸들러가 없어 그대로 사라진다.)
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
if not _root_logger.handlers:
    _root_logger.addHandler(_file_handler)
    _root_logger.addHandler(_stream_handler)

logger = logging.getLogger(__name__)


app = Flask(__name__)

# 기동 시점에 경로를 확정한다. env 가 없는 파일을 가리키면 여기서 바로 죽는다
# (요청이 들어와야 500 이 나던 예전 동작보다 마운트 누락을 훨씬 빨리 알 수 있다).
_startup_config_path = resolve_config_path()
for _warning in config_path_module.warnings:
    logger.warning(f"[config] {_warning}")
logger.info(config_path_module.describe_config(_startup_config_path))

# 펌프 성능곡선은 러너를 띄우지 않고 이 프로세스에서 바로 계산하므로 설정 내용 자체가 필요하다.
# (최적화/모니터는 경로만 서브프로세스에 넘기면 되니 여기서 파싱하지 않는다.)
# 기동 시 1회만 읽는다. 설정을 바꿨으면 compose 의 --force-recreate 로 컨테이너를 다시 띄운다.
_APP_CONFIG = load_config(_startup_config_path)

# 현장에 맞는 성능곡선 엔진을 기동 시점에 한 번 고정한다(고산/군산). 설정에 키가
# 없으면 고산이다. 로그를 남기는 것은 설정 마운트를 잘못해 엉뚱한 엔진이 떴을 때
# 요청 결과가 아니라 기동 로그에서 먼저 드러나게 하려는 것이다.
_pump_curve = pump_curve_engine.get_engine(_APP_CONFIG)
logger.info(pump_curve_engine.describe_engine(_APP_CONFIG))
_pump_curve.apply_table_config(_APP_CONFIG.get("pump_curve"))


def start_background_process(command: list[str], log_prefix: str) -> tuple[subprocess.Popen, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    api_log_path = OUTPUT_DIR / f"{log_prefix}_{datetime.now():%Y%m%d_%H%M%S}.log"
    log_file = api_log_path.open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(
            command,
            cwd=str(BASE_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
    finally:
        log_file.close()
    return process, api_log_path


@app.get("/health")
def health():
    # 헬스체크는 30초 주기로 들어온다. 로그를 남기면 정작 봐야 할 요청 로그가 밀려나므로 남기지 않는다.
    return jsonify({"status": "OK"})


@app.get("/optimize/<hist_id>")
def optimize(hist_id: str):
    return start_optimizer(hist_id, RUNNER_PATH, "api_optimizer")


def start_optimizer(hist_id: str, runner_path: Path, log_prefix: str):
    hist_id = str(hist_id).strip()
    logger.info(f"[optimize] 요청 histId={hist_id or '(비어 있음)'} runner={runner_path.name}")

    if not hist_id:
        logger.warning("[optimize] histId 가 비어 있어 요청을 거절했다.")
        return jsonify({"accepted": False, "message": "histId가 없습니다."}), 400

    config_path = resolve_config_path()
    if not config_path.exists():
        logger.error(f"[optimize] 설정 파일을 찾지 못했다. histId={hist_id} path={config_path}")
        return (
            jsonify(
                {
                    "accepted": False,
                    "histId": hist_id,
                    "message": f"설정 파일을 찾지 못했습니다. {config_path}",
                }
            ),
            500,
        )

    if not runner_path.exists():
        logger.error(f"[optimize] 실행 파일을 찾지 못했다. histId={hist_id} path={runner_path}")
        return (
            jsonify(
                {
                    "accepted": False,
                    "histId": hist_id,
                    "message": f"실행 파일을 찾지 못했습니다. {runner_path}",
                }
            ),
            500,
        )

    command = [
        sys.executable,
        str(runner_path),
        "--config",
        str(config_path),
        "--hist-id",
        hist_id,
    ]

    try:
        process, api_log_path = start_background_process(command, f"{log_prefix}_{hist_id}")
    except Exception as exc:
        logger.exception(f"[optimize] 러너 기동 실패. histId={hist_id} command={command}")
        return (
            jsonify(
                {
                    "accepted": False,
                    "histId": hist_id,
                    "message": f"최적화 실행을 시작하지 못했습니다. {exc}",
                }
            ),
            500,
        )

    # 러너 자신의 출력은 docker logs 가 아니라 이 파일로만 간다(stdout 을 파일로 리다이렉트하므로).
    # 응답의 logFile 필드를 놓치더라도 여기서 경로를 되찾을 수 있게 남긴다.
    logger.info(f"[optimize] 러너 기동 완료. histId={hist_id} pid={process.pid} log={api_log_path}")

    return jsonify(
        {
            "accepted": True,
            "histId": hist_id,
            "pid": process.pid,
            "config": str(config_path),
            "logFile": str(api_log_path),
        }
    )


@app.get("/monitor/run")
def monitor_run():
    target_ts = request.args.get("target_ts")
    logger.info(f"[monitor] 요청 target_ts={target_ts or '(미지정)'}")

    config_path = resolve_config_path()
    if not config_path.exists():
        logger.error(f"[monitor] 설정 파일을 찾지 못했다. path={config_path}")
        return (
            jsonify(
                {
                    "accepted": False,
                    "message": f"설정 파일을 찾을 수 없습니다. {config_path}",
                }
            ),
            500,
        )

    if not MONITOR_RUNNER_PATH.exists():
        logger.error(f"[monitor] 실행 파일을 찾지 못했다. path={MONITOR_RUNNER_PATH}")
        return (
            jsonify(
                {
                    "accepted": False,
                    "message": f"실행 파일을 찾지 못했습니다. {MONITOR_RUNNER_PATH}",
                }
            ),
            500,
        )

    command = [
        sys.executable,
        str(MONITOR_RUNNER_PATH),
        "--config",
        str(config_path),
    ]
    if target_ts:
        command.extend(["--target-ts", target_ts])

    try:
        process, api_log_path = start_background_process(command, "api_monitor")
    except Exception as exc:
        logger.exception(f"[monitor] 러너 기동 실패. target_ts={target_ts} command={command}")
        return (
            jsonify(
                {
                    "accepted": False,
                    "message": f"모니터링 실행을 시작하지 못했습니다. {exc}",
                }
            ),
            500,
        )

    logger.info(f"[monitor] 러너 기동 완료. pid={process.pid} log={api_log_path}")

    return jsonify(
        {
            "accepted": True,
            "pid": process.pid,
            "config": str(config_path),
            "logFile": str(api_log_path),
        }
    )


def _open_pump_curve_db() -> _pump_curve.DbManager:
    """설정의 db 블록으로 읽기 전용 커넥션을 연다.

    DbManager 가 database/db 두 키를 모두 받으므로 optimizer 설정을 그대로 넘긴다.
    """
    return _pump_curve.DbManager(_APP_CONFIG["db"])


@app.get("/pump-curve/auto/<start_date>/<end_date>/<pump_comb>")
def pump_curve_auto(start_date: str, end_date: str, pump_comb: str):
    """펌프 조합의 실제 운전 데이터로 성능곡선을 자동 산출한다.

    pumpHz 는 "1:45,3:48" 형태의 선택 파라미터다(펌프번호:목표주파수). 군산 엔진은
    이 주파수 ±허용오차 안의 데이터만 쓰고, 고산 엔진은 무시한다. 값의 출처인
    TB_PUMP_CAL C_ORD=2 행은 미입력이면 비어 있으므로 없는 것이 정상 경로다.
    """
    pump_hz = request.args.get("pumpHz")
    logger.info(
        f"[pump-curve/auto] 요청 start={start_date} end={end_date} comb={pump_comb} "
        f"hz={pump_hz or '(미지정)'}"
    )
    try:
        pump_nums = _pump_curve.parse_pump_combination(pump_comb)
        db = _open_pump_curve_db()
        try:
            result = _pump_curve.run_auto(
                db=db,
                start_date=start_date,
                end_date=end_date,
                pump_nums=pump_nums,
                pump_hz=pump_hz,
            )
        finally:
            db.close()
        return jsonify({"status": "success", "result": result})
    except _pump_curve.ScriptError as exc:
        # 업무 예외다(조회 기간에 RAW 가 없다, 좌표가 부족하다 등).
        # 코드 결함이 아니므로 traceback 없이 한 줄만 남긴다.
        logger.warning(
            f"[pump-curve/auto] 산출 불가 start={start_date} end={end_date} comb={pump_comb} - {exc}"
        )
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        # 예상 못 한 결함이다. 원인 추적에 traceback 전체가 필요하다.
        logger.exception(
            f"[pump-curve/auto] 처리 실패 start={start_date} end={end_date} comb={pump_comb}"
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.post("/pump-curve/manual")
def pump_curve_manual():
    """화면에서 입력한 좌표로 성능곡선을 산출하고 같은 기간의 운전 지표를 계산한다."""
    body = request.get_json(silent=True) or {}
    start_date = body.get("startDate") or body.get("start_date")
    end_date = body.get("endDate") or body.get("end_date")
    pump_comb = body.get("pumpComb") or body.get("pump_comb")
    points = body.get("points")
    # auto 와 같은 선택 파라미터. 군산 엔진만 사용하고 고산 엔진은 무시한다.
    pump_hz = body.get("pumpHz") or body.get("pump_hz")

    point_count = len(points) if isinstance(points, (list, tuple)) else "-"
    logger.info(
        f"[pump-curve/manual] 요청 start={start_date} end={end_date} "
        f"comb={pump_comb} points={point_count} hz={pump_hz or '(미지정)'}"
    )

    if not start_date or not end_date or not pump_comb or points is None:
        # 어느 키가 비었는지까지 남긴다. 프론트 전송 누락과 값 형식 오류를 구분하기 위한 것이다.
        missing = [
            name
            for name, value in (
                ("startDate", start_date),
                ("endDate", end_date),
                ("pumpComb", pump_comb),
                ("points", points),
            )
            if not value
        ]
        logger.warning(f"[pump-curve/manual] 필수값 누락 - {', '.join(missing)}")
        return jsonify({
            "status": "error",
            "message": "startDate, endDate, pumpComb, points are required.",
        }), 400

    try:
        pump_nums = _pump_curve.parse_pump_combination(str(pump_comb))
        points_text: Any = points if isinstance(points, str) else json.dumps(points, ensure_ascii=False)
        db = _open_pump_curve_db()
        try:
            result = _pump_curve.run_manual(
                db=db,
                start_date=str(start_date),
                end_date=str(end_date),
                pump_nums=pump_nums,
                points_text=points_text,
                pump_hz=pump_hz,
            )
        finally:
            db.close()
        return jsonify({"status": "success", "result": result})
    except _pump_curve.ScriptError as exc:
        logger.warning(
            f"[pump-curve/manual] 산출 불가 start={start_date} end={end_date} comb={pump_comb} - {exc}"
        )
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception(
            f"[pump-curve/manual] 처리 실패 start={start_date} end={end_date} comb={pump_comb}"
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30092)
