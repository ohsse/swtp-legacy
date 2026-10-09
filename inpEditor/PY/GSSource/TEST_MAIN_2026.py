#!/usr/bin/env python
# coding: utf-8
"""
TEST_MAIN_2026_DB.py  —  MAIN_2026.py 오프라인 정확도 테스트 (개발 DB 버전)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEST_MAIN_2026.py 와 동일한 로직이지만, 로컬 pickle 대신
개발 DB(maria-ems-db-dev)의 TB_RAWDATA 테이블에서 원시데이터를 조회한다.

테스트 기간:
  SIM_START : 2025-06-01 00:10:00
  SIM_END   : 2026-06-29 23:00:00

DB 조회 방식:
  - 테스트 기간 전체 데이터를 1회 일괄 조회 (태그별 pivot)
  - 이후는 pickle 버전과 동일하게 슬라이딩 윈도우 시뮬레이션 수행
"""

# =============================================================================
# 설정
# =============================================================================
import os, sys, warnings, time, json
import numpy as np
import pandas as pd
import pymysql
import xgboost as xgb
from pymysql.cursors import DictCursor
from datetime import datetime, timedelta
from tqdm import tqdm
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

warnings.filterwarnings('ignore')

# ── 경로 ─────────────────────────────────────────────────────────────────────
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))

TAGLIST_PATH = os.path.join(_THIS_DIR, 'GS_taglist_250904.xlsx')
CONN_PATH    = os.path.join(_THIS_DIR, 'libs', 'connections.json')

# 저장된 XGBoost 모델 경로
MODEL_DIR  = os.path.join(_THIS_DIR, 'saved_model', 'xgb')

SHEETNAME = 'Gosan'

# ── 테스트 기간 ───────────────────────────────────────────────────────────────
SIM_START = '2025-11-01 00:10:00'   # 조회 시작 (WINDOW_MIN 워밍업 포함)
SIM_END   = '2026-06-29 23:00:00'   # 조회 종료

# ── 시뮬레이션 파라미터 ───────────────────────────────────────────────────────
WINDOW_MIN   = 2160      # DB FETCH 창 크기 (분): 36시간 (MAIN_2026과 동일)
STEP_EVERY   = 1         # 몇 10분 스텝마다 예측할지 (6 = 60분 간격, 1 = 10분마다)
MAX_STEPS    = None      # None = 전체 시뮬레이션 (정수 지정 시 해당 횟수만)
SAVE_RESULTS = False     # True: Excel + 그래프 저장
CHUNK_DAYS   = 21        # 기간이 길 때 분할 단위 (일), 0 또는 None = 분할 없음

# ── Horizon 정의 (saved_model/xgb 내 폴더 기준) ─────────────────────────────
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

# 그래프 한글 폰트
mpl.rcParams['font.family']        = 'Malgun Gothic'
mpl.rcParams['axes.unicode_minus'] = False


# ============================================================
# XGBoost용 lag 기반 피처 생성
# ============================================================

# 저장된 모델과 동일한 피처 구성 (lag 6개 + rmean12)
_DEFAULT_LAGS    = [1, 2, 3, 6, 12, 24]
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
# 0. DB 연결 헬퍼
# =============================================================================

def _open_db() -> pymysql.connections.Connection:
    """libs/connections.json 의 maria-ems-db-gs 설정으로 운영 DB 연결 반환."""
    with open(CONN_PATH, encoding='utf-8') as f:
        cfg = json.load(f)['maria-ems-db-gs']
    return pymysql.connect(**cfg)


# =============================================================================
# 1. 초기화 — 모델 / 스케일러 로드
# =============================================================================

