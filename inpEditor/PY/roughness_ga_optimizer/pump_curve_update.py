#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto 모드:
  - TB_RAWDATA에서 기간/펌프조합 데이터 조회
  - 송수유량(Q) - 송수압력(P) 기준 2차 회귀식 산출
  - 최근 1,000개 가동 데이터 기준 평균 오차율 산출
  - 전력 원단위, 전력비 원단위 산출

manual 모드:
  - 웹에서 전달받은 좌표로 2차 회귀식 산출
  - 같은 기간/펌프조합의 최근 1,000개 가동 데이터 기준 평균 오차율 산출
  - 같은 실제 운전 데이터 기준 전력 원단위, 전력비 원단위 산출

실행 예시:
python pump_curve_update.py --mode auto --start-date 2025-01-01 --end-date 2025-03-31 --pump-comb 1,3,5

python pump_curve_update.py --mode manual --start-date 2025-01-01 --end-date 2025-03-31 --pump-comb 1,3,5 \
  --points "[[3000,85],[4000,78],[5000,68],[6000,55],[7000,40]]"
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import pymysql

from config_path import load_config, resolve_config_path



RAWDATA_TABLE = "TB_RAWDATA"
POWER_PRICE_TABLE = "TB_POWER_PRICE"

# RAWDATA 컬럼
COL_TS = "TS"
COL_TAG = "TAGNAME"
COL_VALUE = "VALUE"

# 펌프 가동 태그 설정
PUMP_RUN_TAGS: Dict[int, str] = {
    1: "701-367-PMB-4002",
    2: "701-367-PMB-4005",
    3: "701-367-PMB-4009",
    4: "701-367-PMB-4014",
    5: "701-367-PMB-4023",
    6: "701-367-PMB-4032",
    7: "701-367-PMB-4041",
    8: "701-367-PMB-4303",
    9: "701-367-PMB-4082",
    10: "701-367-PMB-4086",
    11: "701-367-PMB-4090",
}

# 송수유량 태그: 두 태그 합산 사용, 단위 m3/h
FLOW_TAGS: List[str] = [
    "701-367-FRI-4001",
    "701-367-FRI-4004",
]

# 압력 태그
PRESSURE_TAG = "701-367-PRI-4100"

# 펌프 전력 태그
PUMP_POWER_TAGS: Dict[int, str] = {
    1: "701-367-PWI-4015",
    2: "701-367-PWI-4017",
    3: "701-367-PWI-4019",
    4: "701-367-PWI-4021",
    5: "701-367-PWI-4023",
    6: "701-367-PWI-4025",
    7: "701-367-PWI-4027",
    8: "701-367-PWI-4301",
    9: "701-367-PWI-4043",
    10: "701-367-PWI-4045",
    11: "701-367-PWI-4047",
}

# 펌프별 전력값을 kW로 환산하기 위한 계수.
# 8번 펌프 전력 태그는 W 기준으로 판단되어 0.001을 적용한다.
PUMP_POWER_TO_KW_SCALE: Dict[int, float] = {
    8: 0.001,
}



class ScriptError(Exception):
    """웹/백엔드에서 식별 가능한 스크립트 오류."""


def json_default(obj: Any) -> Any:
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat(sep=" ")
    return str(obj)


def print_json_and_exit(payload: Dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=json_default))
    raise SystemExit(exit_code)


def parse_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise ScriptError("start-date/end-date는 YYYY-MM-DD 형식이어야 합니다.")

    if e_date < s_date:
        raise ScriptError("end-date는 start-date보다 빠를 수 없습니다.")

    start_dt = datetime.combine(s_date, time(0, 0, 0))
    end_dt = datetime.combine(e_date, time(23, 59, 59))
    return start_dt, end_dt


def parse_pump_combination(pump_comb: str) -> List[int]:
    if not pump_comb or not pump_comb.strip():
        raise ScriptError("pump-comb 값이 비어 있습니다.")

    nums: List[int] = []
    for part in pump_comb.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ScriptError(f"펌프 조합 값이 숫자가 아닙니다: {part}")
        n = int(part)
        if n not in PUMP_RUN_TAGS:
            raise ScriptError(f"지원하지 않는 펌프 번호입니다: {n}")
        nums.append(n)

    nums = sorted(set(nums))
    if not nums:
        raise ScriptError("유효한 펌프 조합이 없습니다.")
    return nums


