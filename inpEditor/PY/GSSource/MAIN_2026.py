#!/usr/bin/env python
# coding: utf-8
"""
MAIN_2026.py  —  XGBoost 기반 고산정수장 실시간 예측
시트 : Gosan (단일)
모델 : XGBoost Booster (.json)
예측 horizons : 10분 / 20분 / 30분 / 40분 / 50분 / 60분 / 120분 / 180분 / 360분
스케줄 : 10분마다 실행 (최소 예측 단위와 동일)
"""
# =============================================================================
# 1. 임포트 및 경로 설정
# =============================================================================
import json
import os
import re
import sys
import time
import logging

import numpy as np
import pandas as pd
import xgboost as xgb
import pymysql
import schedule
from pymysql.cursors import DictCursor
from datetime import datetime, timedelta
from pytz import timezone
from sqlalchemy import create_engine
from logging.handlers import RotatingFileHandler

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 설정 경로 주입 규약 ─────────────────────────────────────────────────────
# roughness_ga_optimizer 와 동일한 규약을 쓴다.
#   APP_CONFIG      : 런타임 설정 JSON 경로 (기본 config.json)
#   APP_CONNECTIONS : DB 접속 정보 JSON 경로 (기본 libs/connections.json)
# env 가 가리킨 파일이 없으면 조용히 기본값으로 떨어지지 않고 즉시 실패한다.
# 마운트를 빠뜨렸을 때 기본 db_key(고산 운영 DB)로 붙어버리는 사고를 막기 위해서다.
_PATH_WARNINGS = []


def _resolve_path(env_name: str, default_relative: str) -> str:
    """env -> (상대경로면 모듈 디렉터리 기준 절대화) -> 기본값 순으로 설정 파일 경로를 정한다."""
    raw = os.environ.get(env_name)
    if raw:
        path = raw if os.path.isabs(raw) else os.path.join(_THIS_DIR, raw)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{env_name} 가 가리키는 설정 파일이 없습니다: {path}")
        return path
    _PATH_WARNINGS.append(f"{env_name} 미설정 - 모듈 기본값 사용: {default_relative}")
    return os.path.join(_THIS_DIR, default_relative)


_CONFIG_PATH = _resolve_path('APP_CONFIG', 'config.json')
_CONN_PATH = _resolve_path('APP_CONNECTIONS', os.path.join('libs', 'connections.json'))
_APP_CONFIG_CACHE = None


def get_app_config() -> dict:
    """Read GSSource runtime config. Missing values fall back to safe defaults."""
    global _APP_CONFIG_CACHE
    if _APP_CONFIG_CACHE is None:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, encoding='utf-8') as f:
                _APP_CONFIG_CACHE = json.load(f)
        else:
            # APP_CONFIG 를 준 경우는 _resolve_path 에서 이미 걸러졌다.
            # 여기 오는 것은 env 미설정 + 기본 파일도 없는 경우뿐이다.
            _APP_CONFIG_CACHE = {}
    return _APP_CONFIG_CACHE


def _config_section(name: str) -> dict:
    value = get_app_config().get(name, {})
    return value if isinstance(value, dict) else {}


def _safe_table_name(table_name: str, default: str) -> str:
    name = str(table_name or default)
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"Invalid table name: {name}")
    return name



# ============================================================
# XGBoost용 lag 기반 피처 생성
# ============================================================

# 저장된 모델과 동일한 피처 구성 (lag 6개 + rmean12)
_DEFAULT_LAGS    = [1, 2, 3, 6, 12, 24]
TEST_BASE_DATE = _config_section("prediction").get("test_base_date")
_ROLLING_WINDOWS = [12]   # rmean12 만 사용 (학습 시 설정과 동일)