def initialization_xgb():
    """
    saved_model/xgb/Gosan_{horizon}/ 디렉토리 기반으로
    horizon별 XGBoost Booster 모델을 로드.

    - var_list, target_list 는 저장된 .json 모델 파일에서 동적으로 추출
    - 스케일러 없음 (XGBoost 모델은 원시값 기준 학습)
    - GS_taglist_250904.xlsx 는 DB 태그명 매핑용으로만 사용
    """
    # ── 태그리스트: DB 태그명 ↔ 변수명 매핑용 ────────────────────────
    worksheet = pd.read_excel(TAGLIST_PATH, sheet_name=SHEETNAME, header=0)
    worksheet = worksheet.dropna(axis=1).reset_index(drop=True)
    df_meta   = worksheet.loc[
        (worksheet['비고'] != 'NU') & (worksheet['사용'] == 'Y')
    ].reset_index(drop=True)

    # ── 10min 모델의 feature_names에서 입력 변수목록 동적 추출 ────────
    sample_dir = os.path.join(MODEL_DIR, f'{SHEETNAME}_10min')
    sample_files = [f for f in os.listdir(sample_dir) if f.endswith('.json')]
    if not sample_files:
        raise FileNotFoundError(f"XGBoost 모델 파일 없음: {sample_dir}")

    # target_list: 모델 파일명에서 추출
    target_list = sorted([os.path.splitext(f)[0] for f in sample_files])

    # var_list: 샘플 모델 feature_names에서 접미어(_lag*, _rmean*) 제거하여 추출
    import re
    sample_model = xgb.Booster()
    sample_model.load_model(os.path.join(sample_dir, sample_files[0]))
    var_set: list = []
    for fn in sample_model.feature_names:
        m = re.match(r'^(.+?)_(lag|rmean)\d+$', fn)
        if m:
            v = m.group(1)
            if v not in var_set:
                var_set.append(v)
    var_list = var_set
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
        print(f"  모델 로드: {model_name} ({len(models)}개 타겟)")

    return df_meta, models_by_horizon, var_list, target_list


# =============================================================================
# 2. 개발 DB → 테스트 기간 원시데이터 일괄 조회
# =============================================================================

def load_rawdata_from_db(df_meta) -> pd.DataFrame:
    """
    개발 DB TB_RAWDATA 에서 SIM_START ~ SIM_END 구간을 일괄 조회하여
    변수명 컬럼 / 1분 DatetimeIndex DataFrame 으로 반환.

    - WINDOW_MIN 워밍업을 위해 SIM_START 이전 WINDOW_MIN 분도 함께 조회
    - 태그별 조회 후 pivot → 1분 freq reindex
    """
    # 워밍업 포함 실제 조회 시작 시각
    fetch_start = (pd.Timestamp(SIM_START) - timedelta(minutes=WINDOW_MIN)).strftime('%Y-%m-%d %H:%M:%S')
    fetch_end   = SIM_END

    tag_list = df_meta['태그명'].tolist()
    tag2var  = dict(zip(df_meta['태그명'], df_meta['변수명']))

    print(f"\n[개발 DB 조회]")
    print(f"  DB     : maria-ems-db-gs  /  테이블: TB_RAWDATA")
    print(f"  기간   : {fetch_start}  ~  {fetch_end}")
    print(f"  태그 수: {len(tag_list)}개")

    conn = _open_db()
    try:
        cursor = conn.cursor(DictCursor)

        # 태그 목록을 IN 절로 한 번에 조회 (태그 수가 적어 안전)
        placeholders = ', '.join(['%s'] * len(tag_list))
        sql = f"""
            SELECT TS, TAGNAME, VALUE
            FROM TB_RAWDATA
            WHERE TAGNAME IN ({placeholders})
              AND TS >= %s
              AND TS <= %s
            ORDER BY TS ASC
        """
        params = tag_list + [fetch_start, fetch_end]
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        raise RuntimeError(f"TB_RAWDATA 조회 결과 없음 ({fetch_start} ~ {fetch_end})")

    print(f"  조회 완료: {len(rows):,} 행")

    # DataFrame 변환 및 pivot
    raw = pd.DataFrame(rows)
    raw['TS']    = pd.to_datetime(raw['TS'])
    raw['VALUE'] = pd.to_numeric(raw['VALUE'], errors='coerce')

    # 태그명 → 변수명 치환 후 pivot (중복 TSxTAGNAME은 mean 처리)
    raw['var'] = raw['TAGNAME'].map(tag2var)
    pivot = raw.pivot_table(index='TS', columns='var', values='VALUE', aggfunc='mean')
    pivot.index.name = None

    # 1분 freq 완전 인덱스로 reindex (결측 구간 NaN 보장)
    full_idx = pd.date_range(start=pivot.index.min(), end=pivot.index.max(), freq='1min')
    pivot    = pivot.reindex(full_idx)

    # H 접두사 변수 합산 (태그리스트와 동일하게)
    var_list_height = [s for s in pivot.columns if str(s).startswith('H')]
    var_first_two   = [s.split('_')[0] for s in var_list_height]
    var_height_uniq = list(set(var_first_two))
    if len(var_height_uniq) != len(var_list_height):
        for prefix in var_height_uniq:
            height_cols = [s for s in var_list_height if s.startswith(prefix)]
            if len(height_cols) > 1:
                pivot[prefix] = pivot[height_cols].sum(axis=1)
                pivot.drop(columns=height_cols, inplace=True)

    # 태그리스트에 없는 컬럼 제거 후 누락 태그 경고
    expected_vars = df_meta['변수명'].tolist()
    missing_vars  = [v for v in expected_vars if v not in pivot.columns]
    if missing_vars:
        print(f"  [경고] DB에 없는 변수(태그): {missing_vars}")

    print(f"  최종 shape: {pivot.shape}  범위: {pivot.index[0]} ~ {pivot.index[-1]}")
    return pivot


