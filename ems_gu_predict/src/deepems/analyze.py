"""탐색적 데이터 분석(EDA) — 학습 전에 데이터 자체를 점검하기 위한 도구.

학습 파이프라인(pipeline.prepare_data)과 같은 태그리스트 로딩·원본 로딩·
리샘플링 함수를 그대로 재사용한다 — 여기서 보는 통계와 실제 학습에
들어가는 데이터가 서로 다른 전처리를 거쳐 어긋나는 일이 없도록 하기
위함이다 (이 저장소 전체를 관통하는 원칙: pipeline.py 상단 docstring 참고).

train/val/test로 나누지 않고 전 기간을 대상으로 본다 — "지금 이 데이터가
학습하기에 괜찮은 상태인가"를 학습 전에 확인하는 용도이기 때문이다.

태그리스트 엑셀은 시트가 여러 개다 — 시트 하나가 "단계"(정수장/배수지 등)
하나에 대응한다 (예: gunsan=군산정수장, gj=국가산단, nw=나운, osd=오식도).
main_guns_v1.py도 gunsan 시트로 정수장을, 나머지 시트들로 하위 배수지를
따로 예측한다(predict_and_upload_flux_test). 이 모듈도 마찬가지로 시트별로
분석을 나눠서, 각 시트 결과를 analysis/<시트>/ 에 따로 저장한다.

python -m deepems.analyze --config configs/gunsan.yaml                 # config의 data.sheet 하나만
python -m deepems.analyze --config configs/gunsan.yaml --sheet gj       # 다른 시트 하나로 덮어쓰기
python -m deepems.analyze --config configs/gunsan.yaml --all-sheets     # 태그리스트의 모든 시트

기본 통계(결측/이상치/자기상관/feature 상관관계) 외에, 아래 두 가지도 항상 같이 계산한다
(비용이 커서 빠르게 훑어보고 싶을 때만 --skip-* 로 끈다):
  - 계절성/주기성: 요일별·월별 패턴(weekday_profile/monthly_profile), 자기상관 곡선을 촘촘히
    계산해 국소 피크(=주기)를 찾는 detect_periodicities. 기본 2일치 lag까지 보므로 주간(7일)
    주기까지 보려면 --acf-max-lag-minutes 10080 처럼 늘려야 한다.
  - CCF(교차상관): 동시 상관이 강한 태그쌍만 골라(기본 |corr|>=0.5, 최대 40쌍) lag을 움직이며
    상관이 최대가 되는 지연시간을 찾는다 — 관망 상 상류->하류 신호 전파 지연을 잡아내기 위함.

python -m deepems.analyze --config configs/gu_db.yaml --skip-seasonality --skip-ccf   # 빠른 훑어보기
python -m deepems.analyze --config configs/gu_db.yaml --clean                          # 기존 분석 폴더를 지우고 새로
python -m deepems.analyze --config configs/gu_db.yaml --acf-max-lag-minutes 10080     # 주간 주기까지
python -m deepems.analyze --config configs/gu_db.yaml --ccf-corr-threshold 0.3 --ccf-max-pairs 80
"""
from __future__ import annotations

import argparse
import dataclasses
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from .config import Config
from .data import (
    add_time_features,
    apply_column_start_dates,
    combine_max_columns,
    find_segments,
    impute_stuck_values,
    resample_and_flag_gaps,
    stuck_run_mask,
)
from .plotting import get_plt as _plt
from .plotting import small_multiples_grid as _small_multiples_grid
from .taglist import (
    REFERENCE_NETWORK_EDGES,
    REFERENCE_SAME_SITE_GROUPS,
    TagInfo,
    classify_quantity,
    combine_max,
    feature_vars,
    filter_excluded,
    is_valve_tag,
    list_sheets,
    load_taglist,
    short_tag_name,
    target_vars,
)

DEFAULT_LAGS_MINUTES = [1, 5, 10, 30, 60, 180, 1440]


@dataclasses.dataclass
class AnalysisData:
    tags: list[TagInfo]
    feature_cols: list[str]
    target_cols: list[str]
    raw_grid: pd.DataFrame  # freq 그리드로 리샘플만 하고 채우지 않은 원본 (컬럼별 결측 확인용)
    filled: pd.DataFrame  # 학습과 동일하게 ffill_limit_minutes만큼 채운 버전
    valid_mask: pd.Series  # filled 기준, 모든 컬럼이 유효한 행 (학습에서 실제로 쓰이는 부분)


def load_full_raw(cfg: Config) -> AnalysisData:
    # combine_max_columns로 합쳐질 태그(예: H3_1/H3_2 -> H3)는 raw 로딩 단계까지는
    # 개별 원본으로 존재해야 하므로, pipeline.prepare_data와 똑같이 병합 전
    # tags_raw로 먼저 로딩하고, 그 다음 raw DataFrame과 tags를 같이 병합한다.
    tags_raw = load_taglist(cfg.data.taglist_path, cfg.data.sheet, cfg.data.mode)
    tags_raw = filter_excluded(tags_raw, cfg.data.exclude_vars)

    if cfg.data.source == "csv":
        from .data import load_raw_frame

        raw = load_raw_frame(
            tags_raw, cfg.data.rawdata_dir, cfg.data.raw_filename_template, cfg.data.start_date, cfg.data.end_date
        )
    elif cfg.data.source == "db":
        from .db_source import load_raw_frame_db

        raw = load_raw_frame_db(tags_raw, cfg.data, cfg.data.start_date, cfg.data.end_date)
    else:  # pragma: no cover
        raise ValueError(f"unknown data.source: {cfg.data.source}")

    raw = combine_max_columns(raw, cfg.data.combine_max_columns)
    tags = combine_max(tags_raw, cfg.data.combine_max_columns)
    feature_cols = feature_vars(tags)
    target_cols = target_vars(tags)

    raw = raw[feature_cols]
    raw = apply_column_start_dates(raw, cfg.data.column_start_dates)

    # ffill_limit_minutes=0 -> 리샘플 그리드에 채우기 없이 그대로 (컬럼별 결측 파악용)
    raw_grid, _ = resample_and_flag_gaps(raw, cfg.data.freq, ffill_limit_minutes=0)
    filled, valid_mask = resample_and_flag_gaps(
        raw, cfg.data.freq, cfg.data.ffill_limit_minutes, linear_interp_columns=cfg.data.linear_interp_columns
    )

    if cfg.data.stuck_value_min_minutes:
        # pipeline.prepare_data와 반드시 같은 기준으로 걸러야 한다 — 안 그러면
        # 여기서 보는 통계(특히 자기상관)가 실제 학습 데이터보다 낙관적으로
        # 나온다. 실제로 osd 시트 P6이 몇 달씩 0.0으로 고정된 구간을 안 걸렀을
        # 때, "자기상관 0.999"라는 착시가 나온 적이 있다 (그 구간은 정의상
        # 완벽하게 "안 변하는" 값이라 lag-1 상관계수를 크게 부풀린다) — 3개월
        # 짧은 구간만 봤을 때는 같은 태그가 0.6 근처로 나왔던 것과 대조됨.
        # stuck_value_impute_columns가 있으면 pipeline.prepare_data와 똑같이
        # 그 컬럼은 제외 대신 값으로 대체한다(stuck_value_impute_method로
        # median/linear 선택 — data.impute_stuck_values 참고).
        if cfg.data.stuck_value_impute_columns:
            filled = impute_stuck_values(
                filled, raw_grid, cfg.data.freq, cfg.data.stuck_value_min_minutes, cfg.data.stuck_value_impute_columns,
                method=cfg.data.stuck_value_impute_method,
            )
        valid_mask = valid_mask & ~stuck_run_mask(
            raw_grid, cfg.data.freq, cfg.data.stuck_value_min_minutes,
            exclude_columns=cfg.data.stuck_value_impute_columns,
        )

    if cfg.data.time_features:
        # raw_grid/filled 둘 다에 넣어야 한다 — 안 그러면 이 둘을 feature_cols
        # 기준으로 순회하는 missing_by_column/descriptive_stats 등에서
        # KeyError가 난다. 시각에서 결정적으로 계산되므로 raw_grid(채우기 전)
        # 기준으로 넣어도 결측이 생기지 않는다.
        raw_grid = add_time_features(raw_grid, cfg.data.time_features)
        filled = add_time_features(filled, cfg.data.time_features)
        feature_cols = feature_cols + [f for f in cfg.data.time_features if f not in feature_cols]

    return AnalysisData(
        tags=tags, feature_cols=feature_cols, target_cols=target_cols,
        raw_grid=raw_grid, filled=filled, valid_mask=valid_mask,
    )


def analyzed_vars(data: AnalysisData) -> list[str]:
    """EDA(탐색적 데이터 분석)에서 "변수 하나하나 개별로 훑어보는" 함수들
    (autocorrelation_table, hourly/weekday/monthly_profile, acf_curve,
    plot_target_overview, plot_network_graph 등)이 대상으로 삼는 변수 목록.

    data.target_cols(role=="target"만)도, data.feature_cols(target+variable
    은 맞지만 time_features까지 포함)도 아니고 그 사이다 — role="variable"
    태그(예: 밸브 개도 V2/V4, 또는 나중에 target에서 variable로 바뀐 태그)는
    "모델 target으로 학습하지 않는다"는 뜻일 뿐 "데이터 분석 대상이 아니다"는
    뜻이 아니기 때문에 target_cols로 좁히면 안 되고, hour_sin/hour_cos 같은
    시간 feature는 원본 계측 데이터가 아니라 학습용으로 만든 파생값이라
    "시계열/자기상관을 눈으로 확인해볼 대상" 목록엔 안 어울려서 feature_cols
    그대로 쓰기도 마땅치 않다(다만 correlation_matrix/cross_correlation_pairs
    처럼 "다른 변수와의 관계"를 보는 함수는 시간 feature도 유용한 정보라
    feature_cols를 그대로 쓴다 — 거긴 안 바꿈).

    data.tags(combine_max로 이미 병합된 후, exclude_vars로 이미 걸러진 후)의
    var_name을 그대로 쓰면 정확히 이 목적에 맞는다.
    """
    return [t.var_name for t in data.tags]


# --------------------------------------------------------------------------
# 순수 계산 함수 (matplotlib 불필요, 합성 데이터로 단위테스트 가능)
# --------------------------------------------------------------------------

def coverage_summary(data: AnalysisData) -> dict:
    n = len(data.valid_mask)
    valid = int(data.valid_mask.sum())
    return {
        "start": data.filled.index.min() if n else None,
        "end": data.filled.index.max() if n else None,
        "total_rows": n,
        "valid_rows": valid,
        "valid_ratio_%": 100 * valid / n if n else float("nan"),
    }


def missing_by_column(data: AnalysisData) -> pd.DataFrame:
    """리샘플 그리드 기준(채우기 전) 컬럼별 결측 비율. ffill_limit_minutes로도
    못 채울 만큼 자주/오래 비는 센서를 먼저 찾아내는 용도."""
    n = len(data.raw_grid)
    rows = []
    for col in data.feature_cols:
        na = int(data.raw_grid[col].isna().sum())
        rows.append({"column": col, "n": n, "missing": na, "missing_ratio_%": 100 * na / n if n else float("nan")})
    df = pd.DataFrame(rows)
    return df.sort_values("missing_ratio_%", ascending=False).reset_index(drop=True)


def gap_report(valid_mask: pd.Series, freq: str) -> pd.DataFrame:
    """valid_mask가 False로 이어지는(=학습 윈도우에서 제외되는) 구간을 큰 순으로.
    window.min_segment_minutes를 얼마로 잡아야 할지, purge_minutes가 충분한지
    가늠하는 데 쓴다."""
    inverted = ~valid_mask
    segments = find_segments(inverted, min_rows=1)
    freq_delta = pd.Timedelta(freq)
    idx = valid_mask.index
    rows = []
    for s, e in segments:
        start, end = idx[s], idx[e - 1]
        duration_min = ((end - start) + freq_delta) / pd.Timedelta(minutes=1)
        rows.append({"start": start, "end": end, "duration_minutes": duration_min, "n_rows": e - s})
    df = pd.DataFrame(rows, columns=["start", "end", "duration_minutes", "n_rows"])
    if len(df):
        df = df.sort_values("duration_minutes", ascending=False).reset_index(drop=True)
    return df


def stuck_value_report(data: AnalysisData, freq: str, min_run_minutes: int = 60) -> pd.DataFrame:
    """값이 min_run_minutes 이상 정확히 똑같은 값을 반복하는 구간을 찾는다.

    센서/통신이 죽어서 마지막 값(혹은 0)을 그대로 반복 송신하는 경우를 잡기
    위함이다. 이런 구간은 NaN이 아니라서 gap_report/missing_by_column에는
    안 걸리지만, 실제로는 물리적 신호가 아니라 "고장난 채로 있는" 값이라
    학습에 그대로 쓰면 안 된다. dev DB의 osd 시트 P6(891-365-PRI-8800)에서
    2025-09~2026-03 사이 값이 정확히 0.0으로 몇 달간 고정된 것을 이렇게 발견했다
    (실제 배관 압력이 몇 달간 정확히 0일 수는 없다 — 센서/통신 장애로 판단).
    """
    freq_delta = pd.Timedelta(freq)
    min_rows = max(1, int(pd.Timedelta(minutes=min_run_minutes) / freq_delta))
    rows = []
    for col in data.feature_cols:
        s = data.raw_grid[col]
        same_as_prev = s.eq(s.shift(1)) & s.notna()
        for seg_start, seg_end in find_segments(same_as_prev, min_rows=min_rows):
            # same_as_prev[i]==True는 s[i]==s[i-1]이라는 뜻이므로, 고정값 구간은
            # 실제로는 seg_start 한 칸 앞(그 값이 처음 나타난 시점)부터 시작된다.
            run_start_pos = max(seg_start - 1, 0)
            start, end = s.index[run_start_pos], s.index[seg_end - 1]
            duration_min = ((end - start) + freq_delta) / pd.Timedelta(minutes=1)
            rows.append(
                {"column": col, "start": start, "end": end, "duration_minutes": duration_min, "stuck_value": s.iloc[run_start_pos]}
            )
    df = pd.DataFrame(rows, columns=["column", "start", "end", "duration_minutes", "stuck_value"])
    if len(df):
        df = df.sort_values("duration_minutes", ascending=False).reset_index(drop=True)
    return df


def descriptive_stats(data: AnalysisData) -> pd.DataFrame:
    """실제 단위(스케일 전) 기준 컬럼별 분포 요약. p01/p99를 min/max와 같이 보면
    outlier.lower_quantile/upper_quantile(기본 0.01/0.99)로 clip했을 때
    꼬리값이 얼마나 잘려나가는지 감을 잡을 수 있다."""
    rows = []
    for col in data.feature_cols:
        s = data.raw_grid[col].dropna()
        if len(s) == 0:
            rows.append({"column": col, "n": 0})
            continue
        rows.append(
            {
                "column": col, "n": len(s),
                "mean": s.mean(), "std": s.std(),
                "min": s.min(), "p01": s.quantile(0.01), "p25": s.quantile(0.25),
                "median": s.median(), "p75": s.quantile(0.75), "p99": s.quantile(0.99),
                "max": s.max(),
            }
        )
    return pd.DataFrame(rows)