def make_xgb_features(df: pd.DataFrame, target_cols: list, horizon: int,
                      lags: list = None):
    """
    XGBoost용 lag 기반 피처 + 시간 피처 생성.

    Parameters
    ----------
    df          : 스케일된 시계열 DataFrame (10분 단위 DatetimeIndex)
    target_cols : 예측 대상 컬럼 목록
    horizon     : 예측 스텝 수 (10분 단위, 예: 1→+10분, 6→+60분)
    lags        : 사용할 lag 목록 (None이면 기본값 사용)
                  기본: [1~12, 18, 24, 36, 48, 72, 96, 144]
                  → 최근 2시간(촘촘) + 4·6·8·12·16·24시간 전

    Returns
    -------
    X : pd.DataFrame  lag 피처 + 시간 피처
    y : pd.DataFrame  horizon 스텝 후 target 값
    """
    if lags is None:
        lags = _DEFAULT_LAGS

    feat_frames = []

    # lag 피처 생성
    for col in df.columns:
        for lag in lags:
            feat_frames.append(df[col].shift(lag).rename(f'{col}_lag{lag}'))

    # rolling 통계 피처 (shift(1)로 미래 누수 방지) — rmean 만 사용
    for col in df.columns:
        s = df[col].shift(1)
        for w in _ROLLING_WINDOWS:
            feat_frames.append(s.rolling(w).mean().rename(f'{col}_rmean{w}'))

    # 시간 피처 (주기성 인코딩)
    hour_float = df.index.hour + df.index.minute / 60.0
    feat_frames.append(pd.Series(
        np.sin(2 * np.pi * hour_float / 24), index=df.index, name='sin_hour'))
    feat_frames.append(pd.Series(
        np.cos(2 * np.pi * hour_float / 24), index=df.index, name='cos_hour'))
    feat_frames.append(pd.Series(
        df.index.dayofweek, index=df.index, name='dayofweek'))
    feat_frames.append(pd.Series(
        (df.index.dayofweek >= 5).astype(int), index=df.index, name='is_weekend'))

    X = pd.concat(feat_frames, axis=1)

    # 타겟: horizon 스텝 후 값
    y = df[target_cols].shift(-horizon)

    # NaN 제거
    valid = X.notna().all(axis=1) & y.notna().all(axis=1)
    X = X[valid]
    y = y[valid]

    return X, y


# =============================================================================
# 2. 경로 설정 및 상수
# =============================================================================

# ── 시트 및 경로 설정 ──────────────────────────────────────────────────────
SHEETNAME    = 'Gosan'
TAGLIST_PATH = os.path.join(_THIS_DIR, 'GS_taglist_250904.xlsx')
LOG_PATH     = os.path.join(_THIS_DIR, 'log', 'log_2026.txt')

# 저장된 XGBoost 모델 경로
MODEL_DIR = os.path.join(_THIS_DIR, 'saved_model', 'xgb')

# ── 예측 Horizon 정의 (saved_model/xgb 내 폴더 기준) ────────────────────────
# key: 이름(모델 디렉토리명과 일치), value: 10분 단위 스텝 수
HORIZONS: dict = {
    '10min' :  1,
    '20min' :  2,
    '30min' :  3,
    '40min' :  4,
    '50min' :  5,
    '60min' :  6,
    '120min': 12,
    '180min': 18,
    '360min': 36,
}

# horizon → tag_pred_l duration_cd 매핑
HORIZON_CD: dict = {
    '10min' : '10M',
    '20min' : '20M',
    '30min' : '30M',
    '40min' : '40M',
    '50min' : '50M',
    '60min' : '1H',
    '120min': '2H',
    '180min': '3H',
    '360min': '6H',
}

# DB에서 가져올 1분 단위 레코드 수
# 최대 lag = 144스텝 × 10분 = 1440분 → 여유 포함 2160분(36시간)
DB_FETCH_LIMIT  = int(_config_section("prediction").get("db_fetch_limit", 2160))
UPLOAD_BATCH_SIZE = int(_config_section("prediction").get("upload_batch_size", 500))   # tag_pred_l INSERT 배치 크기


# =============================================================================
# 2. 로깅 설정
# =============================================================================
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
_log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
_file_handler  = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)
_file_handler.setFormatter(_log_formatter)
_file_handler.setLevel(logging.INFO)

logger = logging.getLogger('xgb_main')
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(_file_handler)

# 경로 해석은 logger 준비 전에 끝나므로 여기서 몰아서 남긴다.
for _warning in _PATH_WARNINGS:
    logger.warning(_warning)


def describe_config() -> str:
    """적용된 설정 파일과 DB 대상을 한 줄로 요약한다(비밀번호 제외)."""
    try:
        db = get_db_config()
        target = f"{db.get('host')}:{db.get('port', 3306)}/{db.get('db')}"
    except Exception as exc:
        target = f"<확인 실패: {exc}>"
    return f"[config] APP_CONFIG={_CONFIG_PATH} APP_CONNECTIONS={_CONN_PATH} db={target}"


