"""mass_balance.py의 물리 시뮬레이션(질량보존)이 남기는 잔차(실제-시뮬레이션)를
작은 회귀 모델로 보정하는 모듈 — Stage 2 하이브리드("물리 + ML 잔차 보정")의
ML 절반.

mass_balance.backtest_multistep()으로 이미 "물리 모델이 persistence보다
나은지"는 확인했다(H7, 역산 면적 기준으로 나음). 이 모듈은 그 물리 모델이
남기는 오차 자체에 아직 배울 수 있는 패턴(계절성, 최근 추세 등)이 남아있는지
확인하고, 있다면 작은 Ridge 회귀로 걷어낸다 — 물리 법칙이 못 담아내는 부분
(예: 저수조 형상이 완전한 직육면체가 아니라 수위에 따라 실효 면적이 달라짐,
증발, 계측 안 되는 소규모 누수/월류 등)을 데이터로 보정하는 셈이다.

굳이 이 저장소의 메인 학습 파이프라인(pipeline.py/model.py, PyTorch 시퀀스
모델)을 쓰지 않고 sklearn.linear_model.Ridge로 시작하는 이유: 잔차가 정말
학습할 가치가 있는 패턴인지부터 싸고 빠르게 확인하려는 것이다 — 여기서
유의미한 skill이 나오면 나중에 더 표현력 있는 모델(GradientBoosting, 작은
신경망)로 키우는 건 쉽지만, 처음부터 무거운 모델을 쓰면 "정말 배울 게
있어서 좋아진 건지, 그냥 모델이 커서 우연히 좋아진 건지" 구분하기 어렵다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .mass_balance import simulate_level
from .metrics import skill_score

MODEL_TYPES = ("ridge", "gbr")  # fit_residual_model()의 model_type이 고르는 값

# build_residual_dataset()이 만드는 feature 목록 — fit_residual_model()/
# evaluate_residual_correction()의 기본값과 항상 같이 맞춰서 바꿀 것.
FEATURE_COLS: list[str] = [
    "level0", "recent_dH", "recent_inflow_mean", "recent_outflow_mean", "hour_sin", "hour_cos",
]


def build_residual_dataset(
    level: pd.Series,
    inflow: pd.Series,
    outflow: pd.Series,
    area_m2: float,
    freq_minutes: float,
    horizon_steps: int,
    stride: int = 1,
    trend_window_steps: int = 12,
) -> pd.DataFrame:
    """각 origin(예측 시작 시점)마다 "그 시점에 이미 알 수 있는 정보"로 feature를,
    "물리 시뮬레이션이 그 시점 이후 horizon_steps만큼 틀린 정도"를 target
    (residual = actual - simulated)으로 모아 하나의 DataFrame으로 돌려준다.

    feature는 일부러 단순하게 잡았다 — 지금 이 시점의 수위(level0), 최근
    trend_window_steps(기본 12스텝=1시간) 동안의 수위 변화량(recent_dH)과
    평균 유입/유출(recent_inflow_mean/recent_outflow_mean), 그리고 하루 중
    시각(hour_sin/hour_cos, taglist 분석에서 확인된 뚜렷한 일간 주기성을
    반영). "최근 추세가 물리 모델의 오차와 관련 있는가", "시간대에 따라
    오차 경향이 다른가"를 볼 수 있으면 충분하다는 전제다 — 부족하면 나중에
    FEATURE_COLS에 항목을 추가하면 된다.

    mass_balance.backtest_multistep()과 같은 방식으로 origin/horizon 구간에
    결측이 있으면 조용히 건너뛴다. simulated/actual/level0(=persistence
    baseline)도 결과에 같이 남겨서 evaluate_residual_correction()이 별도
    재계산 없이 바로 쓸 수 있게 한다.
    """
    idx = level.index
    n = len(idx)
    rows = []
    for start in range(trend_window_steps, n - horizon_steps, stride):
        end = start + horizon_steps
        level0 = level.iloc[start]
        if pd.isna(level0):
            continue
        inflow_win = inflow.iloc[start + 1 : end + 1]
        outflow_win = outflow.iloc[start + 1 : end + 1]
        if inflow_win.isna().any() or outflow_win.isna().any():
            continue
        actual = level.iloc[end]
        if pd.isna(actual):
            continue

        recent_inflow = inflow.iloc[start - trend_window_steps + 1 : start + 1]
        recent_outflow = outflow.iloc[start - trend_window_steps + 1 : start + 1]
        recent_level_start = level.iloc[start - trend_window_steps]
        if recent_inflow.isna().any() or recent_outflow.isna().any() or pd.isna(recent_level_start):
            continue

        simulated = float(simulate_level(level0, inflow_win, outflow_win, area_m2, freq_minutes).iloc[-1])
        ts = idx[start]
        hour_frac = ts.hour + ts.minute / 60.0
        rows.append(
            {
                "origin": ts, "target_time": idx[end],
                "level0": float(level0),
                "recent_dH": float(level0 - recent_level_start),
                "recent_inflow_mean": float(recent_inflow.mean()),
                "recent_outflow_mean": float(recent_outflow.mean()),
                "hour_sin": float(np.sin(2 * np.pi * hour_frac / 24)),
                "hour_cos": float(np.cos(2 * np.pi * hour_frac / 24)),
                "simulated": simulated, "actual": float(actual),
                "residual": float(actual) - simulated,
            }
        )
    return pd.DataFrame(
        rows,
        columns=["origin", "target_time", *FEATURE_COLS, "simulated", "actual", "residual"],
    )


def chronological_split(dataset: pd.DataFrame, train_ratio: float = 0.7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """origin 시간순으로 정렬한 뒤 앞 train_ratio를 train, 나머지를 test로
    나눈다 — 이 저장소의 메인 파이프라인(split.py 등)과 같은 원칙(미래 데이터로
    과거를 학습하지 않도록 시간순 분할, 셔플 안 함)을 그대로 따른다."""
    ordered = dataset.sort_values("origin").reset_index(drop=True)
    cut = int(len(ordered) * train_ratio)
    return ordered.iloc[:cut].reset_index(drop=True), ordered.iloc[cut:].reset_index(drop=True)


def fit_residual_model(
    dataset: pd.DataFrame,
    feature_cols: list[str] = FEATURE_COLS,
    model_type: str = "ridge",
    alpha: float = 1.0,
    gbr_kwargs: dict | None = None,
) -> RegressorMixin:
    """dataset(보통 chronological_split의 train 쪽)으로 잔차를 예측하는 모델을
    학습한다. model_type="ridge"(기본)면 StandardScaler + Ridge, "gbr"이면
    GradientBoostingRegressor(스케일링 불필요 — 트리 분할은 단조 변환에
    불변이라 표준화해도 안 해도 결과가 같다).

    StandardScaler가 ridge에 필요한 이유: FEATURE_COLS의 스케일이 서로 크게
    다르다(level0/hour_sin/hour_cos는 대략 -1~10 범위인데 recent_inflow_mean/
    recent_outflow_mean은 수천 단위) — Ridge의 L2 페널티는 계수 크기를
    그대로 비교하므로, 스케일 안 맞추면 원래 스케일이 큰 feature는 계수가
    자동으로 작아져야 같은 영향력을 내는데 그 작은 계수가 오히려 더 크게
    벌점을 받는 셈이 돼서 불공평하게 눌린다.

    model_type="gbr"을 추가한 이유(실측): H7 잔차에 ridge를 실제로 붙여보니
    skill_vs_simulated가 1h -0.18, 3h +0.008, 6h -0.036으로 사실상 도움이
    안 됐다(스케일링 전/후 거의 동일 — 스케일 문제가 아니라 이 6개 feature로
    설명되는 "선형" 관계가 거의 없다는 뜻이었다). ridge가 놓치는 비선형/
    상호작용 관계(예: "유입이 평소보다 많으면서 동시에 야간일 때만 오차가
    커진다" 같은 조건부 패턴)가 있는지 트리 기반 모델로 다시 확인하기 위해
    추가했다.

    alpha(ridge의 L2 정규화 강도)는 feature가 6개뿐이고 표본은 많을 것으로
    예상돼(수만~수십만) 기본값 1.0이면 충분히 보수적이다. gbr_kwargs로
    GradientBoostingRegressor 생성자에 넘길 값을 덮어쓸 수 있다 — 기본값
    (n_estimators=200, max_depth=3, learning_rate=0.05)은 표본 수 대비
    과적합을 피하려고 일부러 얕고 보수적으로 잡았다.
    """
    if model_type not in MODEL_TYPES:
        raise ValueError(f"model_type은 {MODEL_TYPES} 중 하나여야 합니다: {model_type!r}")

    X = dataset[feature_cols].to_numpy(dtype=float)
    y = dataset["residual"].to_numpy(dtype=float)

    if model_type == "ridge":
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    else:
        kwargs = {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05, "random_state": 42}
        kwargs.update(gbr_kwargs or {})
        model = GradientBoostingRegressor(**kwargs)
    model.fit(X, y)
    return model


def evaluate_residual_correction(
    dataset: pd.DataFrame, model: RegressorMixin, feature_cols: list[str] = FEATURE_COLS
) -> dict:
    """dataset(보통 chronological_split의 test 쪽, 즉 학습에 안 쓰인 구간)에서
    "물리 모델 + ML 잔차 보정"이 "물리 모델만" 대비, 그리고 persistence(level0)
    대비 얼마나 나은지를 MAE/skill_score(metrics.skill_score와 동일 정의,
    1 - model_mae/baseline_mae)로 요약한다.

    skill_vs_simulated가 이 함수의 핵심 판단 기준이다 — 0보다 크면 "물리
    시뮬레이션 위에 ML이 실제로 뭔가를 더 배웠다"는 뜻이고, 0 근처거나
    음수면 "물리 모델 오차엔 이 feature들로 잡을 수 있는 패턴이 딱히 없다"
    (Ridge가 배울 게 없어서 사실상 0을 예측하거나, 과적합해서 test에선
    오히려 해가 됐다)는 뜻이다.

    dataset이 비어있으면(호출부가 미리 len() 확인 안 해도 되게) 전부 nan을
    돌려준다.
    """
    if len(dataset) == 0:
        return {
            "n": 0, "mae_corrected": float("nan"), "mae_simulated": float("nan"), "mae_persistence": float("nan"),
            "skill_vs_persistence": float("nan"), "skill_vs_simulated": float("nan"),
        }
    predicted_residual = model.predict(dataset[feature_cols].to_numpy(dtype=float))
    corrected = dataset["simulated"].to_numpy(dtype=float) + predicted_residual
    actual = dataset["actual"].to_numpy(dtype=float)
    simulated = dataset["simulated"].to_numpy(dtype=float)
    level0 = dataset["level0"].to_numpy(dtype=float)  # persistence baseline

    mae_corrected = float(np.mean(np.abs(actual - corrected)))
    mae_simulated = float(np.mean(np.abs(actual - simulated)))
    mae_persistence = float(np.mean(np.abs(actual - level0)))
    return {
        "n": len(dataset),
        "mae_corrected": mae_corrected, "mae_simulated": mae_simulated, "mae_persistence": mae_persistence,
        "skill_vs_persistence": skill_score(mae_corrected, mae_persistence),
        "skill_vs_simulated": skill_score(mae_corrected, mae_simulated),
    }