def clip_series(s: pd.Series, lower_q: float, upper_q: float) -> pd.Series:
    """s의 분위수(lower_q~upper_q) 밖 값만 clip. NaN은 그대로 NaN."""
    valid = s.dropna()
    if len(valid) == 0:
        return s
    lo, hi = valid.quantile(lower_q), valid.quantile(upper_q)
    return s.clip(lo, hi)


def compare_tag_series(a: pd.Series, b: pd.Series, freq: str, label_a: str = "a", label_b: str = "b") -> dict:
    """서로 다른 출처(예: 다른 DB/사이트/시스템)에서 받은 두 시계열이 같은
    실측을 가리키는지 비교한다 — 인덱스가 정확히 안 맞을 수 있으므로(측정
    주기/샘플링 시각이 다를 수 있음) `freq`로 리샘플(평균)한 뒤 공통 구간
    (둘 다 유효한 시각)만 남겨 상관계수/평균차이/비율을 계산한다.

    2026-09-11 추가: 고산(Gosan) EMS DB(ems_db_gs_dump_*)와 군산(Gunsan)
    EMS DB(ems_db_gu_dump_*)가 같은 물리 시설(나운배수지)을 서로 다른
    태그 코드(701-365-FRI-8009 vs 891-365-FRI-8600)로 각자 계측하는지
    확인하려고 만들었다 — 나운배수지는 고산에서도 관리한다는 사용자 확인
    (taglist.py의 REFERENCE_* 상수들과 같은 성격의 "실측/현장 정보").
    이런 교차 검증은 여러 사이트를 다루게 되면 반복될 수 있어 일회성
    스크립트 대신 여기 공용 함수로 둔다.

    - `corr`이 1에 가까우면 같은 신호를 (스케일/오프셋 차이만 있을 수 있게)
      추적한다는 뜻이고, 0에 가까우면 서로 무관한 신호라는 뜻이다.
    - `median_ratio`(a/b의 중앙값)가 1에 가까우면 같은 단위로 같은 값을
      재는 것, 다른 상수에 가까우면 단위/계측 지점이 다를 가능성.
    - 공통 구간이 전혀 없으면(n=0) 모든 통계를 nan으로 채워 돌려준다
      (호출부가 미리 len 체크 안 해도 되게).
    """
    a_resampled = a.resample(freq).mean()
    b_resampled = b.resample(freq).mean()
    common = pd.DataFrame({label_a: a_resampled, label_b: b_resampled}).dropna()

    if len(common) == 0:
        return {
            "n": 0, "corr": float("nan"), "mean_a": float("nan"), "mean_b": float("nan"),
            "std_a": float("nan"), "std_b": float("nan"), "mean_diff": float("nan"),
            "std_diff": float("nan"), "median_ratio": float("nan"),
        }

    diff = common[label_a] - common[label_b]
    ratio = (common[label_a] / common[label_b].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "n": len(common),
        "corr": float(common[label_a].corr(common[label_b])),
        "mean_a": float(common[label_a].mean()), "mean_b": float(common[label_b].mean()),
        "std_a": float(common[label_a].std()), "std_b": float(common[label_b].std()),
        "mean_diff": float(diff.mean()), "std_diff": float(diff.std()),
        "median_ratio": float(ratio.median()) if len(ratio) else float("nan"),
    }


def autocorrelation_table(
    data: AnalysisData,
    lags_minutes: list[int] | None = None,
    robust_lower_q: float = 0.01,
    robust_upper_q: float = 0.99,
) -> pd.DataFrame:
    """타깃 변수의 lag별 자기상관. lag_1min이 1에 가까울수록 naive(persistence)
    예측의 R²/MAE가 저절로 좋게 나온다 — model이 그보다 나은지 판단할 때
    (baseline이 얼마나 강력한 상대인지) 학습 전에 미리 참고하는 용도.

    raw(원본)와 robust_clipped(분위수로 clip한 버전) 두 가지를 같이 낸다.
    센서 글리치 하나가 극단값(예: 정상 범위가 수천인데 값이 수십만~수백만)이면
    Pearson 상관계수는 그 한두 점에 완전히 휘둘려서 raw 자기상관이 실제
    신호의 예측 가능성과 무관하게 0에 가깝게 나올 수 있다 — 이 저장소의
    gunsan 데이터에서 실제로 관측된 현상이다 (Q_GunSnS: raw ≈ 0.01,
    robust_clipped ≈ 0.99). 그래서 raw만 보고 "이 변수는 예측하기 어렵다"고
    판단하면 안 되고, robust_clipped와 extreme_value_flags()를 같이 봐야 한다.

    data.valid_mask로 미리 걸러진(결측·고정값 제외) 값만 쓴다 — 안 그러면
    반대 방향의 착시가 생긴다: 값이 몇 달씩 고정된 구간은 정의상 "완벽하게
    안 변하는" 값이라 자기상관을 실제보다 크게 부풀린다. osd 시트 P6이
    실제로 이랬다 — 몇 달간 0.0으로 고정된 구간을 포함해서 계산하면
    자기상관 0.999가 나오지만, 그 구간을 빼면 (진짜 예측 가능성인) 훨씬
    낮은 값이 나온다. pipeline.prepare_data도 같은 valid_mask 기준으로
    학습 데이터를 고르므로, 이렇게 해야 여기서 보는 통계와 실제 학습에
    쓰이는 데이터가 일치한다.
    """
    lags_minutes = lags_minutes or DEFAULT_LAGS_MINUTES
    rows = []
    for col in analyzed_vars(data):
        raw_s = data.filled[col].where(data.valid_mask)
        robust_s = clip_series(raw_s, robust_lower_q, robust_upper_q)
        for kind, s in (("raw", raw_s), ("robust_clipped", robust_s)):
            row = {"target": col, "kind": kind}
            for lag in lags_minutes:
                row[f"lag_{lag}min"] = s.autocorr(lag=lag) if len(s) > lag else float("nan")
            rows.append(row)
    return pd.DataFrame(rows)


def extreme_value_flags(stats: pd.DataFrame) -> pd.DataFrame:
    """descriptive_stats() 결과에서, max가 p99보다(또는 min이 p01보다) IQR 대비
    얼마나 튀어나와 있는지를 계산한다. 값이 크면(수십 배 이상) 소수의 센서
    글리치가 있다는 뜻이고, 이런 컬럼은 raw 상관계수/자기상관이 왜곡되기 쉽다."""
    df = stats.copy()
    iqr = (df["p75"] - df["p25"]).replace(0, np.nan)
    df["max_extremity_iqr"] = (df["max"] - df["p99"]) / iqr
    df["min_extremity_iqr"] = (df["p01"] - df["min"]) / iqr
    df["worst_extremity_iqr"] = df[["max_extremity_iqr", "min_extremity_iqr"]].max(axis=1)
    cols = ["column", "min", "p01", "p99", "max", "max_extremity_iqr", "min_extremity_iqr", "worst_extremity_iqr"]
    return df[cols].sort_values("worst_extremity_iqr", ascending=False).reset_index(drop=True)


def hourly_profile(data: AnalysisData) -> pd.DataFrame:
    """시간대별(0~23시) 평균·표준편차 — 일간 수요 패턴 확인용. target뿐 아니라
    role="variable" 태그(밸브 개도 등, analyzed_vars 참고)도 포함한다."""
    cols = analyzed_vars(data)
    df = data.filled.loc[data.valid_mask, cols].copy()
    df["hour"] = df.index.hour
    agg = df.groupby("hour")[cols].agg(["mean", "std"])
    agg.columns = [f"{col}_{stat}" for col, stat in agg.columns]
    return agg.reset_index()


def weekday_profile(data: AnalysisData) -> pd.DataFrame:
    """요일별(0=월 ~ 6=일) 평균·표준편차 — 평일/주말 수요 패턴 확인용.
    hourly_profile과 짝을 이룬다: hourly_profile이 하루 안의 리듬을, 이 함수는
    요일에 따른 리듬을 본다 (예: 산업단지 급수는 주말에 확 줄 수 있음)."""
    cols = analyzed_vars(data)
    df = data.filled.loc[data.valid_mask, cols].copy()
    df["weekday"] = df.index.weekday
    agg = df.groupby("weekday")[cols].agg(["mean", "std"])
    agg.columns = [f"{col}_{stat}" for col, stat in agg.columns]
    return agg.reindex(range(7)).reset_index()


def monthly_profile(data: AnalysisData) -> pd.DataFrame:
    """월별(1~12, 연도 무관하게 합침) 평균·표준편차 — 계절성(여름철 급수량
    증가 등) 확인용. 학습 데이터가 여러 해에 걸쳐 있을 때만 각 달마다 표본이
    여러 해 분 섞여 안정적인 평균이 나온다."""
    cols = analyzed_vars(data)
    df = data.filled.loc[data.valid_mask, cols].copy()
    df["month"] = df.index.month
    agg = df.groupby("month")[cols].agg(["mean", "std"])
    agg.columns = [f"{col}_{stat}" for col, stat in agg.columns]
    return agg.reindex(range(1, 13)).reset_index()


def _freq_to_minutes(freq: str) -> float:
    return pd.Timedelta(freq) / pd.Timedelta(minutes=1)


def _fast_corr(a: np.ndarray, b: np.ndarray) -> float:
    """NaN을 pairwise로 무시하는 Pearson 상관계수 (numpy 기반, pandas .corr()보다
    훨씬 빠르다 — acf_curve/cross_correlation_pairs가 lag마다 이걸 반복 호출한다)."""
    mask = ~np.isnan(a) & ~np.isnan(b)
    if mask.sum() < 2:
        return float("nan")
    a, b = a[mask], b[mask]
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _cross_corr_at_lag(a: np.ndarray, b: np.ndarray, lag_steps: int) -> float:
    """corr(a[t - lag_steps], b[t]) — lag_steps>0이면 a의 과거 값과 b의 현재 값을
    맞춰본다(=a가 b를 lag_steps만큼 선행할 때 상관이 얼마나 되는지). lag_steps<0이면
    반대로 b가 a를 선행하는 경우. lag_steps=0은 동시 상관(corr_lag0)과 같다.
    acf_curve는 a=b(자기 자신)로 이 함수를 쓴다."""
    n = len(a)
    if lag_steps == 0:
        return _fast_corr(a, b)
    if abs(lag_steps) >= n:
        return float("nan")
    if lag_steps > 0:
        return _fast_corr(a[:-lag_steps], b[lag_steps:])
    k = -lag_steps
    return _fast_corr(a[k:], b[:-k])


def acf_curve(
    data: AnalysisData,
    freq: str,
    max_lag_minutes: int = 2880,
    step_minutes: int | None = None,
    robust_lower_q: float = 0.01,
    robust_upper_q: float = 0.99,
) -> pd.DataFrame:
    """타깃 변수별 자기상관을 lag=0부터 max_lag_minutes까지 촘촘하게(step_minutes
    간격, 기본은 freq 그대로) 계산한 곡선. autocorrelation_table의 고정 lag
    (1/5/10/30/60/180/1440분) 몇 개만으로는 못 보는 국소 피크 — 예를 들어 정확히
    24시간·12시간 주기에서 상관이 다시 튀어오르는 지점 — 을 detect_periodicities로
    찾아내기 위한 원본 데이터다. 기본 max_lag_minutes=2880(2일)이면 일간 주기와
    반나절 주기까지는 잡을 수 있다 — 주간(7일) 주기까지 보려면 늘려야 한다.

    이상치에 흔들리지 않도록 robust_clipped(분위수 clip) 값만 쓴다 — raw 대비
    비교는 이미 autocorrelation_table에서 하므로 여기서 중복하지 않는다.
    """
    freq_min = _freq_to_minutes(freq)
    step_minutes = step_minutes or freq_min
    step_steps = max(1, round(step_minutes / freq_min))
    max_lag_steps = max(step_steps, round(max_lag_minutes / freq_min))

    rows = []
    for col in analyzed_vars(data):
        s = clip_series(data.filled[col].where(data.valid_mask), robust_lower_q, robust_upper_q)
        values = s.to_numpy(dtype=float)
        for lag_steps in range(0, max_lag_steps + 1, step_steps):
            acf = _cross_corr_at_lag(values, values, lag_steps)
            rows.append(
                {
                    "target": col,
                    "lag_minutes": lag_steps * freq_min,
                    "lag_hours": lag_steps * freq_min / 60,
                    "acf": acf,
                }
            )
    return pd.DataFrame(rows)


def detect_periodicities(
    acf_df: pd.DataFrame,
    min_lag_minutes: float = 60,
    prominence: float = 0.03,
    top_n: int = 5,
) -> pd.DataFrame:
    """acf_curve() 결과에서 (자기 자신과의 상관인) lag=0 근방을 제외한 국소 피크를
    찾는다. 피크가 있는 lag은 그 주기로 신호가 "돌아온다"는 뜻이다 — 예를 들어
    lag≈1440분(24시간)에 뚜렷한 피크가 있으면 일간 수요 패턴이 강하다는 뜻이고,
    lag≈10080분(7일, acf_curve의 max_lag_minutes를 그만큼 늘렸을 때)에 피크가
    있으면 주간(평일/주말) 패턴이 강하다는 뜻이다. 학습 feature에 시간대/요일을
    넣을지, window_size를 얼마나 길게 잡아야 이런 주기를 모델이 볼 수 있을지
    판단하는 근거로 쓴다.
    """
    rows = []
    for target, grp in acf_df.groupby("target", sort=False):
        grp = grp[grp["lag_minutes"] >= min_lag_minutes].sort_values("lag_minutes").reset_index(drop=True)
        if len(grp) < 3:
            continue
        acf_vals = grp["acf"].to_numpy()
        finite = np.isfinite(acf_vals)
        if finite.sum() < 3:
            continue
        search_vals = np.where(finite, acf_vals, -1.0)  # NaN은 피크 후보에서 제외
        peaks, props = find_peaks(search_vals, prominence=prominence)
        for pos, peak_idx in enumerate(peaks):
            rows.append(
                {
                    "target": target,
                    "lag_minutes": grp.loc[peak_idx, "lag_minutes"],
                    "lag_hours": grp.loc[peak_idx, "lag_hours"],
                    "acf": grp.loc[peak_idx, "acf"],
                    "prominence": props["prominences"][pos],
                }
            )
    df = pd.DataFrame(rows, columns=["target", "lag_minutes", "lag_hours", "acf", "prominence"])
    if len(df):
        df = df.sort_values(["target", "acf"], ascending=[True, False]).groupby("target", sort=False).head(top_n).reset_index(drop=True)
    return df