# =============================================================================
# 3. DB 연결 / 조회 함수
# =============================================================================

def get_db_config() -> dict:
    """Read the selected DB connection from APP_CONNECTIONS (기본 libs/connections.json)."""
    db_key = get_app_config().get('db_key', 'maria-ems-db-gs')
    with open(_CONN_PATH, encoding='utf-8') as f:
        connections = json.load(f)
    if db_key not in connections:
        raise KeyError(f"DB connection key not found: {db_key}")
    return connections[db_key]


def open_db():
    """고산 MariaDB 연결 반환. 실패 시 None."""
    try:
        db_config = get_db_config().copy()
        db_config.pop("prediction_table", None)
        return pymysql.connect(**db_config)
    except Exception:
        logger.exception("DB 연결 실패")
        return None


def get_prediction_table() -> str:
    return _safe_table_name(_config_section("prediction").get("table"), "tag_pred_l")


def get_prediction_history_table() -> str:
    return _safe_table_name(_config_section("prediction").get("history_table"), "tag_pred_h")


def get_rawdata_table() -> str:
    return _safe_table_name(_config_section("prediction").get("rawdata_table"), "TB_RAWDATA")


def get_pump_result_table() -> str:
    return _safe_table_name(_config_section("pump_routing").get("table"), "TB_PUMP_RST")


def is_pump_routing_enabled() -> bool:
    return bool(_config_section("pump_routing").get("enabled", True))


def _format_ref_timestamp(ref_time=None) -> str:
    """Return a KST timestamp string used as the prediction reference time."""
    KST = timezone('Asia/Seoul')
    if ref_time is None:
        now = datetime.now().astimezone(KST)
        if TEST_BASE_DATE:
            return f"{TEST_BASE_DATE} {now.strftime('%H:%M')}:00"
        return now.strftime('%Y-%m-%d %H:%M:00')

    if isinstance(ref_time, datetime):
        dt = ref_time
    else:
        dt = pd.to_datetime(ref_time).to_pydatetime()

    if dt.tzinfo is not None:
        dt = dt.astimezone(KST).replace(tzinfo=None)
    return dt.strftime('%Y-%m-%d %H:%M:00')


def _fetch_tag(connection, tag_name: str, ref_time: str) -> pd.DataFrame:
    """특정 태그의 최신 데이터를 DB에서 조회 후 DatetimeIndex DataFrame 반환."""
    cursor = connection.cursor(DictCursor)
    try:
        cursor.execute(
            """
            SELECT TS AS 'Datetime', VALUE
            FROM {rawdata_table}
            WHERE TAGNAME = %s AND TS <= %s
            ORDER BY TS DESC
            LIMIT %s
            """.format(rawdata_table=get_rawdata_table()),
            (tag_name, ref_time, DB_FETCH_LIMIT),
        )
        rows = cursor.fetchall()
    except Exception:
        logger.exception(f"DB 조회 실패 - {tag_name}")
        return pd.DataFrame(columns=['VALUE'])

    if not rows:
        logger.warning(f"[데이터 없음] {tag_name} ({ref_time})")
        return pd.DataFrame(columns=['VALUE'])

    df = pd.DataFrame(rows)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.set_index('Datetime').sort_index()
    df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
    return df


# =============================================================================
# 4. 초기화 — 모델 + 스케일러 일괄 로드 (프로세스 시작 시 1회 실행)
# =============================================================================

