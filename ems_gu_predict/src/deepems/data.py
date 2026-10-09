"""데이터 적재 · 리샘플링 · 결측 구간 처리 · 시간순 분할 · 이상치/스케일링.

기존 코드 대비 바뀐 점 (왜 바꿨는지는 deepEMS/README.md 참고):

1. 시퀀스를 만들기 전에 "실제 시간이 연속인 구간"만 골라낸다
   (find_segments). 기존 코드는 IQR/dropna로 행이 빠진 뒤에도
   행 순서(위치)로만 슬라이딩 윈도우를 만들어서, 60개 행이 실제로는
   60분이 아닐 수 있었다.
2. train/val/test를 스케일링·이상치처리보다 먼저, 시간순으로
   자르고, 분할 경계에는 purge 구간을 둬서 겹치는 슬라이딩 윈도우로
   정보가 새는 것을 막는다.
3. 이상치는 행을 지우는 대신(winsorize) train 통계로만 clip한다.
   test에는 적용하지 않아서, 실제 이상상황에서 모델이 얼마나
   틀리는지를 평가지표에서 감추지 않는다.
4. 스케일러는 train 구간에서만 fit한다.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from .taglist import TagInfo

_SCALER_CLASSES = {"minmax": MinMaxScaler, "robust": RobustScaler, "standard": StandardScaler}


def load_raw_frame(
    tags: list[TagInfo],
    rawdata_dir: str,
    filename_template: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """태그별 CSV를 읽어 변수명 컬럼을 가진 하나의 DataFrame으로 합친다."""
    series_list = []
    for tag in tags:
        path = Path(rawdata_dir) / filename_template.format(tag=tag.tag_name)
        s = pd.read_csv(path, names=["Datetime", tag.var_name])
        s["Datetime"] = pd.to_datetime(s["Datetime"])
        s = s.dropna(subset=["Datetime"]).drop_duplicates(subset=["Datetime"])
        s = s.set_index("Datetime").sort_index()
        series_list.append(s[tag.var_name])

    df = pd.concat(series_list, axis=1)
    if start_date is not None:
        df = df.loc[df.index >= pd.Timestamp(start_date)]
    if end_date is not None:
        df = df.loc[df.index <= pd.Timestamp(end_date)]
    return df.sort_index()


def check_feature_coverage(raw: pd.DataFrame, min_coverage_warn: float = 0.5) -> pd.Series:
    """컬럼(태그)별 실제 데이터 비율을 확인하고, 커버리지가 0인 태그가 있으면
    바로 에러를 낸다.

    태그리스트는 계속 바뀔 수 있다(예: 새 target 추가) — 새로 추가된 태그가
    아직 그 소스(CSV/DB)에 데이터가 하나도 없으면, 그 컬럼이 통째로 NaN이
    되어 모든 행이 무효 처리되고 결국 학습 시퀀스가 0개가 되는 채로 조용히
    실패한다(원인을 한참 뒤에야 알게 됨). 이를 미리 잡아서 어떤 태그가
    문제인지 바로 알려준다.
    """
    coverage = raw.notna().mean()
    empty_cols = coverage[coverage == 0].index.tolist()
    if empty_cols:
        raise ValueError(
            f"다음 태그에 지정한 기간 동안 데이터가 전혀 없습니다: {empty_cols}. "
            f"태그리스트가 최근에 바뀌었다면(예: 새 target 추가) 그 태그가 아직 이 소스(csv/db)에 "
            f"없는 것일 수 있습니다. 확인 후 태그리스트에서 빼거나(비고를 'NU'로), "
            f"data.start_date를 그 태그의 실제 수집 시작일 이후로 조정하세요."
        )
    low_cov = coverage[coverage < min_coverage_warn]
    if len(low_cov):
        print(f"  [경고] 다음 태그는 지정 기간 동안 데이터 비율이 {min_coverage_warn:.0%} 미만입니다: {low_cov.round(3).to_dict()}")
    return coverage


def apply_column_start_dates(raw: pd.DataFrame, column_start_dates: dict[str, str]) -> pd.DataFrame:
    """column_start_dates에 지정된 컬럼은, 그 날짜 이전 값을 전부 NaN으로 만든다.

    센서가 나중에 설치돼서 그 전엔 값이 없거나(0), 의미 없는 노이즈만 있는
    태그를 위한 것이다 — 예: Q8은 2025-03-27 전엔 -10~30 사이를 맴도는 값뿐이다가
    그날부터 실제 유량(수백 단위)이 찍히기 시작했다. resample_and_flag_gaps가
    이후 이 NaN 구간을 다른 결측과 똑같이 처리하므로(ffill_limit을 넘으면
    valid_mask=False), 이 함수 자체는 그냥 값을 지우기만 하면 된다.

    data.start_date를 통째로 늦추는 것과 다르다 — data.start_date는 모든
    컬럼에 적용되어 다른 태그의 이전 데이터까지 같이 버리지만, 이건 지정한
    컬럼 하나만 건드린다.
    """
    if not column_start_dates:
        return raw
    out = raw.copy()
    for col, start in column_start_dates.items():
        if col not in out.columns:
            continue
        cutoff = pd.Timestamp(start)
        out.loc[out.index < cutoff, col] = float("nan")
    return out


def combine_max_columns(raw: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    """groups={새 컬럼명: [원본 컬럼들]}에 대해, 각 그룹의 원소 중 결측이 아닌
    값들의 최댓값을 새 컬럼에 넣고 원본 컬럼은 지운다 (pandas DataFrame.max의
    기본 skipna=True — 한쪽만 결측이면 있는 값을 그대로 쓰고, 둘 다 있으면
    큰 쪽, 둘 다 결측이면 결측 유지).

    H3_1/H3_2, H7_1/H7_2처럼 같은 지점의 서로 다른 두 수위 센서를 하나의
    대표값으로 합칠 때 쓴다 — 실제로 상관계수 0.98 이상으로 사실상 중복
    신호였다(analysis/GU_db/near_duplicate_features.csv). 리샘플 전(원본
    해상도) raw DataFrame에 적용해야 한다 — pipeline.prepare_data 참고.
    """
    if not groups:
        return raw
    out = raw.copy()
    for new_name, members in groups.items():
        present = [m for m in members if m in out.columns]
        if not present:
            continue
        combined = out[present].max(axis=1, skipna=True)
        out = out.drop(columns=present)
        out[new_name] = combined
    return out


_TIME_FEATURE_FNS = {
    # sin/cos 쌍으로 넣는 이유: 시(hour)나 요일(dayofweek)을 정수 그대로 넣으면
    # 23시와 0시가 모델 입력값 상으로는 정반대(멀리 떨어진 값)로 보이지만,
    # 실제로는 1시간 차이인 "주기적" 관계다. sin/cos 좌표로 바꾸면 이 원형
    # 거리가 그대로 유클리드 거리로 보존된다 — 시계열의 시간 feature에 쓰는
    # 표준적인 방법.
    "hour_sin": lambda idx: np.sin(2 * np.pi * (idx.hour + idx.minute / 60) / 24),
    "hour_cos": lambda idx: np.cos(2 * np.pi * (idx.hour + idx.minute / 60) / 24),
    "dow_sin": lambda idx: np.sin(2 * np.pi * idx.dayofweek / 7),
    "dow_cos": lambda idx: np.cos(2 * np.pi * idx.dayofweek / 7),
    "month_sin": lambda idx: np.sin(2 * np.pi * (idx.month - 1) / 12),
    "month_cos": lambda idx: np.cos(2 * np.pi * (idx.month - 1) / 12),
}


def add_time_features(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """df.index(시각)에서 직접 계산되는 주기적 시간 feature(hour_sin 등)를
    컬럼으로 추가한다. 실측(analyze.py의 acf_curve/detect_periodicities)으로
    확인된 강한 일간 주기성(거의 모든 target이 lag≈24시간에서 자기상관 국소
    피크를 보임 — analysis/GU_db/periodicities.csv)을 모델이 288스텝(5분
    리샘플 기준 24시간)치 원시 신호만으로 암묵적으로 추론하는 대신, 지금이
    하루 중 언제인지를 직접적인 입력으로 준다.

    센서 값과 달리 시각에서 결정적으로 계산되므로 결측이 있을 수 없다 —
    resample_and_flag_gaps로 만든 valid_mask(결측 여부) 계산이 끝난 뒤,
    filled DataFrame에 추가해야 한다 (pipeline.prepare_data 참고). target으로
    쓰이지 않고 feature_cols에만 더해진다.
    """
    if not features:
        return df
    unknown = [f for f in features if f not in _TIME_FEATURE_FNS]
    if unknown:
        raise ValueError(f"알 수 없는 time_feature: {unknown}. 사용 가능: {sorted(_TIME_FEATURE_FNS)}")
    out = df.copy()
    for name in features:
        out[name] = _TIME_FEATURE_FNS[name](out.index).astype(float)
    return out


def add_lever_change_features(df: pd.DataFrame, columns: list[str], diff_steps: list[int]) -> pd.DataFrame:
    """레버 태그(V2/V4/Q_GunS 등)의 "지금 막 움직이고 있는가"를 명시적 feature로
    추가한다 - `{col}_diff{step}` = `df[col].diff(step)`.

    2026-09-11 실측 근거: 후보 모델 8종 전부가 Q7의 급격한 사각형 모양
    낙폭(예: window origin=2026-03-22 01:55, horizon step 35~45)을 똑같이
    놓쳤는데, 실측을 대조해보니 그 구간이 V2 밸브를 24.09 -> 19.15로 실제
    조작한 시점과 정확히 일치했다(`scripts/DEVNOTES.md` 참고). 원시 레버
    값(V2 자체)은 이미 feature_cols에 있지만, 모델이 "값이 24.09다"와
    "값이 방금 24.09에서 19.15로 바뀌었다"를 구분하려면 변화량을 직접
    줘야 한다 - 원시값 시퀀스에서 그 차이를 스스로 추론하게 두는 것보다
    명시적으로 주는 편이 특히 트리 기반 모델(XGBoost/LightGBM)에 더 잘
    먹힌다.

    미래의 레버 조작 자체를 예측해주진 않는다(그건 애초에 과거 데이터에
    없는 정보라 불가능 - 모듈 docstring 참고) - 다만 조작이 "막 시작된"
    시점 이후의 horizon 예측이, 그 조작을 감지하지 못했을 때보다는 나아질
    수 있다는 가설을 테스트하기 위한 것.

    diff는 앞쪽 `step`개 행에서 NaN이 생긴다 - `valid_mask`는 이 함수
    호출 전(resample_and_flag_gaps 시점)에 이미 계산이 끝난 상태라 이
    NaN을 모른다(add_time_features와 같은 자리에서 호출되는 게 전제).
    valid_mask를 다시 계산하는 대신, "직전 데이터가 아직 없다"는 걸
    "변화 없음(0)"으로 간주해 0으로 채운다 - 다른 feature 컬럼처럼 이
    함수가 만드는 컬럼은 항상 NaN 없이 정의돼야 한다는 게 목표다(P6
    고정구간 NaN 전파 버그, `impute_stuck_values`와 같은 원칙 - NaN을
    windowing 단계까지 조용히 흘려보내지 않는다).
    """
    if not columns or not diff_steps:
        return df
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"lever_diff_columns에 df에 없는 컬럼이 있습니다: {missing}")
    out = df.copy()
    for col in columns:
        for step in diff_steps:
            out[f"{col}_diff{step}"] = out[col].diff(step).fillna(0.0)
    return out


def resample_and_flag_gaps(
    df: pd.DataFrame, freq: str, ffill_limit_minutes: int, linear_interp_columns: list[str] | None = None
) -> tuple[pd.DataFrame, pd.Series]:
    """고정 간격 그리드로 리샘플링하고, 짧은 결측만 채운 뒤 "이 시점 값이
    신뢰할 만한가"를 valid_mask로 명시적으로 표시한다.

    기본은 ffill(직전값 유지)이지만, linear_interp_columns에 적힌 컬럼은 대신
    linear interpolation(선형 보간)으로 채운다 — 압력처럼 매끄럽게 변하는
    신호는 결측 동안 "계단식으로 멈춰있었다"고 가정하는 ffill보다 두 관측치
    사이를 직선으로 잇는 편이 더 그럴듯하다 (config.py의
    DataConfig.linear_interp_columns 참고). 둘 다 같은 limit(연속으로 채울 수
    있는 최대 개수)을 공유하고, limit_area="inside"로 두 관측치 "사이"만
    채운다 — 데이터 시작/끝단의 결측(바깥쪽)까지 채우면 ffill과 동작이
    달라져 일관성이 깨진다.

    기존 코드처럼 결측 행을 조용히 지우지 않는다 — 대신 valid_mask가
    False인 지점에서 시퀀스를 끊어서(연속 구간 분리) 학습/평가에
    쓰이는 모든 윈도우가 실제로 연속된 시간을 담도록 보장한다.

    주의: 예전엔 `pd.date_range(df.index.min(), df.index.max(), freq=freq)`로
    직접 그리드를 만들어 reindex했는데, freq가 원본 데이터 간격(1분)과
    다르면(예: 5분) 버그가 났다 — resample()의 버킷 경계는 pandas 기본
    origin(자정 등)에 맞춰지는데, df.index.min()이 정각이 아니면(예: 00:01)
    직접 만든 grid는 그보다 1분 밀린 자리에서 시작해서 resample 결과와
    한 번도 안 맞아떨어져 전부 NaN이 됐다 (실제로 5분 리샘플링 도입
    직후 발견됨). resample()이 이미 빈 구간까지 포함한 완전한 grid를
    만들어주므로, 별도 reindex 없이 그 결과를 그대로 쓴다.
    """
    freq_delta = pd.Timedelta(freq)
    df = df.resample(freq).mean()

    limit = max(0, int(round(ffill_limit_minutes * (pd.Timedelta(minutes=1) / freq_delta))))
    if limit > 0:
        df_filled = df.copy()
        linear_cols = [c for c in (linear_interp_columns or []) if c in df.columns]
        ffill_cols = [c for c in df.columns if c not in linear_cols]
        if linear_cols:
            df_filled[linear_cols] = df[linear_cols].interpolate(method="linear", limit=limit, limit_area="inside")
        if ffill_cols:
            df_filled[ffill_cols] = df[ffill_cols].ffill(limit=limit)
    else:
        df_filled = df
    valid_mask = df_filled.notna().all(axis=1)
    return df_filled, valid_mask


def find_segments(valid_mask: pd.Series, min_rows: int) -> list[tuple[int, int]]:
    """valid_mask가 연속으로 True인 [start, end) 위치 구간 목록 (min_rows 미만은 버림).

    numpy로 벡터화되어 있다 — stuck_run_mask()가 컬럼마다 이 함수를 호출하는데,
    DB 전체 기간(수백만 행) 데이터에서는 순수 파이썬 반복문으로는 눈에 띄게
    느려서(수십 초~분 단위) 벡터화했다.
    """
    arr = valid_mask.to_numpy()
    n = len(arr)
    if n == 0:
        return []
    # 값이 바뀌는 위치(경계)를 한 번에 찾는다.
    change_points = np.flatnonzero(arr[1:] != arr[:-1]) + 1
    starts = np.concatenate(([0], change_points))
    ends = np.concatenate((change_points, [n]))
    is_true_run = arr[starts]
    lengths = ends - starts
    keep = is_true_run & (lengths >= min_rows)
    return list(zip(starts[keep].tolist(), ends[keep].tolist()))


def _stuck_segments(s: pd.Series, min_rows: int) -> list[tuple[int, int]]:
    """s가 min_rows 이상 정확히 고정된 [start, end) 위치 구간 목록 (같은 값이
    처음 나타난 시점부터 포함하도록 한 칸 앞당김). stuck_run_mask/
    impute_stuck_values가 공유하는 핵심 로직."""
    same_as_prev = s.eq(s.shift(1)) & s.notna()
    segments = []
    for seg_start, seg_end in find_segments(same_as_prev, min_rows=min_rows):
        run_start_pos = max(seg_start - 1, 0)
        segments.append((run_start_pos, seg_end))
    return segments


def stuck_run_mask(
    raw_grid: pd.DataFrame, freq: str, min_minutes: int, exclude_columns: list[str] | None = None
) -> pd.Series:
    """raw_grid의 어느 컬럼이든(exclude_columns는 제외) min_minutes 이상 값이
    정확히 고정되어 있는 행을 True로 표시.

    실제 물리 신호(압력/유량)가 그렇게 오래 완전히 안 변할 수는 없으므로,
    센서/통신 장애로 마지막 값(또는 0)이 그대로 반복 기록된 것으로 본다.
    NaN이 아니라서 기존 valid_mask(resample_and_flag_gaps)는 이런 구간을
    "정상"으로 취급하지만, 실제로는 학습에 쓰면 안 되는 구간이다 — dev DB의
    osd 시트 P6이 2025-09~2026-03 사이 몇 달간 정확히 0.0을 반복한 사례로
    실제 발견됨 (analyze.py의 stuck_value_report와 같은 로직).

    exclude_columns에 있는 컬럼은 여기서 건너뛴다 — 그 컬럼에 고정 구간이
    있어도 전체 valid_mask를 무효로 만들지 않는다는 뜻이다. feature_cols ==
    target_cols인 joint 모델에서 태그 하나(P6)의 장기 고정이 나머지 태그
    전부를 학습에서 끌어내리는 걸 막기 위해 쓴다 — 대신 그 컬럼은
    impute_stuck_values로 값 자체를 중앙값으로 채워서 쓴다
    (config.py의 DataConfig.stuck_value_impute_columns 참고).
    """
    exclude = set(exclude_columns or [])
    freq_delta = pd.Timedelta(freq)
    min_rows = max(1, int(pd.Timedelta(minutes=min_minutes) / freq_delta))
    mask = pd.Series(False, index=raw_grid.index)
    for col in raw_grid.columns:
        if col in exclude:
            continue
        for seg_start, seg_end in _stuck_segments(raw_grid[col], min_rows):
            mask.iloc[seg_start:seg_end] = True
    return mask


def impute_stuck_values(
    filled: pd.DataFrame, raw_grid: pd.DataFrame, freq: str, min_minutes: int, columns: list[str],
    method: str = "median",
) -> pd.DataFrame:
    """columns에 지정한 컬럼에서 min_minutes 이상 정확히 고정된 구간(raw_grid
    기준 — ffill로 생긴 가짜 "고정"과 헷갈리지 않기 위해 ffill 전 원본을 본다)을
    찾아, filled의 그 구간 값을 채운다.

    stuck_run_mask로 그 구간 전체를 무효 처리(valid_mask=False)하는 대신 쓰는
    절충안이다 — feature_cols == target_cols인 joint 모델(GU 시트)에서는
    태그 하나(P6)가 몇 달간 고정되면 그 기간 24개 태그 전체가 한꺼번에
    학습에서 빠져버린다. P6 자체를 그 기간에 정확히 예측할 순 없어도(신호가
    없으므로), 그럴듯한 값으로 채워서 나머지 태그들의 그 기간 데이터는
    살린다. stuck_run_mask 호출 시 이 columns를 exclude_columns로 같이
    넘겨야 이 목적이 완성된다(안 그러면 여기서 값을 대체해도 valid_mask가
    여전히 그 구간을 무효 처리한다).

    method="median"(기본): 구간 전체를 해당 컬럼의 중앙값(고정 구간을 뺀
    나머지 값 기준)이라는 하나의 상수로 채운다.

    method="linear": 구간 시작 직전의 마지막 실측값과 끝난 직후의 첫
    실측값을 직선으로 이어서 채운다. median과 달리 완전한 상수가 아니라
    추세가 있는 값을 준다 — 원래 변동폭이 좁은 태그(예: P6, 4.26~4.36
    범위)에서는 정확도 손해가 미미하면서, median 상수가 만드는 "몇 달간
    완전히 평평한 가짜 구간"(평가 지표를 왜곡시킴 — 2026-09-10 P6 사례로
    실측) 문제를 크게 줄인다. 구간이 데이터 맨 앞/뒤에 걸려 한쪽 끝값이
    없으면(예: 측정 시작부터 고정) 그 구간만 median으로 대체한다(fallback).
    """
    if method not in ("median", "linear"):
        raise ValueError(f"method는 'median' 또는 'linear'여야 합니다: {method!r}")

    freq_delta = pd.Timedelta(freq)
    min_rows = max(1, int(pd.Timedelta(minutes=min_minutes) / freq_delta))
    out = filled.copy()
    for col in columns:
        if col not in raw_grid.columns:
            continue
        segments = _stuck_segments(raw_grid[col], min_rows)
        if not segments:
            continue
        col_pos = out.columns.get_loc(col)
        stuck = pd.Series(False, index=out.index)
        median_fallback_segments: list[tuple[int, int]] = []
        for seg_start, seg_end in segments:
            if method == "linear":
                before_pos, after_pos = seg_start - 1, seg_end
                before_val = out[col].iloc[before_pos] if before_pos >= 0 else np.nan
                after_val = out[col].iloc[after_pos] if after_pos < len(out) else np.nan
                # before_pos/after_pos가 배열 범위 안에 있어도, 그 위치 자체가
                # (예: 다른 원인의 짧은 결측이 마침 이 경계와 겹쳐서) NaN일 수
                # 있다 — 이 경우를 안 걸러내면 np.linspace(NaN, val, n)이
                # 구간 전체를 NaN으로 오염시킨다(2026-09-11 실측으로 발견:
                # P6의 장기 고정 구간 경계에서 실제로 발생 — window 288/288
                # 스텝이 전부 NaN이 되어 있었다). 범위 체크만으론 부족하고
                # 유한값인지까지 확인해야 한다.
                if np.isfinite(before_val) and np.isfinite(after_val):
                    n = seg_end - seg_start
                    out.iloc[seg_start:seg_end, col_pos] = np.linspace(before_val, after_val, n + 2)[1:-1]
                    continue
                median_fallback_segments.append((seg_start, seg_end))  # 끝값이 없거나 NaN이라 보간 불가
            else:
                median_fallback_segments.append((seg_start, seg_end))
            stuck.iloc[seg_start:seg_end] = True
        if median_fallback_segments:
            # 중앙값은 "고정 구간 전체"(method 불문)를 뺀 나머지 값 기준으로
            # 계산해야 median 대상 구간 자체가 median 계산에 섞여 왜곡되지 않는다.
            all_stuck = pd.Series(False, index=out.index)
            for seg_start, seg_end in segments:
                all_stuck.iloc[seg_start:seg_end] = True
            median = out.loc[~all_stuck, col].median()
            if not np.isfinite(median):
                # 고정 구간을 뺀 나머지가 전부 NaN이면(그 컬럼이 사실상 데이터가
                # 없다는 뜻) 조용히 NaN으로 채우는 대신 바로 알아챌 수 있게 에러를
                # 낸다 — 위 linear 폴백과 마찬가지로 "채웠다고 착각하지만 실제로는
                # NaN인 채로 넘어가는" 상황을 막기 위함.
                raise ValueError(
                    f"{col}의 median 대체값이 NaN입니다 - 고정 구간을 뺀 나머지 데이터가 전부 결측인지 확인할 것."
                )
            out.loc[stuck, col] = median
    return out


@dataclasses.dataclass
class SplitRanges:
    train: tuple[pd.Timestamp, pd.Timestamp]
    val: tuple[pd.Timestamp, pd.Timestamp]
    test: tuple[pd.Timestamp, pd.Timestamp]


def time_based_split(
    index: pd.DatetimeIndex,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    purge_minutes: int,
) -> SplitRanges:
    """행 개수가 아니라 실제 달력 시간 기준으로 앞/중간/뒤를 자른다.

    분할 경계 양쪽으로 purge_minutes 만큼 버려서, window_size+horizon
    길이의 슬라이딩 윈도우가 두 split에 걸쳐 겹치는 정보 누수를 막는다
    (기존 코드는 model.fit(validation_split=0.2)로 이미 만들어진
    슬라이딩 윈도우 배열을 뒤에서부터 잘라, window_size=60인데
    sliding_step=5라 인접 시퀀스가 92% 겹치는 상태로 train/val이 나뉘었다).
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
    start, end = index.min(), index.max()
    span = end - start
    train_end = start + span * train_ratio
    val_end = train_end + span * val_ratio
    purge = pd.Timedelta(minutes=purge_minutes)
    return SplitRanges(
        train=(start, train_end - purge),
        val=(train_end + purge, val_end - purge),
        test=(val_end + purge, end),
    )