# =============================================================================
# 3. 단일 스텝 예측
# =============================================================================

def predict_one_step(window_1min: pd.DataFrame, var_list: list,
                     target_list: list, models_by_horizon: dict):
    """
    window_1min : WINDOW_MIN 분 슬라이스 (DB FETCH 모사)
    Returns: {horizon_label: {target: float}}  예측값 (원시 스케일)
    None 이면 피처 생성 실패 (데이터 부족 등)
    """
    # 유량 이상값 제거 (Q < 10 → NaN)
    w = window_1min[var_list].copy()
    flux_cols = [c for c in w.columns if c.startswith('Q')]
    for c in flux_cols:
        w[c] = w[c].where(w[c] >= 10, other=np.nan)

    # 10분 리샘플링
    data_10min = w.resample('10min').mean()
    data_10min = data_10min.fillna(data_10min.mean())

    if data_10min.shape[0] < 150:
        return None   # 데이터 부족

    # XGBoost 피처 생성 (스케일링 없이 원시값 사용, horizon=0 → 마지막 행이 유효)
    X_all, _ = make_xgb_features(data_10min[var_list], target_cols=target_list, horizon=0)
    if X_all.empty:
        return None

    x_latest  = X_all.iloc[[-1]]
    dmatrix   = xgb.DMatrix(x_latest)

    # horizon별 XGBoost 예측
    results: dict = {}
    for horizon_label, models in models_by_horizon.items():
        row = {}
        for target in target_list:
            y = float(models[target].predict(dmatrix)[0])
            row[target] = max(0.0, y)   # RELU
        results[horizon_label] = row

    return results


# =============================================================================
# 4. 정확도 지표 계산
# =============================================================================

def smape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-8) -> float:
    return float(
        np.mean(2 * np.abs(y_true - y_pred) /
                (np.abs(y_true) + np.abs(y_pred) + eps)) * 100
    )


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    from sklearn.metrics import mean_squared_error, r2_score
    mae  = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    sm   = smape(y_true, y_pred)
    r2   = float(r2_score(y_true, y_pred))
    return {'MAE': mae, 'RMSE': rmse, 'sMAPE(%)': sm, 'R2': r2, 'N': len(y_true)}


# =============================================================================
# 5. 시뮬레이션 메인 루프
# =============================================================================