def initialization_xgb():
    """
    saved_model/xgb/Gosan_{horizon}/ 디렉토리 기반으로
    horizon별 XGBoost Booster 모델을 로드.

    - var_list, target_list 는 저장된 .json 모델 파일에서 동적 추출
    - 스케일러 없음 (XGBoost 모델은 원시값 기준 학습)
    - df_meta 는 DB 태그명 매핑용으로만 사용

    Returns
    -------
    df_meta           : 태그리스트 메타 DataFrame
    models_by_horizon : {horizon_label: {target: xgb.Booster}}
    var_list          : 입력 변수명 리스트 (모델 feature_names에서 추출)
    target_list       : 예측 대상 변수명 리스트 (모델 파일명에서 추출)
    """
    # ── 태그리스트: DB 태그명 ↔ 변수명 매핑용 ─────────────────────────
    worksheet = pd.read_excel(TAGLIST_PATH, sheet_name=SHEETNAME, header=0)
    worksheet = worksheet.dropna(axis=1).reset_index(drop=True)
    df_meta   = worksheet.loc[
        (worksheet['비고'] != 'NU') & (worksheet['사용'] == 'Y')
    ].reset_index(drop=True)

    # ── 10min 모델의 feature_names 에서 var_list / target_list 동적 추출 ──
    sample_dir   = os.path.join(MODEL_DIR, f'{SHEETNAME}_10min')
    sample_files = [f for f in os.listdir(sample_dir) if f.endswith('.json')]
    if not sample_files:
        raise FileNotFoundError(f"XGBoost 모델 파일 없음: {sample_dir}")

    target_list = sorted([os.path.splitext(f)[0] for f in sample_files])

    sample_booster = xgb.Booster()
    sample_booster.load_model(os.path.join(sample_dir, sample_files[0]))
    var_list: list = []
    for fn in sample_booster.feature_names:
        m = re.match(r'^(.+?)_(lag|rmean)\d+$', fn)
        if m:
            v = m.group(1)
            if v not in var_list:
                var_list.append(v)
    print(f"  입력 변수({len(var_list)}개): {var_list}")
    print(f"  예측 타겟({len(target_list)}개): {target_list}")

    # ── horizon별 XGBoost 모델 로드 ──────────────────────────────────
    models_by_horizon: dict = {}
    for horizon_label in HORIZONS:
        model_name = f"{SHEETNAME}_{horizon_label}"
        m_dir      = os.path.join(MODEL_DIR, model_name)
        models: dict = {}
        for target in target_list:
            model_file = os.path.join(m_dir, f"{target}.json")
            if not os.path.exists(model_file):
                raise FileNotFoundError(f"모델 파일 없음: {model_file}")
            booster = xgb.Booster()
            booster.load_model(model_file)
            models[target] = booster
        models_by_horizon[horizon_label] = models
        print(f"  모델 로드 완료: {model_name}  (타겟 {len(models)}개)")

    logger.info(
        f"초기화 완료 — horizons={list(HORIZONS)}, "
        f"변수={len(var_list)}개, 타겟={target_list}"
    )
    return df_meta, models_by_horizon, var_list, target_list


# =============================================================================
# 5. 실시간 예측 함수
# =============================================================================