def normalize_pump_combination(pump_nums: Sequence[int]) -> str:
    return ",".join(str(n) for n in sorted(set(int(x) for x in pump_nums)))


def parse_manual_points(points_text: str) -> np.ndarray:
    if not points_text:
        raise ScriptError("manual 모드에서는 points 인자가 필요합니다.")

    try:
        raw = json.loads(points_text)
    except json.JSONDecodeError as e:
        raise ScriptError(f"points JSON 파싱 실패: {e}")

    if not isinstance(raw, list):
        raise ScriptError("points는 [[flow, pressure], ...] 형태의 배열이어야 합니다.")

    points: List[Tuple[float, float]] = []
    for item in raw:
        # 두 형식을 모두 수용한다.
        #  1) [flow, pressure] 2원소 배열/튜플
        #  2) {"flow": .., "head": ..} 형태의 객체(BE PumpCurvePoint 직렬화 형식, x/y 별칭도 허용)
        if isinstance(item, dict):
            flow_val = item.get("flow", item.get("x"))
            pressure_val = item.get("head", item.get("pressure", item.get("y")))
            if flow_val is None or pressure_val is None:
                raise ScriptError('points의 각 객체는 {"flow", "head"} 키를 가져야 합니다.')
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            flow_val, pressure_val = item[0], item[1]
        else:
            raise ScriptError('points의 각 항목은 [flow, pressure] 배열 또는 {"flow", "head"} 객체여야 합니다.')
        try:
            q = float(flow_val)
            p = float(pressure_val)
        except (TypeError, ValueError):
            raise ScriptError("points의 flow/pressure는 숫자여야 합니다.")
        points.append((q, p))

    if len(points) < 3:
        raise ScriptError("2차 회귀식 산출에는 최소 3개 좌표가 필요합니다.")

    return np.array(points, dtype=float)



def apply_table_config(section: Optional[Dict[str, Any]]) -> None:
    """설정의 pump_curve 섹션으로 조회 대상 테이블명을 정한다.

    api_server 와 CLI 가 같은 함수를 쓴다.
    round_digits 는 읽지 않는다. 계수/상수를 반올림 없이 원값으로 내보내기 때문이다.
    """
    global RAWDATA_TABLE, POWER_PRICE_TABLE

    section = section or {}
    RAWDATA_TABLE = str(section.get("rawdata_table") or "TB_RAWDATA")
    POWER_PRICE_TABLE = str(section.get("power_price_table") or "TB_POWER_PRICE")