def _ccf_curve_and_best(
    a: str, b: str, get_fn, freq_min: float, max_lag_steps: int, step_steps: int,
) -> tuple[pd.DataFrame, dict | None]:
    """한 쌍(a, b)의 lag별 CCF 곡선과 "상관이 최대가 되는 지연시간" 요약 행을
    계산한다. cross_correlation_pairs()(동시 상관 임계값을 넘는 쌍만)와
    ccf_for_pairs()(임계값 없이 주어진 쌍 전부) 둘 다 이 함수를 공유한다 —
    "곡선 하나를 어떻게 계산하는지"와 "어떤 쌍을 고를지"를 분리했다.

    요약 행이 None이면(유효한 lag이 하나도 없음, 예: 두 시계열이 전혀 안 겹침)
    호출부가 건너뛰어야 한다는 뜻이다.
    """
    va, vb = get_fn(a), get_fn(b)
    curve_rows = [
        {"lag_minutes": lag_steps * freq_min, "ccf": _cross_corr_at_lag(va, vb, lag_steps)}
        for lag_steps in range(-max_lag_steps, max_lag_steps + 1, step_steps)
    ]
    curve_df = pd.DataFrame(curve_rows)
    finite = curve_df.dropna(subset=["ccf"])
    if len(finite) == 0:
        return curve_df, None
    best = finite.loc[finite["ccf"].abs().idxmax()]
    if best["lag_minutes"] == 0:
        direction = "동시(지연 없음)"
    elif best["lag_minutes"] > 0:
        direction = f"{a}가 {b}를 {best['lag_minutes']:.0f}분 선행"
    else:
        direction = f"{b}가 {a}를 {-best['lag_minutes']:.0f}분 선행"
    row = {
        "a": a, "b": b, "corr_lag0": _fast_corr(va, vb),
        "best_lag_minutes": best["lag_minutes"], "best_ccf": best["ccf"], "direction": direction,
    }
    return curve_df, row


def cross_correlation_pairs(
    data: AnalysisData,
    corr: pd.DataFrame,
    freq: str,
    corr_threshold: float = 0.5,
    max_lag_minutes: int = 120,
    step_minutes: int | None = None,
    max_pairs: int = 40,
    robust_lower_q: float = 0.01,
    robust_upper_q: float = 0.99,
) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
    """동시 상관(correlation_matrix)이 corr_threshold 이상인 변수쌍에 대해서만,
    lag을 -max_lag_minutes~+max_lag_minutes로 움직여가며 교차상관(CCF)을 계산해
    상관이 최대가 되는 지연시간을 찾는다.

    군산 관망은 물리적으로 연결돼 있다(정수장 → 배수지 → 하위 배수지). 상류의
    변화가 몇 분~몇 시간 뒤에 하류에 반영되는 "전파 지연"이 있을 수 있는데,
    lag=0에서의 동시 상관(corr_lag0)만 보면 이 지연을 놓친다 — 실제로는 최적
    지연에서 상관이 더 강할 수 있다. best_lag_minutes가 0이 아니면 두 태그
    사이에 실제 시간차가 있다는 신호이고(양수면 a가 b를 선행, 음수면 b가 a를
    선행), 이건 window_size/horizon 설계와 "이 태그를 다른 태그 예측에 얼마나
    도움이 되는 feature로 볼지" 판단에 직접 쓸 수 있다.

    전체 쌍(태그 N개면 N*(N-1)/2쌍 — GU 시트 24개면 276쌍)을 다 계산하면 느려지므로,
    동시 상관이 이미 약한(물리적 연관성이 낮아 보이는) 쌍은 건너뛴다. threshold를
    넘는 쌍이 max_pairs보다 많으면 |corr_lag0|이 큰 순으로 max_pairs개만 계산한다.
    (주의: 이 임계값 때문에, 지연이 길어서 동시 상관 자체는 약한 진짜 관계는
    여기서 놓칠 수 있다 — 관망도 상 이미 연결이 알려진 쌍을 임계값 없이 보려면
    ccf_for_pairs()를 대신 쓸 것.)

    반환값: (요약 표, {(a, b): 전체 lag 곡선 DataFrame} — 상위 쌍 플롯용).
    """
    freq_min = _freq_to_minutes(freq)
    step_minutes = step_minutes or freq_min
    step_steps = max(1, round(step_minutes / freq_min))
    max_lag_steps = max(step_steps, round(max_lag_minutes / freq_min))

    cols = list(corr.columns)
    candidates: list[tuple[str, str, float]] = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            v = corr.iloc[i, j]
            if pd.notna(v) and abs(v) >= corr_threshold:
                candidates.append((cols[i], cols[j], float(v)))
    candidates.sort(key=lambda t: abs(t[2]), reverse=True)
    candidates = candidates[:max_pairs]

    series_cache: dict[str, np.ndarray] = {}

    def _get(col: str) -> np.ndarray:
        if col not in series_cache:
            s = clip_series(data.filled[col].where(data.valid_mask), robust_lower_q, robust_upper_q)
            series_cache[col] = s.to_numpy(dtype=float)
        return series_cache[col]

    summary_rows = []
    curves: dict[tuple[str, str], pd.DataFrame] = {}
    for a, b, _corr_lag0 in candidates:
        curve_df, row = _ccf_curve_and_best(a, b, _get, freq_min, max_lag_steps, step_steps)
        curves[(a, b)] = curve_df
        if row is not None:
            summary_rows.append(row)

    summary = pd.DataFrame(summary_rows, columns=["a", "b", "corr_lag0", "best_lag_minutes", "best_ccf", "direction"])
    if len(summary):
        summary = summary.reindex(summary["best_ccf"].abs().sort_values(ascending=False).index).reset_index(drop=True)
    return summary, curves


def ancestor_pairs(reference_edges: list[tuple[str, str]], target: str) -> list[tuple[str, str]]:
    """reference_edges(관망도, 인접 hop만 있는 상류->하류 목록)에서 target의
    모든 상류 조상(ancestor, 몇 단계든 상관없이)을 찾아 (조상, target) 쌍
    목록으로 돌려준다.

    인접 CCF(정수장->개정분기, 개정분기->국가산단, ... 처럼 한 hop씩)를 이어
    붙여서는 "정수장 조작이 결국 몇 분 뒤에 Q7(오식도 유입)에 반영되는가"
    같은 다단계 누적 지연을 정확히 알 수 없다 — 중간에 저수조가 끼면 각
    구간의 지연이 단순히 더해지지 않고 완충/왜곡되기 때문이다. 그래서 상류
    끝(정수장 등)과 target을 직접 쌍으로 놓고 CCF를 재는 게 유일하게 정확한
    방법이고, 이 함수는 그 쌍 목록을 자동으로 만들어준다. ccf_for_pairs()와
    같이 쓴다.

    target이 reference_edges에 아예 없으면(고립 노드) 빈 리스트를 돌려준다.
    """
    import networkx as nx

    g = nx.DiGraph()
    g.add_edges_from(reference_edges)
    if target not in g:
        return []
    return [(a, target) for a in sorted(nx.ancestors(g, target))]


def descendant_pairs(reference_edges: list[tuple[str, str]], source: str) -> list[tuple[str, str]]:
    """ancestor_pairs()의 반대 방향 — reference_edges에서 source의 모든 하류
    자손(descendant, 몇 단계든)을 찾아 (source, 자손) 쌍 목록으로 돌려준다.

    예: source="Q4"(국가산단)면 그 하류에 있는 Q8/Q6/P6/Q7/H7/O7이 전부
    자손이다. 밸브처럼 관망도 자체에는 없는 변수(REFERENCE_NETWORK_EDGES의
    노드가 아님)가 "내가 통제하는 지점보다 더 하류의 무엇에 영향을 주는가"
    (예: 국가산단밸브가 오식도배수지 수위에 영향을 주는지)를 물을 때, 밸브가
    속한 지점의 대표 노드(_site_anchor_for_valve 참고)를 source로 넣어 쓴다.

    source가 reference_edges에 아예 없으면 빈 리스트를 돌려준다.
    """
    import networkx as nx

    g = nx.DiGraph()
    g.add_edges_from(reference_edges)
    if source not in g:
        return []
    return [(source, d) for d in sorted(nx.descendants(g, source))]


def _site_anchor_for_valve(
    valve_var: str, same_site_groups: list[list[str]], reference_edges: list[tuple[str, str]]
) -> str | None:
    """valve_var(밸브 개도 등, REFERENCE_NETWORK_EDGES 노드가 아닌 변수)가 속한
    same_site_groups 그룹에서, REFERENCE_NETWORK_EDGES의 노드이기도 한 다른
    멤버를 하나 찾아 돌려준다 — 밸브 자신은 관망도 노드가 아니므로, 밸브가
    있는 "지점"을 대표하는 노드를 거쳐야 descendant_pairs()로 하류를 찾을 수
    있다(예: V2(지방산단밸브) -> Q2를 거쳐 Q2의 하류(H3 등)를 찾음).

    valve_var가 어느 그룹에도 없거나, 그 그룹에 관망도 노드가 하나도 없으면
    None을 돌려준다.
    """
    topo_nodes = {a for a, b in reference_edges} | {b for a, b in reference_edges}
    for group in same_site_groups:
        if valve_var in group:
            for member in group:
                if member != valve_var and member in topo_nodes:
                    return member
    return None


def valve_control_summary(
    data: AnalysisData,
    control_cols: list[str],
    always_fixed_ratio: float = 0.98,
    round_decimals: int = 1,
) -> pd.DataFrame:
    """밸브 개도 등 제어 변수(taglist.is_valve_tag로 판별된 태그)가
    "상시개방/고정"인지 "실제로 움직이며 제어되는지" 판별한다.

    raw_grid(리샘플만 하고 ffill 채우기 전)를 쓴다 — filled를 쓰면 ffill이
    결측 구간을 직전값으로 메워서 "값이 안 바뀐 시간"이 실제보다 부풀려져
    보인다(missing_by_column/stuck_value_report와 같은 이유로 raw_grid를 씀).

    핵심 판단 지표는 pct_at_mode: round_decimals로 반올림한 값 중 가장 흔한
    값(mode)이 전체 유효 관측치에서 차지하는 비율이다. 이게
    always_fixed_ratio(기본 98%) 이상이면 "사실상 한 값에 고정 — 상시개방
    (또는 특정 개도로 고정)으로 추정"으로, 아니면 "제어로 추정"(여러 값을
    오가며 실제로 움직임)으로 분류한다.

    다만 이건 통계적 추정일 뿐이다 — 실제로 "완전 개방"인지 "중간값에서
    고정"인지는 태그의 실제 스케일(0~100% 등)을 모르면 이 함수만으론 알 수
    없다. mean/min/max/mode_value를 같이 보고 판단할 것. distinct_values(반올림
    기준 서로 다른 값 개수)와 n_transitions(값이 바뀐 횟수)는 판단 근거를
    수치로 보여준다 — 예를 들어 pct_at_mode가 90%라도 distinct_values가
    2~3개뿐이면 "가끔 몇 단계로만 조정"이라는 뜻이라 진짜 연속 제어와는
    다르다.
    """
    rows = []
    for col in control_cols:
        s = data.raw_grid[col].dropna() if col in data.raw_grid.columns else pd.Series(dtype=float)
        if len(s) == 0:
            rows.append({"column": col, "n": 0, "classification": "판단 불가(데이터 없음)"})
            continue
        rounded = s.round(round_decimals)
        mode_value = rounded.mode().iloc[0]
        pct_at_mode = 100 * float((rounded == mode_value).mean())
        distinct_values = int(rounded.nunique())
        n_transitions = int((rounded != rounded.shift()).sum() - 1)  # shift(1)의 첫 NaN만큼 -1
        classification = "상시개방/고정 추정" if pct_at_mode >= always_fixed_ratio * 100 else "제어 추정"
        rows.append(
            {
                "column": col, "n": len(s),
                "mean": s.mean(), "std": s.std(), "min": s.min(), "max": s.max(),
                "mode_value": mode_value, "pct_at_mode": pct_at_mode,
                "distinct_values": distinct_values, "n_transitions": n_transitions,
                "classification": classification,
            }
        )
    return pd.DataFrame(rows)


def ccf_for_pairs(
    data: AnalysisData,
    freq: str,
    pairs: list[tuple[str, str]],
    max_lag_minutes: int = 4320,
    step_minutes: int | None = None,
    robust_lower_q: float = 0.01,
    robust_upper_q: float = 0.99,
) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
    """cross_correlation_pairs()와 달리 동시 상관(corr_lag0) 임계값으로 후보를
    거르지 않고, 주어진 pairs를 전부 계산한다.

    관망 상 실제로 연결된 것으로 이미 알려진 쌍(taglist.REFERENCE_NETWORK_EDGES,
    ancestor_pairs())은 지연이 길수록 오히려 동시 상관은 약해지므로(그게 바로
    "지연이 있다"는 신호인데도), cross_correlation_pairs()의 corr_threshold에
    걸러져 애초에 lag을 못 재보고 넘어갈 수 있다 — 실제로 오식도배수지 체인
    (Q7->H7->O7)이 실측 연결은 있는데 기본 설정(threshold=0.5, max_lag=120분)
    으로는 안 잡혔던 사례가 있다(docs/GU_network_topology.md "데이터 기반
    검증" 참고). max_lag_minutes 기본값도 그래서 3일(4320분)로 훨씬 넉넉하게
    잡았다 — 저수조 완충으로 지연이 몇 시간 단위일 수 있어서다. 그만큼 계산
    비용이 크므로(쌍 하나당 lag 후보가 max_lag_minutes/freq개), 소수의 특정
    쌍(예: ancestor_pairs 결과)에만 쓰는 걸 전제로 한다 — 전체 N*(N-1)/2쌍에는
    cross_correlation_pairs()를 쓸 것.

    pairs에 데이터에 없는 변수(data.feature_cols에 없는 var_name)가 섞여
    있으면 조용히 건너뛴다 — target_cols가 아니라 feature_cols 기준이라,
    role="variable"인 변수(예: 밸브 개도처럼 target으로는 안 쓰지만 데이터엔
    있는 변수)도 쌍에 넣을 수 있다. 반환 스키마는 cross_correlation_pairs()와
    같아서 plot_top_ccf_pairs()를 그대로 재사용할 수 있다.
    """
    freq_min = _freq_to_minutes(freq)
    step_minutes = step_minutes or freq_min
    step_steps = max(1, round(step_minutes / freq_min))
    max_lag_steps = max(step_steps, round(max_lag_minutes / freq_min))

    node_set = set(data.feature_cols)
    series_cache: dict[str, np.ndarray] = {}

    def _get(col: str) -> np.ndarray:
        if col not in series_cache:
            s = clip_series(data.filled[col].where(data.valid_mask), robust_lower_q, robust_upper_q)
            series_cache[col] = s.to_numpy(dtype=float)
        return series_cache[col]

    summary_rows = []
    curves: dict[tuple[str, str], pd.DataFrame] = {}
    seen: set[tuple[str, str]] = set()
    for a, b in pairs:
        if a not in node_set or b not in node_set or (a, b) in seen:
            continue
        seen.add((a, b))
        curve_df, row = _ccf_curve_and_best(a, b, _get, freq_min, max_lag_steps, step_steps)
        curves[(a, b)] = curve_df
        if row is not None:
            summary_rows.append(row)

    summary = pd.DataFrame(summary_rows, columns=["a", "b", "corr_lag0", "best_lag_minutes", "best_ccf", "direction"])
    if len(summary):
        summary = summary.reindex(summary["best_ccf"].abs().sort_values(ascending=False).index).reset_index(drop=True)
    return summary, curves