def predict_xgb(df_meta, models_by_horizon, var_list, target_list, ref_time=None):
    """
    DB에서 최신 데이터를 가져와 전처리 후 horizon별 XGBoost 예측 수행.

    처리 순서:
      1) DB 조회 (1분 단위, 최근 DB_FETCH_LIMIT 행)
      2) H 접두사 변수 합산
      3) 유량 변수 이상값 제거 (Q < 10 → NaN)
      4) 10분 단위 리샘플링 (mean)
      5) make_xgb_features(horizon=0) → 마지막 행 추출
      6) xgb.DMatrix 변환 후 horizon별 XGBoost 예측 → RELU(≥0)

    Returns
    -------
    results_by_horizon : {horizon_label: pd.DataFrame}
        컬럼: {target}_Predict
        인덱스: 예측 대상 시각 (last_timestamp + horizon × 10분)
    current_vals       : pd.Series  마지막 타임스텝 값 (펌프 라우팅용)
    pred_timestamp     : str        기준 시각 (KST 문자열)
    """
    # 10초 대기 — DB의 1분 단위 데이터가 갱신되기까지의 여유 시간
    if ref_time is None and time.localtime().tm_sec < 10:
        time.sleep(10 - time.localtime().tm_sec)

    pred_timestamp = _format_ref_timestamp(ref_time)
    print(f"  [기준시각] {pred_timestamp} (KST)")

    # ── 1. DB 데이터 조회 ──────────────────────────────────────────────
    db_conn = open_db()
    if db_conn is None:
        logger.error("DB 연결 실패 — 예측 중단")
        return None, None, None, None

    data_df = pd.DataFrame(
        index=pd.date_range(end=pred_timestamp, periods=DB_FETCH_LIMIT, freq='1min')
    )
    try:
        for i in range(len(df_meta)):
            tag = df_meta['태그명'][i]
            var = df_meta['변수명'][i]
            col_df = _fetch_tag(db_conn, tag, pred_timestamp)
            data_df[var] = col_df['VALUE'] if not col_df.empty else np.nan
    finally:
        db_conn.close()

    # ── 2. H 접두사 변수 합산 ─────────────────────────────────────────
    var_list_2      = df_meta['변수명'].tolist()
    var_list_height = [s for s in var_list_2 if s[0] == 'H']
    var_first_two   = [s.split('_')[0] for s in var_list_height]
    var_height_uniq = list(set(var_first_two))
    if len(var_height_uniq) != len(var_list_height):
        for prefix in var_height_uniq:
            height_cols = [s for s in var_list_height if s.startswith(prefix)]
            if len(height_cols) > 1:
                data_df[prefix] = data_df[height_cols].sum(axis=1)
                data_df.drop(columns=height_cols, inplace=True)
                for col in height_cols:
                    var_list_2.remove(col)
                var_list_2.append(prefix)

    if set(var_list) != set(var_list_2):
        logger.error(f"변수 불일치 — 모델: {sorted(var_list)}, 데이터: {sorted(var_list_2)}")
        return None, None, None, None

    # ── 3. 유량 이상값 제거 (Q < 10 → NaN) ───────────────────────────
    flux_cols = [c for c in data_df.columns if c.startswith('Q')]
    if flux_cols:
        data_df[flux_cols] = data_df[flux_cols].where(data_df[flux_cols] >= 10, other=np.nan)

    # ── 4. 10분 단위 리샘플링 ─────────────────────────────────────────
    data_10min = data_df[var_list].resample('10min').mean()

    # 현재 마지막 10분 타임스텝의 원래 스케일 값 저장 (펌프 라우팅용)
    current_raw = data_10min.iloc[-1].copy()

    # NaN을 열 평균으로 대체 (예측 입력이 NaN이면 XGBoost 오류 발생)
    data_10min = data_10min.fillna(data_10min.mean())

    if data_10min.shape[0] < 30:
        logger.warning(f"데이터 행 수 부족: {data_10min.shape[0]}행 (최소 30 필요)")

    # ── 5. XGBoost 피처 생성 (스케일링 없이 원시값 사용) ────────────────
    # horizon=0 을 사용하면 타겟이 현재값(NaN 없음) → 마지막 행이 유효한 피처로 포함됨
    X_all, _ = make_xgb_features(
        data_10min[var_list], target_cols=target_list, horizon=0
    )
    if X_all.empty:
        logger.error("피처 생성 실패 — 데이터 행 부족 (최대 lag 24 스텝 미충족)")
        return None, None, None, None

    x_latest = X_all.iloc[[-1]]   # shape: (1, n_features)
    dmatrix  = xgb.DMatrix(x_latest)

    # ── 6. horizon별 XGBoost 예측 ─────────────────────────────────────
    last_dt            = data_10min.index[-1]
    results_by_horizon = {}
    pred_records:  list = []   # tag_pred_l 업로드용
    var2tag  = dict(zip(df_meta['변수명'], df_meta['태그명']))

    for horizon_label, h_steps in HORIZONS.items():
        predict_dt       = last_dt + timedelta(minutes=h_steps * 10)
        predict_dt_round = pd.Timestamp(predict_dt).round('10min')  # 10분 반올림
        # crt_dttm = 예측시간(pred_dttm)에서 해당 예측구간만큼 뺀 기준시각
        # (10분 예측이면 -10분, 1시간 예측이면 -60분 → 결국 예측 기준시각)
        crt_dttm         = predict_dt_round - timedelta(minutes=h_steps * 10)
        models     = models_by_horizon[horizon_label]
        row        = {}
        for target in target_list:
            try:
                y_orig = float(models[target].predict(dmatrix)[0])
                row[f"{target}_Predict"] = max(0.0, y_orig)   # RELU (음수 방지)
            except Exception:
                logger.exception(f"예측 실패: {target} ({horizon_label})")
                row[f"{target}_Predict"] = np.nan

            # tag_pred_l 레코드 수집
            pred_records.append({
                'tag_no'     : var2tag.get(target, target),
                'pred_dttm'  : predict_dt_round,
                'crt_dttm'   : crt_dttm,
                'duration_cd': HORIZON_CD[horizon_label],
                'pred_value' : round(max(0.0, row.get(f"{target}_Predict", 0.0)), 4),
            })

        results_by_horizon[horizon_label] = pd.DataFrame(row, index=[predict_dt])
        pv = {k: f"{v:.2f}" for k, v in row.items()}
        print(f"    [{horizon_label}] → {predict_dt.strftime('%H:%M')}  {pv}")

    current_vals = {
        t: (float(current_raw[t]) if pd.notna(current_raw.get(t)) else np.nan)
        for t in target_list
    }

    logger.info(f"예측 완료 — 기준={pred_timestamp}, horizons={list(HORIZONS)}")
    return results_by_horizon, pd.Series(current_vals), pred_timestamp, pred_records


