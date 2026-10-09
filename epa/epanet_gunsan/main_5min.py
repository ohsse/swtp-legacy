from __future__ import annotations

import argparse
import json
import logging
import math
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pymysql
from pymysql.cursors import DictCursor


LOGGER = logging.getLogger("gunsan_control")

RAW_TABLE = "TB_RAWDATA"
PRED_TABLE = "TB_CTR_TNK_RST"
RULE_TABLE = "TB_CTRL_RULE_CFG"
CMD_TABLE = "TB_CTRL_CMD_RST"
RATE_TABLE = "TB_RT_RATE_INF"
PUMP_CAL_TABLE = "TB_PUMP_CAL"
WPP_TAG_CODE_TABLE = "TB_WPP_TAG_CODE"
EPA_TOTAL_TABLE = "TB_TOT_ALG"
EPA_FLOW_TABLE = "TB_FR_VAL"
EPA_PUMP_FLOW_LINK_ID = "45"
PUMP_HORIZONS = (1, 5, 15, 30)


LOCK_NAME = "GUNSAN_CTRL_5MIN"

# 섀도우 스택용 테이블 전환(2026-09-29, 벤더 드롭마다 재적용: 2026-09-30, 2026-10-01). 기본값이면 위 운영 테이블 그대로다.
#   --prediction-table : 수요예측 조회 테이블 (섀도우 TB_CTR_TNK_RST_SH)
#   --cmd-table        : 추천 저장·직전 추천 조회 테이블 (섀도우 TB_CTRL_CMD_RST_SH)
# 실측(TB_RAWDATA)·규칙(TB_CTRL_RULE_CFG)·요금(TB_RT_RATE_INF)·성능곡선(TB_PUMP_CAL)·EPA PRE 결과(TB_TOT_ALG/TB_FR_VAL)는
# 읽기만 하므로 운영 테이블을 쓴다.
# 저장 테이블이 기본값이 아니면 DB 잠금 이름도 갈라, 같은 DB 의 운영 루프와 서로 막지 않게 한다.
_TABLE_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def configure_tables(args) -> None:
    global PRED_TABLE, CMD_TABLE, LOCK_NAME
    for opt, value in (("--prediction-table", args.prediction_table), ("--cmd-table", args.cmd_table)):
        if not _TABLE_NAME_RE.match(value or ""):
            raise ValueError(f"{opt} 테이블명이 올바르지 않습니다: {value!r}")
    PRED_TABLE = args.prediction_table
    if args.cmd_table != CMD_TABLE:
        LOCK_NAME = f"{LOCK_NAME}:{args.cmd_table}"
    CMD_TABLE = args.cmd_table


NORMAL_CONTROL_CYCLES = 2  # 5분 판단 기준 정상 제어 최소간격 = 10분

TAGS = {
    "clearwell_1": "891-365-LEI-4000",
    "clearwell_2": "891-365-LEI-4001",

    "naun_level_1": "891-365-LEI-8600",
    "naun_level_2": "891-365-LEI-8601",

    "osik_level_1": "891-365-LEI-8652",
    "osik_level_2": "891-365-LEI-8653",

    "send_flow": "891-365-FRI-8950",
    "send_pressure": "891-365-PRI-4000",

    "naun_inflow": "891-365-FRI-8600",
    "osik_inflow": "891-365-FRI-8652",
    "osik_outflow": "891-365-FRI-8653",

    "national_flow": "891-365-FRI-8602",
    "gunjang_flow": "891-365-FRI-8802",

    "local_valve": "891-365-POI-8600",
    "national_valve": "891-365-POI-8601",

    "pump1_run": "891-365-PMB-4017",
    "pump2_run": "891-365-PMB-4022",
    "pump3_run": "891-365-PMB-4027",
    "pump4_run": "891-365-PMB-4032",

    "pump1_hz": "891-365-SPI-4000",
    "pump2_hz": "891-365-SPI-4001",
    "pump3_hz": "891-365-SPI-4002",
    "pump4_hz": "891-365-SPI-4003",
}

PUMPS = [
    (1, TAGS["pump1_run"], TAGS["pump1_hz"]),
    (2, TAGS["pump2_run"], TAGS["pump2_hz"]),
    (3, TAGS["pump3_run"], TAGS["pump3_hz"]),
    (4, TAGS["pump4_run"], TAGS["pump4_hz"]),
]

PRED_IDS = [
    "Q_GunS_Predict",
    "P_GunS_Predict",
    "Q2_Predict",
    "Q7_Predict",
    "Q4_Predict",
    "Q8_Predict",
]


@dataclass(frozen=True)
class Reading:
    ts: datetime
    value: float


@dataclass
class ReservoirState:
    name: str
    level: float
    trend_mph: Optional[float]
    target: Optional[float]
    state: str
    direction: int
    error: float
    sensor_diff: Optional[float]
    single_sensor: bool
    projected_level: Optional[float] = None
    hard_low: Optional[float] = None
    hard_high: Optional[float] = None
    soft_low: Optional[float] = None
    soft_high: Optional[float] = None
    danger: bool = False


@dataclass
class DeviceCommand:
    cmd_yn: str = "N"
    status: str = "NO_COMMAND"
    current: Optional[float] = None
    target: Optional[float] = None
    observe_until: Optional[datetime] = None


@dataclass
class PumpBaseRecommendation:
    pred_q: float
    pred_p: float
    pump_grp: Any
    c_idx: Any
    pump_comb: str
    freq_hz: float
    nearest_q: float
    nearest_p: float
    distance: float


def load_db_config(path: str, key: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and key in data and isinstance(data[key], dict):
        cfg = dict(data[key])
    elif isinstance(data, dict) and all(
            k in data for k in ("host", "port", "user", "password")
    ) and ("db" in data or "database" in data):
        cfg = dict(data)
    else:
        raise KeyError(
            f'connections.json에서 "{key}" 키를 찾을 수 없거나 DB 접속정보 형식이 다릅니다.'
        )

    cfg.setdefault("port", 3306)
    return cfg


def connect_db(cfg: Dict[str, Any]):
    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg.get("port", 3306)),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg.get("db") or cfg.get("database"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=10,
        read_timeout=60,
        write_timeout=60,
    )


