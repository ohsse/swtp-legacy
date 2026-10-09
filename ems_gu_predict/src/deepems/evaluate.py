"""Test set에서 모델 vs baseline 비교 리포트를 만든다.

이 파일이 이번 재설계의 핵심 산출물이다: "naive forecasting이
높게 나올 수 있다"는 문제에 대한 답을, 리포트에 숫자로 남긴다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from .baselines import moving_average_forecast, persistence_forecast, seasonal_naive_forecast
from .config import Config
from .metrics import build_comparison_report
from .pipeline import PreparedData


def _inverse_transform(pipeline, target_cols: list[str], arr: np.ndarray) -> np.ndarray:
    """[N, horizon, n_targets] 스케일 값을 타깃별로 역변환."""
    out = np.empty_like(arr, dtype=np.float64)
    for t, col in enumerate(target_cols):
        flat = arr[:, :, t].reshape(-1)
        out[:, :, t] = pipeline.inverse_transform_col(col, flat).reshape(arr.shape[0], arr.shape[1])
    return out


@torch.no_grad()
def model_predict(model: torch.nn.Module, X: np.ndarray, device: str, batch_size: int = 512) -> np.ndarray:
    model.eval()
    preds = []
    for i in range(0, len(X), batch_size):
        xb = torch.from_numpy(X[i : i + batch_size]).to(device)
        preds.append(model(xb).cpu().numpy())
    return np.concatenate(preds, axis=0) if preds else np.empty((0,))


# 스케일된([0,1]) target 윈도우의 horizon 구간 표준편차가 이보다 작으면 "사실상
# 상수"로 본다. 스케일 공간에서 재는 이유는 태그마다 실제 단위 스케일이 크게
# 달라서(유량은 수백, 압력은 한 자리 등) 실제 단위 기준 절대 문턱값 하나로는
# 공정하지 않기 때문 — evaluate_test_split 참고.
FLAT_WINDOW_STD_THRESHOLD = 1e-6


def evaluate_test_split(
    cfg: Config, data: PreparedData, model: torch.nn.Module, device: str
) -> pd.DataFrame:
    ws = data.windows["test"]
    if len(ws.X) == 0:
        raise ValueError("test split has no usable windows (구간이 너무 짧거나 결측이 많음)")

    model_pred_scaled = model_predict(model, ws.X, device)
    persistence_scaled = persistence_forecast(ws.X, data.target_idx, cfg.window.horizon)
    movavg_scaled = moving_average_forecast(ws.X, data.target_idx, cfg.window.horizon, k=10)
    seasonal_scaled = seasonal_naive_forecast(
        data.split_frames["test"], data.target_cols, ws.origin_ts, cfg.window.horizon, cfg.data.freq
    )

    # 정답 자체가 그 윈도우의 horizon 구간 내내 사실상 상수인 (윈도우, target) 조합을
    # 표시한다 — stuck_value_impute_columns로 장기 고정 구간을 중앙값으로 채운
    # 태그가 test 구간과 겹치면 실제로 발생한다(gu_db.yaml의 P6에서 test 윈도우의
    # 51%가 여기 해당했다). 그런 구간은 persistence 등 어떤 baseline이든 trivial하게
    # 완벽히 맞히므로, skill_score(MAE 비율)가 "모델이 훨씬 못한다"는 착시를 만들
    # 수 있다 — build_comparison_report의 *_active 컬럼이 이 구간을 뺀 참고 지표를
    # 따로 보여준다(원래 지표는 그대로 유지 — metrics.per_horizon_metrics 참고).
    flat_window_mask = ws.y.std(axis=1) < FLAT_WINDOW_STD_THRESHOLD  # [N, n_targets]

    y_true = _inverse_transform(data.pipeline, data.target_cols, ws.y)
    preds_real = {
        "model": _inverse_transform(data.pipeline, data.target_cols, model_pred_scaled),
        "persistence": _inverse_transform(data.pipeline, data.target_cols, persistence_scaled),
        "moving_average": _inverse_transform(data.pipeline, data.target_cols, movavg_scaled),
        "seasonal_naive": _inverse_transform(data.pipeline, data.target_cols, seasonal_scaled),
    }

    return build_comparison_report(y_true, preds_real, data.target_cols, flat_window_mask=flat_window_mask)