# =============================================================================
# 6. DB 저장 — tag_pred_l 예측 결과 업로드
# =============================================================================

def upload_tag_pred_l(pred_records: list) -> dict:
    """Insert prediction records into tag_pred_l with INSERT IGNORE."""
    if not pred_records:
        return {"requested": 0, "inserted": 0}

    prediction_table = get_prediction_table()
    sql = """
        INSERT IGNORE INTO {prediction_table}
            (tag_no, pred_dttm, crt_dttm, duration_cd, pred_value)
        VALUES
            (%(tag_no)s, %(pred_dttm)s, %(crt_dttm)s, %(duration_cd)s, %(pred_value)s)
    """.format(prediction_table=prediction_table)
    total = len(pred_records)
    uploaded = 0
    inserted = 0
    conn = open_db()
    if conn is None:
        logger.error("tag_pred_l upload failed: DB connection unavailable")
        return {"requested": total, "inserted": 0}

    try:
        cursor = conn.cursor()
        for start in range(0, total, UPLOAD_BATCH_SIZE):
            batch = pred_records[start: start + UPLOAD_BATCH_SIZE]
            cursor.executemany(sql, batch)
            inserted += cursor.rowcount
            conn.commit()
            uploaded += len(batch)
        logger.info(f"{prediction_table} INSERT done: requested={uploaded}, inserted={inserted}")
        print(f"    [{prediction_table}] requested={uploaded}, inserted={inserted}")
    except Exception:
        conn.rollback()
        logger.exception(f"{prediction_table} INSERT failed; rollback")
        return {"requested": total, "inserted": inserted}
    finally:
        conn.close()

    return {"requested": total, "inserted": inserted}


def create_prediction_history(pred_dttm=None):
    """예측 실행 이력을 RUNNING 상태로 생성한다."""
    history_table = get_prediction_history_table()
    conn = open_db()
    if conn is None:
        logger.error("prediction history insert failed: DB connection unavailable")
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO {history_table}
                    (start_dttm, pred_dttm, status_cd, err_msg)
                VALUES
                    (%s, %s, %s, %s)
                """.format(history_table=history_table),
                (datetime.now(), pred_dttm, "RUNNING", None),
            )
            conn.commit()
            return cursor.lastrowid
    except Exception:
        conn.rollback()
        logger.exception(f"{history_table} INSERT failed")
        return None
    finally:
        conn.close()


def finish_prediction_history(hist_id, status_cd: str, pred_dttm=None, err_msg=None):
    """예측 실행 이력을 DONE 또는 ERROR 상태로 마감한다."""
    if not hist_id:
        return

    history_table = get_prediction_history_table()
    conn = open_db()
    if conn is None:
        logger.error("prediction history update failed: DB connection unavailable")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE {history_table}
                SET end_dttm = %s,
                    pred_dttm = COALESCE(%s, pred_dttm),
                    status_cd = %s,
                    err_msg = %s
                WHERE hist_id = %s
                """.format(history_table=history_table),
                (datetime.now(), pred_dttm, status_cd, err_msg, hist_id),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(f"{history_table} UPDATE failed: hist_id={hist_id}")
    finally:
        conn.close()


# =============================================================================
# 7. 펌프 운전 추천 라우팅 (10분 예측 기준)
# =============================================================================