def correlation_matrix(data: AnalysisData) -> pd.DataFrame:
    return data.filled.loc[data.valid_mask, data.feature_cols].corr()


def near_duplicate_features(corr: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """상관계수가 threshold 이상인 변수 쌍. 사실상 같은 정보를 중복으로 넣고
    있는 feature가 있는지(예: 같은 배수지 수위를 다른 태그로 두 번) 확인."""
    cols = list(corr.columns)
    rows = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            v = corr.iloc[i, j]
            if pd.notna(v) and abs(v) >= threshold:
                rows.append({"a": cols[i], "b": cols[j], "corr": v})
    df = pd.DataFrame(rows, columns=["a", "b", "corr"])
    if len(df):
        df = df.reindex(df["corr"].abs().sort_values(ascending=False).index).reset_index(drop=True)
    return df


# --------------------------------------------------------------------------
# 시각화 (matplotlib, 화면 없는 환경에서도 동작하도록 Agg 백엔드 사용)
# --------------------------------------------------------------------------

# matplotlib 설정(Agg 백엔드, 한글 폰트)과 small-multiples 그리드 헬퍼는
# visualize.py와 공유하려고 plotting.py로 뺐다 (파일 위 import 참고).


def plot_target_overview(
    data: AnalysisData, out_dir: Path, cols: list[str] | None = None,
    clip_quantiles: tuple[float, float] | None = (0.01, 0.99),
    recent_days: int = 7,
) -> list[Path]:
    """cols를 안 주면 analyzed_vars(data)(target + role="variable" 태그 전부,
    시간 feature는 제외) — "target으로 학습 안 함"과 "데이터 분석도 안 함"은
    다른 얘기라서, 밸브 개도(V2/V4)처럼 role="variable"인 태그도 기본으로
    포함한다. cols를 명시로 주면(예: control_cols만 따로) 그 목록만 그린다.

    clip_quantiles: 전체 기간 그래프(일별 평균/최소~최대)를 그리기 전에
    clip_series()로 컬럼별 상하위 분위수 밖 값을 살짝 눌러준다 — 센서 글리치
    한두 개가 그날의 최소~최대 범위를 실제 신호보다 훨씬 넓게 부풀려서, 그
    스파이크 때문에 y축 스케일이 통째로 눌리고 정상 구간의 변화가 안 보이게
    되는 문제를 막는다(V2/V4 시계열에서 실제로 관찰됨). None이면 안 자르고
    원본 그대로. 호출부(run_and_save)는 cfg.outlier.lower_quantile/
    upper_quantile을 그대로 넘겨써서, "이상치로 본다"는 기준이 학습
    파이프라인의 outlier 설정과 하나로 일치한다.

    recent_days: 전체 기간 그래프(일별 집계라 하루 안의 변화는 뭉개짐)와 별도로,
    최근 recent_days일치를 리샘플 없이 원본 해상도 그대로 그린 그래프
    (timeseries_recent{recent_days}d_<col>.png)도 같이 만든다 — 일간 주기나
    밸브의 짧은 스파이크처럼 일별 집계로는 안 보이는 최근 단기 패턴을 보는
    용도. clip_quantiles는 여기엔 적용하지 않는다(원본 그대로 보는 게 목적).
    0이면 생략.
    """
    cols = cols if cols is not None else analyzed_vars(data)
    plt = _plt()
    paths = []

    clipped = pd.DataFrame(
        {col: (clip_series(data.filled[col], *clip_quantiles) if clip_quantiles else data.filled[col]) for col in cols}
    )
    daily = clipped.resample("1D").agg(["mean", "min", "max"])
    for col in cols:
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.plot(daily.index, daily[(col, "mean")], color="steelblue", label="일 평균")
        ax.fill_between(daily.index, daily[(col, "min")], daily[(col, "max")], alpha=0.2, color="steelblue", label="일 최소~최대")
        title = f"{col} — 일별 추이"
        if clip_quantiles:
            title += f" (상하위 {clip_quantiles[0] * 100:.0f}%/{100 - clip_quantiles[1] * 100:.0f}% 이상치는 눌러서 표시)"
        ax.set_title(title)
        ax.legend(loc="upper right")
        fig.tight_layout()
        path = out_dir / f"timeseries_{col}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)

    if recent_days and len(data.filled):
        cutoff = data.filled.index.max() - pd.Timedelta(days=recent_days)
        recent = data.filled.loc[data.filled.index >= cutoff]
        for col in cols:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.plot(recent.index, recent[col], color="darkorange", linewidth=0.9)
            ax.set_title(f"{col} — 최근 {recent_days}일 (원본 해상도, 이상치 제거 없음)")
            fig.tight_layout()
            path = out_dir / f"timeseries_recent{recent_days}d_{col}.png"
            fig.savefig(path, dpi=120)
            plt.close(fig)
            paths.append(path)
    return paths


def plot_gap_timeline(gaps: pd.DataFrame, data: AnalysisData, out_dir: Path) -> Path:
    plt = _plt()
    fig, ax = plt.subplots(figsize=(12, 1.6))
    ax.set_xlim(data.filled.index.min(), data.filled.index.max())
    for _, row in gaps.iterrows():
        ax.axvspan(row["start"], row["end"], color="crimson", alpha=0.7, linewidth=0)
    ax.set_yticks([])
    ax.set_title("결측/불연속 구간 (빨간 부분 — 학습 윈도우에서 제외됨)")
    fig.tight_layout()
    path = out_dir / "gap_timeline.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_autocorrelation(ac: pd.DataFrame, out_dir: Path) -> list[Path]:
    """타깃 변수마다 파일을 하나씩(autocorrelation_<target>.png) 따로 저장한다 —
    태그가 24개로 늘어나면 하나의 그래프에 raw/robust 24*2=48개 선을 다 겹쳐
    그리는 건 legend가 뒤엉켜서 못 읽는다."""
    plt = _plt()
    lag_cols = [c for c in ac.columns if c not in ("target", "kind")]
    paths = []
    for target in ac["target"].unique():
        grp = ac[ac["target"] == target]
        fig, ax = plt.subplots(figsize=(6, 3.5))
        for _, row in grp.iterrows():
            style = "-" if row["kind"] == "robust_clipped" else "--"
            ax.plot(lag_cols, [row[c] for c in lag_cols], marker="o", linestyle=style, label=row["kind"])
        ax.set_ylim(-1.05, 1.05)
        ax.axhline(0, color="gray", linewidth=0.8)
        ax.set_ylabel("자기상관")
        ax.set_xlabel("lag")
        ax.legend()
        ax.set_title(f"{target} 자기상관 (점선=raw, 실선=이상치 clip 후)")
        fig.tight_layout()
        path = out_dir / f"autocorrelation_{target}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)
    return paths


def plot_seasonal_profiles(
    data: AnalysisData, hourly: pd.DataFrame, weekday: pd.DataFrame, monthly: pd.DataFrame, out_dir: Path
) -> list[Path]:
    """변수마다(target + role="variable", analyzed_vars 참고) 파일을 하나씩
    (seasonal_<변수>.png) 따로 저장한다. 파일 하나 안에 시간대별/요일별/월별
    서브플롯 3개를 나란히 둬서, 그 변수 하나의 계절성을 한눈에 볼 수 있게 한다.
    hourly/weekday/monthly가 analyzed_vars(data) 기준으로 계산된 것이어야
    컬럼이 맞는다(hourly_profile 등 참고)."""
    plt = _plt()
    specs = [
        (hourly, "hour", "시간대별(0~23시)"),
        (weekday, "weekday", "요일별(0=월~6=일)"),
        (monthly, "month", "월별(1~12월, 연도 합산)"),
    ]
    paths = []
    for col in analyzed_vars(data):
        fig, axes = plt.subplots(1, 3, figsize=(11, 3))
        for ax, (df, xcol, title_kr) in zip(axes, specs):
            mean_col, std_col = f"{col}_mean", f"{col}_std"
            ax.plot(df[xcol], df[mean_col], color="steelblue")
            ax.fill_between(
                df[xcol], df[mean_col] - df[std_col], df[mean_col] + df[std_col],
                alpha=0.2, color="steelblue",
            )
            ax.set_title(title_kr, fontsize=9)
        fig.suptitle(f"{col} — 시간대별/요일별/월별 패턴 (선=평균, 음영=±표준편차)")
        fig.tight_layout()
        path = out_dir / f"seasonal_{col}.png"
        fig.savefig(path, dpi=110)
        plt.close(fig)
        paths.append(path)
    return paths


def plot_acf_curve(acf_df: pd.DataFrame, periodicities: pd.DataFrame, out_dir: Path) -> list[Path]:
    """타깃 변수마다 파일을 하나씩(acf_curve_<target>.png) 따로 저장한다."""
    plt = _plt()
    paths = []
    for t in acf_df["target"].unique():
        grp = acf_df[acf_df["target"] == t]
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(grp["lag_hours"], grp["acf"], color="darkorange", linewidth=1)
        ax.axhline(0, color="gray", linewidth=0.6)
        peaks = periodicities[periodicities["target"] == t]
        if len(peaks):
            ax.scatter(peaks["lag_hours"], peaks["acf"], color="crimson", s=18, zorder=3)
        ax.set_ylim(-1.05, 1.05)
        ax.set_xlabel("lag (시간)")
        ax.set_ylabel("자기상관")
        ax.set_title(f"{t} 자기상관 곡선 (빨간 점=국소 피크=주기성 후보)")
        fig.tight_layout()
        path = out_dir / f"acf_curve_{t}.png"
        fig.savefig(path, dpi=110)
        plt.close(fig)
        paths.append(path)
    return paths


def plot_top_ccf_pairs(
    ccf_summary: pd.DataFrame, ccf_curves: dict[tuple[str, str], pd.DataFrame], out_dir: Path, top_n: int = 8,
    filename: str = "ccf_top_pairs.png", title: str = "교차상관(CCF) 상위 쌍 (점선=상관이 최대가 되는 지연시간)",
    x_axis_hours: bool = False,
) -> Path | None:
    """filename/title을 바꿔주면 cross_correlation_pairs()(임계값 통과 쌍)뿐 아니라
    ccf_for_pairs()(경로 지연시간 재추정, 예: path_lag_Q7.png) 결과도 같은
    small-multiples 그리드로 그릴 수 있다. x_axis_hours=True면 lag 축을 분 대신
    시간 단위로 표시한다 — max_lag_minutes가 며칠 단위일 때(ccf_for_pairs
    기본값처럼) 분 단위 눈금은 너무 촘촘해서 못 읽는다."""
    if len(ccf_summary) == 0:
        return None
    plt = _plt()
    top = ccf_summary.head(top_n)
    fig, axes, nrows, ncols = _small_multiples_grid(plt, len(top), ncols=min(4, len(top)), subplot_w=3.6, subplot_h=2.6)
    for i, (_, row) in enumerate(top.iterrows()):
        ax = axes[i // ncols][i % ncols]
        curve = ccf_curves[(row["a"], row["b"])]
        x = curve["lag_minutes"] / 60 if x_axis_hours else curve["lag_minutes"]
        best_x = row["best_lag_minutes"] / 60 if x_axis_hours else row["best_lag_minutes"]
        ax.plot(x, curve["ccf"], color="seagreen")
        ax.axvline(best_x, color="crimson", linestyle="--", linewidth=1)
        ax.axhline(0, color="gray", linewidth=0.6)
        ax.set_title(f"{row['a']} vs {row['b']} ({best_x:+.1f}{'h' if x_axis_hours else 'm'})", fontsize=8)
        ax.set_ylim(-1.05, 1.05)
    for j in range(len(top), nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    path = out_dir / filename
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _hierarchical_positions(
    all_targets: list[str], reference_edges: list[tuple[str, str]],
    same_site_groups: list[list[str]] | None = None,
) -> dict[str, tuple[float, float]] | None:
    """reference_edges(실측 관망도, "상류 -> 하류" 방향)를 따라 각 태그가 관망
    상 몇 단계 하류인지(depth)를 구해서 x좌표로 쓴다 — 예를 들어 오식도배수지의
    `Q7`(유입) -> `H7`(수위) -> `O7`(유출)이 실제 순서 그대로 왼쪽에서 오른쪽으로
    나란히 놓이게 한다. CCF 상관 기반 spring_layout은 통계적으로 가까운 태그를
    묶을 뿐 실제 상류/하류 순서를 보장하지 않으므로, 순서가 확실한 정보
    (reference_edges)가 있을 땐 그걸 레이아웃에 직접 반영하는 게 더 낫다.

    같은 depth 안에서의 y좌표는 barycenter 1-pass(부모 태그들의 y 평균 순으로
    정렬)로 정해서, 같은 계통끼리는 가까이 모이고 선이 덜 꼬이게 한다.
    reference_edges에 없거나 root에서 못 닿는 태그(참조 정보가 없는 경우)는
    맨 오른쪽 별도 칸에 모아, 순서를 아는 태그들의 배치를 방해하지 않게 한다
    — 단, same_site_groups로 그 태그가 속한 지점을 알 수 있으면(아래 참고)
    그 예외다.

    same_site_groups(신규, 선택)를 주면, reference_edges 자체엔 없는 태그(예:
    밸브 개도 V2/V4 — REFERENCE_NETWORK_EDGES는 지점 간 연결만 담아서 밸브는
    노드로도 없음)라도 같은 지점 그룹의 다른 멤버가 depth를 가지고 있으면 그
    depth를 그대로 물려받는다. 이게 없으면 이런 태그는 무조건 맨 오른쪽 orphan
    칸으로 밀려나서, same_site_groups가 그어주는 "같은 지점" 굵은 선이 화면을
    가로지르는 긴 대각선이 돼버린다(그룹의 다른 멤버는 원래 자리에, 이 태그만
    엉뚱하게 먼 곳에 있으므로).

    root(상류 시작점: 들어오는 화살표가 없는 노드)가 하나도 없으면(예: 순환
    관계뿐이거나 reference_edges가 all_targets와 전혀 안 겹치면) None을 반환해서
    호출부가 spring_layout으로 대체하게 한다.
    """
    import networkx as nx

    node_set = set(all_targets)
    ref_graph = nx.DiGraph()
    ref_graph.add_nodes_from(all_targets)
    for a, b in reference_edges:
        if a in node_set and b in node_set:
            ref_graph.add_edge(a, b)

    roots = [n for n in ref_graph.nodes if ref_graph.in_degree(n) == 0 and ref_graph.out_degree(n) > 0]
    if not roots:
        return None

    depth: dict[str, int] = {}
    queue = list(roots)
    for r in roots:
        depth[r] = 0
    qi = 0
    while qi < len(queue):
        node = queue[qi]
        qi += 1
        for nxt in ref_graph.successors(node):
            if nxt not in depth:
                depth[nxt] = depth[node] + 1
                queue.append(nxt)

    if same_site_groups:
        for group in same_site_groups:
            known = [g for g in group if g in depth]
            if not known:
                continue
            anchor_depth = min(depth[g] for g in known)
            for g in group:
                if g in node_set and g not in depth:
                    depth[g] = anchor_depth

    reachable_max = max(depth.values(), default=0)
    orphan_depth = reachable_max + 2  # 한 칸 띄워서 "관계를 모르는 태그"임을 시각적으로 구분
    for t in all_targets:
        depth.setdefault(t, orphan_depth)

    by_depth: dict[int, list[str]] = {}
    for t in all_targets:
        by_depth.setdefault(depth[t], []).append(t)

    y_of: dict[str, float] = {}
    pos: dict[str, tuple[float, float]] = {}
    for d in sorted(by_depth):
        nodes_here = by_depth[d]
        if d == 0 or d == orphan_depth:
            ordered = nodes_here  # 시작점/고아 태그는 원래 순서 그대로
        else:
            def _barycenter(n: str) -> float:
                parents = [p for p in ref_graph.predecessors(n) if p in y_of]
                return sum(y_of[p] for p in parents) / len(parents) if parents else 0.0

            ordered = sorted(nodes_here, key=_barycenter)
        n = len(ordered)
        for i, node in enumerate(ordered):
            y = i - (n - 1) / 2  # 세로 가운데 정렬
            y_of[node] = y
            pos[node] = (float(d), float(y))
    return pos


def plot_network_graph(
    ccf_summary: pd.DataFrame, all_targets: list[str], out_dir: Path,
    reference_edges: list[tuple[str, str]] | None = None,
    label_map: dict[str, str] | None = None,
    same_site_groups: list[list[str]] | None = None,
) -> Path | None:
    """cross_correlation_pairs() 결과를 방향 그래프로 그려서, "관망이 이렇게
    연결돼 있을 것이다"라는 가정이 아니라 데이터에서 실측된 연결 관계를
    보여준다.

    - lag가 0이 아닌 쌍(진짜 선행/후행이 잡힌 경우)은 빨간 화살표로
      "선행 -> 후행"을 표시한다. 실측 예(analysis/GU_db_noq8): `P_GunS`가
      `P_Ham`/`Q4`/`Q7`을 5분 선행 — 정수장 압력이 하류 배수지/유량에 몇 분
      뒤 반영된다는 도메인 지식과 일치했다.
    - lag=0(동시)인 쌍은 회색 실선으로만 표시한다 — 5분 해상도로는 방향을
      못 잡을 만큼 전파가 빠르다는 뜻이지, 연결이 없다는 뜻이 아니다.
    - cross_correlation_pairs()의 상관 임계값을 못 넘어 어떤 태그와도 선이
      없는 target은 흰 속으로 혼자 떨어져 나온다 — 그것도 정보다(이 태그가
      나머지 관망과 통계적으로 독립적으로 움직인다는 뜻).
    - 노드 색은 taglist.classify_quantity()로 구분한 물리량 종류(유량/압력/
      수위)다 — 태그명 접두문자(Q/O=유량, P=압력, H=수위) 규칙을 그대로
      쓴다. 압력 노드가 유량 노드를 선행하는 관계는 "상류 압력 변화가
      하류 유량에 반영된다"는 식으로 물리적으로 해석하기 쉬워진다.

    reference_edges(신규, 선택)를 주면 검정 점선으로 같이 그린다 —
    taglist.REFERENCE_NETWORK_EDGES(사용자가 제공한 실측 관망도)처럼 "실제로
    이렇게 연결돼 있다고 알려진" 관계를 CCF가 데이터에서 찾아낸 관계 위에
    겹쳐서, 서로 얼마나 맞아떨어지는지(또는 안 맞는지) 바로 비교할 수 있게
    한다. 두 지점이 검정 점선(실측 연결)과 빨간/회색 선(CCF 검출) 둘 다로
    이어져 있으면 서로 검증된 것이고, 점선만 있으면 "실제로는 연결돼 있지만
    5분 해상도 CCF로는 못 잡음"(예: 오식도배수지처럼 저수조가 완충 작용을
    해서 상관이 약해지는 경우), 반대로 빨간/회색 선만 있으면 "CCF는 찾았지만
    실측 관망도에는 없는 관계"(우연한 상관일 수 있어 더 낮은 신뢰도 —
    실측 예: `H3`~`P5`, 관망도상 서로 다른 가지라 근거가 약함)라는 뜻이다.

    reference_edges가 있으면 노드 배치도 CCF 상관(spring_layout) 대신 실제
    상류->하류 순서(_hierarchical_positions, x축=관망 상 깊이)를 우선한다 —
    예를 들어 `Q7`(유입)->`H7`(수위)->`O7`(유출)이 실제 순서 그대로 왼쪽에서
    오른쪽으로 나란히 보인다. CCF로 고립된(흰 속) 노드도 여기서는 랜덤하게
    안 흩어지고 관망도 상 제자리(깊이)에 남는다 — "통계적으로는 안 엮였지만
    실제로는 이 위치에 있는 태그"라는 걸 위치만으로도 알 수 있다.

    label_map(신규, 선택)을 주면 노드에 변수명(var_name) 대신 그 값(보통
    tag_name — 실제 태그 코드, 예: `891-365-FRI-8950`)을 표시한다. 그래프
    내부 로직(연결·색·위치 판단)은 여전히 var_name 기준으로 동작한다 —
    label_map은 화면에 보이는 글자만 바꾼다. 매핑에 없는 노드는 var_name을
    그대로 쓴다.

    same_site_groups(신규, 선택)를 주면 같은 지점(site)에 있는 태그끼리
    (예: 정수장의 유량/압력, 오식도배수지의 유입유량-수위-유출유량) 굵은
    회색 실선으로 이어서 시각적으로 "묶는다" — taglist.REFERENCE_SAME_SITE_GROUPS
    참고. reference_edges(지점 A -> 지점 B, 물이 흐르는 방향)와는 성격이
    다른 관계라서(같은 위치에서 같이 재는 값들이지, 물이 그 사이로 흐르는
    게 아니다) 선을 구분한다 — 점선(지점 간 흐름)보다 굵은 실선(같은 지점).

    상관관계일 뿐 인과관계 증명이 아니고, 실제 관로도(분기점·관경 등)가
    아니라 통계적으로 추정한 결과라는 한계는 그대로 남는다 —
    cross_correlation_pairs() docstring 참고.

    ccf_summary는 보통 이 함수의 all_targets보다 넓은 범위(data.feature_cols
    전체 — target이 아닌 밸브 개도 등도 포함)에서 계산된 결과이므로, all_targets
    (이 그래프의 노드 집합)에 없는 변수가 낀 쌍은 조용히 건너뛴다(ref_pairs/
    same_site_pairs와 같은 방식) — 안 그러면 그 변수의 좌표(pos)가 없어서
    그리다 KeyError가 난다.
    """
    if len(ccf_summary) == 0 and not reference_edges:
        return None
    import networkx as nx

    plt = _plt()
    node_set = set(all_targets)
    graph = nx.Graph()
    graph.add_nodes_from(all_targets)
    directed_edges: list[tuple[str, str, float, float]] = []  # (선행, 후행, lag분, ccf)
    undirected_edges: list[tuple[str, str, float]] = []  # (a, b, ccf)
    for _, row in ccf_summary.iterrows():
        a, b, lag, ccf = row["a"], row["b"], row["best_lag_minutes"], row["best_ccf"]
        if a not in node_set or b not in node_set:
            # ccf_summary는 cross_correlation_pairs()가 data.feature_cols(전체
            # feature) 기준 상관행렬로 찾은 쌍이라, target이 아닌 변수(예: 밸브
            # 개도 V2/V4, 또는 role이 target->variable로 바뀐 P1 등)가 섞여
            # 나올 수 있다 — 이 그래프의 노드 집합(all_targets)엔 없는 변수라
            # 조용히 건너뛴다(안 그러면 아래 pos[a] 조회에서 KeyError).
            continue
        graph.add_edge(a, b, weight=abs(ccf))
        if lag > 0:
            directed_edges.append((a, b, lag, ccf))
        elif lag < 0:
            directed_edges.append((b, a, -lag, ccf))
        else:
            undirected_edges.append((a, b, ccf))

    ref_pairs: list[tuple[str, str]] = []
    if reference_edges:
        for a, b in reference_edges:
            if a in node_set and b in node_set:
                ref_pairs.append((a, b))
                if not graph.has_edge(a, b):
                    # 레이아웃에도 약하게 반영 — 실측 연결인데 CCF로는 안 잡힌 쌍도
                    # 너무 멀리 밀려나지 않게(비교하기 좋게) 최소한의 인력을 준다.
                    graph.add_edge(a, b, weight=0.3)

    # 같은 지점(site) 안의 태그끼리(유량-압력, 유입유량-수위-유출유량 등)는
    # ref_pairs(지점 간 흐름)보다 더 강하게 묶는다 — 레이아웃에도 더 큰
    # weight를 줘서 spring_layout 대체 경로에서 서로 더 가깝게 붙는다.
    same_site_pairs: list[tuple[str, str]] = []
    if same_site_groups:
        for group in same_site_groups:
            present = [g for g in group if g in node_set]
            for a, b in zip(present, present[1:]):
                same_site_pairs.append((a, b))
                if not graph.has_edge(a, b):
                    graph.add_edge(a, b, weight=0.6)

    # reference_edges가 있으면 실제 상류->하류 순서(depth)를 x좌표로 쓰는
    # 계층형 레이아웃을 우선한다 — 예: Q7(유입)->H7(수위)->O7(유출)이 그 순서
    # 그대로 나란히 보이게. 참조 정보가 없거나(reference_edges=None) 계층을
    # 못 구하면(root가 없음) spring_layout으로 대체한다 — 그때는 CCF 상관이
    # 강한 쌍일수록 서로 가깝게, 연결 없는 target은 밀려나서 자연히 떨어져
    # 보인다. seed 고정 — 재실행해도 같은 그림이 나오게.
    pos = _hierarchical_positions(all_targets, reference_edges, same_site_groups) if reference_edges else None
    hierarchical = pos is not None
    if pos is None:
        pos = nx.spring_layout(graph, seed=42, k=1.4 / max(len(all_targets) ** 0.5, 1), weight="weight")

    if hierarchical:
        depths = [xy[0] for xy in pos.values()]
        ys = [xy[1] for xy in pos.values()]
        width = max(8.0, 2.2 * (max(depths) - min(depths) + 1))
        height = max(8.0, 1.1 * (max(ys) - min(ys) + 1))
        fig, ax = plt.subplots(figsize=(width, height))
    else:
        fig, ax = plt.subplots(figsize=(10, 10))
    for a, b in ref_pairs:
        ax.plot(
            [pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
            color="black", linestyle=":", linewidth=1.3, alpha=0.55, zorder=0,
        )
    for a, b in same_site_pairs:
        ax.plot(
            [pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
            color="dimgray", linestyle="-", linewidth=2.4, alpha=0.75, zorder=0,
        )

    for a, b, ccf in undirected_edges:
        x = [pos[a][0], pos[b][0]]
        y = [pos[a][1], pos[b][1]]
        ax.plot(x, y, color="gray", alpha=min(abs(ccf), 1.0), linewidth=0.8 + 2.2 * abs(ccf), zorder=1)

    for a, b, lag, ccf in directed_edges:
        ax.annotate(
            "", xy=pos[b], xytext=pos[a],
            arrowprops=dict(
                arrowstyle="-|>", color="crimson", alpha=min(abs(ccf), 1.0), lw=1 + 3 * abs(ccf),
                shrinkA=26, shrinkB=26, connectionstyle="arc3,rad=0.08",
            ),
            zorder=2,
        )
        mid = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2)
        ax.annotate(f"{lag:.0f}분", mid, fontsize=7, color="crimson", ha="center", zorder=2)

    # 노드 색은 물리량 종류(유량/압력/수위)로 구분한다 — 예를 들어 압력 노드가
    # 유량 노드를 선행하는 관계는 "상류 압력 변화가 하류 유량에 반영된다"는
    # 식으로 물리적으로 해석하기 쉬워진다. 연결 여부(고립인지)는 색이 아니라
    # 채움 여부로 따로 표시해서, 두 정보(종류/연결)를 동시에 보여준다. 네모
    # 박스(bbox)로 그리는 이유는 tag_name(label_map)이 var_name보다 훨씬 긴
    # 문자열이라(예: "740-914-PRI-1009") 고정 크기 원형 마커 안에는
    # 안 들어가기 때문이다 — bbox는 글자 길이에 맞춰 폭이 자동으로 늘어난다.
    quantity_colors = {"유량": "steelblue", "압력": "darkorange", "수위": "seagreen", "기타": "gray"}
    connected = {t for a, b, _, _ in directed_edges for t in (a, b)} | {t for a, b, _ in undirected_edges for t in (a, b)}
    for t in all_targets:
        x, y = pos[t]
        color = quantity_colors[classify_quantity(t)]
        label = label_map.get(t, t) if label_map else t
        if t in connected:
            box = dict(boxstyle="square,pad=0.35", facecolor=color, edgecolor="black", linewidth=0.8)
            text_color = "white"
        else:
            box = dict(boxstyle="square,pad=0.35", facecolor="white", edgecolor=color, linewidth=2.0)
            text_color = color
        ax.text(x, y, label, ha="center", va="center", fontsize=7, color=text_color, zorder=4, bbox=box)

    from matplotlib.lines import Line2D

    quantities_present = sorted({classify_quantity(t) for t in all_targets}, key=lambda q: (q == "기타", q))
    legend_elems = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor=quantity_colors[q], markersize=12, label=q)
        for q in quantities_present
    ]
    legend_elems.append(
        Line2D([0], [0], marker="s", color="w", markerfacecolor="white", markeredgecolor="black",
               markeredgewidth=1.5, markersize=12, label="연결 없음(고립)")
    )
    if ref_pairs:
        legend_elems.append(Line2D([0], [0], color="black", linestyle=":", linewidth=1.5, label="실측 관망도 기준 연결(지점 간)"))
    if same_site_pairs:
        legend_elems.append(Line2D([0], [0], color="dimgray", linestyle="-", linewidth=2.4, label="같은 지점 내 태그 관계"))
    # loc="upper left" 등 축 내부 자리는 실제 데이터(특히 계층형 레이아웃의
    # depth=0 열처럼 y가 넓게 퍼진 경우)와 겹쳐서 노드를 가릴 수 있다(실측:
    # P_Ham이 범례 박스 뒤에 가려짐) — 축 바깥(오른쪽 여백)에 고정해서
    # 어떤 레이아웃이 나오든 노드를 가리지 않게 한다. savefig의
    # bbox_inches="tight"가 잘리지 않게 캔버스를 넓혀준다.
    ax.legend(
        handles=legend_elems, loc="upper left", bbox_to_anchor=(1.01, 1.0),
        fontsize=8, framealpha=0.9, title="노드 색=물리량, 흰 속=고립",
    )

    title = "교차상관 기반 추정 관망 구조 (빨간 화살표=선행→후행, 회색 선=동시 상관)"
    if ref_pairs:
        title += "\n검정 점선=지점 간 연결, 굵은 회색 실선=같은 지점 내 태그 관계 (둘 다 실측 관망도 기준)"
    ax.set_title(title)
    ax.axis("off")
    # tight_layout()은 축 내부 기준으로만 여백을 맞춰서 축 바깥에 둔 범례와
    # 충돌 경고가 난다 — savefig의 bbox_inches="tight"가 범례까지 포함해서
    # 캔버스를 다시 계산해주므로 여기선 생략한다.
    path = out_dir / "network_graph.png"
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_correlation_heatmap(corr: pd.DataFrame, out_dir: Path) -> Path:
    plt = _plt()
    n = len(corr.columns)
    fig, ax = plt.subplots(figsize=(0.45 * n + 2, 0.45 * n + 2))
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(n))
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticks(range(n))
    ax.set_yticklabels(corr.columns)
    fig.colorbar(im, ax=ax, fraction=0.046)
    ax.set_title("feature 간 상관관계")
    fig.tight_layout()
    path = out_dir / "feature_correlation.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def _valve_bin_boxplot(
    ax, valve: pd.Series, value: pd.Series, n_bins: int,
) -> int | None:
    """밸브 개도(valve)를 분위수(pd.qcut) 기준 n_bins개 구간으로 나눠, 구간별
    value 분포를 ax에 박스플롯으로 그린다. plot_valve_flow_distribution()과
    plot_valve_transfer_ratio()가 공유하는 그리기 로직 — "밸브 개도 구간별로
    뭔가의 분포를 본다"는 틀은 같고 그 "뭔가"(유량 절대값 vs 전달률)만
    다르기 때문이다.

    균등 폭 구간(pd.cut) 대신 분위수 구간을 쓰는 이유: 밸브가 특정 개도
    근처에 몰려 있으면(예: 거의 항상 열림, valve_control_summary 참고)
    균등 폭 구간은 그 구간에 데이터가 텅 비거나 한쪽에 쏠려서 박스플롯이
    의미 없어질 수 있다.

    구간을 2개 이상 못 나누면(예: 밸브가 거의 상수) None을 돌려준다 — 그
    경우 호출부가 그림 자체를 포기해야 한다(빈 그림을 만들지 않기 위함).
    성공하면 실제로 나눠진 구간 수를 돌려준다(duplicates="drop"로 인해
    n_bins보다 적을 수 있다).
    """
    try:
        bins = pd.qcut(valve, q=n_bins, duplicates="drop")
    except ValueError:
        return None
    n_actual_bins = bins.cat.categories.size
    if n_actual_bins < 2:
        return None
    grouped = [value[bins == cat].to_numpy() for cat in bins.cat.categories]
    labels = [f"{cat.left:.1f}~{cat.right:.1f}" for cat in bins.cat.categories]
    ax.boxplot(grouped, labels=labels, showfliers=False)
    return n_actual_bins