def run_simulation(df_meta, raw_1min: pd.DataFrame, models_by_horizon: dict,
                   var_list: list, target_list: list):
    """
    raw_1min 전체를 슬라이딩 윈도우로 순회하며 예측 → 정확도 누적.

    Returns
    -------
    records              : list of dict  스텝별 전체 예측 기록
    summary_df           : pd.DataFrame  horizon x target 정확도 요약
    store                : dict          시각화용 누적 데이터
    pred_records_upload  : list of dict  tag_pred_l 업로드용 레코드
    """
    all_ts  = raw_1min.index   # 1분 단위 DatetimeIndex
    n_total = len(all_ts)

    # SIM_START 부터 시뮬레이션 시작 (WINDOW_MIN 워밍업 건너뜀)
    sim_start_ts = pd.Timestamp(SIM_START)
    # SIM_START 에 해당하는 인덱스 위치
    warmup_idx = all_ts.searchsorted(sim_start_ts)
    # 안전 마진: 최소 WINDOW_MIN 확보
    warmup_idx = max(warmup_idx, WINDOW_MIN)

    # STEP_EVERY x 10분 간격으로 스텝 인덱스 생성
    step_indices = list(range(warmup_idx,
                              n_total - max(HORIZONS.values()) * 10,
                              STEP_EVERY * 10))
    if MAX_STEPS is not None:
        step_indices = step_indices[:MAX_STEPS]

    print(f"\n[시뮬레이션 시작]")
    print(f"  데이터 범위 : {all_ts[0]} ~ {all_ts[-1]}")
    print(f"  시뮬레이션  : {all_ts[warmup_idx]} ~ {SIM_END}")
    print(f"  예측 스텝 수: {len(step_indices):,}  "
          f"(STEP_EVERY={STEP_EVERY} x 10분 = {STEP_EVERY * 10}분 간격)")
    print(f"  Horizons   : {list(HORIZONS.keys())}")
    print()

    # 누적 컨테이너: {horizon_label: {target: {'pred': [], 'true': [], 'ts': []}}}
    store: dict = {
        hl: {t: {'pred': [], 'true': [], 'ts': []} for t in target_list}
        for hl in HORIZONS
    }
    records: list = []

    # tag_pred_l 업로드용 (변수명 → 태그명 역매핑)
    var2tag = dict(zip(df_meta['변수명'], df_meta['태그명']))
    pred_records_upload: list = []
    pred_id_counter = 1

    t0 = time.time()
    for i_raw in tqdm(step_indices, desc='예측 진행'):
        cur_ts = all_ts[i_raw]

        # 직전 WINDOW_MIN 분 슬라이스 (DB FETCH 모사)
        window = raw_1min.iloc[max(0, i_raw - WINDOW_MIN): i_raw]

        results = predict_one_step(window, var_list, target_list,
                                   models_by_horizon)
        if results is None:
            continue

        for horizon_label, h_steps in HORIZONS.items():
            pred_dt       = cur_ts + timedelta(minutes=h_steps * 10)
            pred_dt_floor = pred_dt.floor('10min')

            # 실제값 조회
            if pred_dt_floor not in raw_1min.index:
                nearby = raw_1min.loc[
                    (raw_1min.index >= pred_dt_floor - timedelta(minutes=5)) &
                    (raw_1min.index <= pred_dt_floor + timedelta(minutes=5))
                ]
                if nearby.empty:
                    continue
                actual_row = nearby[var_list].mean()
            else:
                actual_row = raw_1min.loc[pred_dt_floor, var_list]

            row_pred = {'기준시각': cur_ts, '예측시각': pred_dt, 'horizon': horizon_label}
            crt_dttm = datetime.now()
            for target in target_list:
                pred_val = results[horizon_label][target]
                true_val = float(actual_row[target]) if pd.notna(actual_row.get(target)) else np.nan

                if pd.notna(true_val) and true_val >= 0:
                    store[horizon_label][target]['pred'].append(pred_val)
                    store[horizon_label][target]['true'].append(true_val)
                    store[horizon_label][target]['ts'].append(pred_dt)

                row_pred[f"{target}_pred"] = round(pred_val, 4)
                row_pred[f"{target}_true"] = round(true_val, 4) if pd.notna(true_val) else np.nan

                # tag_pred_l 업로드용 레코드 (pred_dttm 10분 단위 반올림)
                pred_dt_round = pd.Timestamp(pred_dt).round('10min')
                pred_records_upload.append({
                    'pred_id'    : pred_id_counter,
                    'tag_no'     : var2tag.get(target, target),
                    'pred_dttm'  : pred_dt_round,
                    'crt_dttm'   : crt_dttm,
                    'duration_cd': HORIZON_CD[horizon_label],
                    'pred_value' : round(pred_val, 4),
                })
                pred_id_counter += 1

            records.append(row_pred)

    elapsed = time.time() - t0
    print(f"\n시뮬레이션 완료  (소요: {elapsed:.1f}초, {len(records):,}건 기록)")

    # ── 정확도 요약 ─────────────────────────────────────────────────────
    summary_rows = []
    print(f"\n{'=' * 70}")
    print(f"  정확도 요약")
    print(f"{'=' * 70}")
    for horizon_label in HORIZONS:
        for target in target_list:
            yp = np.array(store[horizon_label][target]['pred'])
            yt = np.array(store[horizon_label][target]['true'])
            if len(yt) < 2:
                continue
            m = compute_metrics(yt, yp)
            summary_rows.append({
                'Horizon'  : horizon_label,
                '변수명'   : target,
                'N'        : m['N'],
                'MAE'      : round(m['MAE'],      4),
                'RMSE'     : round(m['RMSE'],     4),
                'sMAPE(%)' : round(m['sMAPE(%)'], 2),
                'R2'       : round(m['R2'],       4),
            })
            print(f"  [{horizon_label:6s}] {target:<15s}  "
                  f"MAE={m['MAE']:8.2f}  RMSE={m['RMSE']:8.2f}  "
                  f"sMAPE={m['sMAPE(%)']:5.2f}%  R²={m['R2']:.4f}  N={m['N']:,}")
    print(f"{'=' * 70}")

    summary_df = pd.DataFrame(summary_rows)
    return records, summary_df, store, pred_records_upload