def _pump_yn_old(Q: float, P: float) -> list:
    """구정수장(PUMP_GRP=1) 펌프 ON/OFF 추천 — 기존 운전 곡선 기반."""
    upper1  =  58.6613373258886  - 0.00527586346649821  * Q + 1.2957874682855E-07  * Q**2
    lower2  =  -3.43193582761012 + 0.00120472303735243  * Q - 4.08245928068585E-08 * Q**2
    lower3  =   2.95             + 0.000497             * Q - 0.0000000229         * Q**2
    lower4  =   0.120821964429389 + 0.000853219487279097 * Q - 3.52433865423429E-08 * Q**2
    lower5  =   0.46770987097162  + 0.000872862970476709 * Q - 3.89262100721736E-08 * Q**2
    lower6  =  -0.759451815235986 + 0.0010218039074961  * Q - 4.43777727901476E-08 * Q**2

    if   P >= upper1: return [0, 0, 0, 1, 1, 1, 1]
    elif P >= lower2: return [0, 1, 0, 1, 0, 1, 1]
    elif P >= lower3: return [0, 1, 0, 1, 1, 0, 1]
    elif P >= lower4: return [0, 0, 0, 1, 1, 1, 0]
    elif P >= lower5: return [0, 0, 0, 1, 1, 0, 1]
    elif P >= lower6: return [0, 1, 0, 1, 0, 1, 0]
    else:             return [0, 1, 0, 0, 1, 0, 1]


def _create_pump_df(timestamp: str, Q: float, P: float,
                    pump_idxs, pump_yn: list, freqs: list, pump_grp: int):
    """펌프 운전 추천 DataFrame 생성."""
    ts = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    df = pd.DataFrame({
        'RGSTR_TIME'     : [timestamp] * len(pump_idxs),
        'pump_idx'       : list(pump_idxs),
        'pump_yn'        : pump_yn,
        'FREQ'           : freqs,
        'PUMP_GRP'       : pump_grp,
        'TUBE_PRSR_PRDCT': Q,
        'PRDCT_MEAN'     : P,
        'PRDCT_TIME_DIFF': 10,   # XGBoost 최소 예측 단위 = 10분
    })
    df['OPT_IDX'] = (
        f'701-367-FRI-{pump_grp}:{ts.strftime("%Y%m%d%H-")}-'
        f'{datetime.now().strftime("%H%M")}'
    )
    return df


def process_pump_routing(results_by_horizon: dict, engine):
    """
    10분 예측 결과를 사용하여 펌프 운전 추천을 계산하고 TB_PUMP_RST 에 저장.
    사용 타겟: Q_GS_NEW_Predict, Q_GS_OLD_Predict, P_GS_NEW_Predict, P_GS_OLD_Predict
    """
    df_10 = results_by_horizon.get('10min')
    if df_10 is None or df_10.empty:
        return

    pump_dfs = []
    for pred_dt, row in df_10.iterrows():
        ts_str = pred_dt.strftime('%Y-%m-%d %H:%M:%S')

        # 신정수장 (PUMP_GRP=2, 펌프 4대)
        q_new = row.get('Q_GS_NEW_Predict', np.nan)
        p_new = row.get('P_GS_NEW_Predict', np.nan)
        if pd.notna(q_new) and pd.notna(p_new):
            pump_dfs.append(
                _create_pump_df(ts_str, q_new, p_new,
                                range(1, 5), [0, 0, 1, 0], [None]*4, 2)
            )
            if p_new < 0:
                logger.warning(f"[신] 압력 음수 예측: P={p_new:.4f}")

        # 구정수장 (PUMP_GRP=1, 펌프 7대)
        q_old = row.get('Q_GS_OLD_Predict', np.nan)
        p_old = row.get('P_GS_OLD_Predict', np.nan)
        if pd.notna(q_old) and pd.notna(p_old):
            pump_yn = _pump_yn_old(q_old, p_old)
            pump_dfs.append(
                _create_pump_df(ts_str, q_old, p_old,
                                range(1, 8), pump_yn, [None]*7, 1)
            )
            if p_old < 0:
                logger.warning(f"[구] 압력 음수 예측: P={p_old:.4f}")

    if not pump_dfs:
        return

    try:
        pd.concat(pump_dfs, ignore_index=True).to_sql(
            get_pump_result_table(), engine, if_exists='append', index=False
        )
        logger.info("펌프 추천 DB 저장 완료")
    except Exception:
        logger.exception("TB_PUMP_RST 저장 실패")


# =============================================================================
# 8. 단일 예측 실행 (스케줄러 콜백)
# =============================================================================