def plot_valve_flow_distribution(
    data: AnalysisData, valve_col: str, flow_col: str, out_dir: Path, n_bins: int = 10,
) -> Path | None:
    """밸브 개도(valve_col)를 n_bins개 구간으로 나눠서, 각 구간에서 같은
    지점 유량(flow_col)이 어떻게 분포하는지 박스플롯으로 보여준다 — "밸브를
    이만큼 열면 유량이 대략 이 범위"라는 감을 직접 눈으로 확인하는 용도.
    valve_control_summary()의 상시개방/제어 판별이나 ccf_for_pairs()의
    (밸브,유량) 동시상관 하나로는 "관계가 있다/없다" 정도만 알 수 있지,
    그 관계의 형태(선형인지, 특정 구간에서만 반응하는지, 개도가 낮을 때는
    유량이 안정적이다가 높을 때만 흩어지는지 등)는 안 보인다 — 이 그림이
    그 형태를 보여준다.

    주의: 이 그림은 유량 "절대값"을 본다 — 정수장이 그 시점에 총 얼마나
    송수하고 있었는지와 뒤섞인다(정수장 총 송수량 자체가 크면 이 지점
    유량도 따라 커지는 게 정상이라, 밸브의 순수한 "분배 조절" 효과와
    "정수장 총량 변화" 효과가 이 그림만으론 안 구분된다) — 그 구분이
    필요하면 plot_valve_transfer_ratio()를 쓸 것.

    data.raw_grid(ffill 채우기 전 원본)를 쓴다 — valve_control_summary와
    같은 이유로, ffill이 만드는 "안 바뀐 것처럼 보이는" 구간이 분포를
    왜곡하는 걸 막는다.

    두 컬럼 다 data.raw_grid에 없거나, 유효한(둘 다 결측 아닌) 행이 하나도
    없거나, 밸브 값이 거의 다 같아서 구간을 2개 이상 못 나누면(예: 상시
    고정 밸브) None을 돌려준다 — 그 경우 이 그림 자체가 의미가 없다.
    """
    if valve_col not in data.raw_grid.columns or flow_col not in data.raw_grid.columns:
        return None
    df = data.raw_grid[[valve_col, flow_col]].dropna()
    if len(df) == 0:
        return None

    plt = _plt()
    fig, ax = plt.subplots(figsize=(10, 5))
    n_actual_bins = _valve_bin_boxplot(ax, df[valve_col], df[flow_col], n_bins)
    if n_actual_bins is None:
        plt.close(fig)
        return None
    fig.set_size_inches(max(8, 1.1 * n_actual_bins), 5)
    ax.set_xlabel(f"{valve_col} 개도 구간 (분위수 기준)")
    ax.set_ylabel(f"{flow_col} 유량")
    ax.set_title(f"{valve_col} 개도별 {flow_col} 유량 분포 (구간 {n_actual_bins}개, 극단치는 표시 생략)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    path = out_dir / f"valve_flow_distribution_{valve_col}.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_valve_transfer_ratio(
    data: AnalysisData,
    valve_col: str,
    numerator_col: str,
    denominator_col: str,
    out_dir: Path,
    n_bins: int = 10,
    ratio_clip_quantiles: tuple[float, float] = (0.01, 0.99),
) -> Path | None:
    """밸브 개도(valve_col) 구간별로, 정수장 총 송수유량(denominator_col,
    보통 Q_GunS) 대비 그 밸브가 있는 지점 유량(numerator_col, 예: V2 -> Q2,
    V4 -> Q4)의 비율("전달률" = numerator/denominator)이 어떻게 분포하는지
    박스플롯으로 보여준다.

    plot_valve_flow_distribution()과의 차이: 그쪽은 유량 절대값이라 정수장
    총 송수량 변화와 뒤섞이지만, 비율(전달률)을 보면 총량과 무관하게
    "이 밸브가 전체 송수량 중 이 지점으로 얼마를 돌리고 있는가"만 남는다
    — 2026-09-11, 사용자 요청: 개도별 유량 절대값 대신 이 전달률을 보고
    싶다고 확인.

    denominator_col이 0에 가까우면 비율이 발산하므로, denominator가
    ratio_clip_quantiles 하한 분위수보다 작은 행("정수장이 사실상 멈춰있던
    시점")은 제외한다. 계산된 비율 자체도 ratio_clip_quantiles로 clip해서
    극단치(순간적인 유량계 오차로 비율이 튀는 경우)가 박스플롯 스케일을
    망가뜨리지 않게 한다 — analyze.clip_series와 같은 방식.

    세 컬럼 중 하나라도 data.raw_grid에 없거나, 유효한 행이 하나도 없거나,
    밸브 값이 거의 다 같아서 구간을 2개 이상 못 나누면 None을 돌려준다.
    """
    cols = [valve_col, numerator_col, denominator_col]
    if any(c not in data.raw_grid.columns for c in cols):
        return None
    df = data.raw_grid[cols].dropna()
    if len(df) == 0:
        return None

    denom_floor = df[denominator_col].quantile(ratio_clip_quantiles[0])
    df = df[df[denominator_col] > max(denom_floor, 0.0)]
    if len(df) == 0:
        return None

    ratio = clip_series(df[numerator_col] / df[denominator_col], *ratio_clip_quantiles)

    plt = _plt()
    fig, ax = plt.subplots(figsize=(10, 5))
    n_actual_bins = _valve_bin_boxplot(ax, df[valve_col], ratio, n_bins)
    if n_actual_bins is None:
        plt.close(fig)
        return None
    fig.set_size_inches(max(8, 1.1 * n_actual_bins), 5)
    ax.set_xlabel(f"{valve_col} 개도 구간 (분위수 기준)")
    ax.set_ylabel(f"{numerator_col} / {denominator_col} (전달률)")
    ax.set_title(f"{valve_col} 개도별 {numerator_col}/{denominator_col} 전달률 분포 (구간 {n_actual_bins}개)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    path = out_dir / f"valve_transfer_ratio_{valve_col}.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# 오케스트레이션
# --------------------------------------------------------------------------

@dataclasses.dataclass
class AnalysisResult:
    sheet: str
    out_dir: Path
    coverage: dict
    error: str | None = None  # 실패한 시트는 여기에 에러 메시지, coverage는 빈 dict


def _maybe_clean(out_dir: Path, clean: bool) -> None:
    """clean=True이고 out_dir가 이미 있으면 통째로 지운다.

    예전 실행에서 만들어졌지만 지금은 더 이상 생성되지 않는 파일(예: 컬럼/옵션이
    바뀌어 이름이 달라진 플롯)이 새 결과와 섞여 남는 걸 막는다 — 실제로
    autocorrelation.png 하나였던 게 태그별 autocorrelation_<태그>.png 여러 개로
    바뀌었을 때, --clean 없이 재실행하면 옛 파일이 새 파일들과 함께 폴더에
    남아 있었다. run_and_save에서 분리해 파일시스템 부수효과만 가볍게
    단위테스트할 수 있게 했다.
    """
    if clean and out_dir.exists():
        print(f"[0/5] 기존 분석 결과 삭제 중: {out_dir} ...")
        shutil.rmtree(out_dir)


def run_and_save(
    cfg: Config,
    out_dir: str | Path | None = None,
    make_plots: bool = True,
    clean: bool = False,
    skip_seasonality: bool = False,
    skip_ccf: bool = False,
    acf_max_lag_minutes: int = 2880,
    ccf_max_lag_minutes: int = 120,
    ccf_corr_threshold: float = 0.5,
    ccf_max_pairs: int = 40,
    path_lag_targets: list[str] | None = None,
    path_lag_max_minutes: int = 4320,
    skip_valve_analysis: bool = False,
    valve_downstream_max_lag_minutes: int = 4320,
    recent_days: int = 7,
) -> AnalysisResult:
    # 학습 산출물(cfg.output.dir, 기본 runs/<sheet>)과 섞이지 않는 전용 폴더
    # (기본 analysis/<sheet>)에 저장한다.
    out_dir = Path(out_dir) if out_dir else Path(cfg.output.analysis_dir.format(sheet=cfg.data.sheet))
    _maybe_clean(out_dir, clean)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] 데이터 로딩 중 (source={cfg.data.source}) ...")
    data = load_full_raw(cfg)

    print("[2/5] 기본 통계 계산 중 ...")
    coverage = coverage_summary(data)
    missing = missing_by_column(data)
    gaps = gap_report(data.valid_mask, cfg.data.freq)
    stuck = stuck_value_report(data, cfg.data.freq)
    stats = descriptive_stats(data)
    extremes = extreme_value_flags(stats)
    autocorr = autocorrelation_table(data, robust_lower_q=cfg.outlier.lower_quantile, robust_upper_q=cfg.outlier.upper_quantile)
    hourly = hourly_profile(data)
    corr = correlation_matrix(data)
    dupes = near_duplicate_features(corr)

    missing.to_csv(out_dir / "missing_by_column.csv", index=False, encoding="utf-8-sig")
    gaps.to_csv(out_dir / "gaps.csv", index=False, encoding="utf-8-sig")
    stuck.to_csv(out_dir / "stuck_values.csv", index=False, encoding="utf-8-sig")
    stats.to_csv(out_dir / "descriptive_stats.csv", index=False, encoding="utf-8-sig")
    extremes.to_csv(out_dir / "extreme_value_flags.csv", index=False, encoding="utf-8-sig")
    autocorr.to_csv(out_dir / "autocorrelation.csv", index=False, encoding="utf-8-sig")
    hourly.to_csv(out_dir / "hourly_profile.csv", index=False, encoding="utf-8-sig")
    corr.to_csv(out_dir / "feature_correlation.csv", encoding="utf-8-sig")
    dupes.to_csv(out_dir / "near_duplicate_features.csv", index=False, encoding="utf-8-sig")

    weekday = monthly = acf = periodicities = None
    if skip_seasonality:
        print("[3/5] 계절성/주기성 분석 생략 (--skip-seasonality)")
    else:
        print("[3/5] 계절성/주기성 분석 중 (요일별/월별 패턴, 자기상관 곡선) ...")
        weekday = weekday_profile(data)
        monthly = monthly_profile(data)
        acf = acf_curve(
            data, cfg.data.freq, max_lag_minutes=acf_max_lag_minutes,
            robust_lower_q=cfg.outlier.lower_quantile, robust_upper_q=cfg.outlier.upper_quantile,
        )
        periodicities = detect_periodicities(acf)
        weekday.to_csv(out_dir / "weekday_profile.csv", index=False, encoding="utf-8-sig")
        monthly.to_csv(out_dir / "monthly_profile.csv", index=False, encoding="utf-8-sig")
        acf.to_csv(out_dir / "acf_curve.csv", index=False, encoding="utf-8-sig")
        periodicities.to_csv(out_dir / "periodicities.csv", index=False, encoding="utf-8-sig")

    ccf_summary, ccf_curves = pd.DataFrame(), {}
    if skip_ccf:
        print("[4/5] 교차상관(CCF)/지연시간 분석 생략 (--skip-ccf)")
    else:
        print(f"[4/5] 교차상관(CCF)/지연시간 분석 중 (|corr|>={ccf_corr_threshold} 쌍 최대 {ccf_max_pairs}개) ...")
        ccf_summary, ccf_curves = cross_correlation_pairs(
            data, corr, cfg.data.freq, corr_threshold=ccf_corr_threshold,
            max_lag_minutes=ccf_max_lag_minutes, max_pairs=ccf_max_pairs,
            robust_lower_q=cfg.outlier.lower_quantile, robust_upper_q=cfg.outlier.upper_quantile,
        )
        if len(ccf_summary):
            ccf_summary.to_csv(out_dir / "cross_correlation_pairs.csv", index=False, encoding="utf-8-sig")

    # 경로 지연시간(path lag) 재추정 — cross_correlation_pairs()의 corr_threshold
    # 필터를 거치지 않고, 관망도 상 target의 모든 상류 조상과 target을 직접
    # 쌍으로 놓고 CCF를 잰다. 예: --path-lag-target Q7이면 정수장(Q_GunS/P_GunS)
    # 등에서 오식도배수지 유입(Q7)까지 실제로 몇 분/시간 지연되는지를 직접
    # 잰다 — "제어 후 언제 효과가 나타나는가"를 알아야 하는 3단계(부족 시
    # 정수장 유량/압력 추천)의 실행 가능 리드타임을 정하는 데 쓰인다.
    path_lag_results: dict[str, pd.DataFrame] = {}
    path_lag_curves: dict[str, dict[tuple[str, str], pd.DataFrame]] = {}
    if path_lag_targets:
        print(f"[4b/5] 경로 지연시간 재추정 중 (target={path_lag_targets}, max_lag={path_lag_max_minutes}분) ...")
        for target in path_lag_targets:
            pairs = ancestor_pairs(REFERENCE_NETWORK_EDGES, target)
            if not pairs:
                print(f"  - {target}: REFERENCE_NETWORK_EDGES에 조상이 없음(고립 노드) - 건너뜀")
                continue
            summary, curves = ccf_for_pairs(
                data, cfg.data.freq, pairs, max_lag_minutes=path_lag_max_minutes,
                robust_lower_q=cfg.outlier.lower_quantile, robust_upper_q=cfg.outlier.upper_quantile,
            )
            path_lag_results[target] = summary
            path_lag_curves[target] = curves
            if len(summary):
                summary.to_csv(out_dir / f"path_lag_{target}.csv", index=False, encoding="utf-8-sig")

    # 밸브(제어 변수 — 예: V2=지방산단밸브 개도, V4=국가산단밸브 개도) 분석.
    # 대상은 tag_name의 계측 코드가 POI(taglist.is_valve_tag)인 태그로 자동
    # 판별한다 — role(taglist 엑셀 "비고" 컬럼, target/variable)로 판별하지
    # 않는 이유: role은 "모델 target으로 쓰는지"를 나타내는 모델링 상의
    # 구분이라, role을 깜빡 잘못 표기해도(또는 나중에 밸브를 target으로 쓰게
    # 바뀌어도) 밸브 분석은 태그 자체의 정체성(POI 코드)만 보고 켜지는 게
    # 더 안전하다 — is_valve_tag() docstring 참고. --skip-valve-analysis가
    # 없는 한 자동으로 돈다. 세 가지를 본다:
    #  1. 상시개방/고정인지 실제로 제어되는지 (valve_control_summary)
    #  2. 밸브와 같은 지점 유량/압력의 관계 (REFERENCE_SAME_SITE_GROUPS로 같은
    #     그룹에 있는 멤버와 CCF — 밸브가 원인이면 거의 동시~수 분 내로 반영될 것)
    #  3. 밸브가 하류 배수지 수위에 주는 영향 (밸브가 속한 지점의 관망도
    #     대표 노드(_site_anchor_for_valve)를 거쳐 descendant_pairs로 하류
    #     "수위" 변수만 골라 CCF — path_lag 분석에서 H7/H3 같은 수위는 반영에
    #     수 시간이 걸리는 걸 이미 확인했으므로 max_lag을 넉넉하게 잡는다)
    control_cols = [t.var_name for t in data.tags if is_valve_tag(t.tag_name)]
    valve_summary = pd.DataFrame()
    valve_flow_partner: dict[str, str] = {}  # 밸브 -> 같은 지점 유량 태그 (plot_valve_flow_distribution용)
    valve_site_summary, valve_site_curves = pd.DataFrame(), {}
    valve_level_summary, valve_level_curves = pd.DataFrame(), {}
    if control_cols and skip_valve_analysis:
        print(f"[4c/5] 밸브 분석 생략 (--skip-valve-analysis, 대상: {control_cols})")
    elif control_cols:
        print(f"[4c/5] 밸브(제어 변수) 분석 중 (대상: {control_cols}) ...")
        valve_summary = valve_control_summary(data, control_cols)
        valve_summary.to_csv(out_dir / "valve_control_summary.csv", index=False, encoding="utf-8-sig")

        site_pairs: list[tuple[str, str]] = []
        level_pairs: list[tuple[str, str]] = []
        for v in control_cols:
            group = next((g for g in REFERENCE_SAME_SITE_GROUPS if v in g), None)
            if group:
                site_pairs += [(v, m) for m in group if m != v]
                flow_partner = next((m for m in group if m != v and classify_quantity(m) == "유량"), None)
                if flow_partner:
                    valve_flow_partner[v] = flow_partner
            anchor = _site_anchor_for_valve(v, REFERENCE_SAME_SITE_GROUPS, REFERENCE_NETWORK_EDGES)
            if anchor:
                level_pairs += [
                    (v, d) for _, d in descendant_pairs(REFERENCE_NETWORK_EDGES, anchor)
                    if classify_quantity(d) == "수위"
                ]
        if site_pairs:
            valve_site_summary, valve_site_curves = ccf_for_pairs(
                data, cfg.data.freq, site_pairs, max_lag_minutes=ccf_max_lag_minutes,
                robust_lower_q=cfg.outlier.lower_quantile, robust_upper_q=cfg.outlier.upper_quantile,
            )
            if len(valve_site_summary):
                valve_site_summary.to_csv(out_dir / "valve_site_relation.csv", index=False, encoding="utf-8-sig")
        if level_pairs:
            valve_level_summary, valve_level_curves = ccf_for_pairs(
                data, cfg.data.freq, level_pairs, max_lag_minutes=valve_downstream_max_lag_minutes,
                robust_lower_q=cfg.outlier.lower_quantile, robust_upper_q=cfg.outlier.upper_quantile,
            )
            if len(valve_level_summary):
                valve_level_summary.to_csv(out_dir / "valve_downstream_level_relation.csv", index=False, encoding="utf-8-sig")

    plot_paths: list[Path] = []
    if make_plots:
        print("[5/5] 그래프 저장 중 ...")
        clip_quantiles = (cfg.outlier.lower_quantile, cfg.outlier.upper_quantile)
        plot_paths += plot_target_overview(data, out_dir, clip_quantiles=clip_quantiles, recent_days=recent_days)
        plot_paths.append(plot_gap_timeline(gaps, data, out_dir))
        plot_paths += plot_autocorrelation(autocorr, out_dir)
        plot_paths.append(plot_correlation_heatmap(corr, out_dir))
        if weekday is not None:
            plot_paths += plot_seasonal_profiles(data, hourly, weekday, monthly, out_dir)
            plot_paths += plot_acf_curve(acf, periodicities, out_dir)
        if len(ccf_summary):
            ccf_plot = plot_top_ccf_pairs(ccf_summary, ccf_curves, out_dir)
            if ccf_plot:
                plot_paths.append(ccf_plot)
            tag_name_map = {t.var_name: short_tag_name(t.tag_name) for t in data.tags}
            network_plot = plot_network_graph(
                ccf_summary, analyzed_vars(data), out_dir,
                reference_edges=REFERENCE_NETWORK_EDGES, label_map=tag_name_map,
                same_site_groups=REFERENCE_SAME_SITE_GROUPS,
            )
            if network_plot:
                plot_paths.append(network_plot)
        for target, summary in path_lag_results.items():
            if not len(summary):
                continue
            path_lag_plot = plot_top_ccf_pairs(
                summary, path_lag_curves[target], out_dir, top_n=len(summary),
                filename=f"path_lag_{target}.png",
                title=f"{target}까지의 경로 지연시간 (상류 조상 각각 vs {target}, 점선=상관 최대 지연)",
                x_axis_hours=True,
            )
            if path_lag_plot:
                plot_paths.append(path_lag_plot)
        # control_cols(밸브 개도 등)의 timeseries_*.png는 위 plot_target_overview(data, out_dir, ...)
        # 호출에 이미 포함돼 있다 — 그 호출의 cols 기본값이 analyzed_vars(data)라
        # control_cols도 자동으로 그려진다(따로 또 부를 필요 없음).
        if len(valve_site_summary):
            valve_site_plot = plot_top_ccf_pairs(
                valve_site_summary, valve_site_curves, out_dir, top_n=len(valve_site_summary),
                filename="valve_site_relation.png",
                title="밸브 개도 vs 같은 지점 유량/압력 (점선=상관 최대 지연)",
            )
            if valve_site_plot:
                plot_paths.append(valve_site_plot)
        if len(valve_level_summary):
            valve_level_plot = plot_top_ccf_pairs(
                valve_level_summary, valve_level_curves, out_dir, top_n=len(valve_level_summary),
                filename="valve_downstream_level_relation.png",
                title="밸브 개도 vs 하류 배수지 수위 (점선=상관 최대 지연)",
                x_axis_hours=True,
            )
            if valve_level_plot:
                plot_paths.append(valve_level_plot)
        for valve, flow_col in valve_flow_partner.items():
            flow_dist_plot = plot_valve_flow_distribution(data, valve, flow_col, out_dir)
            if flow_dist_plot:
                plot_paths.append(flow_dist_plot)
            # 정수장 총 송수유량(Q_GunS) 대비 이 지점 유량의 "전달률" — 절대
            # 유량 분포(위)만으론 정수장 총량 변화와 밸브의 분배 조절 효과가
            # 안 구분되므로, Q_GunS가 있는 시트(GU)에서는 이 그림도 같이 만든다.
            if "Q_GunS" in data.raw_grid.columns and flow_col != "Q_GunS":
                ratio_plot = plot_valve_transfer_ratio(data, valve, flow_col, "Q_GunS", out_dir)
                if ratio_plot:
                    plot_paths.append(ratio_plot)
    else:
        print("[5/5] 그래프 생략 (make_plots=False)")

    _write_markdown_summary(
        out_dir, cfg, coverage, missing, gaps, stuck, extremes, autocorr, dupes, plot_paths,
        periodicities=periodicities, ccf_summary=ccf_summary, path_lag_results=path_lag_results,
        valve_summary=valve_summary, valve_site_summary=valve_site_summary, valve_level_summary=valve_level_summary,
    )

    print(f"\n분석 결과 저장 위치: {out_dir.resolve()}")
    return AnalysisResult(sheet=cfg.data.sheet, out_dir=out_dir, coverage=coverage)


def run_all_sheets(
    cfg: Config, sheets: list[str] | None = None, make_plots: bool = True, **run_kwargs,
) -> list[AnalysisResult]:
    """태그리스트의 시트(=정수장/배수지 등 단계)마다 분석을 따로 돌려
    analysis/<시트>/ 에 각각 저장한다. 시트 하나가 실패해도(예: 그 단계
    태그의 원본 데이터가 아직 없음) 나머지 시트는 계속 진행하고,
    실패 내용은 analysis/index.md에 같이 남긴다. run_kwargs는 run_and_save에
    그대로 전달된다 (skip_seasonality, skip_ccf, ccf_corr_threshold 등)."""
    sheets = sheets or list_sheets(cfg.data.taglist_path)
    results: list[AnalysisResult] = []
    for sheet in sheets:
        print(f"\n===== [{sheet}] 분석 시작 =====")
        sheet_cfg = dataclasses.replace(cfg, data=dataclasses.replace(cfg.data, sheet=sheet))
        try:
            results.append(run_and_save(sheet_cfg, make_plots=make_plots, **run_kwargs))
        except Exception as e:
            print(f"[{sheet}] 실패: {type(e).__name__}: {e}")
            fallback_dir = Path(cfg.output.analysis_dir.format(sheet=sheet))
            results.append(AnalysisResult(sheet=sheet, out_dir=fallback_dir, coverage={}, error=f"{type(e).__name__}: {e}"))

    index_path = _write_index(cfg, results)
    print(f"\n전체 시트 요약: {index_path.resolve()}")
    return results


def _write_index(cfg: Config, results: list[AnalysisResult]) -> Path:
    index_dir = results[0].out_dir.parent if results else Path(cfg.output.analysis_dir.format(sheet="_")).parent
    index_dir.mkdir(parents=True, exist_ok=True)

    # source(csv/db)별로 다른 파일명을 써서, --source db로 돌린 결과가
    # csv 기반 index.md를 덮어쓰지 않도록 한다 (analysis_dir이 <sheet>_db처럼
    # 시트마다 접미사가 붙어도 그 부모 폴더 analysis/ 는 공유되기 때문).
    index_name = "index.md" if cfg.data.source == "csv" else f"index_{cfg.data.source}.md"

    lines = [
        f"# 시트(단계)별 데이터 분석 요약 — {len(results)}개 (source={cfg.data.source})",
        "", "| sheet | 상태 | 기간 | 유효 비율 | 리포트 |", "|---|---|---|---|---|",
    ]
    for r in results:
        if r.error:
            lines.append(f"| {r.sheet} | ❌ {r.error} | - | - | - |")
        else:
            c = r.coverage
            lines.append(
                f"| {r.sheet} | ✅ | {c['start']} ~ {c['end']} | {c['valid_ratio_%']:.2f}% | "
                f"[{r.out_dir.name}/analysis_report.md]({r.out_dir.name}/analysis_report.md) |"
            )
    index_path = index_dir / index_name
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path


def _write_markdown_summary(
    out_dir: Path, cfg: Config, coverage: dict, missing: pd.DataFrame,
    gaps: pd.DataFrame, stuck: pd.DataFrame, extremes: pd.DataFrame, autocorr: pd.DataFrame, dupes: pd.DataFrame, plot_paths: list[Path],
    periodicities: pd.DataFrame | None = None, ccf_summary: pd.DataFrame | None = None,
    path_lag_results: dict[str, pd.DataFrame] | None = None,
    valve_summary: pd.DataFrame | None = None, valve_site_summary: pd.DataFrame | None = None,
    valve_level_summary: pd.DataFrame | None = None,
) -> None:
    lines = [
        f"# 데이터 분석 리포트 — {cfg.data.sheet}",
        "",
        f"- 기간: {coverage['start']} ~ {coverage['end']}",
        f"- 전체 {coverage['total_rows']:,}행 중 학습에 쓸 수 있는(연속·결측없음) 행: "
        f"{coverage['valid_rows']:,} ({coverage['valid_ratio_%']:.2f}%)",
        f"- 결측/불연속 구간: {len(gaps)}개"
        + (f", 가장 긴 구간 {gaps.iloc[0]['duration_minutes']:.0f}분 ({gaps.iloc[0]['start']} ~ {gaps.iloc[0]['end']})" if len(gaps) else ""),
        "",
        "## 컬럼별 결측 비율 상위 5개",
        "",
        missing.head(5).to_markdown(index=False),
        "",
    ]

    worst_stuck = stuck.iloc[0] if len(stuck) else None
    if worst_stuck is not None and worst_stuck["duration_minutes"] >= 1440:
        lines += [
            "## 🛑 값이 고정된 구간(센서/통신 고장 의심) 발견",
            "",
            f"`{worst_stuck['column']}`이 **{worst_stuck['duration_minutes']/1440:.1f}일** 동안 "
            f"정확히 같은 값({worst_stuck['stuck_value']:.4g})을 반복했습니다 "
            f"({worst_stuck['start']} ~ {worst_stuck['end']}). 실제 물리 신호가 이렇게 오래 완전히 "
            "고정될 수는 없으므로, 센서/통신 장애로 마지막 값(또는 0)이 그대로 반복 기록됐을 가능성이 "
            "높습니다. NaN이 아니라서 결측으로 잡히지 않지만, 이 구간을 그대로 학습에 쓰면 안 됩니다 — "
            "현장에서 해당 태그의 센서 상태를 먼저 확인하세요. 전체 목록은 stuck_values.csv.",
            "",
            stuck.head(5).to_markdown(index=False),
            "",
        ]

    worst = extremes.iloc[0] if len(extremes) else None
    if worst is not None and worst["worst_extremity_iqr"] > 20:
        lines += [
            "## ⚠ 극단값(센서 글리치 의심) 발견",
            "",
            f"`{worst['column']}`의 max/min이 정상 범위(p01~p99)에서 IQR의 "
            f"{worst['worst_extremity_iqr']:.0f}배만큼 벗어나 있습니다 "
            f"(min={worst['min']:.3g}, p01={worst['p01']:.3g}, p99={worst['p99']:.3g}, max={worst['max']:.3g}). "
            "센서 통신 오류 등으로 인한 극단값 몇 개일 가능성이 높습니다. 아래 자기상관 표의 raw 값이 "
            "이런 값 때문에 왜곡될 수 있으니 robust_clipped 값을 같이 보세요. 전체 목록은 extreme_value_flags.csv.",
            "",
            extremes.head(5).to_markdown(index=False),
            "",
        ]

    lines += [
        "## 타깃 변수 자기상관 (naive baseline이 얼마나 강력한지 미리 보기)",
        "",
        autocorr.to_markdown(index=False),
        "",
        "lag_1min이 1에 가까우면(보통 물리량이 관성이 큰 신호일수록) 짧은 horizon에서는 persistence(직전값 유지) baseline도 매우 강력합니다. "
        "학습 후 skill_score(evaluate.py)가 이 baseline을 넘는지 반드시 같이 확인하세요. "
        "raw와 robust_clipped 차이가 크면 위 극단값 문제 때문이니, 실제 신호의 예측 가능성은 robust_clipped 쪽을 참고하세요.",
        "",
    ]
    if len(dupes):
        lines += [
            f"## 서로 거의 같은 정보를 담은 feature 쌍 (|corr| >= 0.95, {len(dupes)}건)",
            "",
            dupes.to_markdown(index=False),
            "",
        ]

    if periodicities is not None:
        lines += [
            "## 계절성/주기성 — 자기상관 곡선의 국소 피크",
            "",
            "타깃별 자기상관 곡선(acf_curve.csv)에서 국소적으로 상관이 다시 튀어오르는 lag를 찾은 결과입니다. "
            "24시간(1440분) 근처에 피크가 있으면 일간 수요 패턴이, 7일(10080분) 근처에 피크가 있으면 "
            "주간(평일/주말) 패턴이 뚜렷하다는 뜻입니다 — window_size가 이 주기를 볼 만큼 긴지, "
            "요일/시간 feature를 추가할 가치가 있는지 판단하는 근거로 쓰세요. "
            "변수별 원시 패턴(시간대별/요일별/월별)은 seasonal_<변수명>.png, 자기상관 곡선은 acf_curve_<변수명>.png, 전체 목록은 periodicities.csv.",
            "",
        ]
        if len(periodicities):
            lines += [periodicities.head(15).to_markdown(index=False), ""]
        else:
            lines += ["(뚜렷한 국소 피크가 발견되지 않았습니다 — 이 기간/lag 범위에서는 강한 주기성이 없거나, acf-max-lag-minutes를 늘려야 더 긴 주기를 볼 수 있습니다.)", ""]

    if ccf_summary is not None:
        lines += [
            "## 교차상관(CCF) — 태그 간 시간 지연",
            "",
            "동시 상관이 강한(|corr| >= 임계값) 변수쌍만 대상으로, lag을 움직여가며 상관이 최대가 되는 "
            "지연시간을 찾은 결과입니다. best_lag_minutes가 0이 아니면 관망 상에서 실제 신호 전파 지연이 "
            "있다는 뜻입니다(양수: a가 b를 선행). 상위 쌍의 lag별 곡선은 ccf_top_pairs.png, 전체 목록은 "
            "cross_correlation_pairs.csv, 이 관계 전체를 방향 그래프로 그린 것은 network_graph.png "
            "(빨간 화살표=선행→후행, 회색 선=동시 상관이라 방향은 못 잡음, 노드 색=물리량 종류(유량/"
            "압력/수위, 파랑/주황/초록), 흰 속=어떤 태그와도 강하게 안 엮인 고립 태그) — 관망이 "
            "실제로 이렇게 연결돼 있을 것이라는 가정이 아니라 데이터에서 나온 결과입니다.",
            "",
        ]
        if len(ccf_summary):
            lines += [ccf_summary.head(15).to_markdown(index=False), ""]
        else:
            lines += ["(임계값을 넘는 변수쌍이 없었습니다 — --ccf-corr-threshold를 낮추면 더 약한 관계도 볼 수 있습니다.)", ""]

    if path_lag_results:
        lines += [
            "## 경로 지연시간(path lag) — 상류 조상 -> target 직접 CCF",
            "",
            "cross_correlation_pairs()의 동시 상관 임계값을 거치지 않고, 관망도(taglist."
            "REFERENCE_NETWORK_EDGES) 상 target의 모든 상류 조상 각각과 target을 직접 쌍으로 "
            "놓고 CCF를 잰 결과입니다. best_lag_minutes가 이 상류 지점을 조작했을 때 target에 "
            "실제로 반영되기까지 걸리는 시간의 추정치입니다 — 제어(예: 정수장 유량/압력 추천)의 "
            "실행 가능 리드타임을 정하는 근거로 씁니다.",
            "",
        ]
        for target, summary in path_lag_results.items():
            lines.append(f"### {target}")
            lines.append("")
            if len(summary):
                lines += [summary.to_markdown(index=False), ""]
            else:
                lines += ["(유효한 lag를 하나도 못 찾음 — 데이터 겹치는 구간이 없거나 두 시계열 중 하나가 상수)", ""]

    if valve_summary is not None and len(valve_summary):
        lines += [
            "## 밸브(제어 변수) 분석",
            "",
            "### 1) 상시개방/고정 vs 제어",
            "",
            "pct_at_mode(반올림한 값 중 가장 흔한 값이 차지하는 비율)가 98% 이상이면 "
            "\"상시개방/고정 추정\", 아니면 \"제어 추정\"으로 분류했습니다. 다만 실제 스케일(0~100% 등)을 "
            "모르면 \"완전 개방\"인지 \"중간값에 고정\"인지까지는 이 표만으로 못 가릅니다 — mean/min/max와 "
            "함께 보세요. distinct_values/n_transitions가 둘 다 작으면(예: 2~3개, 며칠에 한 번) 연속 "
            "제어가 아니라 가끔 몇 단계로만 조정한다는 뜻입니다.",
            "",
            valve_summary.to_markdown(index=False),
            "",
        ]
        if valve_site_summary is not None and len(valve_site_summary):
            lines += [
                "### 2) 밸브 vs 같은 지점 유량/압력",
                "",
                "밸브가 그 지점의 원인이라면 거의 동시~수 분 내에 유량/압력에 반영되는 게 정상입니다. "
                "best_lag_minutes가 크게 나오면(수십 분 이상) 밸브가 그 유량/압력의 직접 원인이 아니거나, "
                "제어 자체가 드물어(위 표의 n_transitions 참고) CCF가 우연한 상관을 주웠을 수 있습니다.",
                "",
                valve_site_summary.to_markdown(index=False),
                "",
            ]
        if valve_level_summary is not None and len(valve_level_summary):
            lines += [
                "### 3) 밸브 vs 하류 배수지 수위",
                "",
                "밸브가 속한 지점에서 관망도(taglist.REFERENCE_NETWORK_EDGES) 상 하류에 있는 모든 수위 "
                "태그와의 관계입니다. 수위는 유입-유출의 누적값이라 반영에 몇 시간이 걸릴 수 있어(path lag "
                "분석 참고) lag 범위를 넉넉하게 잡았습니다. corr_lag0이 약한데 best_lag만 큰 쌍은 "
                "우연일 수 있으니 |best_ccf| 자체가 뚜렷한지도 같이 보세요.",
                "",
                valve_level_summary.to_markdown(index=False),
                "",
            ]
    (out_dir / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out-dir", default=None, help="단일 시트 분석 시에만 사용 (여러 시트 저장 위치는 output.analysis_dir로 자동 결정됨)")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--clean", action="store_true", help="분석 폴더에 남아있는 기존 결과를 먼저 통째로 삭제하고 새로 만든다 (컬럼/옵션이 바뀌어 이전에 생성된 파일이 새 결과와 섞여 남는 것을 방지)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sheet", default=None, help="config의 data.sheet 대신 이 시트 하나만 분석")
    group.add_argument("--all-sheets", action="store_true", help="태그리스트의 모든 시트(단계)를 각각 분석")
    parser.add_argument("--source", choices=["csv", "db"], default=None, help="config의 data.source를 덮어씀")
    parser.add_argument("--db-environment", default=None, help="config의 data.db_environment를 덮어씀 (prod/dev/local)")
    parser.add_argument("--start-date", default=None, help="config의 data.start_date를 덮어씀 (DB는 기간이 넓어 좁혀야 할 때 유용)")
    parser.add_argument("--end-date", default=None, help="config의 data.end_date를 덮어씀")
    parser.add_argument("--skip-seasonality", action="store_true", help="요일별/월별 패턴, 자기상관 곡선/주기성 탐지를 생략 (여러 시트를 빠르게 훑어볼 때 유용)")
    parser.add_argument("--skip-ccf", action="store_true", help="태그 간 교차상관(CCF)/지연시간 분석을 생략")
    parser.add_argument("--acf-max-lag-minutes", type=int, default=2880, help="자기상관 곡선을 계산할 최대 lag(분). 기본 2880분(2일). 주간 주기까지 보려면 늘릴 것 (예: 10080)")
    parser.add_argument("--ccf-max-lag-minutes", type=int, default=120, help="교차상관을 계산할 최대 lag(분, 양방향). 기본 120분")
    parser.add_argument("--ccf-corr-threshold", type=float, default=0.5, help="이 값 이상 동시 상관인 변수쌍만 교차상관을 계산 (기본 0.5)")
    parser.add_argument("--ccf-max-pairs", type=int, default=40, help="교차상관을 계산할 최대 변수쌍 수 (기본 40, |동시 상관| 큰 순)")
    parser.add_argument(
        "--path-lag-target", action="append", dest="path_lag_targets", default=None,
        help="이 태그(var_name, 예: Q7)의 관망도(REFERENCE_NETWORK_EDGES) 상 모든 상류 조상과 "
        "직접 CCF를 재서 경로 지연시간을 추정한다(동시 상관 임계값 없이, path_lag_<target>.csv/png). "
        "여러 번 줄 수 있음 (예: --path-lag-target Q7 --path-lag-target H7)",
    )
    parser.add_argument(
        "--path-lag-max-minutes", type=int, default=4320,
        help="path-lag-target의 CCF를 계산할 최대 lag(분, 양방향). 기본 4320분(3일). 저수조 완충으로 "
        "지연이 몇 시간 단위일 수 있어 ccf-max-lag-minutes보다 넉넉하게 잡음",
    )
    parser.add_argument(
        "--skip-valve-analysis", action="store_true",
        help="밸브 분석(상시개방 여부/같은 지점 유량-압력 관계/하류 수위 영향)을 생략. 기본은 "
        "tag_name의 계측 코드가 POI인 태그(taglist.is_valve_tag)가 taglist에 있으면 자동으로 돈다",
    )
    parser.add_argument(
        "--valve-downstream-max-lag-minutes", type=int, default=4320,
        help="밸브 vs 하류 배수지 수위 CCF를 계산할 최대 lag(분, 양방향). 기본 4320분(3일)",
    )
    parser.add_argument(
        "--recent-days", type=int, default=7,
        help="timeseries_<변수>.png(전체 기간, 일별 집계)와 별도로 timeseries_recent<N>d_<변수>.png"
        "(최근 N일, 원본 해상도)도 같이 만든다. 기본 7일, 0이면 생략",
    )
    args = parser.parse_args()
    cfg = Config.from_yaml(args.config)

    data_overrides = {}
    if args.sheet:
        data_overrides["sheet"] = args.sheet
    if args.source:
        data_overrides["source"] = args.source
    if args.db_environment:
        data_overrides["db_environment"] = args.db_environment
    if args.start_date:
        data_overrides["start_date"] = args.start_date
    if args.end_date:
        data_overrides["end_date"] = args.end_date
    if data_overrides:
        cfg = dataclasses.replace(cfg, data=dataclasses.replace(cfg.data, **data_overrides))

    if args.source == "db" and args.out_dir is None and "{sheet}_db" not in cfg.output.analysis_dir:
        # CSV 기반 분석 결과(analysis/<sheet>/)와 섞이지 않도록 별도 폴더에 저장한다.
        # gu_db.yaml처럼 config 자체가 이미 source: db + analysis_dir가 "{sheet}_db"인
        # 경우에는(원래도 db 전용 config), --source db를 CLI로 또 넘겨도 건너뛴다 —
        # 안 그러면 "{sheet}_db"에 또 "_db"가 붙어 analysis/GU_db_db 처럼 중복된다.
        db_analysis_dir = cfg.output.analysis_dir.replace("{sheet}", "{sheet}_db")
        cfg = dataclasses.replace(cfg, output=dataclasses.replace(cfg.output, analysis_dir=db_analysis_dir))

    run_kwargs = dict(
        clean=args.clean,
        skip_seasonality=args.skip_seasonality,
        skip_ccf=args.skip_ccf,
        acf_max_lag_minutes=args.acf_max_lag_minutes,
        ccf_max_lag_minutes=args.ccf_max_lag_minutes,
        ccf_corr_threshold=args.ccf_corr_threshold,
        ccf_max_pairs=args.ccf_max_pairs,
        path_lag_targets=args.path_lag_targets,
        path_lag_max_minutes=args.path_lag_max_minutes,
        skip_valve_analysis=args.skip_valve_analysis,
        valve_downstream_max_lag_minutes=args.valve_downstream_max_lag_minutes,
        recent_days=args.recent_days,
    )
    if args.all_sheets:
        run_all_sheets(cfg, make_plots=not args.no_plots, **run_kwargs)
    else:
        run_and_save(cfg, out_dir=args.out_dir, make_plots=not args.no_plots, **run_kwargs)


if __name__ == "__main__":
    main()
