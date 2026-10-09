"""단순 baseline 예측기.

기존 코드에는 이 파일에 해당하는 것이 전혀 없었다 — 그래서 학습된
Attention-LSTM의 "정확도 95%"가 그냥 직전 값을 유지하는 것보다
나은지 확인할 방법이 없었다. evaluate.py는 아래 baseline들과
모델을 실제 물리 단위(스케일 역변환 후) 오차로 나란히 비교해서
리포트한다.

세 가지를 제공한다:
- persistence: 마지막 관측값을 horizon 내내 그대로 사용.
- moving_average: 최근 k분 평균을 horizon 내내 사용.
- seasonal_naive: 정확히 하루(또는 설정한 계절 주기) 전 같은 시각의
  값. 상수 수요 패턴 대신 일간 주기를 반영하는 좀 더 어려운
  baseline이라, 모델이 이것보다도 못하면 일간 패턴조차 못 배운 것.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def persistence_forecast(X: np.ndarray, target_idx: list[int], horizon: int) -> np.ndarray:
    last = X[:, -1, target_idx]  # [N, n_targets]
    return np.repeat(last[:, None, :], horizon, axis=1)


def compute_inverse_persistence_weights(
    X: np.ndarray, y: np.ndarray, target_idx: list[int], eps: float = 1e-3, max_weight: float | None = 3.0
) -> np.ndarray:
    """target별 persistence(직전값 유지) MAE의 역수를, 평균이 1이 되도록
    정규화해서 반환한다 — train.py가 학습 loss의 target별 가중치로 쓴다
    (표준적인 inverse-variance/inverse-error 멀티태스크 가중치).

    스케일된 [0,1] 공간 기준으로 계산한다 (학습 loss도 그 공간에서 계산되므로).
    target이 여러 개고 예측 난이도가 서로 크게 다를 때(예: GU 시트처럼 24개
    target을 한 모델로), 원래 잡음이 크고 예측하기 어려운(=persistence MAE가
    큰) target은 웬만큼 잘 학습된 모델이라도 오차(따라서 제곱오차)가 자연히
    더 크다 — 가중치 없이 평균 MSE를 쓰면 이 "원래 시끄러운" target의 큰
    오차값이 손실을 지배해서, 상대적으로 깨끗하고 정밀하게 맞출 수 있는
    target의 미세한 개선 신호가 그 안에 묻혀버린다. 그래서 어려운(MAE 큰)
    target의 가중치는 낮추고, 쉬운(MAE 작은) target의 가중치는 높인다.
    eps는 이미 완벽에 가깝게 예측되는(MAE≈0) target의 가중치가 무한대로
    발산하는 것을 막는 하한이다.

    max_weight(신규)는 그 반대 방향의 문제를 막는다 — eps 하나만으로는 부족할
    수 있다. 실제로 gu_db.yaml 학습에서 `P6`(2023~2025년 중반 train 기간 동안
    실제로 안정적이었던 신호 — persistence MAE 0.0014)과 `H7`(원래도 거의
    완벽하게 매끄러운 수위 신호, persistence MAE 0.0021)이 각각 정규화 가중치
    6.58, 5.19를 받았다 — 나머지 16개 target(0.1~0.66)의 10배 이상이라, 전체
    손실의 약 65%를 이 둘이 차지했다. 그 결과 이 두 target이 실제 학습 후
    skill_vs_persistence가 -1.2~-1.7로 크게 나빠졌다(다른 target 학습을
    밀어내고, "이미 거의 완벽한" 신호에서 억지로 더 줄이려다 과적합).
    max_weight로 정규화 가중치 상한을 두면(기본 3.0 — 나머지 target들의
    자연스러운 상위권과 비슷한 수준), 이런 극단적으로 예측하기 쉬운 target이
    손실을 독식하는 걸 막는다. None이면 상한 없음(기존 동작).

    주의(실측): 이 cap을 더 낮추면(예: 2.0) 항상 더 좋아지는 건 아니다.
    H7은 test 전체에서 persistence가 항상 거의 완벽해서(진짜 개선 여지가
    없는 신호) cap을 낮출수록 계속 나아졌지만(skill -0.66 -> -0.29),
    P6은 다르다 — P6의 낮은 train MAE는 stuck_value_impute_columns의 median
    채우기 때문이 아니라(그 장기 고정 구간은 2025-09부터라 train(~2025-07
    까지)엔 거의 안 걸림, 실측 flat 비율 0.01%) train 기간 동안 실제로
    안정적이었던 것뿐이다. 그래서 cap을 낮춰 P6의 가중치를 뺏으면 모델이
    P6 학습에 덜 신경 쓰게 되어, test의 실제 변동 구간(evaluate.py의
    flat_window_mask로 장기 고정 구간을 뺀 부분) 예측이 오히려 나빠졌다
    (skill_active -0.18 -> -0.34). 즉 이 두 target은 "가중치가 크다"는
    증상은 같아도 원인이 다르다 — cap 값을 바꿀 때마다 test_report.csv의
    skill_vs_persistence_active로 실제 방향을 확인할 것.
    """
    pred = persistence_forecast(X, target_idx, y.shape[1])
    mae = np.mean(np.abs(pred - y), axis=(0, 1))  # [n_targets]
    weights = 1.0 / (mae + eps)
    weights = weights / weights.mean()
    if max_weight is not None:
        # 주의: 여기서 clip 후 다시 "평균 1"로 재정규화하면 안 된다 — 클리핑으로
        # 줄어든 만큼을 나머지 전체에 다시 나눠 곱하는 셈이라, 방금 max_weight로
        # 눌러놓은 값 자체가 재정규화 과정에서 다시 max_weight를 넘어 튀어
        # 오른다(실제로 max_weight=3.0으로 클리핑했는데 재정규화 후 4.41이
        # 나온 걸 실측으로 확인함). clip만 하고 끝낸다 — 평균이 1보다 약간
        # 작아질 수 있지만(이번 P6/H7 사례에서 clip 전 18 -> clip 후 12.23,
        # 평균 0.68), 이건 전체 손실 크기를 균일하게 살짝 줄이는 정도라
        # target 간 상대적 균형을 왜곡하지 않는다 — 원래 문제(가중치 하나가
        # 손실을 독식)보다 훨씬 무해하다.
        weights = np.minimum(weights, max_weight)
    return weights.astype(np.float32)


def moving_average_forecast(
    X: np.ndarray, target_idx: list[int], horizon: int, k: int = 10
) -> np.ndarray:
    k = min(k, X.shape[1])
    avg = X[:, -k:, target_idx].mean(axis=1)
    return np.repeat(avg[:, None, :], horizon, axis=1)


def seasonal_naive_forecast(
    df: pd.DataFrame,
    target_cols: list[str],
    origin_ts: np.ndarray,
    horizon: int,
    freq: str,
    season: pd.Timedelta = pd.Timedelta(days=1),
) -> np.ndarray:
    """origin_ts(예측 시작 시점) 기준 (origin - season + k*freq) 값을 사용.
    해당 시점이 df에 없으면(구간 경계 등) NaN으로 채워, 집계 시
    nanmean으로 그 샘플만 제외되도록 한다.
    """
    freq_delta = pd.Timedelta(freq)
    lag_steps = int(round(season / freq_delta))
    lookup = df[target_cols]
    n = len(origin_ts)
    out = np.full((n, horizon, len(target_cols)), np.nan, dtype=np.float32)
    idx = lookup.index
    for i, ts in enumerate(pd.to_datetime(origin_ts)):
        base = ts - lag_steps * freq_delta
        for k in range(horizon):
            t = base + (k + 1) * freq_delta
            if t in idx:
                out[i, k, :] = lookup.loc[t].to_numpy()
    return out