def initialize_runtime():
    """Load models and DB engine once for scheduler/API execution."""
    global _df_meta, _models_by_horizon, _var_list, _target_list, _db_cfg, _engine
    required = ("_df_meta", "_models_by_horizon", "_var_list", "_target_list", "_engine")
    if all(name in globals() for name in required):
        return

    print("\n[init] Loading XGBoost models...")
    (
        _df_meta,
        _models_by_horizon,
        _var_list,
        _target_list,
    ) = initialization_xgb()
    print("[init] Done\n")

    _db_cfg = get_db_config()
    _engine = create_engine(
        f"mysql+pymysql://{_db_cfg['user']}:{_db_cfg['password']}"
        f"@{_db_cfg['host']}:{_db_cfg['port']}/{_db_cfg['db']}"
    )


def run_prediction(target_ts=None, enable_pump_routing=None):
    """Run one prediction cycle. target_ts enables historical rebuild calls."""
    KST = timezone('Asia/Seoul')
    start = time.time()
    hist_id = None
    pred_ts = None
    print(f"\n{'='*60}")
    print(f"[prediction start] {datetime.now().astimezone(KST).strftime('%Y-%m-%d %H:%M:%S')} (KST), target={target_ts or 'latest'}")

    try:
        if enable_pump_routing is None:
            enable_pump_routing = is_pump_routing_enabled()
        hist_id = create_prediction_history()
        initialize_runtime()
        results_by_horizon, current_vals, pred_ts, pred_records = predict_xgb(
            _df_meta, _models_by_horizon, _var_list, _target_list, ref_time=target_ts
        )

        if results_by_horizon is None:
            logger.error("No prediction result; skip DB upload")
            finish_prediction_history(hist_id, "ERROR", pred_ts, "no prediction result")
            return {
                "success": False,
                "histId": hist_id,
                "targetTs": str(target_ts) if target_ts is not None else pred_ts,
                "message": "no prediction result",
            }

        upload_result = upload_tag_pred_l(pred_records)

        if enable_pump_routing:
            process_pump_routing(results_by_horizon, _engine)

        finish_prediction_history(hist_id, "DONE", pred_ts)
        elapsed = time.time() - start
        print(f"[prediction done] elapsed={elapsed:.2f}s")
        return {
            "success": True,
            "histId": hist_id,
            "targetTs": pred_ts,
            "upload": upload_result,
            "pumpRouting": bool(enable_pump_routing),
            "elapsedSec": elapsed,
        }

    except Exception as exc:
        logger.exception("run_prediction failed")
        finish_prediction_history(hist_id, "ERROR", pred_ts, str(exc))
        return {
            "success": False,
            "histId": hist_id,
            "targetTs": str(target_ts) if target_ts is not None else pred_ts,
            "message": str(exc),
        }



# =============================================================================
# 9. 엔트리포인트 — 초기화 후 스케줄 루프 시작
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  MAIN_2026.py  XGBoost 고산정수장 실시간 예측")
    print("=" * 60)

    # ── 전역 초기화 (1회) ──────────────────────────────────────────────
    print("\n[초기화] XGBoost 모델 로드 중...")
    (
        _df_meta,
        _models_by_horizon,
        _var_list,
        _target_list,
    ) = initialization_xgb()
    print("[초기화] 완료\n")

    # ── DB engine 생성 (펌프 추천용 SQLAlchemy) ────────────────────────
    _db_cfg = get_db_config()
    _engine = create_engine(
        f"mysql+pymysql://{_db_cfg['user']}:{_db_cfg['password']}"
        f"@{_db_cfg['host']}:{_db_cfg['port']}/{_db_cfg['db']}"
    )

    # ── 스케줄 등록: 매 정각·10분·20분·30분·40분·50분에 실행 ────────────
    for _min in ('00', '10', '20', '30', '40', '50'):
        schedule.every().hour.at(f':{_min}').do(run_prediction)
    print("스케줄러 시작 — 매 10분 정각마다 예측 실행 (Ctrl+C 로 종료)")
    print(f"다음 예정 시각: {schedule.next_run()}\n")

    # 시작 즉시 1회 실행
    run_prediction()

    while True:
        try:
            schedule.run_pending()
        except Exception:
            logger.exception("스케줄러 루프 예외 발생")
        time.sleep(1)