# =============================================================================
# 6. 결과 저장 및 시각화
# =============================================================================

def save_and_plot(records, summary_df, store, target_list,
                  pred_records_upload=None, out_dir=None):
    """Excel 저장 + horizon x target 시계열 / 산점도 그래프 저장."""
    if out_dir is None:
        out_dir = os.path.join(_THIS_DIR, 'test_results_2026')
    os.makedirs(out_dir, exist_ok=True)

    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # ── 1. 전체 예측 기록 Excel ───────────────────────────────────────
    if records:
        records_df = pd.DataFrame(records)
        excel_path = os.path.join(out_dir, f'db_test_predictions_{now_str}.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='정확도_요약', index=False)
            records_df.to_excel(writer, sheet_name='전체_예측기록', index=False)
            for hl in HORIZONS:
                sub = records_df[records_df['horizon'] == hl].copy()
                sub.to_excel(writer, sheet_name=f'예측_{hl}', index=False)
        print(f"\nExcel 저장: {excel_path}")

    # ── 2. tag_pred_l.xlsx 저장 (DB 업로드 테스트용) ──────────────────
    if pred_records_upload:
        upload_df   = pd.DataFrame(pred_records_upload)
        upload_path = os.path.join(out_dir, f'tag_pred_l_{now_str}.xlsx')
        upload_df.to_excel(upload_path, index=False)
        print(f"tag_pred_l 저장: {upload_path}  ({len(upload_df):,}건)")

    # ── 3. 시계열 비교 그래프 ─────────────────────────────────────────
    for target in target_list:
        n_h = len(HORIZONS)
        fig, axes = plt.subplots(n_h, 1, figsize=(18, n_h * 3.5), sharex=False)
        if n_h == 1:
            axes = [axes]
        fig.suptitle(f"[{target}] 예측 vs 실측 — 개발 DB 테스트", fontsize=13)

        for ax, (horizon_label, _) in zip(axes, HORIZONS.items()):
            yp = np.array(store[horizon_label][target]['pred'])
            yt = np.array(store[horizon_label][target]['true'])
            ts = store[horizon_label][target]['ts']
            if len(yt) < 2:
                ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                        transform=ax.transAxes)
                continue
            m = compute_metrics(yt, yp)
            ax.plot(ts, yt, color='steelblue', linewidth=0.6, alpha=0.9, label='실측값')
            ax.plot(ts, yp, color='tomato',    linewidth=0.6, alpha=0.8, label='예측값')
            ax.set_title(
                f"{horizon_label}  MAE={m['MAE']:.2f}  RMSE={m['RMSE']:.2f}  "
                f"sMAPE={m['sMAPE(%)']:.2f}%  R²={m['R2']:.4f}  N={m['N']:,}",
                fontsize=9
            )
            ax.legend(loc='upper right', fontsize=7)
            ax.grid(True, linewidth=0.3, alpha=0.4)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right', fontsize=7)

        plt.tight_layout()
        fig_path = os.path.join(out_dir, f'{target}_timeseries_{now_str}.png')
        plt.savefig(fig_path, dpi=130)
        plt.close()
        print(f"그래프 저장: {fig_path}")

    # ── 4. 산점도 그래프 ─────────────────────────────────────────────
    for target in target_list:
        n_h = len(HORIZONS)
        fig, axes = plt.subplots(1, n_h, figsize=(n_h * 4, 4))
        if n_h == 1:
            axes = [axes]
        fig.suptitle(f"[{target}] 산점도 — 예측 vs 실측", fontsize=12)

        for ax, (horizon_label, _) in zip(axes, HORIZONS.items()):
            yp = np.array(store[horizon_label][target]['pred'])
            yt = np.array(store[horizon_label][target]['true'])
            if len(yt) < 2:
                continue
            m = compute_metrics(yt, yp)
            ax.scatter(yt, yp, s=1.5, alpha=0.3, color='steelblue')
            lim = [min(yt.min(), yp.min()), max(yt.max(), yp.max())]
            ax.plot(lim, lim, 'r--', linewidth=0.8, label='y=x')
            ax.set_xlabel('실측값')
            ax.set_ylabel('예측값')
            ax.set_title(
                f"{horizon_label}  R²={m['R2']:.4f}\n"
                f"sMAPE={m['sMAPE(%)']:.2f}%",
                fontsize=8
            )
            ax.legend(fontsize=7)

        plt.tight_layout()
        fig_path = os.path.join(out_dir, f'{target}_scatter_{now_str}.png')
        plt.savefig(fig_path, dpi=130)
        plt.close()
        print(f"그래프 저장: {fig_path}")


