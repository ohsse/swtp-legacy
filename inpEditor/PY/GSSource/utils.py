"""
GS EMS 공통 유틸리티 함수 모음
"""

import pandas as pd
import numpy as np
import os
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm


# ============================================================
# 경로 유틸
# ============================================================

def check_path(path=None):
    if path:
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        print("경로가 지정되지 않았습니다.")
    return path


# ============================================================
# 날짜 연속성 체크
# ============================================================

def check_date_continuity(data):
    start_date = data.index[0]
    end_date = data.index[-1]

    all_ts = pd.date_range(start_date, end_date, freq="1min")
    all_ts = all_ts.to_frame(index=False, name="ts")

    return pd.merge(all_ts, data, left_on="ts", right_index=True, how="left").set_index('ts')


# ============================================================
# IQR 필터링 함수
# ============================================================

def IQR_scale(df, columns):
    Q1 = df[columns].quantile(q=0.25)
    Q3 = df[columns].quantile(q=0.75)
    IQR = Q3 - Q1
    filters = [((df[col] <= Q3[col] + 3 * IQR[col]) & (df[col] >= Q1[col] - 3 * IQR[col])) for col in columns]
    combined_filter = np.logical_and.reduce(filters)
    df_IQR = df[combined_filter]
    print(f"No. of {columns}: {len(df)}, IQR: {len(df_IQR)}")
    return df_IQR


def IQR_filtering_per_column(series: pd.Series, m=1.5):
    Q1 = series.quantile(q=0.25)
    Q3 = series.quantile(q=0.75)
    IQR = Q3 - Q1
    filter_ = (series <= Q3 + m * IQR) & (series >= Q1 - m * IQR)
    series_IQR = series[filter_]
    print(f"No. of data: {len(series)}, IQR: {len(series_IQR)}")
    return filter_


# ============================================================
# Zero 필터링 함수
# ============================================================

def zero_filtering_per_column(series: pd.Series):
    filter_ = series > 0.1
    series_nonzero = series[filter_]
    print(f"No. of data: {len(series)}, Non-zero: {len(series_nonzero)}")
    return filter_


# ============================================================
# Holding 필터링 함수
# ============================================================

def Holding_filter(df, columns=None, threshold=60, verbose=True):
    """
    연속된 동일 값이 threshold 이상일 경우 False 처리.
    """
    if columns is None:
        columns = df.columns

    total_len = len(df)
    final_mask = np.ones(total_len, dtype=bool)
    log_messages = []

    for col in columns:
        values = df[col].values
        mask = np.ones(total_len, dtype=bool)

        start_idx = 0
        with tqdm(total=total_len, desc=f"Processing '{col}'", unit="rows") as pbar:
            while start_idx < total_len:
                current_value = values[start_idx]
                end_idx = start_idx + 1
                while (
                    end_idx < total_len
                    and not (pd.isna(values[end_idx]) or pd.isna(current_value))
                    and values[end_idx] == current_value
                ):
                    end_idx += 1
                run_length = end_idx - start_idx
                if run_length >= threshold:
                    mask[start_idx:end_idx] = False
                    if verbose:
                        log_messages.append(
                            f"[{col}] value '{current_value}' repeated {run_length} times "
                            f"({df.index[start_idx]} to {df.index[end_idx - 1]}) → masked"
                        )
                pbar.update(run_length)
                start_idx = end_idx
        final_mask &= mask

    tqdm.write(f"\nHolding filter created. Rows passing filter: {final_mask.sum()} / {len(df)}")
    if verbose and log_messages:
        tqdm.write("\nRepeated Value Log:")
        for msg in log_messages:
            tqdm.write(msg)
    return final_mask


