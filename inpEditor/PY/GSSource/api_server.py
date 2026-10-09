from __future__ import annotations

import re
import threading
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

from flask import Flask, jsonify

import MAIN_2026


app = Flask(__name__)

# 기동 시점에 "어떤 설정 파일로 어느 DB에 붙는지"를 stdout(docker logs)과 로그 파일 양쪽에 남긴다.
# 마운트를 빠뜨려 엉뚱한 DB에 붙은 상태를 조용히 지나치지 않기 위한 장치다.
for _warning in MAIN_2026._PATH_WARNINGS:
    print(f"[config] WARNING {_warning}", flush=True)
_startup_config = MAIN_2026.describe_config()
print(_startup_config, flush=True)
MAIN_2026.logger.info(_startup_config)

# 이 API는 가장 최근 재수집 작업 상태만 메모리에 보관한다.
# 실제 예측 결과는 APP_CONFIG 설정 파일에 지정된 DB 테이블에 저장된다.
_job_lock = threading.Lock()
_current_job: dict[str, Any] | None = None


def _parse_date(value: Any) -> date:
    """YYMMDD, YYYYMMDD, YYYY-MM-DD 형식의 날짜 문자열을 해석한다."""
    text = str(value or "").strip()
    if re.fullmatch(r"\d{6}", text):
        return datetime.strptime(text, "%y%m%d").date()
    if re.fullmatch(r"\d{8}", text):
        return datetime.strptime(text, "%Y%m%d").date()
    return datetime.strptime(text, "%Y-%m-%d").date()


def _build_slots(from_day: date, to_day: date) -> list[datetime]:
    """요청 날짜 범위를 10분 단위 예측 기준시각 목록으로 변환한다."""
    if from_day > to_day:
        raise ValueError("from date must be less than or equal to to date")

    current = datetime.combine(from_day, time(0, 0))
    end = datetime.combine(to_day, time(23, 50))
    slots: list[datetime] = []
    while current <= end:
        slots.append(current)
        current += timedelta(minutes=10)
    return slots


def _set_job_status(**updates: Any) -> None:
    """상태 조회 API에서 사용할 메모리 작업 상태를 갱신한다."""
    global _current_job
    with _job_lock:
        if _current_job is not None:
            _current_job.update(updates)


def _run_rebuild(job_id: str, slots: list[datetime]) -> None:
    """과거 예측 재수집을 백그라운드에서 실행한다.

    저장은 MAIN_2026.upload_tag_pred_l()의 INSERT IGNORE 방식을 그대로 사용한다.
    그래서 이미 존재하는 예측 row는 유지되고, 누락된 row만 추가된다.
    """
    inserted_total = 0
    requested_total = 0
    failures: list[dict[str, Any]] = []

    _set_job_status(status="RUNNING", startedAt=datetime.now().isoformat(timespec="seconds"))

    for index, slot in enumerate(slots, start=1):
        _set_job_status(current=index, currentTarget=slot.strftime("%Y-%m-%d %H:%M:%S"))
        result = MAIN_2026.run_prediction(target_ts=slot, enable_pump_routing=False)

        if result.get("success"):
            upload = result.get("upload") or {}
            requested_total += int(upload.get("requested") or 0)
            inserted_total += int(upload.get("inserted") or 0)
        else:
            failures.append(
                {
                    "target": slot.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": result.get("message"),
                }
            )

    status = "COMPLETE" if not failures else "COMPLETE_WITH_ERROR"
    _set_job_status(
        status=status,
        finishedAt=datetime.now().isoformat(timespec="seconds"),
        requestedRows=requested_total,
        insertedRows=inserted_total,
        failures=failures,
        message="INSERT IGNORE keeps existing rows and inserts only missing rows.",
    )


@app.get("/health")
def health():
    """API 서버 생존 여부를 확인하는 간단한 엔드포인트."""
    return jsonify({"status": "OK"})


def _start_rebuild(from_value: str, to_value: str):
    """요청 날짜를 검증하고 작업 상태를 만든 뒤 백그라운드 작업을 시작한다."""
    global _current_job

    if not from_value or not to_value:
        return jsonify({"status": "ERROR", "message": "from and to are required. Example: 250101, 2025-01-01"}), 400

    try:
        from_day = _parse_date(from_value)
        to_day = _parse_date(to_value)
        slots = _build_slots(from_day, to_day)
    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400

    with _job_lock:
        # READY(시작 대기)와 RUNNING(실행 중)을 모두 진행 중으로 간주해 중복 실행을 막는다.
        # RUNNING만 검사하면 스레드가 상태를 전환하기 전 윈도우에서 두 번째 요청이 통과해
        # 재수집 스레드가 동시에 두 개 뜰 수 있다.
        if _current_job and _current_job.get("status") in ("READY", "RUNNING"):
            return jsonify({"status": "ERROR", "message": "another rebuild job is already running", "job": _current_job}), 409

        job_id = uuid.uuid4().hex
        _current_job = {
            "jobId": job_id,
            "status": "READY",
            "from": from_day.isoformat(),
            "to": to_day.isoformat(),
            "total": len(slots),
            "current": 0,
            "createdAt": datetime.now().isoformat(timespec="seconds"),
        }
        # 백그라운드 스레드가 같은 dict를 동시에 수정하므로,
        # lock 안에서 응답용 스냅샷을 복사해 직렬화 중 데이터 레이스를 피한다.
        job_snapshot = dict(_current_job)

    thread = threading.Thread(target=_run_rebuild, args=(job_id, slots), daemon=True)
    thread.start()

    return jsonify(job_snapshot), 202


@app.get("/predict/rebuild/<from_value>/<to_value>")
def rebuild_predictions(from_value: str, to_value: str):
    """과거 예측 재수집을 시작한다.

    호출 예시:
      GET /predict/rebuild/260409/260410
      GET /predict/rebuild/20260409/20260410
      GET /predict/rebuild/2026-04-09/2026-04-10
    """
    return _start_rebuild(from_value, to_value)


@app.get("/predict/rebuild/status")
def rebuild_status():
    """최근 재수집 작업의 메모리 상태를 반환한다."""
    with _job_lock:
        if _current_job is None:
            return jsonify({"status": "EMPTY", "message": "no rebuild job has been started"})
        return jsonify(dict(_current_job))


if __name__ == "__main__":
    app_config = MAIN_2026.get_app_config()
    api_config = app_config.get("api", {}) if isinstance(app_config.get("api", {}), dict) else {}
    app.run(host=api_config.get("host", "0.0.0.0"), port=int(api_config.get("port", 30093)))