@dataclasses.dataclass
class FeaturePipeline:
    """train 구간 통계로만 fit하는 이상치 clip + 스케일러.

    학습과 추론(production)이 반드시 같은 객체를 pickle로 공유하도록
    설계했다 — 기존 코드는 학습 시 dropna()로 결측을 버리고 추론 시엔
    fillna(현재 60행의 평균)을 쓰는 등 두 경로의 전처리가 달랐다.
    """

    feature_cols: list[str]
    clip_bounds: dict[str, tuple[float, float]] = dataclasses.field(default_factory=dict)
    scalers: dict[str, MinMaxScaler | RobustScaler | StandardScaler] = dataclasses.field(default_factory=dict)
    outlier_enabled: bool = True
    lower_q: float = 0.01
    upper_q: float = 0.99
    # 컬럼별 (lower_q, upper_q) override. 여기 없는 컬럼은 위 lower_q/upper_q를 쓴다.
    # analyze.py의 autocorrelation.csv(raw vs robust_clipped)로 어떤 컬럼에
    # override가 필요한지 판단하는 방법은 config.py의 OutlierConfig 참고.
    column_overrides: dict[str, tuple[float, float]] = dataclasses.field(default_factory=dict)
    # "minmax"(기본) | "robust"(median/IQR) | "standard"(평균/표준편차) -
    # config.OutlierConfig.scaler_type/column_scaler_overrides와 같은 뜻.
    # quantile clip을 거쳐도 남은 값이 한쪽으로 치우친 컬럼(운영자 수동
    # 개입이 섞인 Q_GunS 등)엔 robust가 더 안정적일 수 있다 - 문서
    # network_control_simulation_design.md 규칙11 참고.
    scaler_type: str = "minmax"
    column_scaler_overrides: dict[str, str] = dataclasses.field(default_factory=dict)

    def _scaler_for(self, col: str):
        name = self.column_scaler_overrides.get(col, self.scaler_type)
        return _SCALER_CLASSES[name]()

    def fit(self, train_df: pd.DataFrame) -> "FeaturePipeline":
        for col in self.feature_cols:
            vals = train_df[col].dropna()
            if self.outlier_enabled:
                col_lower_q, col_upper_q = self.column_overrides.get(col, (self.lower_q, self.upper_q))
                lo, hi = vals.quantile(col_lower_q), vals.quantile(col_upper_q)
                self.clip_bounds[col] = (float(lo), float(hi))
                vals = vals.clip(lo, hi)
            scaler = self._scaler_for(col)
            scaler.fit(vals.to_frame())
            self.scalers[col] = scaler
        return self

    def transform(self, df: pd.DataFrame, clip: bool) -> pd.DataFrame:
        out = df.copy()
        for col in self.feature_cols:
            series = out[col]
            if clip and self.outlier_enabled and col in self.clip_bounds:
                lo, hi = self.clip_bounds[col]
                series = series.clip(lo, hi)
            out[col] = self.scalers[col].transform(series.to_frame())[:, 0]
        return out

    def inverse_transform_col(self, col: str, values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values).reshape(-1, 1)
        return self.scalers[col].inverse_transform(arr)[:, 0]