def Holding_filter_per_column(series: pd.Series, threshold=60, verbose=True):
    """
    연속된 동일 값이 threshold 이상일 경우 False 처리 (단일 컬럼 버전).
    """
    total_len = len(series)
    mask = np.ones(total_len, dtype=bool)
    log_messages = []

    start_idx = 0
    with tqdm(total=total_len, desc=f"Processing series", unit="rows") as pbar:
        while start_idx < total_len:
            current_value = series.iloc[start_idx]
            end_idx = start_idx + 1
            while (
                end_idx < total_len
                and not (pd.isna(series.iloc[end_idx]) or pd.isna(current_value))
                and series.iloc[end_idx] == current_value
            ):
                end_idx += 1
            run_length = end_idx - start_idx
            if run_length >= threshold:
                mask[start_idx:end_idx] = False
                if verbose:
                    log_messages.append(
                        f"value '{current_value}' repeated {run_length} times "
                        f"({series.index[start_idx]} to {series.index[end_idx - 1]}) → masked"
                    )
            pbar.update(run_length)
            start_idx = end_idx

    tqdm.write(f"\nHolding filter created. Rows passing filter: {mask.sum()} / {len(series)}")
    if verbose and log_messages:
        tqdm.write("\nRepeated Value Log:")
        for msg in log_messages:
            tqdm.write(msg)
    return mask


# ============================================================
# 결측값 보간 함수
# ============================================================

def fill_missing_all_columns(data, cols=None):
    """
    시계열 인덱스 DataFrame의 결측값을 날짜×시간 피벗 기반으로 보간.
    """
    if cols is None:
        cols = data.select_dtypes(include='number').columns.tolist()

    all_filled = []
    for col in cols:
        cp_data = data[[col]].copy()
        cp_data["ts"] = cp_data.index
        cp_data["time"] = cp_data.index.time
        cp_data["day"] = cp_data.index.date

        pivot = cp_data.pivot(index="day", columns="time", values=col)
        pivot = pivot.ffill().ffill(axis=1)

        fill_df = pivot.stack().reset_index()
        fill_df["ts"] = pd.to_datetime(fill_df["day"].astype(str) + " " + fill_df["time"].astype(str))
        fill_df.rename(columns={0: col}, inplace=True)
        all_filled.append(fill_df[["ts", col]])

    result = all_filled[0]
    for df in all_filled[1:]:
        result = pd.merge(result, df, on="ts", how="outer")
    result = result.set_index("ts").sort_index()
    return result


# ============================================================
# 리샘플링 함수
# ============================================================

def resampling(df, resam_term):
    df = df.reset_index(drop=False)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.set_index('Datetime')
    df = df.resample(rule=resam_term).mean()
    df = df.dropna()
    print(f"No. of resampled: {len(df)}")
    return df


# ============================================================
# 데이터 검증 함수
# ============================================================

def validate_dataset(trainX, trainY, name="train"):
    def check_stats(label, array):
        print(f"\nChecking {label} ...")
        if isinstance(array, pd.DataFrame):
            array = array.values
        print(f"Shape: {array.shape}")
        print(f"NaN count: {np.isnan(array).sum()}")
        print(f"Inf count: {np.isinf(array).sum()}")
        if np.isnan(array).any() or np.isinf(array).any():
            print("NaN or Inf detected!")
        print(f"Max: {np.nanmax(array):.5f}")
        print(f"Min: {np.nanmin(array):.5f}")
        print(f"Mean: {np.nanmean(array):.5f}")
        print(f"Std: {np.nanstd(array):.5f}")
        if np.nanmax(np.abs(array)) > 1e6:
            print("Warning: Extreme value (>1e6) detected!")
        if np.nanstd(array) == 0:
            print("Warning: No variance — all values are the same.")

    check_stats(f"{name}X", trainX)
    check_stats(f"{name}Y", trainY)

    if name == "train":
        if is_minmax_data(trainX):
            print("trainX is Min-Max scaled.")
        elif is_standard_data(trainX):
            print("trainX is Standard scaled.")
        elif is_robust_data(trainX):
            print("trainX is Robust scaled.")
        else:
            print("trainX does not appear to be scaled.")