# =============================================================================
# 7. tag_pred_l DB 업로드
# =============================================================================

UPLOAD_BATCH_SIZE = 1000   # INSERT 한 번에 처리할 행 수

def upload_tag_pred_l(pred_records_upload: list) -> None:
    """
    pred_records_upload 리스트를 개발 DB의 tag_pred_l 테이블에 INSERT.

    - pred_id 는 auto-increment 이므로 INSERT 시 제외
    - UPLOAD_BATCH_SIZE 단위로 executemany 배치 처리
    - 실패 시 롤백 후 예외 메시지 출력
    """
    if not pred_records_upload:
        print("[업로드] 업로드할 레코드 없음")
        return

    sql = """
        INSERT IGNORE INTO tag_pred_l
            (tag_no, pred_dttm, crt_dttm, duration_cd, pred_value)
        VALUES
            (%(tag_no)s, %(pred_dttm)s, %(crt_dttm)s, %(duration_cd)s, %(pred_value)s)
    """

    total    = len(pred_records_upload)
    uploaded = 0

    conn = _open_db()
    try:
        cursor = conn.cursor()
        for start in range(0, total, UPLOAD_BATCH_SIZE):
            batch = pred_records_upload[start: start + UPLOAD_BATCH_SIZE]
            cursor.executemany(sql, batch)
            conn.commit()
            uploaded += len(batch)
            print(f"  업로드 진행: {uploaded:,} / {total:,}건", end='\r')
        print(f"\n[업로드 완료] tag_pred_l  {uploaded:,}건 INSERT")
    except Exception as e:
        conn.rollback()
        print(f"\n[업로드 실패] 롤백 처리 — {e}")
        raise
    finally:
        conn.close()


# =============================================================================
# 8. 엔트리포인트
# =============================================================================

def _fetch_data_range(tag_list: list) -> tuple:
    """
    개발 DB TB_RAWDATA 에서 테스트 태그 전체의
    실제 연내 시작·종료 시각을 조회.
    Returns: (min_ts_str, max_ts_str)
    """
    placeholders = ', '.join(['%s'] * len(tag_list))
    sql = f"""
        SELECT MIN(TS) AS min_ts, MAX(TS) AS max_ts
        FROM TB_RAWDATA
        WHERE TAGNAME IN ({placeholders})
    """
    conn = _open_db()
    try:
        cursor = conn.cursor(DictCursor)
        cursor.execute(sql, tag_list)
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row or row['min_ts'] is None:
        raise RuntimeError("DB에서 데이터 범위를 조회할 수 없음")

    return (
        pd.Timestamp(row['min_ts']).strftime('%Y-%m-%d %H:%M:%S'),
        pd.Timestamp(row['max_ts']).strftime('%Y-%m-%d %H:%M:%S'),
    )