class DbManager:
    """설정의 DB 블록을 받아 여는 읽기 전용 커넥션.

    optimizer 의 config.json 은 `database`, 예전 connections.json 은 `db` 키를 쓰므로
    둘 다 받는다.
    """

    def __init__(self, cfg: Dict[str, Any], autocommit: bool = False):
        self.conn = pymysql.connect(
            host=cfg["host"],
            port=int(cfg.get("port", 3306)),
            user=cfg["user"],
            password=cfg["password"],
            database=cfg.get("db") or cfg.get("database"),
            charset="utf8mb4",
            autocommit=autocommit,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def fetchall(self, sql: str, params: Tuple[Any, ...] = ()) -> List[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())

    def close(self) -> None:
        self.conn.close()



def make_required_tags(pump_nums: Sequence[int]) -> List[str]:
    tags: List[str] = []
    tags.extend(PUMP_RUN_TAGS.values())
    tags.extend(FLOW_TAGS)
    tags.append(PRESSURE_TAG)
    tags.extend(PUMP_POWER_TAGS[n] for n in pump_nums)
    return sorted(set(tags))


def fetch_rawdata(
    db: DbManager,
    start_dt: datetime,
    end_dt: datetime,
    tag_list: Sequence[str],
) -> pd.DataFrame:

    if not tag_list:
        raise ScriptError("조회할 태그가 없습니다.")

    placeholders = ",".join(["%s"] * len(tag_list))
    sql = f"""
        SELECT {COL_TS}, {COL_TAG}, {COL_VALUE}
        FROM {RAWDATA_TABLE}
        WHERE {COL_TS} >= %s
          AND {COL_TS} <= %s
          AND {COL_TAG} IN ({placeholders})
        ORDER BY {COL_TS}
    """

    rows = db.fetchall(sql, (start_dt, end_dt, *tag_list))
    if not rows:
        raise ScriptError("조회 기간 내 RAW 데이터가 없습니다.")

    df = pd.DataFrame(rows)
    df[COL_TS] = pd.to_datetime(df[COL_TS], errors="coerce")
    df[COL_VALUE] = pd.to_numeric(df[COL_VALUE], errors="coerce")
    df = df.dropna(subset=[COL_TS, COL_TAG, COL_VALUE])

    if df.empty:
        raise ScriptError("유효한 RAW 데이터가 없습니다.")

    df[COL_TS] = df[COL_TS].dt.floor("min")

    pv = df.pivot_table(
        index=COL_TS,
        columns=COL_TAG,
        values=COL_VALUE,
        aggfunc="last",
    ).sort_index()
    
    if pv.empty:
        raise ScriptError("분 단위 기준으로 사용할 데이터가 없습니다.")

    return pv

def fetch_power_price(db: DbManager) -> Dict[int, float]:
    """
    전력비 원단위 계산 함수
    TB_POWER_PRICE에서 시간대별 단가 조회
    컬럼: `TIME`, UNIT_PRICE
    """
    sql = f"""
        SELECT `TIME`, UNIT_PRICE
        FROM {POWER_PRICE_TABLE}
    """
    rows = db.fetchall(sql)
    if not rows:
        raise ScriptError("TB_POWER_PRICE에 전력 단가 데이터가 없습니다.")

    price: Dict[int, float] = {}
    for r in rows:
        try:
            h = int(r["TIME"])
            v = float(r["UNIT_PRICE"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= h <= 23:
            price[h] = v

    missing = sorted(set(range(24)) - set(price))
    if missing:
        raise ScriptError(f"TB_POWER_PRICE에 누락된 시간대가 있습니다: {missing}")

    return price


def build_analysis_frame(raw: pd.DataFrame, pump_nums: Sequence[int]) -> pd.DataFrame:
    """
    분석용 데이터프레임 생성
    반환 columns:
    - FLOW: 송수유량 m3/h
    - PRESSURE: 송수압력
    - POWER_KW: 선택 펌프 전력 합계 kW
    """
    selected = set(int(n) for n in pump_nums)

    required_cols = list(PUMP_RUN_TAGS.values()) + FLOW_TAGS + [PRESSURE_TAG]
    required_cols += [PUMP_POWER_TAGS[n] for n in selected]

    missing = [c for c in required_cols if c not in raw.columns]
    if missing:
        raise ScriptError(f"RAW 데이터에 필요한 태그 컬럼이 없습니다: {missing}")

    df = raw.copy()

    # 정확한 펌프 조합만 추출.
    # 펌프 가동 태그는 정확히 0=OFF, 1=ON 값이 들어온다는 전제.
    run_ok = pd.Series(True, index=df.index)
    for n, tag in PUMP_RUN_TAGS.items():
        state = pd.to_numeric(df[tag], errors="coerce")
        if n in selected:
            run_ok &= state.eq(1)
        else:
            run_ok &= state.eq(0)

    out = pd.DataFrame(index=df.index)
    out["FLOW"] = df[FLOW_TAGS[0]].astype(float) + df[FLOW_TAGS[1]].astype(float)
    out["PRESSURE"] = df[PRESSURE_TAG].astype(float)

    power_total = pd.Series(0.0, index=df.index)
    for n in selected:
        tag = PUMP_POWER_TAGS[n]
        scale = PUMP_POWER_TO_KW_SCALE.get(n, 1.0)
        power_total = power_total + df[tag].astype(float) * scale
    out["POWER_KW"] = power_total

    out = out[run_ok]
    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=["FLOW", "PRESSURE", "POWER_KW"])

    out = out[(out["FLOW"] > 0) & (out["PRESSURE"] > 0) & (out["POWER_KW"] >= 0)]

    if out.empty:
        raise ScriptError("지정 펌프 조합의 유효 가동 데이터가 없습니다.")

    return out.sort_index()


@dataclass(frozen=True)
class CurveCoefficients:
    a: float  # Q^2 계수
    b: float  # Q 계수
    c: float  # 상수항


def fit_quadratic_curve(flow: np.ndarray, pressure: np.ndarray) -> CurveCoefficients:
    q = np.asarray(flow, dtype=float).ravel()
    p = np.asarray(pressure, dtype=float).ravel()

    valid = np.isfinite(q) & np.isfinite(p)
    q = q[valid]
    p = p[valid]

    if len(q) < 3:
        raise ScriptError("2차 회귀식 산출에는 최소 3개 데이터가 필요합니다.")

    if len(np.unique(q)) < 3:
        raise ScriptError("2차 회귀식 산출에는 서로 다른 유량값이 최소 3개 필요합니다.")

    # numpy.polyfit(deg=2) 반환 순서: [a, b, c]
    # P = aQ^2 + bQ + c
    a, b, c = np.polyfit(q, p, deg=2)
    return CurveCoefficients(a=float(a), b=float(b), c=float(c))


def predict_pressure(flow: Union[pd.Series, np.ndarray], coef: CurveCoefficients) -> np.ndarray:
    q = np.asarray(flow, dtype=float)
    return coef.a * (q ** 2) + coef.b * q + coef.c


def calculate_avg_error_rate(
    df: pd.DataFrame,
    coef: CurveCoefficients,
    n_latest: int = 1000,
) -> float:
    """
    지정 기간/조합 데이터 중 시간 기준 최신 n_latest개로 평균 오차율 계산.
    오차율_i = |P_pred_i - P_i| / P_i * 100
    """
    if df.empty:
        raise ScriptError("오차율 계산 대상 데이터가 없습니다.")

    target = df.sort_index().tail(n_latest).copy()
    target = target[target["PRESSURE"] > 0]
    if target.empty:
        raise ScriptError("오차율 계산에 사용할 유효 압력 데이터가 없습니다.")

    pred = predict_pressure(target["FLOW"], coef)
    actual = target["PRESSURE"].to_numpy(dtype=float)
    err = np.abs(pred - actual) / actual * 100.0

    return float(np.nanmean(err))


def calculate_power_unit(df: pd.DataFrame) -> float:
    """
    전력 원단위 = Σ전력사용량(kWh) / Σ송수량(m3)

    분 단위 기준:
    전력사용량_i = POWER_KW / 60
    송수량_i = FLOW(m3/h) / 60
    """
    if df.empty:
        raise ScriptError("전력 원단위 계산 대상 데이터가 없습니다.")

    power_kwh = df["POWER_KW"].astype(float) / 60.0
    flow_m3 = df["FLOW"].astype(float) / 60.0

    denom = float(flow_m3.sum())
    if denom <= 0:
        raise ScriptError("전력 원단위 계산 시 송수량 합계가 0 이하입니다.")

    return float(power_kwh.sum() / denom)


def calculate_power_cost_unit(df: pd.DataFrame, price_by_hour: Dict[int, float]) -> float:
    """
    전력비 원단위 =
    Σ(전력사용량_i(kWh) × 시간대별 전력단가_i) / Σ송수량_i(m3)
    """
    if df.empty:
        raise ScriptError("전력비 원단위 계산 대상 데이터가 없습니다.")

    target = df.copy()
    target["HOUR"] = target.index.hour
    target["UNIT_PRICE"] = target["HOUR"].map(price_by_hour)

    if target["UNIT_PRICE"].isna().any():
        missing = sorted(target.loc[target["UNIT_PRICE"].isna(), "HOUR"].unique().tolist())
        raise ScriptError(f"전력단가 매칭 실패 시간대: {missing}")

    target["POWER_KWH"] = target["POWER_KW"].astype(float) / 60.0
    target["FLOW_M3"] = target["FLOW"].astype(float) / 60.0
    target["POWER_COST"] = target["POWER_KWH"] * target["UNIT_PRICE"].astype(float)

    denom = float(target["FLOW_M3"].sum())
    if denom <= 0:
        raise ScriptError("전력비 원단위 계산 시 송수량 합계가 0 이하입니다.")

    return float(target["POWER_COST"].sum() / denom)


def coef_to_str(v: float) -> Optional[str]:
    """회귀식 계수/상수를 정밀도 손실 없이 문자열로 변환한다(자바 BigDecimal 수신용).

    float(64bit)을 JSON number 로 그대로 내보내면 자바가 double 로 받아 유효자릿수가
    잘리므로, 계수/상수는 문자열로 내보내 자바에서 BigDecimal 로 원값을 보존한다.
    - **절대 반올림하지 않는다**. 2차항 계수 a 는 매우 작아(예: ~1e-7) 반올림하면
      "-0"/"0" 으로 뭉개져 자바 수신이 깨지므로 항상 원값을 쓴다.
    - 음수 0(-0.0)은 양수 0(0.0)으로 정규화해 자바가 "-0" 을 받지 않게 한다.
    - 지수표기 없이(0.0000001 형태) 왕복 가능한 최단 십진 표기로 변환한다
      (BigDecimal 이 지수표기도 파싱하지만 가독성을 위해 일반 표기 사용).
    - NaN/Inf 등 유효하지 않은 값은 None(→ JSON null)으로 내려 자바가 회귀 불가로 판정하게 한다.
    """
    d = float(v)
    if not np.isfinite(d):
        return None
    if d == 0.0:          # -0.0 → 0.0 정규화 (자바 "-0" 수신 방지)
        d = 0.0
    return np.format_float_positional(d, unique=True, trim="-")


def build_result(
    pump_combination: str,
    coef: CurveCoefficients,
    avg_error_rate: float,
    power_unit: float,
    power_cost_unit: float,
    data_count: int,
) -> Dict[str, Any]:
    return {
        "pump_combination": pump_combination,
        "data_count": int(data_count),
        # 회귀식 계수/상수는 반올림 없이 원값 문자열로 내보낸다(자바 BigDecimal 수신).
        # 반올림하면 작은 2차항 계수가 -0 으로 뭉개져 자바 수신이 깨진다.
        # 컬럼 매핑(레거시 SSOT, DrvnConfig.pressureCalValue): P = P_ADD_VAL·Q² + P_MUL_VAL·Q + P_SQRT_MUL_VAL
        # → P_ADD_VAL=2차항 a, P_MUL_VAL=1차항 b, P_SQRT_MUL_VAL=상수항 c (컬럼명이 역할과 반대라 주의)
        "P_ADD_VAL": coef_to_str(coef.a),
        "P_MUL_VAL": coef_to_str(coef.b),
        "P_SQRT_MUL_VAL": coef_to_str(coef.c),
        # 평가지표도 반올림 없이 원값(number)으로 내보낸다
        "avg_error_rate": float(avg_error_rate),
        "power_unit": float(power_unit),
        "power_cost_unit": float(power_cost_unit),
    }



def load_filtered_data_for_request(
    db: DbManager,
    start_date: str,
    end_date: str,
    pump_nums: Sequence[int],
) -> pd.DataFrame:
    start_dt, end_dt = parse_date_range(start_date, end_date)
    tags = make_required_tags(pump_nums)
    raw = fetch_rawdata(db, start_dt, end_dt, tags)
    return build_analysis_frame(raw, pump_nums)


def run_auto(
    db: DbManager,
    start_date: str,
    end_date: str,
    pump_nums: Sequence[int],
    pump_hz: Optional[str] = None,
) -> Dict[str, Any]:
    """실제 운전 데이터로 성능곡선을 산출한다.

    pump_hz 는 받기만 하고 쓰지 않는다. 군산판(pump_curve_update_gunsan)은 펌프별
    목표 주파수로 데이터를 걸러내지만 고산에는 주파수 태그 자체가 없다. 두 모듈의
    시그니처를 맞춰 두어야 리졸버(pump_curve_engine)를 거치는 호출부가 어느 현장인지
    몰라도 되므로, 인자만 받아 무시한다.
    """
    pump_combination = normalize_pump_combination(pump_nums)

    df = load_filtered_data_for_request(db, start_date, end_date, pump_nums)
    coef = fit_quadratic_curve(df["FLOW"].to_numpy(), df["PRESSURE"].to_numpy())

    avg_error_rate = calculate_avg_error_rate(df, coef, n_latest=1000)
    power_unit = calculate_power_unit(df)

    price_by_hour = fetch_power_price(db)
    power_cost_unit = calculate_power_cost_unit(df, price_by_hour)

    return build_result(
        pump_combination=pump_combination,
        coef=coef,
        avg_error_rate=avg_error_rate,
        power_unit=power_unit,
        power_cost_unit=power_cost_unit,
        data_count=len(df),
    )


def run_manual(
    db: DbManager,
    start_date: str,
    end_date: str,
    pump_nums: Sequence[int],
    points_text: str,
    pump_hz: Optional[str] = None,
) -> Dict[str, Any]:
    """사용자 입력 좌표로 회귀하고, 같은 기간 실측 데이터로 운전 지표를 계산한다.

    pump_hz 는 run_auto 와 같은 이유로 받기만 하고 쓰지 않는다.
    """
    pump_combination = normalize_pump_combination(pump_nums)

    points = parse_manual_points(points_text)
    coef = fit_quadratic_curve(points[:, 0], points[:, 1])

    # 수동 모드에서도 같은 기간/조합의 실제 운전 데이터로 지표 계산
    df = load_filtered_data_for_request(db, start_date, end_date, pump_nums)

    avg_error_rate = calculate_avg_error_rate(df, coef, n_latest=1000)
    power_unit = calculate_power_unit(df)

    price_by_hour = fetch_power_price(db)
    power_cost_unit = calculate_power_cost_unit(df, price_by_hour)

    return build_result(
        pump_combination=pump_combination,
        coef=coef,
        avg_error_rate=avg_error_rate,
        power_unit=power_unit,
        power_cost_unit=power_cost_unit,
        data_count=len(df),
    )



def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="펌프 성능곡선 갱신/추출 스크립트")

    ap.add_argument("--mode", choices=["auto", "manual"], required=True, help="auto=자동 회귀, manual=사용자 좌표 회귀")
    ap.add_argument("--start-date", required=True, help="분석 시작일 YYYY-MM-DD")
    ap.add_argument("--end-date", required=True, help="분석 종료일 YYYY-MM-DD")
    ap.add_argument("--pump-comb", required=True, help="펌프 조합 예: 1,3,5")

    ap.add_argument("--points", default="", help='manual 모드 좌표 예: "[[3000,85],[4000,78],[5000,68]]"')

    ap.add_argument(
        "--config",
        default=None,
        help="설정 JSON 경로. 생략하면 APP_CONFIG 환경변수, 그것도 없으면 모듈 기본값을 쓴다.",
    )
    # 테이블명은 설정 파일의 pump_curve 섹션에서 읽는다. 아래 인자는 그 값을 일회성으로 덮어쓸 때만 쓴다.
    ap.add_argument("--rawdata-table", default=None, help="RAWDATA 테이블명. 기본은 설정의 pump_curve.rawdata_table")
    ap.add_argument("--power-price-table", default=None, help="전력단가 테이블명. 기본은 설정의 pump_curve.power_price_table")

    return ap.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    global RAWDATA_TABLE, POWER_PRICE_TABLE

    args = parse_args(argv)

    try:
        # 설정 해석은 optimizer 규약(APP_CONFIG)을 따른다. DB 접속 정보도 같은 파일의 db 블록에서 온다.
        config_file = Path(args.config) if args.config else resolve_config_path()
        config = load_config(config_file)

        apply_table_config(config.get("pump_curve"))
        if args.rawdata_table:
            RAWDATA_TABLE = args.rawdata_table
        if args.power_price_table:
            POWER_PRICE_TABLE = args.power_price_table

        pump_nums = parse_pump_combination(args.pump_comb)
        db = DbManager(config["db"])

        try:
            if args.mode == "auto":
                result = run_auto(
                    db=db,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    pump_nums=pump_nums,
                )
            else:
                result = run_manual(
                    db=db,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    pump_nums=pump_nums,
                    points_text=args.points,
                )
        finally:
            db.close()

        print_json_and_exit(result, exit_code=0)

    except ScriptError as e:
        print_json_and_exit(
            {
                "status": "error",
                "message": str(e),
            },
            exit_code=1,
        )
    except Exception as e:
        print_json_and_exit(
            {
                "status": "error",
                "message": f"예상하지 못한 오류: {e}",
            },
            exit_code=1,
        )


if __name__ == "__main__":
    main()