def fetchone(conn, sql: str, params: Sequence[Any] = ()) -> Optional[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetchall(conn, sql: str, params: Sequence[Any] = ()) -> List[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(conn, sql: str, params: Sequence[Any] = ()) -> int:
    with conn.cursor() as cur:
        return cur.execute(sql, params)


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def floor_5min(ts: datetime) -> datetime:
    return ts.replace(minute=(ts.minute // 5) * 5, second=0, microsecond=0)


def load_rules(conn) -> Dict[str, Any]:
    rows = fetchall(
        conn,
        f"""
        SELECT PARAM_KEY, VALUE_NUM, VALUE_TEXT
        FROM {RULE_TABLE}
        WHERE USE_YN = 'Y'
        """,
    )
    rules: Dict[str, Any] = {}
    for row in rows:
        key = str(row["PARAM_KEY"])
        if row.get("VALUE_NUM") is not None:
            rules[key] = float(row["VALUE_NUM"])
        else:
            rules[key] = row.get("VALUE_TEXT")

    required = [
        "CONTROL_CYCLE_MIN",
        "NAUN_LEVEL_MIN", "NAUN_LEVEL_MAX", "NAUN_LEVEL_TOLERANCE",
        "OSIK_LEVEL_MIN", "OSIK_LEVEL_MAX", "OSIK_LEVEL_TOLERANCE",
        "CLEARWELL_LEVEL_MIN", "CLEARWELL_LEVEL_MAX", "CLEARWELL_TOLERANCE",
        "LEVEL_SENSOR_DIFF_LIMIT",
        "PUMP_FREQ_MIN", "PUMP_FREQ_MAX",
        "PUMP_COARSE_STEP", "PUMP_FINE_STEP", "PUMP_OBSERVE_MIN",
        "NATIONAL_VALVE_MIN", "NATIONAL_VALVE_MAX",
        "LOCAL_VALVE_MIN", "LOCAL_VALVE_MAX",
        "VALVE_STEP", "VALVE_OBSERVE_MIN",
        "LOCAL_VALVE_STEP", "LOCAL_VALVE_OBSERVE_MIN",
        "LOCAL_TRIGGER_LEVEL", "LOCAL_FORCE_CLOSE_LEVEL",
        "LOCAL_RECOVERY_LEVEL", "LOCAL_RECOVERY_STABLE_MIN",
        "PRED_STALE_MIN", "RATE_IDX",
        "MORNING_TARGET_TIME",
        "NAUN_MORNING_TARGET", "OSIK_MORNING_TARGET",
    ]
    missing = [k for k in required if k not in rules]
    if missing:
        raise RuntimeError(f"{RULE_TABLE} 필수 설정값 누락: {', '.join(missing)}")

    # 배수지 수위추세의 미세한 노이즈를 상승/하강으로 오인하지 않기 위한 불감대(m/h).
    # DB에 PARAM_KEY가 있으면 그 값을 사용하고, 없으면 초기 기본값 0.01 m/h를 사용한다.
    rules.setdefault("LEVEL_TREND_DEADBAND_MPH", 0.01)
    # EPANET PRE 결과는 현재 m3/h, m 단위로 저장한다. TB_PUMP_CAL의 Q/P 단위가
    # 다를 경우 아래 선택 설정값으로 환산할 수 있다. 기본은 동일단위(1.0).
    rules.setdefault("EPA_Q_SCALE", 1.0)
    rules.setdefault("EPA_P_SCALE", 1.0)

    return rules


def latest_readings(
        conn,
        tags: Sequence[str],
        target: datetime,
        lookback_min: int,
) -> Dict[str, Reading]:
    if not tags:
        return {}

    placeholders = ",".join(["%s"] * len(tags))
    since = target - timedelta(minutes=lookback_min)
    rows = fetchall(
        conn,
        f"""
        SELECT r.TAGNAME, r.TS, r.VALUE
        FROM {RAW_TABLE} r
        JOIN (
            SELECT TAGNAME, MAX(TS) AS TS
            FROM {RAW_TABLE}
            WHERE TS >= %s
              AND TS <= %s
              AND TAGNAME IN ({placeholders})
            GROUP BY TAGNAME
        ) x
          ON r.TAGNAME = x.TAGNAME
         AND r.TS = x.TS
        """,
        (since, target, *tags),
    )

    result: Dict[str, Reading] = {}
    for row in rows:
        v = as_float(row.get("VALUE"))
        if v is None:
            continue
        result[str(row["TAGNAME"])] = Reading(row["TS"], v)
    return result


def reading_at_or_before(
        conn,
        tag: str,
        target: datetime,
        lookback_min: int = 15,
) -> Optional[Reading]:
    row = fetchone(
        conn,
        f"""
        SELECT TS, VALUE
        FROM {RAW_TABLE}
        WHERE TAGNAME = %s
          AND TS <= %s
          AND TS >= %s
        ORDER BY TS DESC
        LIMIT 1
        """,
        (tag, target, target - timedelta(minutes=lookback_min)),
    )
    if not row:
        return None
    v = as_float(row.get("VALUE"))
    if v is None:
        return None
    return Reading(row["TS"], v)


def valid_level_value(v: Optional[float]) -> bool:
    return v is not None and math.isfinite(v) and v > 0.0


def pair_level_from_readings(
        readings: Dict[str, Reading],
        tag1: str,
        tag2: str,
        diff_limit: float,
) -> Tuple[Optional[float], Optional[float], bool, bool]:
    r1 = readings.get(tag1)
    r2 = readings.get(tag2)
    v1 = r1.value if r1 else None
    v2 = r2.value if r2 else None

    ok1 = valid_level_value(v1)
    ok2 = valid_level_value(v2)

    if not ok1 and not ok2:
        return None, None, False, True

    if ok1 and not ok2:
        return float(v1), None, True, False

    if ok2 and not ok1:
        return float(v2), None, True, False

    assert v1 is not None and v2 is not None
    diff = abs(float(v1) - float(v2))
    hold = diff >= diff_limit
    return max(float(v1), float(v2)), diff, False, hold


def pair_level_at(
        conn,
        tag1: str,
        tag2: str,
        target: datetime,
        diff_limit: float,
        lookback_min: int = 15,
) -> Tuple[Optional[float], Optional[float], bool, bool]:
    r1 = reading_at_or_before(conn, tag1, target, lookback_min)
    r2 = reading_at_or_before(conn, tag2, target, lookback_min)
    readings = {}
    if r1:
        readings[tag1] = r1
    if r2:
        readings[tag2] = r2
    return pair_level_from_readings(readings, tag1, tag2, diff_limit)


def level_trend_15m(
        conn,
        current_level: float,
        tag1: str,
        tag2: str,
        target: datetime,
        diff_limit: float,
) -> Optional[float]:
    prev_target = target - timedelta(minutes=15)
    prev_level, _, _, prev_hold = pair_level_at(
        conn, tag1, tag2, prev_target, diff_limit, lookback_min=10
    )
    if prev_level is None or prev_hold:
        return None
    return (current_level - prev_level) / 0.25


def get_latest_predictions(
        conn,
        target: datetime,
        pred_stale_min: float,
) -> Tuple[Dict[str, dict], bool]:
    placeholders = ",".join(["%s"] * len(PRED_IDS))
    rows = fetchall(
        conn,
        f"""
        SELECT p.*
        FROM {PRED_TABLE} p
        JOIN (
            SELECT DSTRB_ID, MAX(RGSTR_TIME) AS RGSTR_TIME
            FROM {PRED_TABLE}
            WHERE DSTRB_ID IN ({placeholders})
              AND RGSTR_TIME <= %s
            GROUP BY DSTRB_ID
        ) x
          ON p.DSTRB_ID = x.DSTRB_ID
         AND p.RGSTR_TIME = x.RGSTR_TIME
        """,
        (*PRED_IDS, target),
    )

    result = {str(r["DSTRB_ID"]): r for r in rows}
    stale = False
    for pid in PRED_IDS:
        row = result.get(pid)
        if not row or row.get("RGSTR_TIME") is None:
            stale = True
            continue
        age = (target - row["RGSTR_TIME"]).total_seconds() / 60.0
        row["_AGE_MIN"] = age
        if age > pred_stale_min:
            stale = True
    return result, stale

def prediction_value(
        predictions: Dict[str, dict],
        pred_id: str,
        horizon_min: int,
) -> Optional[float]:
    """TB_CTR_TNK_RST의 1/5/15/30분 값을 읽는다. 1분은 PRDCT_VALUE도 허용."""
    row = predictions.get(pred_id)
    if not row:
        return None
    key_map = {str(k).upper(): k for k in row.keys()}
    candidates = (
        ("VALUE_1MIN", "PRDCT_VALUE") if horizon_min == 1
        else (f"VALUE_{horizon_min}MIN",)
    )
    for candidate in candidates:
        actual = key_map.get(candidate.upper())
        if actual is None:
            continue
        value = as_float(row.get(actual))
        if value is not None:
            return value
    return None


def parse_frequency_combo(value: Any) -> Optional[float]:
    if value is None:
        return None
    vals: List[float] = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            v = float(part)
        except (TypeError, ValueError):
            continue
        if math.isfinite(v) and v > 0:
            vals.append(v)
    return sum(vals) / len(vals) if vals else None


def normalize_combination(value: Any) -> str:
    if value is None:
        return ""
    nums: List[int] = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            nums.append(int(float(part)))
        except (TypeError, ValueError):
            return str(value).strip()
    return ",".join(str(x) for x in sorted(set(nums)))


def load_pump_curve_candidates(conn, pump_count: Optional[int] = None) -> List[dict]:
    rows = fetchall(
        conn,
        f"""
        SELECT PUMP_GRP, C_IDX, C_ORD, FC_VAL,
               P_ADD_VAL, P_MUL_VAL, P_SQRT_MUL_VAL,
               PUMP_COMB, PUMP_COUNT, PUMP_PRIORITY, COUNT_IDX,
               FC_MIN_VAL, FC_MAX_VAL, avg_error_rate, data_count
        FROM {PUMP_CAL_TABLE}
        -- TB_PUMP_CAL.USE_YN 은 int(1) 이다. 'Y' 비교는 0 으로 캐스팅돼 비활성 곡선만 뽑힌다.
        -- 벤더 드롭은 'Y' 로 오므로 받을 때마다 1 로 재적용한다 (사용자 확정 2026-10-01).
        WHERE USE_YN = 1
        ORDER BY PUMP_GRP, C_IDX, C_ORD
        """,
    )
    grouped: Dict[Tuple[Any, Any], List[dict]] = {}
    for row in rows:
        grouped.setdefault((row.get("PUMP_GRP"), row.get("C_IDX")), []).append(row)

    candidates: List[dict] = []
    for (pump_grp, c_idx), group in grouped.items():
        ord1 = next((r for r in group if int(r.get("C_ORD") or 0) == 1), None)
        ord2 = next((r for r in group if int(r.get("C_ORD") or 0) == 2), None)
        if ord1 is None or ord2 is None:
            continue
        pump_comb = normalize_combination(ord1.get("PUMP_COMB"))
        freq_hz = parse_frequency_combo(ord2.get("PUMP_COMB"))
        if not pump_comb or freq_hz is None:
            continue
        coeff_row = next((r for r in group
                          if as_float(r.get("P_ADD_VAL")) is not None
                          and as_float(r.get("P_MUL_VAL")) is not None
                          and as_float(r.get("P_SQRT_MUL_VAL")) is not None), None)
        if coeff_row is None:
            continue
        c = as_float(coeff_row.get("P_ADD_VAL"))
        b = as_float(coeff_row.get("P_MUL_VAL"))
        a = as_float(coeff_row.get("P_SQRT_MUL_VAL"))
        if a is None or b is None or c is None:
            continue
        q_min_vals = [as_float(r.get("FC_MIN_VAL")) for r in group if as_float(r.get("FC_MIN_VAL")) is not None]
        q_max_vals = [as_float(r.get("FC_MAX_VAL")) for r in group if as_float(r.get("FC_MAX_VAL")) is not None]
        if q_min_vals and q_max_vals:
            q_min, q_max = min(q_min_vals), max(q_max_vals)
        else:
            fc_vals = [as_float(r.get("FC_VAL")) for r in group if as_float(r.get("FC_VAL")) is not None]
            if len(fc_vals) < 2:
                continue
            q_min, q_max = min(fc_vals), max(fc_vals)
        if q_max <= q_min:
            continue
        row_pump_count = as_float(ord1.get("PUMP_COUNT"))
        if row_pump_count is None:
            row_pump_count = float(len([x for x in pump_comb.split(",") if x.strip()]))
        candidates.append({
            "pump_grp": pump_grp, "c_idx": c_idx, "pump_comb": pump_comb,
            "freq_hz": float(freq_hz), "pump_count": int(round(row_pump_count)),
            "q_min": float(q_min), "q_max": float(q_max),
            "a": float(a), "b": float(b), "c": float(c),
        })
    if pump_count is not None and pump_count > 0:
        same = [c for c in candidates if c["pump_count"] == pump_count]
        if same:
            candidates = same
    return candidates


def curve_pressure(candidate: dict, q: float) -> float:
    return candidate["c"] + candidate["b"] * q + candidate["a"] * q * q


def nearest_qp_curve(
        pred_q: float,
        pred_p: float,
        candidates: List[dict],
        samples_per_curve: int = 201,
) -> Optional[PumpBaseRecommendation]:
    if not candidates:
        return None
    sampled: List[Tuple[dict, float, float]] = []
    for candidate in candidates:
        q_min, q_max = float(candidate["q_min"]), float(candidate["q_max"])
        steps = max(samples_per_curve - 1, 1)
        for i in range(samples_per_curve):
            q = q_min + (q_max - q_min) * i / steps
            p = curve_pressure(candidate, q)
            if math.isfinite(q) and math.isfinite(p):
                sampled.append((candidate, q, p))
    if not sampled:
        return None
    q_values = [q for _, q, _ in sampled]
    p_values = [p for _, _, p in sampled]
    q_scale = max(max(q_values) - min(q_values), 1.0)
    p_scale = max(max(p_values) - min(p_values), 0.01)
    best = None
    for candidate, q, p in sampled:
        distance = math.hypot((pred_q - q) / q_scale, (pred_p - p) / p_scale)
        if best is None or distance < best[0]:
            best = (distance, candidate, q, p)
    if best is None:
        return None
    distance, candidate, near_q, near_p = best
    return PumpBaseRecommendation(
        pred_q=float(pred_q), pred_p=float(pred_p),
        pump_grp=candidate["pump_grp"], c_idx=candidate["c_idx"],
        pump_comb=str(candidate["pump_comb"]), freq_hz=float(candidate["freq_hz"]),
        nearest_q=float(near_q), nearest_p=float(near_p), distance=float(distance),
    )


def get_pump_source_mode(conn) -> int:
    """TB_WPP_TAG_CODE EPA_PUMP.DEFAULT_VALUE: 0=AI 직접, 1=EPANET PRE."""
    rows = fetchall(
        conn,
        f"SELECT DEFAULT_VALUE FROM {WPP_TAG_CODE_TABLE} WHERE FUNC_TYP = %s",
        ("EPA_PUMP",),
    )
    values = set()
    for row in rows:
        try:
            values.add(int(float(row.get("DEFAULT_VALUE"))))
        except (TypeError, ValueError):
            continue
    if not values:
        raise RuntimeError(f"{WPP_TAG_CODE_TABLE}에서 FUNC_TYP='EPA_PUMP' DEFAULT_VALUE를 찾지 못했습니다.")
    if len(values) != 1 or next(iter(values)) not in (0, 1):
        raise RuntimeError(f"EPA_PUMP DEFAULT_VALUE는 0 또는 1 하나여야 합니다: {sorted(values)}")
    return next(iter(values))


def direct_qp_horizons(
        predictions: Dict[str, dict],
        target: datetime,
        stale_min: float,
) -> Tuple[Dict[int, Tuple[float, float]], datetime]:
    qrow = predictions.get("Q_GunS_Predict")
    prow = predictions.get("P_GunS_Predict")
    if not qrow or not prow:
        raise RuntimeError("Q_GunS_Predict/P_GunS_Predict 예측행이 없습니다.")
    stamps = []
    for row in (qrow, prow):
        ts = row.get("RGSTR_TIME")
        if ts is None:
            raise RuntimeError("Q/P 예측 RGSTR_TIME이 없습니다.")
        if not isinstance(ts, datetime):
            ts = datetime.fromisoformat(str(ts))
        age = (target - ts).total_seconds() / 60.0
        if age < -0.1 or age > stale_min:
            raise RuntimeError(f"Q/P 예측이 허용시간 밖입니다: age={age:.1f}분")
        stamps.append(ts)
    values: Dict[int, Tuple[float, float]] = {}
    for h in PUMP_HORIZONS:
        q = prediction_value(predictions, "Q_GunS_Predict", h)
        p = prediction_value(predictions, "P_GunS_Predict", h)
        if q is None or p is None or q <= 0 or p <= 0:
            raise RuntimeError(f"AI {h}분 Q/P 예측값이 없거나 0 이하입니다: Q={q}, P={p}")
        values[h] = (q, p)
    return values, max(stamps)


def epa_qp_horizons(
        conn,
        target: datetime,
        stale_min: float,
        rules: Dict[str, Any],
) -> Tuple[Dict[int, Tuple[float, float]], datetime]:
    total = fetchone(
        conn,
        f"""
        SELECT * FROM {EPA_TOTAL_TABLE}
        WHERE FLG='PRE'
          AND RGSTR_TIME >= %s
          AND RGSTR_TIME < %s
        ORDER BY RGSTR_TIME DESC
        LIMIT 1
        """,
        (target, target + timedelta(minutes=5)),
    )
    if not total:
        raise RuntimeError("EPANET PRE TB_TOT_ALG 결과가 없습니다.")
    ts = total.get("RGSTR_TIME")
    if not isinstance(ts, datetime):
        ts = datetime.fromisoformat(str(ts))
    # EPA PRE는 해당 제어기준시각(ctrl_ts)의 예측묶음을 main_epa_gs가
    # +1~+4분 슬롯에 해석한 결과만 사용한다. 직전 회차 PRE를 재사용하지 않는다.
    slot_delay = (ts - target).total_seconds() / 60.0
    if slot_delay < 0 or slot_delay >= 5:
        raise RuntimeError(f"EPANET PRE 결과시각이 현재 제어슬롯과 맞지 않습니다: delay={slot_delay:.1f}분")

    flow = fetchone(
        conn,
        f"""
        SELECT * FROM {EPA_FLOW_TABLE}
        WHERE FLG='PRE' AND RGSTR_TIME=%s AND LINK_ID=%s
        LIMIT 1
        """,
        (ts, EPA_PUMP_FLOW_LINK_ID),
    )
    if not flow:
        raise RuntimeError(f"EPANET PRE 송수 LINK_ID={EPA_PUMP_FLOW_LINK_ID} 결과가 없습니다.")

    q_scale = float(rules.get("EPA_Q_SCALE", 1.0))
    p_scale = float(rules.get("EPA_P_SCALE", 1.0))
    values: Dict[int, Tuple[float, float]] = {}
    for h in PUMP_HORIZONS:
        q = as_float(flow.get(f"FLW_ALG_RST_VAL_{h}MIN"))
        p = as_float(total.get(f"FP_ALG_RST_VAL_{h}MIN"))
        if q is None or p is None:
            raise RuntimeError(f"EPANET PRE {h}분 Q/P 결과가 없습니다.")
        q = abs(q) * q_scale
        p = p * p_scale
        if q <= 0 or p <= 0:
            raise RuntimeError(f"EPANET PRE {h}분 Q/P가 0 이하입니다: Q={q}, P={p}")
        values[h] = (q, p)
    return values, ts


def qp_recommendations(
        conn,
        qp_values: Dict[int, Tuple[float, float]],
        active_pump_count: int,
        rules: Dict[str, Any],
) -> Dict[int, PumpBaseRecommendation]:
    candidates = load_pump_curve_candidates(
        conn,
        pump_count=active_pump_count if active_pump_count > 0 else None,
    )
    if not candidates:
        raise RuntimeError("TB_PUMP_CAL에서 사용 가능한 펌프 성능곡선을 찾지 못했습니다.")
    result: Dict[int, PumpBaseRecommendation] = {}
    for h in PUMP_HORIZONS:
        q, p = qp_values[h]
        rec = nearest_qp_curve(q, p, candidates)
        if rec is None:
            raise RuntimeError(f"{h}분 Q/P에 대한 펌프 성능곡선 매칭 실패")
        rec.freq_hz = min(
            max(rec.freq_hz, float(rules["PUMP_FREQ_MIN"])),
            float(rules["PUMP_FREQ_MAX"]),
        )
        result[h] = rec
    return result


def hz_direction(target_hz: Optional[float], current_hz: Optional[float], deadband: float = 0.5) -> int:
    if target_hz is None or current_hz is None:
        return 0
    delta = target_hz - current_hz
    if abs(delta) < deadband:
        return 0
    return 1 if delta > 0 else -1


def response_ok_for_pump_base(conn, last: dict, target: datetime) -> Optional[bool]:
    """Q/P Base 제어 후 군산정수장 송수유량이 명령 방향으로 반응했는지 확인."""
    cur_hz = as_float(last.get("PUMP_CUR_HZ"))
    tgt_hz = as_float(last.get("PUMP_TGT_HZ"))
    if cur_hz is None or tgt_hz is None:
        return None
    direction = 1 if tgt_hz > cur_hz else -1 if tgt_hz < cur_hz else 0
    if direction == 0:
        return True
    base_send = reading_at_or_before(conn, TAGS["send_flow"], last["CTRL_TS"], lookback_min=5)
    now_send = reading_at_or_before(conn, TAGS["send_flow"], target, lookback_min=5)
    if not base_send or not now_send:
        return None
    return (now_send.value - base_send.value) * direction > 0



def parse_hhmm(value: Any) -> int:
    if value is None:
        raise ValueError("STN_TM 값이 NULL입니다.")

    if isinstance(value, dt_time):
        return value.hour * 60 + value.minute

    if isinstance(value, timedelta):
        return int(value.total_seconds() // 60) % (24 * 60)

    if isinstance(value, (int, float)):
        n = int(value)
        if 0 <= n <= 23:
            return n * 60
        if 0 <= n <= 2359:
            hh = n // 100
            mm = n % 100
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return hh * 60 + mm

    s = str(value).strip()
    if ":" in s:
        parts = s.split(":")
        hh = int(parts[0])
        mm = int(parts[1])
        return hh * 60 + mm

    n = int(float(s))
    return parse_hhmm(n)


def get_rate_schedule(conn, rate_idx: int, month: int) -> List[Tuple[int, str]]:
    rows = fetchall(
        conn,
        f"""
        SELECT STN_TM, TIMEZONE
        FROM {RATE_TABLE}
        WHERE RATE_IDX = %s
          AND MNTH = %s
        ORDER BY STN_TM
        """,
        (rate_idx, month),
    )
    schedule: List[Tuple[int, str]] = []
    for row in rows:
        try:
            minute = parse_hhmm(row["STN_TM"])
        except Exception:
            continue
        zone = str(row["TIMEZONE"]).strip().upper()
        if zone not in {"L", "M", "H"}:
            continue
        schedule.append((minute, zone))

    if not schedule:
        raise RuntimeError(
            f"{RATE_TABLE}에서 RATE_IDX={rate_idx}, MNTH={month}의 시간대 정보를 찾지 못했습니다."
        )

    dedup: Dict[int, str] = {}
    for minute, zone in schedule:
        dedup[minute] = zone
    return sorted(dedup.items())


def timezone_at(schedule: List[Tuple[int, str]], minute_of_day: int) -> str:
    selected = schedule[-1][1]
    for minute, zone in schedule:
        if minute <= minute_of_day:
            selected = zone
        else:
            break
    return selected


def latest_offpeak_start(conn, target: datetime, rate_idx: int) -> Tuple[str, Optional[datetime]]:
    today_schedule = get_rate_schedule(conn, rate_idx, target.month)
    minute_now = target.hour * 60 + target.minute
    current_zone = timezone_at(today_schedule, minute_now)

    if current_zone != "L":
        return current_zone, None

    events: List[Tuple[datetime, str, str]] = []

    for d in [target.date() - timedelta(days=1), target.date()]:
        sched = get_rate_schedule(conn, rate_idx, d.month)
        prev_zone = sched[-1][1]
        for minute, zone in sched:
            event_dt = datetime.combine(d, dt_time(hour=minute // 60, minute=minute % 60))
            events.append((event_dt, prev_zone, zone))
            prev_zone = zone

    candidates = [
        dt for dt, prev, zone in events
        if dt <= target and zone == "L" and prev != "L"
    ]
    return current_zone, max(candidates) if candidates else None


def parse_target_time(value: Any) -> dt_time:
    s = str(value).strip()
    hh, mm = [int(x) for x in s.split(":")[:2]]
    return dt_time(hour=hh, minute=mm)


def morning_trajectory(
        conn,
        target: datetime,
        rules: Dict[str, Any],
        diff_limit: float,
) -> Tuple[bool, Dict[str, float], Optional[datetime], Optional[datetime], List[str]]:
    reasons: List[str] = []
    rate_idx = int(rules["RATE_IDX"])
    timezone, offpeak_start = latest_offpeak_start(conn, target, rate_idx)

    if timezone != "L" or offpeak_start is None:
        return False, {}, offpeak_start, None, reasons

    target_clock = parse_target_time(rules["MORNING_TARGET_TIME"])
    target_dt = datetime.combine(offpeak_start.date(), target_clock)
    if target_dt <= offpeak_start:
        target_dt += timedelta(days=1)

    if not (offpeak_start <= target < target_dt):
        return False, {}, offpeak_start, target_dt, reasons

    naun_start, _, _, naun_hold = pair_level_at(
        conn,
        TAGS["naun_level_1"],
        TAGS["naun_level_2"],
        offpeak_start,
        diff_limit,
        lookback_min=15,
    )
    osik_start, _, _, osik_hold = pair_level_at(
        conn,
        TAGS["osik_level_1"],
        TAGS["osik_level_2"],
        offpeak_start,
        diff_limit,
        lookback_min=15,
    )

    if naun_start is None or osik_start is None or naun_hold or osik_hold:
        reasons.append("FILL_START_DATA_CHECK")
        return False, {}, offpeak_start, target_dt, reasons

    elapsed = (target - offpeak_start).total_seconds()
    total = (target_dt - offpeak_start).total_seconds()
    ratio = min(max(elapsed / total, 0.0), 1.0)

    naun_goal = float(rules["NAUN_MORNING_TARGET"])
    osik_goal = float(rules["OSIK_MORNING_TARGET"])

    naun_target = naun_start if naun_start >= naun_goal else naun_start + (naun_goal - naun_start) * ratio
    osik_target = osik_start if osik_start >= osik_goal else osik_start + (osik_goal - osik_start) * ratio

    return True, {
        "NAUN": naun_target,
        "OSIK": osik_target,
    }, offpeak_start, target_dt, reasons


def classify_reservoir(
        name: str,
        level: float,
        trend: Optional[float],
        normal_min: float,
        normal_max: float,
        tolerance: float,
        morning_target: Optional[float],
        sensor_diff: Optional[float],
        single_sensor: bool,
        horizon_min: float,
) -> ReservoirState:
    """배수지 수위를 위험한계와 안정수위 밴드로 구분한다.

    - normal_min / normal_max: 최종 안전 하한/상한(HARD LIMIT)
    - tolerance: 안전한계 안쪽에 만드는 선제제어 폭
    - soft_low  = normal_min + tolerance
    - soft_high = normal_max - tolerance
    - trend가 있으면 horizon_min 후 예상수위까지 함께 판단한다.
    """
    hard_low = float(normal_min)
    hard_high = float(normal_max)
    tol = max(float(tolerance), 0.0)

    if not hard_low < hard_high:
        raise ValueError(f"{name} 수위 하한/상한 설정이 올바르지 않습니다: {hard_low}, {hard_high}")

    soft_low = hard_low + tol
    soft_high = hard_high - tol
    if soft_low >= soft_high:
        raise ValueError(
            f"{name} LEVEL_TOLERANCE={tol}가 너무 큽니다. "
            f"안정수위 범위가 사라집니다: {soft_low}~{soft_high}"
        )

    projected = float(level)
    if trend is not None and math.isfinite(trend):
        projected = float(level) + float(trend) * (float(horizon_min) / 60.0)

    low_reference = min(float(level), projected)
    high_reference = max(float(level), projected)

    # 위험수위 도달 또는 horizon 내 이탈 예상: 확인주기를 기다리지 않고 즉시 대응 대상
    if low_reference <= hard_low + 1e-9:
        return ReservoirState(
            name=name, level=level, trend_mph=trend, target=morning_target,
            state="DANGER_LOW", direction=1, error=hard_low - low_reference,
            sensor_diff=sensor_diff, single_sensor=single_sensor,
            projected_level=projected, hard_low=hard_low, hard_high=hard_high,
            soft_low=soft_low, soft_high=soft_high, danger=True,
        )

    if high_reference >= hard_high - 1e-9:
        return ReservoirState(
            name=name, level=level, trend_mph=trend, target=morning_target,
            state="DANGER_HIGH", direction=-1, error=high_reference - hard_high,
            sensor_diff=sensor_diff, single_sensor=single_sensor,
            projected_level=projected, hard_low=hard_low, hard_high=hard_high,
            soft_low=soft_low, soft_high=soft_high, danger=True,
        )

    # 기존 경부하 충수 목표는 유지하되 위험수위 판단보다 우선하지 않는다.
    if morning_target is not None:
        if level < morning_target - tol:
            return ReservoirState(
                name=name, level=level, trend_mph=trend, target=morning_target,
                state="BEHIND", direction=1, error=morning_target - level,
                sensor_diff=sensor_diff, single_sensor=single_sensor,
                projected_level=projected, hard_low=hard_low, hard_high=hard_high,
                soft_low=soft_low, soft_high=soft_high, danger=False,
            )
        if level > morning_target + tol:
            return ReservoirState(
                name=name, level=level, trend_mph=trend, target=morning_target,
                state="AHEAD", direction=-1, error=level - morning_target,
                sensor_diff=sensor_diff, single_sensor=single_sensor,
                projected_level=projected, hard_low=hard_low, hard_high=hard_high,
                soft_low=soft_low, soft_high=soft_high, danger=False,
            )

    # 안전한계에 도달하기 전에 안정수위 밴드에서 선제적으로 미세제어한다.
    if low_reference <= soft_low + 1e-9:
        return ReservoirState(
            name=name, level=level, trend_mph=trend, target=morning_target,
            state="PRE_LOW", direction=1, error=soft_low - low_reference,
            sensor_diff=sensor_diff, single_sensor=single_sensor,
            projected_level=projected, hard_low=hard_low, hard_high=hard_high,
            soft_low=soft_low, soft_high=soft_high, danger=False,
        )

    if high_reference >= soft_high - 1e-9:
        return ReservoirState(
            name=name, level=level, trend_mph=trend, target=morning_target,
            state="PRE_HIGH", direction=-1, error=high_reference - soft_high,
            sensor_diff=sensor_diff, single_sensor=single_sensor,
            projected_level=projected, hard_low=hard_low, hard_high=hard_high,
            soft_low=soft_low, soft_high=soft_high, danger=False,
        )

    return ReservoirState(
        name=name, level=level, trend_mph=trend, target=morning_target,
        state="NORMAL", direction=0, error=0.0,
        sensor_diff=sensor_diff, single_sensor=single_sensor,
        projected_level=projected, hard_low=hard_low, hard_high=hard_high,
        soft_low=soft_low, soft_high=soft_high, danger=False,
    )


def current_pump_state(readings: Dict[str, Reading]) -> Tuple[str, Optional[float], List[int]]:
    active: List[int] = []
    hz_values: List[float] = []

    for pump_no, run_tag, hz_tag in PUMPS:
        run = readings.get(run_tag)
        hz = readings.get(hz_tag)
        if run is not None and run.value > 0:
            active.append(pump_no)
            if hz is not None and math.isfinite(hz.value):
                hz_values.append(float(hz.value))

    combo = ",".join(str(x) for x in active)
    if not active or not hz_values:
        return combo, None, active

    return combo, sum(hz_values) / len(hz_values), active


def get_last_applied_device_command(conn, device: str) -> Optional[dict]:
    """실제 제어가 완료(APPLIED)된 가장 최근 장치 명령만 조회한다.

    Python은 제어 필요 시 READY를 생성하지만, READY는 아직 실제 설비에
    적용된 상태가 아니다. 따라서 제어 후 HOLD/응답확인 기준에는 APPLIED만 사용한다.
    """
    mapping = {
        "pump": ("PUMP_CMD_YN", "PUMP_CMD_STATUS"),
        "local": ("LOCAL_CMD_YN", "LOCAL_CMD_STATUS"),
        "national": ("NATIONAL_CMD_YN", "NATIONAL_CMD_STATUS"),
    }
    yn_col, status_col = mapping[device]
    return fetchone(
        conn,
        f"""
        SELECT *
        FROM {CMD_TABLE}
        WHERE {yn_col} = 'Y'
          AND {status_col} = 'APPLIED'
        ORDER BY CTRL_TS DESC, CTRL_ID DESC
        LIMIT 1
        """,
    )


def row_has_applied_command(row: Optional[dict], device: str) -> bool:
    """해당 결과행의 장치 명령이 실제 적용(APPLIED)됐는지 확인한다."""
    if not row:
        return False
    mapping = {
        "pump": ("PUMP_CMD_YN", "PUMP_CMD_STATUS"),
        "local": ("LOCAL_CMD_YN", "LOCAL_CMD_STATUS"),
        "national": ("NATIONAL_CMD_YN", "NATIONAL_CMD_STATUS"),
    }
    yn_col, status_col = mapping[device]
    return (
            str(row.get(yn_col) or "N").upper() == "Y"
            and str(row.get(status_col) or "").upper() == "APPLIED"
    )


def get_observe_until(last: Optional[dict], device: str) -> Optional[datetime]:
    if not last:
        return None
    return last.get({
                        "pump": "PUMP_OBSERVE_UNTIL",
                        "local": "LOCAL_OBSERVE_UNTIL",
                        "national": "NATIONAL_OBSERVE_UNTIL",
                    }[device])


def command_is_sequence_relevant(
        last: Optional[dict],
        device: str,
        now: datetime,
        control_cycle_min: float,
) -> bool:
    if not last:
        return False

    observe_until = get_observe_until(last, device)
    if observe_until is None:
        return False

    return now <= observe_until + timedelta(minutes=control_cycle_min * 2)


def trend_at(
        conn,
        reservoir: str,
        ts: datetime,
        diff_limit: float,
) -> Optional[float]:
    if reservoir == "NAUN":
        t1, t2 = TAGS["naun_level_1"], TAGS["naun_level_2"]
    else:
        t1, t2 = TAGS["osik_level_1"], TAGS["osik_level_2"]

    level, _, _, hold = pair_level_at(conn, t1, t2, ts, diff_limit, lookback_min=10)
    if level is None or hold:
        return None
    return level_trend_15m(conn, level, t1, t2, ts, diff_limit)


def response_ok_for_national_valve(
        conn,
        last: dict,
        target: datetime,
        current_trend: Optional[float],
        diff_limit: float,
) -> Optional[bool]:
    """국가산단 밸브 제어 후 오식도 유량수지/수위추세 반응을 확인한다.

    FRI-8652(유입)와 FRI-8653(유출)이 모두 있으면
    유량수지(유입-유출)의 개선 여부를 우선 사용한다. 유출값이 없을 때만
    기존 유입유량 변화로 대체한다. 유량수지는 제어 발생의 단독 조건이 아니라
    기존 수위/추세 판단의 반응 확인 보조지표로 사용한다.
    """
    cur_open = as_float(last.get("NATIONAL_CUR_OPEN"))
    tgt_open = as_float(last.get("NATIONAL_TGT_OPEN"))
    if cur_open is None or tgt_open is None:
        return None

    direction = 1 if tgt_open > cur_open else -1 if tgt_open < cur_open else 0
    if direction == 0:
        return True

    base_in = reading_at_or_before(conn, TAGS["osik_inflow"], last["CTRL_TS"], lookback_min=5)
    now_in = reading_at_or_before(conn, TAGS["osik_inflow"], target, lookback_min=5)
    base_out = reading_at_or_before(conn, TAGS["osik_outflow"], last["CTRL_TS"], lookback_min=5)
    now_out = reading_at_or_before(conn, TAGS["osik_outflow"], target, lookback_min=5)
    baseline_trend = trend_at(conn, "OSIK", last["CTRL_TS"], diff_limit)

    if not base_in or not now_in or baseline_trend is None or current_trend is None:
        return None

    if base_out and now_out:
        baseline_balance = base_in.value - base_out.value
        current_balance = now_in.value - now_out.value
        flow_ok = (current_balance - baseline_balance) * direction > 0
    else:
        flow_ok = (now_in.value - base_in.value) * direction > 0

    trend_ok = (current_trend - baseline_trend) * direction > 0
    return flow_ok and trend_ok


def response_ok_for_local_valve(
        conn,
        last: dict,
        target: datetime,
        current_trend: Optional[float],
        diff_limit: float,
) -> Optional[bool]:
    """지방산단 밸브 제어 후 나운 유입유량/수위추세 반응을 확인한다."""
    cur_open = as_float(last.get("LOCAL_CUR_OPEN"))
    tgt_open = as_float(last.get("LOCAL_TGT_OPEN"))
    if cur_open is None or tgt_open is None:
        return None

    direction = 1 if tgt_open > cur_open else -1 if tgt_open < cur_open else 0
    if direction == 0:
        return True

    base_flow = reading_at_or_before(conn, TAGS["naun_inflow"], last["CTRL_TS"], lookback_min=5)
    now_flow = reading_at_or_before(conn, TAGS["naun_inflow"], target, lookback_min=5)
    baseline_trend = trend_at(conn, "NAUN", last["CTRL_TS"], diff_limit)

    if not base_flow or not now_flow or baseline_trend is None or current_trend is None:
        return None

    flow_ok = (now_flow.value - base_flow.value) * direction > 0
    trend_ok = (current_trend - baseline_trend) * direction > 0
    return flow_ok and trend_ok


def device_command_direction(row: Optional[dict], device: str) -> int:
    """저장된 장치명령의 방향(+1 증가/OPEN, -1 감소/CLOSE)을 반환한다."""
    if not row:
        return 0
    cols = {
        "pump": ("PUMP_CUR_HZ", "PUMP_TGT_HZ"),
        "local": ("LOCAL_CUR_OPEN", "LOCAL_TGT_OPEN"),
        "national": ("NATIONAL_CUR_OPEN", "NATIONAL_TGT_OPEN"),
    }
    cur_col, tgt_col = cols[device]
    cur = as_float(row.get(cur_col))
    tgt = as_float(row.get(tgt_col))
    if cur is None or tgt is None:
        return 0
    return 1 if tgt > cur else -1 if tgt < cur else 0


def naun_relief_control_completed(
        last_pump: Optional[dict],
        last_national: Optional[dict],
        ctrl_ts: datetime,
        control_cycle_min: int,
) -> bool:
    """나운 고수위 완화를 위한 1·2순위 제어가 적용되고 관찰까지 끝났는지 확인한다.

    - 펌프 Hz DOWN(-1): 전체 공급량 감소
    - 국가산단 OPEN(+1): 오식도 쪽 배분 증가 → 나운 상대 유입 억제
    """
    candidates = (
        (last_pump, "pump", -1),
        (last_national, "national", 1),
    )
    for row, device, expected_direction in candidates:
        if not row or device_command_direction(row, device) != expected_direction:
            continue
        observe_until = get_observe_until(row, device)
        if observe_until is None or ctrl_ts < observe_until:
            continue
        # 너무 오래된 선행제어를 현재 지방산단 제어의 근거로 사용하지 않는다.
        if ctrl_ts <= observe_until + timedelta(minutes=control_cycle_min * 2):
            return True
    return False


def naun_recovery_stable(
        conn,
        ctrl_ts: datetime,
        current_level: float,
        current_trend: Optional[float],
        diff_limit: float,
        recovery_level: float,
        stable_min: int,
        trend_deadband: float,
) -> bool:
    """지방산단 밸브 원복을 위해 나운이 일정시간 안정/하강했는지 확인한다."""
    if not math.isfinite(current_level) or current_level > recovery_level:
        return False
    if current_trend is None or not math.isfinite(current_trend) or current_trend > trend_deadband:
        return False

    past_level, _, _, past_hold = pair_level_at(
        conn,
        TAGS["naun_level_1"],
        TAGS["naun_level_2"],
        ctrl_ts - timedelta(minutes=stable_min),
        diff_limit,
        lookback_min=max(stable_min, 10),
        )
    if past_level is None or past_hold:
        return False
    return past_level <= recovery_level


def response_ok_for_pump(
        conn,
        last: dict,
        target: datetime,
        naun: ReservoirState,
        osik: ReservoirState,
        diff_limit: float,
) -> Optional[bool]:
    cur_hz = as_float(last.get("PUMP_CUR_HZ"))
    tgt_hz = as_float(last.get("PUMP_TGT_HZ"))
    if cur_hz is None or tgt_hz is None:
        return None

    direction = 1 if tgt_hz > cur_hz else -1 if tgt_hz < cur_hz else 0
    if direction == 0:
        return True

    base_send = reading_at_or_before(conn, TAGS["send_flow"], last["CTRL_TS"], lookback_min=5)
    now_send = reading_at_or_before(conn, TAGS["send_flow"], target, lookback_min=5)
    if not base_send or not now_send:
        return None

    send_ok = (now_send.value - base_send.value) * direction > 0

    trend_checks: List[bool] = []
    for state, reservoir in [(naun, "NAUN"), (osik, "OSIK")]:
        base_trend = trend_at(conn, reservoir, last["CTRL_TS"], diff_limit)
        if base_trend is not None and state.trend_mph is not None:
            trend_checks.append((state.trend_mph - base_trend) * direction > 0)

    if not trend_checks:
        return None

    return send_ok and any(trend_checks)


def choose_pump_step(
        desired_direction: int,
        last: Optional[dict],
        coarse_step: float,
        fine_step: float,
) -> float:
    if desired_direction == 0 or not last:
        return coarse_step

    prev_cur = as_float(last.get("PUMP_CUR_HZ"))
    prev_tgt = as_float(last.get("PUMP_TGT_HZ"))
    if prev_cur is None or prev_tgt is None:
        return coarse_step

    prev_delta = prev_tgt - prev_cur
    prev_dir = 1 if prev_delta > 0 else -1 if prev_delta < 0 else 0

    if prev_dir != desired_direction:
        return coarse_step

    if abs(prev_delta) >= (coarse_step + fine_step) / 2:
        return fine_step

    return coarse_step


def append_reason(reasons: List[str], code: str) -> None:
    if code and code not in reasons:
        reasons.append(code)


def prepend_reason(reasons: List[str], code: str) -> None:
    """시퀀스 상태코드는 REASON_CODE 100자 절단 전에도 남도록 앞쪽에 둔다."""
    if not code:
        return
    if code in reasons:
        reasons.remove(code)
    reasons.insert(0, code)


def get_previous_control_row(conn, ctrl_ts: datetime) -> Optional[dict]:
    return fetchone(
        conn,
        f"""
        SELECT *
        FROM {CMD_TABLE}
        WHERE CTRL_TS < %s
        ORDER BY CTRL_TS DESC, CTRL_ID DESC
        LIMIT 1
        """,
        (ctrl_ts,),
    )


def is_previous_cycle(row: Optional[dict], ctrl_ts: datetime, control_cycle_min: int) -> bool:
    if not row or row.get("CTRL_TS") is None:
        return False
    expected = ctrl_ts - timedelta(minutes=control_cycle_min)
    return row["CTRL_TS"] == expected


def wait_direction_from_row(row: Optional[dict], device: str) -> Optional[int]:
    if not row:
        return None
    reason = str(row.get("REASON_CODE") or "")
    if device == "pump":
        tokens = {1: "PUMP_WAIT_UP", -1: "PUMP_WAIT_DOWN", 0: "PUMP_WAIT_HOLD"}
    elif device == "local":
        tokens = {1: "LOCAL_WAIT_OPEN", -1: "LOCAL_WAIT_CLOSE", 0: "LOCAL_WAIT_HOLD"}
    elif device == "national":
        tokens = {1: "NATIONAL_WAIT_OPEN", -1: "NATIONAL_WAIT_CLOSE", 0: "NATIONAL_WAIT_HOLD"}
    else:
        raise ValueError(f"지원하지 않는 시퀀스 장치입니다: {device}")
    for direction, token in tokens.items():
        if token in reason:
            return direction
    return None


def save_wait_direction(reasons: List[str], device: str, direction: int) -> None:
    if device == "pump":
        token = {1: "PUMP_WAIT_UP", -1: "PUMP_WAIT_DOWN", 0: "PUMP_WAIT_HOLD"}[direction]
    elif device == "local":
        token = {1: "LOCAL_WAIT_OPEN", -1: "LOCAL_WAIT_CLOSE", 0: "LOCAL_WAIT_HOLD"}[direction]
    elif device == "national":
        token = {1: "NATIONAL_WAIT_OPEN", -1: "NATIONAL_WAIT_CLOSE", 0: "NATIONAL_WAIT_HOLD"}[direction]
    else:
        raise ValueError(f"지원하지 않는 시퀀스 장치입니다: {device}")
    prepend_reason(reasons, token)


def sequence_allows_control(
        *,
        device: str,
        desired_direction: int,
        danger: bool,
        ctrl_ts: datetime,
        control_cycle_min: int,
        previous_row: Optional[dict],
        last_command: Optional[dict],
) -> Tuple[bool, str]:
    """5분 판단 / 정상 10분 최소 제어간격 시퀀스.

    정상상태:
      - 실제 제어 직후 다음 5분 주기는 무조건 HOLD하며 판단방향 저장
      - 그 다음 5분에 같은 방향이면 제어
      - 방향이 바뀌면 HOLD 후 새 방향을 다시 기준으로 저장
    위험수위:
      - 위 시퀀스를 우회하고 즉시 제어 가능
    """
    if desired_direction == 0:
        return False, "NO_DIRECTION"

    if danger:
        return True, "DANGER_BYPASS"

    prev_is_cycle = is_previous_cycle(previous_row, ctrl_ts, control_cycle_min)

    # 바로 전 5분 주기의 명령이 실제 APPLIED 됐을 때만 이번 주기를 HOLD한다.
    # READY는 Python이 생성한 제어 후보일 뿐 실제 설비 적용으로 간주하지 않는다.
    if prev_is_cycle and row_has_applied_command(previous_row, device):
        return False, "POST_CONTROL_HOLD"

    # 명령 후 첫 관찰주기가 누락된 경우에도 최소 한 번의 판단 저장을 요구한다.
    if last_command and last_command.get("CTRL_TS") is not None:
        elapsed = (ctrl_ts - last_command["CTRL_TS"]).total_seconds() / 60.0
        if 0 < elapsed < control_cycle_min * NORMAL_CONTROL_CYCLES and not prev_is_cycle:
            return False, "POST_CONTROL_HOLD"

    # 직전 5분 HOLD에서 저장한 방향과 현재 방향이 같아야 후속 제어 허용.
    if prev_is_cycle:
        prev_wait = wait_direction_from_row(previous_row, device)
        if prev_wait is not None:
            if prev_wait == desired_direction:
                return True, "DIRECTION_CONFIRMED"
            return False, "DIRECTION_CHANGED"

    # 시작 시점/시퀀스가 없는 상태의 최초 제어는 즉시 허용.
    return True, "INITIAL_CONTROL"


def control_once(conn, ctrl_ts: datetime, dry_run: bool = False) -> dict:
    rules = load_rules(conn)

    exists = fetchone(
        conn,
        f"SELECT CTRL_ID FROM {CMD_TABLE} WHERE CTRL_TS = %s ORDER BY CTRL_ID DESC LIMIT 1",
        (ctrl_ts,),
    )
    if exists:
        LOGGER.info("이미 처리된 제어시각입니다: %s (CTRL_ID=%s)", ctrl_ts, exists["CTRL_ID"])
        return {"skipped": True, "ctrl_ts": ctrl_ts, "ctrl_id": exists["CTRL_ID"]}

    reasons: List[str] = []

    control_cycle = int(rules["CONTROL_CYCLE_MIN"])
    raw_fresh_min = max(control_cycle * 2, 10)

    required_tags = list(dict.fromkeys(TAGS.values()))
    readings = latest_readings(conn, required_tags, ctrl_ts, raw_fresh_min)


    must_have = [
        TAGS["clearwell_1"], TAGS["clearwell_2"],
        TAGS["naun_level_1"], TAGS["naun_level_2"],
        TAGS["osik_level_1"], TAGS["osik_level_2"],
        TAGS["send_flow"],
        TAGS["osik_inflow"],
        TAGS["national_valve"],
    ]
    missing_core = [tag for tag in must_have if tag not in readings]
    global_hold = False
    if missing_core:
        global_hold = True
        append_reason(reasons, "RAW_DATA_MISSING")

    # 오식도 유출유량(FRI-8653)은 배분판단의 보조지표이므로 누락 시 전체 제어를
    # 중단하지 않고 기존 수위/추세 + 유입유량 로직으로 폴백한다.
    if TAGS["osik_outflow"] not in readings:
        append_reason(reasons, "OSIK_OUTFLOW_MISSING")

    diff_limit = float(rules["LEVEL_SENSOR_DIFF_LIMIT"])

    naun_level, naun_diff, naun_single, naun_sensor_hold = pair_level_from_readings(
        readings, TAGS["naun_level_1"], TAGS["naun_level_2"], diff_limit
    )
    osik_level, osik_diff, osik_single, osik_sensor_hold = pair_level_from_readings(
        readings, TAGS["osik_level_1"], TAGS["osik_level_2"], diff_limit
    )

    if naun_sensor_hold:
        global_hold = True
        append_reason(reasons, "LEVEL_SENSOR_CHECK_NAUN")
    if osik_sensor_hold:
        global_hold = True
        append_reason(reasons, "LEVEL_SENSOR_CHECK_OSIK")
    if naun_single:
        append_reason(reasons, "NAUN_SINGLE_SENSOR")
    if osik_single:
        append_reason(reasons, "OSIK_SINGLE_SENSOR")

    if naun_level is None or osik_level is None:
        global_hold = True
        append_reason(reasons, "LEVEL_DATA_INVALID")

    predictions, pred_stale = get_latest_predictions(
        conn, ctrl_ts, float(rules["PRED_STALE_MIN"])
    )
    if pred_stale:
        append_reason(reasons, "PRED_STALE")

    morning_active = False
    morning_targets: Dict[str, float] = {}
    offpeak_start = None
    morning_target_dt = None
    try:
        morning_active, morning_targets, offpeak_start, morning_target_dt, fill_reasons = morning_trajectory(
            conn, ctrl_ts, rules, diff_limit
        )
        for r in fill_reasons:
            append_reason(reasons, r)
    except Exception:
        LOGGER.exception("전력 시간대 또는 경부하 충수 목표 계산 실패")
        append_reason(reasons, "RATE_TIME_CHECK")

    naun_trend = None
    osik_trend = None
    if naun_level is not None and not naun_sensor_hold:
        naun_trend = level_trend_15m(
            conn, naun_level, TAGS["naun_level_1"], TAGS["naun_level_2"],
            ctrl_ts, diff_limit
        )
    if osik_level is not None and not osik_sensor_hold:
        osik_trend = level_trend_15m(
            conn, osik_level, TAGS["osik_level_1"], TAGS["osik_level_2"],
            ctrl_ts, diff_limit
        )

    if naun_level is None:
        naun_level = math.nan
    if osik_level is None:
        osik_level = math.nan

    naun = classify_reservoir(
        "NAUN",
        naun_level,
        naun_trend,
        float(rules["NAUN_LEVEL_MIN"]),
        float(rules["NAUN_LEVEL_MAX"]),
        float(rules["NAUN_LEVEL_TOLERANCE"]),
        morning_targets.get("NAUN") if morning_active else None,
        naun_diff,
        naun_single,
        control_cycle,
    )
    osik = classify_reservoir(
        "OSIK",
        osik_level,
        osik_trend,
        float(rules["OSIK_LEVEL_MIN"]),
        float(rules["OSIK_LEVEL_MAX"]),
        float(rules["OSIK_LEVEL_TOLERANCE"]),
        morning_targets.get("OSIK") if morning_active else None,
        osik_diff,
        osik_single,
        control_cycle,
    )

    if morning_active:
        append_reason(reasons, "MORNING_FILL")

    if naun.state != "NORMAL":
        append_reason(reasons, f"NAUN_{naun.state}")
    if osik.state != "NORMAL":
        append_reason(reasons, f"OSIK_{osik.state}")

    cw1 = readings.get(TAGS["clearwell_1"])
    cw2 = readings.get(TAGS["clearwell_2"])
    cw_vals = [r.value for r in [cw1, cw2] if r is not None and math.isfinite(r.value)]
    cw_min = min(cw_vals) if cw_vals else None
    cw_max = max(cw_vals) if cw_vals else None

    clearwell_low_limit = float(rules["CLEARWELL_LEVEL_MIN"]) - float(rules["CLEARWELL_TOLERANCE"])
    clearwell_high_limit = float(rules["CLEARWELL_LEVEL_MAX"]) + float(rules["CLEARWELL_TOLERANCE"])

    if cw_min is None:
        global_hold = True
        append_reason(reasons, "CLEARWELL_DATA_MISSING")

    combo, pump_cur_hz, active_pumps = current_pump_state(readings)
    local_cur = readings.get(TAGS["local_valve"])
    national_cur = readings.get(TAGS["national_valve"])
    local_cur_open = local_cur.value if local_cur else None
    national_cur_open = national_cur.value if national_cur else None

    osik_in = readings.get(TAGS["osik_inflow"])
    osik_out = readings.get(TAGS["osik_outflow"])
    osik_flow_balance = (
        float(osik_in.value) - float(osik_out.value)
        if osik_in is not None and osik_out is not None
        else None
    )

    pump_cmd = DeviceCommand(current=pump_cur_hz, target=pump_cur_hz)
    local_cmd = DeviceCommand(current=local_cur_open, target=local_cur_open)
    national_cmd = DeviceCommand(current=national_cur_open, target=national_cur_open)

    # ------------------------------------------------------------
    # 제어 방향 결정
    # - 펌프 Hz: EPA_PUMP.DEFAULT_VALUE에 따라 AI Q/P 또는 EPANET PRE Q/P 선택
    # - 5분 Q/P가 Base Hz를 결정하고, 1/15/30분은 방향 지속성 검증에 사용
    # - 나운/오식도 동방향 수위 이상은 Base Hz에 피드백 보정
    # - 국가산단 밸브는 나운/오식도 배분 불균형을 보정
    # ------------------------------------------------------------
    pump_direction = 0
    national_direction = 0
    pump_reference_hz: Optional[float] = None
    pump_source_mode: Optional[int] = None
    pump_source_name = "UNKNOWN"
    pump_source_ts: Optional[datetime] = None
    pump_qp_values: Dict[int, Tuple[float, float]] = {}
    pump_qp_recs: Dict[int, PumpBaseRecommendation] = {}
    pump_horizon_mixed = False
    pump_horizon_hold = False

    both_same = naun.direction != 0 and naun.direction == osik.direction
    trend_deadband = max(float(rules.get("LEVEL_TREND_DEADBAND_MPH", 0.01)), 0.0)
    naun_falling = (
            naun.trend_mph is not None and math.isfinite(naun.trend_mph)
            and naun.trend_mph < -trend_deadband
    )
    naun_rising = (
            naun.trend_mph is not None and math.isfinite(naun.trend_mph)
            and naun.trend_mph > trend_deadband
    )
    osik_falling = (
            osik.trend_mph is not None and math.isfinite(osik.trend_mph)
            and osik.trend_mph < -trend_deadband
    )
    osik_rising = (
            osik.trend_mph is not None and math.isfinite(osik.trend_mph)
            and osik.trend_mph > trend_deadband
    )
    osik_balance_deficit = osik_flow_balance is not None and osik_flow_balance < 0.0
    osik_balance_surplus = osik_flow_balance is not None and osik_flow_balance > 0.0

    # 1) 펌프 Q/P 출처 선택 및 4 Horizon 성능곡선 매칭
    try:
        pump_source_mode = get_pump_source_mode(conn)
        if pump_source_mode == 0:
            pump_source_name = "AI"
            pump_qp_values, pump_source_ts = direct_qp_horizons(
                predictions, ctrl_ts, float(rules["PRED_STALE_MIN"])
            )
            append_reason(reasons, "PUMP_SRC_AI")
        else:
            pump_source_name = "EPA"
            pump_qp_values, pump_source_ts = epa_qp_horizons(
                conn, ctrl_ts, float(rules["PRED_STALE_MIN"]), rules
            )
            append_reason(reasons, "PUMP_SRC_EPA")

        pump_qp_recs = qp_recommendations(
            conn, pump_qp_values, len(active_pumps), rules
        )
        rec5 = pump_qp_recs[5]
        base_hz = rec5.freq_hz

        # 두 배수지가 동시에 부족/과다하면 5분 Base Hz에 수위 피드백을 추가한다.
        feedback_offset_hz = (
            naun.direction * float(rules["PUMP_COARSE_STEP"])
            if both_same else 0.0
        )
        pump_reference_hz = min(
            max(base_hz + feedback_offset_hz, float(rules["PUMP_FREQ_MIN"])),
            float(rules["PUMP_FREQ_MAX"]),
        )
        pump_direction = hz_direction(pump_reference_hz, pump_cur_hz)

        # 1/15/30분 성능곡선 결과로 5분 제어방향의 지속성을 확인한다.
        if pump_direction != 0 and pump_cur_hz is not None:
            horizon_dirs = {
                h: hz_direction(pump_qp_recs[h].freq_hz, pump_cur_hz)
                for h in (1, 15, 30)
            }
            support = sum(d == pump_direction for d in horizon_dirs.values())
            oppose = sum(d == -pump_direction for d in horizon_dirs.values())
            if oppose >= 2 and not (naun.danger or osik.danger):
                pump_horizon_hold = True
                pump_direction = 0
                append_reason(reasons, "PUMP_HORIZON_REVERSAL_HOLD")
            elif support >= 2:
                append_reason(reasons, "PUMP_HORIZON_CONFIRMED")
            else:
                pump_horizon_mixed = True
                append_reason(reasons, "PUMP_HORIZON_MIXED")
    except Exception as exc:
        LOGGER.warning("펌프 Q/P 기준값 산정 불가: %s", exc)
        append_reason(reasons, "PUMP_QP_SOURCE_CHECK")
        pump_direction = 0
        pump_reference_hz = pump_cur_hz

    # 두 배수지가 동시에 위험수위인 경우에는 예측보다 안전수위 방향을 우선한다.
    reservoir_danger_override = (
            naun.danger and osik.danger
            and naun.direction != 0 and naun.direction == osik.direction
    )
    if reservoir_danger_override and pump_cur_hz is not None:
        pump_direction = naun.direction
        pump_reference_hz = min(
            max(
                pump_cur_hz + pump_direction * float(rules["PUMP_COARSE_STEP"]),
                float(rules["PUMP_FREQ_MIN"]),
                ),
            float(rules["PUMP_FREQ_MAX"]),
        )
        append_reason(reasons, "PUMP_RESERVOIR_DANGER_OVERRIDE")

    # 2) 국가산단 밸브: 배분 불균형 + 오식도 유량수지 보조판단
    distribution_close = (
            naun_falling
            and (osik_rising or (osik.direction == -1 and osik_balance_surplus))
            and osik.direction != 1
    )
    distribution_open = (
            naun_rising
            and (osik_falling or (osik.direction == 1 and osik_balance_deficit))
            and naun.direction != 1
    )

    if distribution_close:
        national_direction = -1
        append_reason(reasons, "DIST_NAUN_DOWN_OSIK_UP")
        if osik_balance_surplus:
            append_reason(reasons, "OSIK_BALANCE_SURPLUS")
    elif distribution_open:
        national_direction = 1
        append_reason(reasons, "DIST_NAUN_UP_OSIK_DOWN")
        if osik_balance_deficit:
            append_reason(reasons, "OSIK_BALANCE_DEFICIT")
    else:
        # 오식도 단독 또는 나운과 반대방향이면 국가산단으로 국부 배분을 보정한다.
        if osik.direction != 0 and (naun.direction == 0 or osik.direction != naun.direction):
            national_direction = osik.direction

    if global_hold:
        pump_direction = 0
        national_direction = 0
        append_reason(reasons, "GLOBAL_HOLD")

    # 위험수위(현재 또는 5분 후 예상)가 해당 제어방향과 일치하면 10분 시퀀스를 우회한다.
    pump_danger = pump_direction != 0 and (
            reservoir_danger_override
            or (naun.danger and naun.direction == pump_direction)
            or (osik.danger and osik.direction == pump_direction)
    )
    national_danger = (
            national_direction != 0
            and osik.danger
            and osik.direction == national_direction
    )

    previous_row = get_previous_control_row(conn, ctrl_ts)
    last_pump_all = get_last_applied_device_command(conn, "pump")
    last_local_all = get_last_applied_device_command(conn, "local")
    last_national_all = get_last_applied_device_command(conn, "national")

    # APPLIED 명령의 observe_until 값만 표시/응답검증용으로 사용한다.
    pump_observe = get_observe_until(last_pump_all, "pump")
    local_observe = get_observe_until(last_local_all, "local")
    national_observe = get_observe_until(last_national_all, "national")
    pump_cmd.observe_until = pump_observe if pump_observe and ctrl_ts < pump_observe else None
    local_cmd.observe_until = local_observe if local_observe and ctrl_ts < local_observe else None
    national_cmd.observe_until = national_observe if national_observe and ctrl_ts < national_observe else None

    last_pump = (
        last_pump_all
        if command_is_sequence_relevant(last_pump_all, "pump", ctrl_ts, control_cycle)
        else None
    )
    last_local = (
        last_local_all
        if command_is_sequence_relevant(last_local_all, "local", ctrl_ts, control_cycle)
        else None
    )
    last_national = (
        last_national_all
        if command_is_sequence_relevant(last_national_all, "national", ctrl_ts, control_cycle)
        else None
    )

    # ------------------------------------------------------------
    # 지방산단 분기밸브: 나운 고수위 최종(Fallback) 제어
    # - 4.30m 초과 + 상승 지속: 1·2순위(펌프 DOWN 또는 국가산단 OPEN)가
    #   APPLIED되고 관찰시간까지 끝났는데도 상승할 때만 CLOSE
    # - 4.35m 초과: 선행제어 대기 없이 강제 CLOSE
    # - 원복: 4.25m 이하에서 10분 이상 안정/하강 확인 후 5%p씩 OPEN
    # ------------------------------------------------------------
    local_direction = 0
    local_force_close = False
    local_conditional_close = False
    local_recovery_ready = False
    higher_priority_completed = False

    local_trigger_level = float(rules["LOCAL_TRIGGER_LEVEL"])
    local_force_level = float(rules["LOCAL_FORCE_CLOSE_LEVEL"])
    local_recovery_level = float(rules["LOCAL_RECOVERY_LEVEL"])
    local_recovery_stable_min = int(rules["LOCAL_RECOVERY_STABLE_MIN"])

    if not global_hold and math.isfinite(naun.level):
        higher_priority_completed = naun_relief_control_completed(
            last_pump_all, last_national_all, ctrl_ts, control_cycle
        )
        local_force_close = naun.level > local_force_level
        local_conditional_close = (
                naun.level > local_trigger_level
                and naun.level <= local_force_level
                and naun_rising
                and higher_priority_completed
        )

        # 원복은 실제 지방산단 제어 이력이 있고 현재 개도가 최대보다 낮을 때만 허용한다.
        last_local_reason = str(last_local_all.get("REASON_CODE") or "") if last_local_all else ""
        local_managed = (
                last_local_all is not None
                and any(token in last_local_reason for token in (
            "LOCAL_FALLBACK_CLOSE", "LOCAL_FORCE_CLOSE", "LOCAL_RECOVERY_OPEN"
        ))
                and local_cur_open is not None
                and local_cur_open < float(rules["LOCAL_VALVE_MAX"]) - 0.5
        )
        if local_managed:
            local_recovery_ready = naun_recovery_stable(
                conn,
                ctrl_ts,
                naun.level,
                naun.trend_mph,
                diff_limit,
                local_recovery_level,
                local_recovery_stable_min,
                trend_deadband,
            )

        if local_force_close or local_conditional_close:
            local_direction = -1
        elif local_recovery_ready:
            local_direction = 1

    # 4.35m 초과 강제 CLOSE는 정상 10분 방향확인 시퀀스를 우회한다.
    # 극저수위(DANGER_LOW)에서 원복 OPEN이 필요한 경우도 안전 우선으로 우회한다.
    local_danger = local_force_close or (
            local_direction > 0 and naun.danger and naun.direction == 1
    )

    # ------------------------------------------------------------
    # 펌프 Hz 제어
    # 정상: 5분마다 판단, 실제 제어 후 다음 5분 HOLD + 방향 저장,
    #       그 다음 5분 동일방향 확인 시 제어 => 정상 최소 10분 간격
    # 위험: 시퀀스 우회하여 즉시 제어 가능
    # ------------------------------------------------------------
    if pump_direction != 0:
        if pump_cur_hz is None or not active_pumps:
            append_reason(reasons, "PUMP_STATE_CHECK")
        elif not (float(rules["PUMP_FREQ_MIN"]) <= pump_cur_hz <= float(rules["PUMP_FREQ_MAX"])):
            append_reason(reasons, "PUMP_RANGE_CHECK")
        elif pump_direction > 0 and cw_min is not None and cw_min < clearwell_low_limit:
            append_reason(reasons, "CLEARWELL_LOW")
        elif pump_direction < 0 and cw_max is not None and cw_max > clearwell_high_limit:
            append_reason(reasons, "CLEARWELL_HIGH")
        else:
            allow_pump, pump_gate = sequence_allows_control(
                device="pump",
                desired_direction=pump_direction,
                danger=pump_danger,
                ctrl_ts=ctrl_ts,
                control_cycle_min=control_cycle,
                previous_row=previous_row,
                last_command=last_pump_all,
            )

            if not allow_pump:
                save_wait_direction(reasons, "pump", pump_direction)
                append_reason(reasons, f"PUMP_{pump_gate}")
            else:
                # 위험수위가 아니면 직전 제어의 실제 효과까지 확인하고 추가제어한다.
                response_ok: Optional[bool] = True
                if not pump_danger and last_pump:
                    prev_cur = as_float(last_pump.get("PUMP_CUR_HZ"))
                    prev_tgt = as_float(last_pump.get("PUMP_TGT_HZ"))
                    if prev_cur is not None and prev_tgt is not None:
                        prev_dir = 1 if prev_tgt > prev_cur else -1 if prev_tgt < prev_cur else 0
                        if prev_dir == pump_direction:
                            if both_same or reservoir_danger_override:
                                response_ok = response_ok_for_pump(
                                    conn, last_pump, ctrl_ts, naun, osik, diff_limit
                                )
                            else:
                                response_ok = response_ok_for_pump_base(
                                    conn, last_pump, ctrl_ts
                                )

                if response_ok is False:
                    save_wait_direction(reasons, "pump", pump_direction)
                    append_reason(reasons, "PUMP_NO_RESPONSE")
                elif response_ok is None:
                    save_wait_direction(reasons, "pump", pump_direction)
                    append_reason(reasons, "PUMP_RESPONSE_CHECK")
                else:
                    # 5분 Base Hz까지 단계적으로 접근한다. 위험수위는 coarse,
                    # Horizon 방향이 혼재되면 fine step으로 보수적으로 조정한다.
                    step = choose_pump_step(
                        pump_direction,
                        last_pump,
                        float(rules["PUMP_COARSE_STEP"]),
                        float(rules["PUMP_FINE_STEP"]),
                    )
                    if pump_danger:
                        step = float(rules["PUMP_COARSE_STEP"])
                    elif pump_horizon_mixed:
                        step = min(step, float(rules["PUMP_FINE_STEP"]))

                    remaining = (
                        abs(pump_reference_hz - pump_cur_hz)
                        if pump_reference_hz is not None
                        else step
                    )
                    applied_step = min(step, remaining)
                    new_hz = pump_cur_hz + pump_direction * applied_step
                    new_hz = min(
                        max(new_hz, float(rules["PUMP_FREQ_MIN"])),
                        float(rules["PUMP_FREQ_MAX"]),
                    )

                    if abs(new_hz - pump_cur_hz) >= 0.5:
                        pump_cmd.cmd_yn = "Y"
                        # Python은 제어 후보 생성까지만 담당하고 초기 상태를 READY로 기록한다.
                        # 실제 적용 성공 후 Java 제어부가 APPLIED로 변경해야 한다.
                        pump_cmd.status = "READY"
                        pump_cmd.target = new_hz
                        # 5분 판단 × 2회 = 정상 최소 10분 제어간격
                        pump_cmd.observe_until = ctrl_ts + timedelta(minutes=control_cycle * NORMAL_CONTROL_CYCLES)
                        append_reason(
                            reasons,
                            "PUMP_DANGER_UP" if pump_danger and pump_direction > 0
                            else "PUMP_DANGER_DOWN" if pump_danger
                            else "PUMP_UP" if pump_direction > 0
                            else "PUMP_DOWN"
                        )
                    else:
                        append_reason(reasons, "PUMP_LIMIT")
    else:
        # 직전 제어 직후 첫 관찰주기라면 HOLD 판단도 다음 비교를 위해 저장한다.
        if (
                is_previous_cycle(previous_row, ctrl_ts, control_cycle)
                and row_has_applied_command(previous_row, "pump")
                and not pump_danger
        ):
            save_wait_direction(reasons, "pump", 0)
            append_reason(reasons, "PUMP_POST_CONTROL_HOLD")

    # ------------------------------------------------------------
    # 국가산단 밸브 보조제어
    # 펌프와 동일하게 5분 판단 / 정상 최소 10분 제어간격을 적용한다.
    # 오식도 위험수위는 즉시제어 예외.
    # ------------------------------------------------------------
    if national_direction != 0:
        if national_cur_open is None:
            append_reason(reasons, "NATIONAL_DATA_CHECK")
        elif not (
                float(rules["NATIONAL_VALVE_MIN"])
                <= national_cur_open
                <= float(rules["NATIONAL_VALVE_MAX"])
        ):
            append_reason(reasons, "NATIONAL_RANGE_CHECK")
        else:
            allow_national, national_gate = sequence_allows_control(
                device="national",
                desired_direction=national_direction,
                danger=national_danger,
                ctrl_ts=ctrl_ts,
                control_cycle_min=control_cycle,
                previous_row=previous_row,
                last_command=last_national_all,
            )

            if not allow_national:
                save_wait_direction(reasons, "national", national_direction)
                append_reason(reasons, f"NATIONAL_{national_gate}")
            else:
                response_ok: Optional[bool] = True
                if not national_danger and last_national:
                    prev_cur = as_float(last_national.get("NATIONAL_CUR_OPEN"))
                    prev_tgt = as_float(last_national.get("NATIONAL_TGT_OPEN"))
                    if prev_cur is not None and prev_tgt is not None:
                        prev_dir = 1 if prev_tgt > prev_cur else -1 if prev_tgt < prev_cur else 0
                        if prev_dir == national_direction:
                            response_ok = response_ok_for_national_valve(
                                conn, last_national, ctrl_ts,
                                osik.trend_mph, diff_limit
                            )

                if response_ok is False:
                    save_wait_direction(reasons, "national", national_direction)
                    append_reason(reasons, "NATIONAL_NO_RESPONSE")
                elif response_ok is None:
                    save_wait_direction(reasons, "national", national_direction)
                    append_reason(reasons, "NATIONAL_RESPONSE_CHECK")
                else:
                    new_open = national_cur_open + national_direction * float(rules["VALVE_STEP"])
                    new_open = min(
                        max(new_open, float(rules["NATIONAL_VALVE_MIN"])),
                        float(rules["NATIONAL_VALVE_MAX"]),
                    )
                    if abs(new_open - national_cur_open) >= 0.5:
                        national_cmd.cmd_yn = "Y"
                        # Python은 제어 후보 생성까지만 담당하고 초기 상태를 READY로 기록한다.
                        # 실제 적용 성공 후 Java 제어부가 APPLIED로 변경해야 한다.
                        national_cmd.status = "READY"
                        national_cmd.target = new_open
                        national_cmd.observe_until = ctrl_ts + timedelta(minutes=control_cycle * NORMAL_CONTROL_CYCLES)
                        append_reason(
                            reasons,
                            "NATIONAL_DANGER_OPEN" if national_danger and national_direction > 0
                            else "NATIONAL_DANGER_CLOSE" if national_danger
                            else "NATIONAL_OPEN" if national_direction > 0
                            else "NATIONAL_CLOSE"
                        )
                    else:
                        append_reason(reasons, "NATIONAL_LIMIT")
    else:
        if (
                is_previous_cycle(previous_row, ctrl_ts, control_cycle)
                and row_has_applied_command(previous_row, "national")
                and not national_danger
        ):
            save_wait_direction(reasons, "national", 0)
            append_reason(reasons, "NATIONAL_POST_CONTROL_HOLD")


    # ------------------------------------------------------------
    # 지방산단 밸브 최종제어
    # 정상 fallback/recovery는 5분 판단 / 최소 10분 간격,
    # 4.35m 초과 강제 CLOSE는 시퀀스를 우회한다.
    # ------------------------------------------------------------
    if local_direction != 0:
        # 4.35m 초과 시 최초 제어는 즉시 허용하되, 이미 APPLIED된 지방산단 제어의
        # 10분 관찰구간 안에서는 추가 5%p 제어를 중첩하지 않는다.
        if local_cmd.observe_until is not None and ctrl_ts < local_cmd.observe_until:
            save_wait_direction(reasons, "local", local_direction)
            append_reason(reasons, "LOCAL_FORCE_OBSERVE" if local_force_close else "LOCAL_OBSERVE")
        elif local_cur_open is None:
            append_reason(reasons, "LOCAL_DATA_CHECK")
        elif not (
                float(rules["LOCAL_VALVE_MIN"])
                <= local_cur_open
                <= float(rules["LOCAL_VALVE_MAX"])
        ):
            append_reason(reasons, "LOCAL_RANGE_CHECK")
        else:
            allow_local, local_gate = sequence_allows_control(
                device="local",
                desired_direction=local_direction,
                danger=local_danger,
                ctrl_ts=ctrl_ts,
                control_cycle_min=control_cycle,
                previous_row=previous_row,
                last_command=last_local_all,
            )

            if not allow_local:
                save_wait_direction(reasons, "local", local_direction)
                append_reason(reasons, f"LOCAL_{local_gate}")
            else:
                response_ok: Optional[bool] = True
                if not local_danger and last_local:
                    prev_dir = device_command_direction(last_local, "local")
                    if prev_dir == local_direction:
                        response_ok = response_ok_for_local_valve(
                            conn, last_local, ctrl_ts, naun.trend_mph, diff_limit
                        )

                if response_ok is False:
                    save_wait_direction(reasons, "local", local_direction)
                    append_reason(reasons, "LOCAL_NO_RESPONSE")
                elif response_ok is None:
                    save_wait_direction(reasons, "local", local_direction)
                    append_reason(reasons, "LOCAL_RESPONSE_CHECK")
                else:
                    new_open = local_cur_open + local_direction * float(rules["LOCAL_VALVE_STEP"])
                    new_open = min(
                        max(new_open, float(rules["LOCAL_VALVE_MIN"])),
                        float(rules["LOCAL_VALVE_MAX"]),
                    )
                    if abs(new_open - local_cur_open) >= 0.5:
                        local_cmd.cmd_yn = "Y"
                        local_cmd.status = "READY"
                        local_cmd.target = new_open
                        local_cmd.observe_until = ctrl_ts + timedelta(
                            minutes=float(rules["LOCAL_VALVE_OBSERVE_MIN"])
                        )
                        local_reason = (
                            "LOCAL_FORCE_CLOSE" if local_force_close
                            else "LOCAL_FALLBACK_CLOSE" if local_direction < 0
                            else "LOCAL_RECOVERY_OPEN"
                        )
                        # 향후 원복 상태판단에도 사용하므로 LOCAL 동작사유를 앞쪽에 보존한다.
                        prepend_reason(reasons, local_reason)
                    else:
                        append_reason(reasons, "LOCAL_LIMIT")
    else:
        if (
                is_previous_cycle(previous_row, ctrl_ts, control_cycle)
                and row_has_applied_command(previous_row, "local")
                and not local_danger
        ):
            save_wait_direction(reasons, "local", 0)
            append_reason(reasons, "LOCAL_POST_CONTROL_HOLD")

    cmd_yn = "Y" if "Y" in {
        pump_cmd.cmd_yn,
        local_cmd.cmd_yn,
        national_cmd.cmd_yn,
    } else "N"

    if cmd_yn == "N" and not reasons:
        append_reason(reasons, "NORMAL_HOLD")

    reason_code = "|".join(reasons)[:100]

    row = {
        "CTRL_TS": ctrl_ts,
        "CMD_YN": cmd_yn,
        "PRED_STALE_YN": "Y" if pred_stale else "N",

        "PUMP_COMB": combo or None,
        "PUMP_CMD_YN": pump_cmd.cmd_yn,
        "PUMP_CMD_STATUS": pump_cmd.status,
        "PUMP_CUR_HZ": pump_cmd.current,
        "PUMP_TGT_HZ": pump_cmd.target,
        "PUMP_OBSERVE_UNTIL": pump_cmd.observe_until,

        "LOCAL_CMD_YN": local_cmd.cmd_yn,
        "LOCAL_CMD_STATUS": local_cmd.status,
        "LOCAL_CUR_OPEN": local_cmd.current,
        "LOCAL_TGT_OPEN": local_cmd.target,
        "LOCAL_OBSERVE_UNTIL": local_cmd.observe_until,

        "NATIONAL_CMD_YN": national_cmd.cmd_yn,
        "NATIONAL_CMD_STATUS": national_cmd.status,
        "NATIONAL_CUR_OPEN": national_cmd.current,
        "NATIONAL_TGT_OPEN": national_cmd.target,
        "NATIONAL_OBSERVE_UNTIL": national_cmd.observe_until,

        "REASON_CODE": reason_code,
    }

    LOGGER.info(
        "CTRL_TS=%s CMD=%s PUMP=%s %.2f->%.2f LOCAL=%s %.2f->%.2f NATIONAL=%s %.2f->%.2f REASON=%s",
        ctrl_ts,
        cmd_yn,
        pump_cmd.cmd_yn,
        pump_cmd.current if pump_cmd.current is not None else math.nan,
        pump_cmd.target if pump_cmd.target is not None else math.nan,
        local_cmd.cmd_yn,
        local_cmd.current if local_cmd.current is not None else math.nan,
        local_cmd.target if local_cmd.target is not None else math.nan,
        national_cmd.cmd_yn,
        national_cmd.current if national_cmd.current is not None else math.nan,
        national_cmd.target if national_cmd.target is not None else math.nan,
        reason_code,
    )

    if dry_run:
        return {
            "skipped": False,
            "dry_run": True,
            "row": row,
            "naun": naun.__dict__,
            "osik": osik.__dict__,
            "morning_active": morning_active,
            "offpeak_start": offpeak_start,
            "morning_target_dt": morning_target_dt,
            "control_cycle_min": control_cycle,
            "normal_control_interval_min": control_cycle * NORMAL_CONTROL_CYCLES,
            "pump_danger": pump_danger,
            "national_danger": national_danger,
            "local_danger": local_danger,
            "local_force_close": local_force_close,
            "local_conditional_close": local_conditional_close,
            "local_recovery_ready": local_recovery_ready,
            "higher_priority_completed": higher_priority_completed,
            "osik_inflow_m3h": osik_in.value if osik_in is not None else None,
            "osik_outflow_m3h": osik_out.value if osik_out is not None else None,
            "osik_flow_balance_m3h": osik_flow_balance,
            "osik_balance_deficit": osik_balance_deficit,
            "osik_balance_surplus": osik_balance_surplus,
            "level_trend_deadband_mph": trend_deadband,
            "distribution_close": distribution_close,
            "distribution_open": distribution_open,
            "naun_trend_mph": naun.trend_mph,
            "osik_trend_mph": osik.trend_mph,
            "pump_source_mode": pump_source_mode,
            "pump_source": pump_source_name,
            "pump_source_ts": pump_source_ts,
            "pump_reference_hz": pump_reference_hz,
            "pump_horizon_hold": pump_horizon_hold,
            "pump_qp": {h: {"q": pump_qp_values[h][0], "p": pump_qp_values[h][1],
                            "rec_hz": pump_qp_recs[h].freq_hz}
                        for h in pump_qp_recs if h in pump_qp_values},
        }

    sql = f"""
        INSERT INTO {CMD_TABLE} (
            CTRL_TS,
            CMD_YN,
            PRED_STALE_YN,

            PUMP_COMB,
            PUMP_CMD_YN,
            PUMP_CMD_STATUS,
            PUMP_CUR_HZ,
            PUMP_TGT_HZ,
            PUMP_OBSERVE_UNTIL,

            LOCAL_CMD_YN,
            LOCAL_CMD_STATUS,
            LOCAL_CUR_OPEN,
            LOCAL_TGT_OPEN,
            LOCAL_OBSERVE_UNTIL,

            NATIONAL_CMD_YN,
            NATIONAL_CMD_STATUS,
            NATIONAL_CUR_OPEN,
            NATIONAL_TGT_OPEN,
            NATIONAL_OBSERVE_UNTIL,

            REASON_CODE
        )
        VALUES (
            %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s
        )
    """
    params = (
        row["CTRL_TS"],
        row["CMD_YN"],
        row["PRED_STALE_YN"],

        row["PUMP_COMB"],
        row["PUMP_CMD_YN"],
        row["PUMP_CMD_STATUS"],
        row["PUMP_CUR_HZ"],
        row["PUMP_TGT_HZ"],
        row["PUMP_OBSERVE_UNTIL"],

        row["LOCAL_CMD_YN"],
        row["LOCAL_CMD_STATUS"],
        row["LOCAL_CUR_OPEN"],
        row["LOCAL_TGT_OPEN"],
        row["LOCAL_OBSERVE_UNTIL"],

        row["NATIONAL_CMD_YN"],
        row["NATIONAL_CMD_STATUS"],
        row["NATIONAL_CUR_OPEN"],
        row["NATIONAL_TGT_OPEN"],
        row["NATIONAL_OBSERVE_UNTIL"],

        row["REASON_CODE"],
    )

    execute(conn, sql, params)
    ctrl_id = fetchone(conn, "SELECT LAST_INSERT_ID() AS CTRL_ID")["CTRL_ID"]
    return {
        "skipped": False,
        "ctrl_id": ctrl_id,
        "row": row,
        "naun": naun.__dict__,
        "osik": osik.__dict__,
        "morning_active": morning_active,
    }


def acquire_lock(conn) -> bool:
    row = fetchone(conn, "SELECT GET_LOCK(%s, 1) AS OK", (LOCK_NAME,))
    return bool(row and row.get("OK") == 1)


def release_lock(conn) -> None:
    try:
        fetchone(conn, "SELECT RELEASE_LOCK(%s) AS OK", (LOCK_NAME,))
    except Exception:
        pass


def run_cycle(cfg: Dict[str, Any], ctrl_ts: datetime, dry_run: bool) -> dict:
    conn = connect_db(cfg)
    try:
        if not acquire_lock(conn):
            raise RuntimeError("다른 제어 프로세스가 실행 중입니다.")

        try:
            result = control_once(conn, ctrl_ts, dry_run=dry_run)
            if dry_run:
                conn.rollback()
            else:
                conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            release_lock(conn)
    finally:
        conn.close()


def seconds_to_next_control_run(now: datetime, offset_min: int = 2) -> float:
    """5분 기준시각 이후 offset_min에 실행한다.

    기본 +2분은 00분 예측 → main_epa_gs 01분 PRE 완료 → ctr 02분 판단 순서를
    맞추기 위한 값이다. CTRL_TS 자체는 00/05/10/... 기준시각으로 저장된다.
    """
    if not 0 <= offset_min <= 4:
        raise ValueError("schedule-offset-min은 0~4 범위여야 합니다.")
    base = floor_5min(now)
    candidate = base + timedelta(minutes=offset_min)
    if now >= candidate:
        candidate = base + timedelta(minutes=5 + offset_min)
    return max((candidate - now).total_seconds(), 0.5)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="군산정수장 5분 상태판단/정상 10분 제어 추천 (펌프 Hz → 국가산단 → 지방산단 fallback)"
    )
    ap.add_argument("--conn", default="connections.json", help="DB 접속정보 JSON")
    ap.add_argument(
        "--conn-key",
        default="maria-ems-db-gu",
        help="connections.json 내부 접속키",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="현재 5분 기준시각을 1회만 계산하고 종료",
    )
    ap.add_argument(
        "--ts",
        default=None,
        help='특정 시각을 1회 계산: "YYYY-MM-DD HH:MM:SS"',
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="DB 결과 INSERT 없이 계산/로그만 수행",
    )
    ap.add_argument(
        "--schedule-offset-min",
        type=int,
        default=2,
        choices=[0, 1, 2, 3, 4],
        help="5분 기준시각 이후 실제 판단 실행 오프셋. 기본 2분(main_epa_gs +1분 결과 대기)",
    )
    ap.add_argument(
        "--prediction-table",
        default=PRED_TABLE,
        help=f"수요예측 조회 테이블 (기본 {PRED_TABLE}, 섀도우 TB_CTR_TNK_RST_SH)",
    )
    ap.add_argument(
        "--cmd-table",
        default=CMD_TABLE,
        help=f"추천 저장·직전 추천 조회 테이블 (기본 {CMD_TABLE}, 섀도우 TB_CTRL_CMD_RST_SH)",
    )
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return ap


def main() -> int:
    ap = build_arg_parser()
    args = ap.parse_args()
    try:
        configure_tables(args)
    except ValueError as exc:
        ap.error(str(exc))

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    LOGGER.info(
        "테이블: 예측 조회=%s, 추천 저장=%s, 잠금=%s%s, 실행 오프셋=+%d분",
        PRED_TABLE, CMD_TABLE, LOCK_NAME, " (dry-run: 저장 안 함)" if args.dry_run else "",
        args.schedule_offset_min,
    )

    cfg = load_db_config(args.conn, args.conn_key)

    if args.ts:
        ts = datetime.fromisoformat(args.ts)
        result = run_cycle(cfg, floor_5min(ts), args.dry_run)
        print(json.dumps(result, default=str, ensure_ascii=False, indent=2))
        return 0

    if args.once:
        ts = floor_5min(datetime.now())
        result = run_cycle(cfg, ts, args.dry_run)
        print(json.dumps(result, default=str, ensure_ascii=False, indent=2))
        return 0

    LOGGER.info("5분 제어 루프 시작. 종료: Ctrl+C")
    while True:
        wait_sec = seconds_to_next_control_run(datetime.now(), args.schedule_offset_min)
        time.sleep(wait_sec)

        ts = floor_5min(datetime.now())
        try:
            result = run_cycle(cfg, ts, args.dry_run)
            LOGGER.debug("result=%s", result)
        except KeyboardInterrupt:
            raise
        except Exception:
            LOGGER.exception("제어주기 실행 실패: %s", ts)


if __name__ == "__main__":
    raise SystemExit(main())