def _build_chunks(start_str: str, end_str: str, chunk_days: int) -> list:
    """
    SIM_START ~ SIM_END 구간을 chunk_days 일 단위로 분할.
    각 청크는 (chunk_start, chunk_end) 문자열 튜플.
    chunk_days 가 0/None 이거나 전체 기간이 chunk_days 이하면 1개 반환.
    """
    start = pd.Timestamp(start_str)
    end   = pd.Timestamp(end_str)
    if not chunk_days or (end - start).days <= chunk_days:
        return [(start_str, end_str)]

    chunks = []
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=chunk_days), end)
        chunks.append((
            cur.strftime('%Y-%m-%d %H:%M:%S'),
            nxt.strftime('%Y-%m-%d %H:%M:%S'),
        ))
        cur = nxt
    return chunks


if __name__ == '__main__':
    print("=" * 70)
    print("  TEST_MAIN_2026_DB.py  —  XGBoost 고산정수장 오프라인 정확도 테스트")
    print("  데이터 소스: 운영 DB (maria-ems-db-gs) / TB_RAWDATA")
    print("=" * 70)
    print(f"  테스트 기간  : {SIM_START}  ~  {SIM_END}")
    print(f"  CHUNK_DAYS  : {CHUNK_DAYS if CHUNK_DAYS else '분할 없음 (전체 1회)'}")
    print(f"  STEP_EVERY  : {STEP_EVERY} x 10분 = {STEP_EVERY * 10}분 간격 예측")
    print(f"  MAX_STEPS   : {MAX_STEPS if MAX_STEPS else '전체'}")
    print(f"  WINDOW_MIN  : {WINDOW_MIN}분 (= {WINDOW_MIN // 60}시간) 슬라이딩 창")

    # ── 초기화 (모델·스케일러는 1회만 로드) ────────────────────────────
    print("\n[초기화] XGBoost 모델 로드...")
    df_meta, models_by_horizon, var_list, target_list = initialization_xgb()

    # ── DB 실제 데이터 범위 조회 후 SIM_START / SIM_END 조정 ───────
    print("\n[DB 범위 확인] 실제 데이터 간격 조회...")
    db_min, db_max = _fetch_data_range(df_meta['태그명'].tolist())
    print(f"  DB 데이터 범위: {db_min}  ~  {db_max}")

    # SIM_START: DB 시작보다 이없으면 DB 시작으로 클립
    # SIM_END  : DB 종료보다 늦으면 DB 종료로 클립
    adj_start = max(pd.Timestamp(SIM_START), pd.Timestamp(db_min))
    adj_end   = min(pd.Timestamp(SIM_END),   pd.Timestamp(db_max))

    if adj_start >= adj_end:
        raise RuntimeError(
            f"SIM_START({SIM_START}) ≥ SIM_END({SIM_END}) — 유효한 테스트 기간 없음"
        )

    sim_start_adj = adj_start.strftime('%Y-%m-%d %H:%M:%S')
    sim_end_adj   = adj_end.strftime('%Y-%m-%d %H:%M:%S')

    if sim_start_adj != SIM_START or sim_end_adj != SIM_END:
        print(f"  테스트 기간 조정:")
        if sim_start_adj != SIM_START:
            print(f"    SIM_START: {SIM_START}  →  {sim_start_adj}")
        if sim_end_adj != SIM_END:
            print(f"    SIM_END  : {SIM_END}  →  {sim_end_adj}")

    # 전역 변수 갱신
    globals()['SIM_START'] = sim_start_adj
    globals()['SIM_END']   = sim_end_adj

    # ── 청크 분할 ──────────────────────────────────────────────────────
    chunks = _build_chunks(SIM_START, SIM_END, CHUNK_DAYS)
    n_chunks = len(chunks)
    print(f"\n  총 {n_chunks}개 청크로 분할하여 실행")
    for i, (cs, ce) in enumerate(chunks):
        print(f"    [{i+1}/{n_chunks}] {cs}  ~  {ce}")

    # 전체 누적 저장용
    all_records:             list = []
    all_pred_upload:         list = []
    all_summary_rows:        list = []
    all_store: dict = {
        hl: {t: {'pred': [], 'true': [], 'ts': []} for t in target_list}
        for hl in HORIZONS
    }
    pred_id_offset = 1   # 청크 간 pred_id 연속성 유지


    for chunk_idx, (chunk_start, chunk_end) in enumerate(chunks):
        print(f"\n{'━'*70}")
        print(f"  청크 [{chunk_idx+1}/{n_chunks}]  {chunk_start}  ~  {chunk_end}")
        print(f"{'━'*70}")

        # 이 청크 동안만 SIM_START / SIM_END 를 임시 오버라이드
        _orig_start, _orig_end = SIM_START, SIM_END
        import builtins
        # 전역 변수 오버라이드 (함수들이 전역 참조)
        globals()['SIM_START'] = chunk_start
        globals()['SIM_END']   = chunk_end

        # DB 데이터 조회 (청크 단위 — WINDOW_MIN 워밍업 포함)
        print("  [DB 조회] 원시데이터 로드...")
        raw_1min = load_rawdata_from_db(df_meta)

        # 시뮬레이션
        print("  [시뮬레이션] 실행...")
        records, summary_df, store, pred_records_upload = run_simulation(
            df_meta, raw_1min, models_by_horizon, var_list, target_list
        )

        # pred_id 오프셋 적용
        for r in pred_records_upload:
            r['pred_id'] += (pred_id_offset - 1)
        pred_id_offset += len(pred_records_upload)

        # 전체 누적
        all_records.extend(records)
        all_pred_upload.extend(pred_records_upload)
        for hl in HORIZONS:
            for t in target_list:
                all_store[hl][t]['pred'].extend(store[hl][t]['pred'])
                all_store[hl][t]['true'].extend(store[hl][t]['true'])
                all_store[hl][t]['ts'].extend(store[hl][t]['ts'])

        # 정확도 요약 누적
        if not summary_df.empty:
            all_summary_rows.append(summary_df)

        # 전역 변수 복원
        globals()['SIM_START'] = _orig_start
        globals()['SIM_END']   = _orig_end

        # 청크별 DB 업로드
        print(f"  [DB 업로드] tag_pred_l  {len(pred_records_upload):,}건 INSERT...")
        upload_tag_pred_l(pred_records_upload)

    # ── 전체 정확도 요약 집계 ──────────────────────────────────────────
    if all_summary_rows:
        full_summary_df = pd.concat(all_summary_rows, ignore_index=True)
        # 같은 Horizon x 변수명 그룹으로 재집계 (N 가중 평균)
        # (간단히 마지막 청크 값 대신 전체 store로 재계산)
        summary_rows_all = []
        print(f"\n{'='*70}")
        print(f"  전체 정확도 요약 (전 청크 합산)")
        print(f"{'='*70}")
        for hl in HORIZONS:
            for t in target_list:
                yp = np.array(all_store[hl][t]['pred'])
                yt = np.array(all_store[hl][t]['true'])
                if len(yt) < 2:
                    continue
                m = compute_metrics(yt, yp)
                summary_rows_all.append({
                    'Horizon'  : hl,
                    '변수명'   : t,
                    'N'        : m['N'],
                    'MAE'      : round(m['MAE'],      4),
                    'RMSE'     : round(m['RMSE'],     4),
                    'sMAPE(%)' : round(m['sMAPE(%)'], 2),
                    'R2'       : round(m['R2'],       4),
                })
                print(f"  [{hl:6s}] {t:<15s}  "
                      f"MAE={m['MAE']:8.2f}  RMSE={m['RMSE']:8.2f}  "
                      f"sMAPE={m['sMAPE(%)']:5.2f}%  R²={m['R2']:.4f}  N={m['N']:,}")
        print(f"{'='*70}")
        full_summary_df = pd.DataFrame(summary_rows_all)
    else:
        full_summary_df = pd.DataFrame()

    # ── 결과 저장 (Excel + 그래프) — SAVE_RESULTS 일 때만 ────────────
    if SAVE_RESULTS:
        print("\n[저장] 전체 결과 Excel / 그래프 저장 중...")
        save_and_plot(all_records, full_summary_df, all_store,
                      target_list, all_pred_upload)

    print("\n[완료]  전체 업로드 건수:", pred_id_offset - 1)

