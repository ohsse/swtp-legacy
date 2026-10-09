"""실제 물리 단위 오차 지표 + baseline 대비 skill score.

기존 노트북들의 "정확도 = (1 - MAE) * 100" 은 MinMax(0~1) 스케일
값 기준이라 (a) 물리 단위로 오차가 얼마나 되는지 감이 안 오고
(b) 값이 완만한 신호에서는 naive 예측도 스케일 MAE가 작아 정확도가
높게 나온다. 여기서는 반드시 스케일 역변환된 실제 단위로 MAE/RMSE/
SMAPE/R²를 계산하고, naive baseline 대비 skill score를 같이 낸다.

skill_score = 1 - MAE(model) / MAE(baseline)
  > 0 : baseline보다 낫다
  = 0 : baseline과 동일
  < 0 : baseline보다 못하다 (모델을 안 쓰느니만 못함)

R²는 skill_score와 목적이 다르다: baseline이 아니라 "그 구간의
평균값만 예측하는 것"과 비교한다 (1 - SS_res/SS_tot). horizon이
짧아 목표 변수가 거의 상수에 가까우면(=naive가 강력하면) R²도
1에 가깝게 나오기 쉬우므로, R² 하나만 보고 "잘 맞춘다"고 판단하지
말고 skill_score(진짜 비교 대상인 naive 대비 우위)와 같이 봐야 한다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.nanmean(np.abs(y_true - y_pred)))


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.nanmean((y_true - y_pred) ** 2)))


def _smape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-6) -> float:
    """Symmetric MAPE (0~200%). 유량처럼 값이 0 근처로 내려가는 변수는
    보통의 MAPE(|y_true|로만 나눔)가 0 나눗셈에 가까워져 수백만% 로
    터진다 — 분모에 |y_pred|도 함께 넣어 이를 막는다."""
    denom = np.clip((np.abs(y_true) + np.abs(y_pred)) / 2, eps, None)
    return float(np.nanmean(np.abs(y_true - y_pred) / denom) * 100)


def _mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-6) -> float:
    """일반적인 MAPE(0~무한대, %). 분모가 |y_true|뿐이라, sMAPE와 달리
    y_true가 0 근처로 내려가는 유량 계열 target(O7/Q7 등)에서는 수백~수만%로
    치솟을 수 있다(위 _smape 주석 참고 — 그래서 sMAPE를 이 프로젝트의
    기본 지표로 써왔다). 2026-09-11 사용자가 모델 비교 지표로 MAPE를
    명시적으로 요청해서 추가했지만, 값이 0 근처를 지나는 target에서는
    SMAPE_%/RMSE 쪽을 더 신뢰할 것 — MAPE_%가 비정상적으로 크게 나오는 건
    모델이 나빠서가 아니라 그 구간에 실측값이 0에 가까운 시점이 많다는
    뜻일 수 있다."""
    denom = np.clip(np.abs(y_true), eps, None)
    return float(np.nanmean(np.abs(y_true - y_pred) / denom) * 100)


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """결정계수. seasonal_naive처럼 NaN이 섞일 수 있는 예측을 감안해
    두 배열 모두 유효한 샘플만 사용한다. 표본이 2개 미만이거나
    y_true 분산이 0이면(그 구간에서 타깃이 상수) 정의되지 않으므로 NaN."""
    mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
    yt, yp = y_true[mask], y_pred[mask]
    if yt.size < 2:
        return float("nan")
    ss_tot = np.sum((yt - yt.mean()) ** 2)
    if ss_tot == 0:
        return float("nan")
    ss_res = np.sum((yt - yp) ** 2)
    return float(1.0 - ss_res / ss_tot)


def per_horizon_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, target_cols: list[str], flat_window_mask: np.ndarray | None = None
) -> pd.DataFrame:
    """y_true, y_pred: [N, horizon, n_targets] (실제 단위). horizon-step x target 별 MAE/RMSE/SMAPE/R².

    flat_window_mask: [N, n_targets] bool, True면 그 (윈도우, target) 조합의 정답
    구간이 사실상 상수였다는 뜻 — 장기 고정 구간을 중앙값으로 채운 태그
    (config.py의 stuck_value_impute_columns 참고)가 test 구간과 겹치면 실제로
    발생한다. 정답이 상수면 어떤 baseline이든(특히 persistence) 그 구간을
    trivial하게 맞히므로, 그 구간을 포함해서 계산한 MAE 비율(skill_score)은
    baseline이 우연히 완벽한 것뿐인데 모델이 "훨씬 못한다"는 착시를 만들 수
    있다(실측: gu_db.yaml P6 — 전체 skill -0.71이었지만, 이 구간을 뺀
    "실질" skill은 -0.18). R2가 이미 ss_tot==0(그 구간에서 target이 상수)이면
    NaN으로 처리하는 것과 같은 이유다.

    그렇다고 이 구간을 원래 MAE/RMSE/SMAPE/R2/skill_vs_*에서 빼지는 않는다 —
    "실제 이상상황에서 모델이 얼마나 틀리는지를 평가지표에서 감추지 않는다"는
    이 프로젝트의 원칙(data.py 상단 docstring) 때문이다. 대신 MAE_active/
    n_active(및 이를 쓰는 skill_vs_*_active) 컬럼을 별도로 추가해서, 기존
    지표는 그대로 두고 "정답이 실제로 움직인 구간만" 본 참고 지표를 나란히
    보여준다. flat_window_mask가 None이면(기본) 이 추가 컬럼은 그냥 원래
    값과 같다.
    """
    n, horizon, n_targets = y_true.shape
    rows = []
    for h in range(horizon):
        for t, name in enumerate(target_cols):
            yt, yp = y_true[:, h, t], y_pred[:, h, t]
            row = {
                "horizon_step": h + 1,
                "target": name,
                "MAE": _mae(yt, yp),
                "RMSE": _rmse(yt, yp),
                "MAPE_%": _mape(yt, yp),
                "SMAPE_%": _smape(yt, yp),
                "R2": _r2(yt, yp),
                "n": int(np.sum(~np.isnan(yt) & ~np.isnan(yp))),
            }
            if flat_window_mask is not None:
                active = ~flat_window_mask[:, t]
                row["MAE_active"] = _mae(yt[active], yp[active])
                row["n_active"] = int(np.sum(active & ~np.isnan(yt) & ~np.isnan(yp)))
            rows.append(row)
    return pd.DataFrame(rows)


def summarize_by_target(per_horizon_df: pd.DataFrame) -> pd.DataFrame:
    """`per_horizon_metrics()`(또는 `build_comparison_report()`)가 낸,
    horizon_step별로 늘어선 표를 target(과 있으면 method)별로 horizon 전체
    평균 낸 요약표로 접는다 — 8개 후보 모델을 O7/Q7/H7 각각에서 "종합적으로
    어느 쪽이 나은지" 한눈에 비교하려면 horizon_step 72개(6시간, 5분 단위)를
    낱낱이 보는 것보다 이 요약이 더 실용적이다.

    n(표본 수)은 합, 나머지 수치 컬럼(MAE/RMSE/MAPE_%/SMAPE_%/R2/skill_vs_*
    등 — 어떤 컬럼이 있든 자동으로 처리)은 horizon_step에 대해 단순평균한다.
    R2/skill_score는 원래 horizon_step마다 별도로 정의된 값이라, 이 단순평균은
    "그 target에서 평균적으로 어느 정도인가"를 보는 근사치이지 전체 구간을
    다시 계산한 정확한 R2/skill은 아니다(예: horizon별 표본 수 n이 다르면
    가중평균이 더 정확할 수 있음) — 모델 후보를 빠르게 순위 매기는 용도로
    충분하다는 전제.
    """
    group_cols = [c for c in ("target", "method") if c in per_horizon_df.columns]
    if not group_cols:
        raise ValueError("per_horizon_df에 'target' 컬럼이 없습니다. per_horizon_metrics() 결과가 맞는지 확인할 것.")
    value_cols = [c for c in per_horizon_df.columns if c not in group_cols and c != "horizon_step"]
    agg = {c: ("sum" if c == "n" else "mean") for c in value_cols}
    return per_horizon_df.groupby(group_cols, as_index=False).agg(agg)


def skill_score(model_mae: float, baseline_mae: float) -> float:
    if baseline_mae == 0 or np.isnan(baseline_mae):
        return float("nan")
    return 1.0 - (model_mae / baseline_mae)


def build_comparison_report(
    y_true: np.ndarray,
    preds: dict[str, np.ndarray],
    target_cols: list[str],
    flat_window_mask: np.ndarray | None = None,
) -> pd.DataFrame:
    """preds: {"model": arr, "persistence": arr, "moving_average": arr, "seasonal_naive": arr}
    (모두 [N, horizon, n_targets], 실제 단위). model을 각 baseline과 skill score로 비교한 표를 만든다.

    flat_window_mask는 per_horizon_metrics로 그대로 전달된다 — MAE_active/
    n_active가 채워지면 skill_vs_*_active(그 구간을 뺀 skill_score)도 같이
    계산한다. 자세한 이유는 per_horizon_metrics 참고.
    """
    per_method = {name: per_horizon_metrics(y_true, arr, target_cols, flat_window_mask) for name, arr in preds.items()}
    for name, df in per_method.items():
        df["method"] = name

    combined = pd.concat(per_method.values(), ignore_index=True)

    if "model" in per_method:
        model_df = per_method["model"].set_index(["horizon_step", "target"])
        for name in preds:
            if name == "model":
                continue
            base_df = per_method[name].set_index(["horizon_step", "target"])
            col = f"skill_vs_{name}"
            combined.loc[combined["method"] == "model", col] = combined.loc[
                combined["method"] == "model"
            ].apply(
                lambda r: skill_score(
                    model_df.loc[(r["horizon_step"], r["target"]), "MAE"],
                    base_df.loc[(r["horizon_step"], r["target"]), "MAE"],
                ),
                axis=1,
            )
            if flat_window_mask is not None:
                active_col = f"skill_vs_{name}_active"
                combined.loc[combined["method"] == "model", active_col] = combined.loc[
                    combined["method"] == "model"
                ].apply(
                    lambda r: skill_score(
                        model_df.loc[(r["horizon_step"], r["target"]), "MAE_active"],
                        base_df.loc[(r["horizon_step"], r["target"]), "MAE_active"],
                    ),
                    axis=1,
                )
    return combined