def is_minmax_data(trainX, feature_range=(0, 1), tol=1e-5):
    if isinstance(trainX, pd.DataFrame):
        trainX = trainX.values
    min_val = np.nanmin(trainX)
    max_val = np.nanmax(trainX)
    return (abs(min_val - feature_range[0]) < tol) and (abs(max_val - feature_range[1]) < tol)


def is_standard_data(trainX, tol=1e-5):
    if isinstance(trainX, pd.DataFrame):
        trainX = trainX.values
    return (abs(np.nanmean(trainX)) < tol) and (abs(np.nanstd(trainX) - 1) < tol)


def is_robust_data(trainX, lower_quantile=0.25, upper_quantile=0.75, tol=1e-5):
    if isinstance(trainX, pd.DataFrame):
        trainX = trainX.values
    q1 = np.nanpercentile(trainX, lower_quantile * 100)
    q3 = np.nanpercentile(trainX, upper_quantile * 100)
    return abs((q3 - q1) - 1) < tol


# ============================================================
# 상관관계 분석 함수
# ============================================================

def cal_corr(df, df_to_sequence, show_map=False):
    corr_matrix = df_to_sequence.corr()
    if show_map:
        import seaborn as sns
        sns.clustermap(corr_matrix, annot=True, cmap='RdYlBu_r', vmin=-1, vmax=1)
        plt.show()

    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), 1).astype(bool))
    ind_a, ind_b = np.where(abs(upper > 0.95))
    for i in range(len(ind_a)):
        print(f"Pearson correlation of {df['변수명'][ind_a[i]]} and {df['변수명'][ind_b[i]]} is higher than 0.95")
    return


# ============================================================
# Gaussian 분포 분리 함수
# ============================================================

def split_into_multiple_Gaussians(data_series, max_components=2):
    """
    다봉분포를 여러 단봉분포로 분리 (Gaussian Mixture Model 기반).
    """
    from sklearn.mixture import GaussianMixture

    data_df = pd.DataFrame(index=data_series.index)
    peaks = []
    data = data_series.dropna().values.reshape(-1, 1)
    lowest_bic = np.infty
    bic = []
    best_gmm = None
    best_n_components = 1

    for n_components in range(1, max_components + 1):
        gmm = GaussianMixture(n_components=n_components, covariance_type='full')
        gmm.fit(data)
        bic.append(gmm.bic(data))
        if bic[-1] < lowest_bic:
            lowest_bic = bic[-1]
            best_gmm = gmm
            best_n_components = n_components

    print(f"Optimal number of components: {best_n_components}")
    labels = best_gmm.predict(data)
    data_df['value'] = data_series.dropna()
    data_df['label'] = labels

    for i in range(best_n_components):
        peaks.append(data_df[data_df['label'] == i]['value'])

    plt.figure(figsize=(10, 6))
    plt.title(data_series.name)
    plt.hist(data, bins=30, density=True, alpha=0.5, color='gray')
    x = np.linspace(np.min(data), np.max(data), 1000).reshape(-1, 1)
    logprob = best_gmm.score_samples(x)
    responsibilities = best_gmm.predict_proba(x)
    pdf = np.exp(logprob)
    pdf_individual = responsibilities * pdf[:, np.newaxis]
    plt.plot(x, pdf, '-k', label='Mixture Density')
    for i in range(best_n_components):
        plt.plot(x, pdf_individual[:, i], '--', label=f'Component {i+1}')
    plt.xlabel('Value')
    plt.ylabel('Density')
    plt.legend()
    plt.show()
    return peaks, best_gmm


# ============================================================
# XGBoost용 lag 기반 피처 생성
# ============================================================

# 기본 lag 목록: 최근 30분 + 주요 시점
_DEFAULT_LAGS    = [1, 2, 3, 6, 12, 24]
_ROLLING_WINDOWS = [12]              # 10분 단위: 2h rolling mean만 사용


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

    # rolling 통계 피처 (shift(1)로 미래 누수 방지, mean만 사용)
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
