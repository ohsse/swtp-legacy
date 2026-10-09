"""Stage 1(O7/Q7 예측) + Stage 2(H7 물리+잔차보정) + Stage 3(레버 추천)를
`preprocess.py`가 준비한 데이터와 `train.py`가 만든 아티팩트로 실행해서
"한 사이클(한 origin 기준) 추천 한 건"을 만든다.

DB/모델 파일 로딩(`schedule.py`가 담당)과 계산 자체를 분리해뒀다 — 여기 있는
함수들은 이미 로딩된 객체(`LoadedArtifacts`, `OfflineArtifacts`, `DataFrame`)만
받으므로 합성 데이터로 온전히 단위테스트할 수 있다(`tests/test_scripts_analysis.py`).
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# train.py(형제 모듈, OfflineArtifacts)를 임포트하므로 이 파일 자신의 디렉터리도
# sys.path에 있어야 한다 — schedule.py가 먼저 넣어주는 경우가 대부분이지만,
# 이 모듈만 단독으로 임포트해도(다른 진입점, REPL 등) 깨지지 않도록 스스로도
# 넣는다(다른 scripts/*.py가 src/를 스스로 넣는 것과 같은 원칙 — 호출자가
# sys.path를 미리 맞춰뒀을 거라 가정하지 않는다).
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from deepems.infer import LoadedArtifacts, predict_next_horizon  # noqa: E402
from deepems.metrics import per_horizon_metrics, summarize_by_target  # noqa: E402
from deepems.recommend import (  # noqa: E402
    compute_target_band,
    lever_has_room,
    recommend_for_band,
    simulate_h7_with_intervention,
)
from deepems.residual_model import FEATURE_COLS as RESIDUAL_FEATURE_COLS  # noqa: E402
from deepems.taglist import LEVER_PHYSICAL_BOUNDS  # noqa: E402

from train import OfflineArtifacts  # noqa: E402


def residual_features_at(
    filled: pd.DataFrame, level_col: str, inflow_col: str, outflow_col: str, trend_window_steps: int,
) -> np.ndarray | None:
    """`residual_model.FEATURE_COLS`와 정확히 같은 순서/정의로, `filled`의 마지막
    시점을 기준(origin)삼아 잔차모델 입력 feature 한 행을 만든다
    (`residual_model.build_residual_dataset`의 한 origin 계산과 같은 식 — 거기선
    여러 origin을 훑지만, 여기선 "지금"이라는 origin 하나만 필요하다).

    trend_window_steps만큼의 과거가 없거나 그 구간에 결측이 있으면 None을
    돌려준다 — 호출부가 잔차보정 없이(물리모델만으로) 진행하게 한다.
    """
    if len(filled) <= trend_window_steps:
        return None
    level0 = filled[level_col].iloc[-1]
    recent_level_start = filled[level_col].iloc[-1 - trend_window_steps]
    recent_inflow = filled[inflow_col].iloc[-trend_window_steps:]
    recent_outflow = filled[outflow_col].iloc[-trend_window_steps:]
    if pd.isna(level0) or pd.isna(recent_level_start) or recent_inflow.isna().any() or recent_outflow.isna().any():
        return None
    ts = filled.index[-1]
    hour_frac = ts.hour + ts.minute / 60.0
    row = {
        "level0": float(level0),
        "recent_dH": float(level0 - recent_level_start),
        "recent_inflow_mean": float(recent_inflow.mean()),
        "recent_outflow_mean": float(recent_outflow.mean()),
        "hour_sin": float(np.sin(2 * np.pi * hour_frac / 24)),
        "hour_cos": float(np.cos(2 * np.pi * hour_frac / 24)),
    }
    return np.array([row[c] for c in RESIDUAL_FEATURE_COLS], dtype=float)


@dataclasses.dataclass
class CycleResult:
    origin: pd.Timestamp
    level0: float
    o7_forecast: pd.Series
    q7_forecast: pd.Series
    target_band: dict
    used_lever: str
    recommendation: dict
    # Stage2가 실제로 "개입 없이 뒀을 때" 예측한 H7 궤적(물리+잔차보정,
    # recommend_for_band 내부의 baseline과 정확히 같은 계산 - delta_lever=0).
    # H7 예측 정확도 평가(2026-09-11 요구사항 3번)에 쓴다. Stage3 판정 자체는
    # 이미 recommend_for_band가 끝냈으므로 여기선 그 결과를 다시 계산해
    # "무엇을 봤길래 이 판정이 나왔는지"를 그대로 남겨두는 것뿐이다.
    h7_forecast: pd.Series
    # Stage1 NN이 joint로 예측한 target 전체(H7/H3 포함 13~15개, horizon x
    # target_cols) - 2026-09-14 요구사항: "비고=='target'인 모든 태그는
    # 예측/추천돼야 한다"에 대응해서 tb_ctr_tnk_rst 업로드가 O7/Q7뿐 아니라
    # 모든 target을 다루려면 이 전체 DataFrame이 필요하다(`upload.
    # build_target_forecast_rows` 참고). H7만 위 h7_forecast(Stage2 하이브리드,
    # 더 정확하다고 판단해서 씀)로 대체되고 나머지는 이 raw NN 예측 그대로 쓴다.
    forecast: pd.DataFrame


def run_cycle(
    art: LoadedArtifacts,
    offline: OfflineArtifacts,
    filled: pd.DataFrame,
    freq_minutes: float,
    band_window_days: float = 21,
    band_lower_quantile: float = 0.25,
    band_upper_quantile: float = 0.75,
    lever_priority: list[str] | None = None,
    search_max_stds: float = 10.0,
    default_search_max: float = 2000.0,
    level_history: pd.Series | None = None,
) -> CycleResult:
    """`filled`(Stage1 feature_cols + offline.level_col/inflow_col/outflow_col을
    전부 컬럼으로 가짐, 마지막 행 시각 = origin)를 기준으로 Stage1 예측 ->
    Stage2 시뮬레이션 -> Stage3 `recommend_for_band` 추천까지 한 번에 실행한다.

    `search_max`(이분탐색으로 delta_lever를 찾는 탐색 상한, `recommend.
    recommend_for_band`가 안 주면 기본 2000.0을 쓴다)를 레버별로 다르게
    정한다 — 레버마다 단위/물리적 범위가 완전히 다른데(밸브 개도는 0~100%,
    유량은 수백~수천) 고정 상수 하나를 모든 레버에 그대로 쓰면 말이 안 된다
    (2026-09-11 실측 dev 백테스트로 발견: V2를 고른 사이클의 55%가
    delta_lever=2000으로 수렴했는데, V2 표준편차가 13.69라 2000은 평소
    변동의 146배 — 밸브가 물리적으로 그렇게까지 안 열린다).

    `band_lower_quantile`/`band_upper_quantile`(기본 0.25/0.75, Q1~Q3)은
    `recommend.compute_target_band`로 그대로 전달된다 — 목표범위를 넓히면
    (예: 0.15/0.85) 개입 빈도가 줄고, 좁히면 더 자주 개입한다.

    대신 `offline.lever_stds[chosen_lever] * search_max_stds`(기본 10배)를
    그 레버의 search_max로 쓴다 — 태그마다 물리적 상한을 별도로 등록해야
    하는(예: 밸브는 0~100%라는 걸 taglist에 새로 추가) 부담 없이, 이미
    갖고 있는 `lever_stds`(평소 변동폭)만으로 자동으로 레버에 맞는 크기를
    정한다는 발상이다. `lever_stds`에 그 레버가 없으면(예: 아주 예전
    아티팩트) `default_search_max`(기존 고정값 2000.0)로 안전하게
    대체한다. 10배도 여전히 크므로(V2 기준 136.9%) 완벽한 물리적 상한은
    아니라는 점은 "알려진 한계"로 남는다 — 진짜 상한(예: 밸브 최대 개도)이
    필요하면 taglist에 그 값을 등록해서 여기서 참조하도록 확장할 것.

    `level_history`를 주면 목표범위를 `filled[level_col]` 대신 이 시계열로
    계산한다(2026-09-28, 조회 분할 - `preprocess.fetch_level_history` 참고).
    이때 `filled`는 Stage1 입력 윈도우만큼만 있어도 된다. 안 주면 예전처럼
    `filled`가 목표범위 기간(`band_window_days`)을 다 담고 있어야 한다.
    """
    level_col, inflow_col, outflow_col = offline.level_col, offline.inflow_col, offline.outflow_col
    band_source = level_history if level_history is not None else filled[level_col]

    forecast = predict_next_horizon(art, filled)
    missing = {"O7", "Q7"} - set(forecast.columns)
    if missing:
        raise ValueError(
            f"Stage1 모델의 target_cols에 {sorted(missing)}이(가) 없습니다. "
            "O7/Q7을 예측하는 run_dir(예: gu_db_noq8_h6)을 써야 합니다."
        )
    o7_forecast, q7_forecast = forecast["O7"], forecast["Q7"]

    origin = filled.index[-1]
    level0 = float(filled[level_col].iloc[-1])
    if pd.isna(level0):
        raise ValueError(f"최근 데이터의 마지막 시점({origin}) {level_col}이 결측입니다. 추천을 건너뜁니다.")

    band = compute_target_band(
        band_source, now=origin, window_days=band_window_days,
        lower_quantile=band_lower_quantile, upper_quantile=band_upper_quantile,
    )
    if band["n"] == 0:
        raise ValueError(f"최근 {band_window_days}일 {level_col} 이력이 없어 목표수위 범위를 정할 수 없습니다.")

    # 방향 필터를 아래에서 적용하려면 "이게 기본 게인 순위였는지"를 알아야
    # 한다 - lever_priority를 호출부가 명시적으로 줬다면 운영자가 의도적으로
    # 정한 순서이므로 이 자동 필터로 재정렬하면 안 된다(테스트/수동 개입
    # 용도로 명시적 우선순위를 준 건데 조용히 무시되면 안 됨).
    used_explicit_priority = lever_priority is not None
    priority = lever_priority or sorted(offline.lever_gains, key=lambda l: -offline.lever_gains[l])
    priority = [l for l in priority if l in offline.lever_gains]
    if not priority:
        raise ValueError("사용 가능한 레버가 없습니다(offline.lever_gains 비어있음, train.py 결과 확인).")

    # residual_features/residual_model은 레버(gain)와 무관하게 한 번만
    # 계산하면 되므로 레버 선택보다 먼저 구한다 - 아래 baseline 방향 판단과
    # 실제 recommend_for_band 호출이 정확히 같은 보정을 써야 두 판정이
    # 어긋나지 않는다(2026-09-11 실측: 물리모델만으로는 목표범위 안이었는데
    # GBR 잔차보정을 더하면 범위 밖이었던 사례가 실제로 있었다).
    residual_features = residual_features_at(filled, level_col, inflow_col, outflow_col, offline.trend_window_steps)
    residual_model = offline.residual_model if residual_features is not None else None

    # 2026-09-14: "V2를 증가/감소로 쓸 수 있는지부터 판단하고, 못 쓰면
    # 게인을 매우 줄인다" 요청 - 게인이 아무리 커도(V2가 늘 1순위로 뽑힘)
    # 이미 밸브가 거의 다 열려있으면(raise 방향 필요) 또는 거의 다 닫혀
    # 있으면(lower 방향 필요) 그 레버는 사실상 못 쓴다. gain=1.0(더미,
    # delta=0이라 무관)으로 baseline 궤적만 미리 시뮬레이션해서 필요한
    # 방향(raise/lower)을 정하고, LEVER_PHYSICAL_BOUNDS에 등록된 레버는
    # 그 방향으로 여유가 있는지 확인한다. 여유가 없으면 우선순위 정렬에서
    # 쓸 effective_gain을 극단적으로 줄여서(1e-6배) 자동으로 다음 순위
    # 레버(예: Q_GunS)로 넘어가게 한다 - "레버를 제외"하는 별도 분기 없이
    # 기존 게인 정렬 로직만 재사용한다. 양쪽 다 벗어나는(both_violated)
    # 애매한 경우나 애초에 개입이 불필요한 경우는 방향을 하나로 못 정하므로
    # 이 필터를 건너뛰고 원래 게인 순위를 그대로 쓴다.
    baseline = simulate_h7_with_intervention(
        level0, o7_forecast, q7_forecast, 0.0, 1.0, offline.area_m2, freq_minutes,
        residual_model=residual_model, residual_features=residual_features,
    )
    below = float(baseline.min()) < band["lower"]
    above = float(baseline.max()) > band["upper"]
    if not used_explicit_priority and below != above:  # 둘 중 하나만 벗어남 - 방향이 명확하고 명시적 우선순위가 없을 때만 필터 적용
        direction = "raise" if below else "lower"
        NO_ROOM_GAIN_FACTOR = 1e-6

        def effective_gain(lever: str) -> float:
            min_v, max_v = LEVER_PHYSICAL_BOUNDS.get(lever, (None, None))
            if lever not in filled.columns or pd.isna(filled[lever].iloc[-1]):
                return offline.lever_gains[lever]  # 현재값을 모르면 판단 불가 - 원래 게인 유지
            current = float(filled[lever].iloc[-1])
            has_room = lever_has_room(current, direction, min_v, max_v, margin=1.0)
            return offline.lever_gains[lever] if has_room else offline.lever_gains[lever] * NO_ROOM_GAIN_FACTOR

        priority = sorted(priority, key=lambda l: -effective_gain(l))

    chosen_lever = priority[0]
    gain = offline.lever_gains[chosen_lever]

    lever_std = offline.lever_stds.get(chosen_lever)
    search_max = lever_std * search_max_stds if lever_std else default_search_max

    recommendation = recommend_for_band(
        level0, o7_forecast, q7_forecast, band["lower"], band["upper"], gain,
        offline.area_m2, freq_minutes, residual_model=residual_model,
        residual_features=residual_features, lever_name=chosen_lever, search_max=search_max,
    )
    # recommend_for_band 내부에서 이미 한 번 계산한 것과 같은 baseline(delta=0)
    # 궤적이다 - recommend_for_band는 min/max 스칼라만 돌려주므로, H7 정확도
    # 평가(horizon 전체 궤적 필요)를 위해 여기서 한 번 더 계산한다. simulate_
    # level 자체가 가벼운 벡터 연산이라 다시 계산하는 비용은 무시할 만하다.
    h7_forecast = simulate_h7_with_intervention(
        level0, o7_forecast, q7_forecast, 0.0, gain, offline.area_m2, freq_minutes,
        residual_model=residual_model, residual_features=residual_features,
    )

    return CycleResult(
        origin=origin, level0=level0, o7_forecast=o7_forecast, q7_forecast=q7_forecast,
        target_band=band, used_lever=chosen_lever, recommendation=recommendation, h7_forecast=h7_forecast,
        forecast=forecast,
    )


def format_cycle_result(result: CycleResult) -> str:
    """운영자가 바로 읽을 수 있는 짧은 텍스트 요약(로그/알림/dev 모드 콘솔 출력용)."""
    rec = result.recommendation
    lines = [
        f"[{result.origin}] 현재수위={result.level0:.4f}, "
        f"목표범위=[{result.target_band['lower']:.4f}, {result.target_band['upper']:.4f}] "
        f"(최근 {result.target_band['n']}개 표본)",
        f"사용 레버: {result.used_lever}",
        f"판정: {rec['action']} - {rec['note']}",
    ]
    if rec["action"] == "raise":
        if rec["delta_lever"] is None:  # achievable=False - search_max까지도 목표를 못 채운 경우(recommend.py 참고)
            lines.append(f"  -> {result.used_lever}를 search_max까지 올려도 목표 미달 (achievable={rec['achievable']})")
        else:
            lines.append(f"  -> {result.used_lever}를 +{rec['delta_lever']:.2f} 조정 권장 (achievable={rec['achievable']})")
    elif rec["action"] == "lower":
        if rec["delta_lever"] is None:
            lines.append(f"  -> {result.used_lever}를 search_max까지 내려도 목표 초과 (achievable={rec['achievable']})")
        else:
            lines.append(f"  -> {result.used_lever}를 {rec['delta_lever']:.2f} 조정 권장 (achievable={rec['achievable']})")
    elif rec["action"] == "conflict":
        lines.append(f"  -> raise={rec['raise']}, lower={rec['lower']} (상수 개입으로는 해결 불가)")
    return "\n".join(lines)


def evaluate_against_actual(result: CycleResult, actual_future_level: pd.Series) -> dict:
    """백테스트(`schedule.py --mode dev`) 전용 — 이 사이클이 추천/판정한 시점
    이후 실제로 관측된 H7(`actual_future_level`, origin 이후 시각 인덱스)과
    비교해, 판정이 사후적으로 맞았는지를 요약한다.

    - `actual_within_band`: 실제 궤적이 그 사이클이 쓴 목표범위 안에 계속
      머물렀는지(action="none"이 맞았다면 True여야 함).
    - `action`이 "raise"/"lower"였다면, 개입을 반영하지 않은 baseline
      예측이 아니라 "실제로 무슨 일이 있었는지"만 보는 사후 점검이라
      (실제 운영자가 그 추천대로 조작했는지 여부는 이 함수가 모른다),
      `note`에 그 한계를 명시한다.
    """
    if len(actual_future_level.dropna()) == 0:
        return {"n": 0, "actual_within_band": None, "note": "실제 미래 데이터 없음(비교 불가)"}
    lower, upper = result.target_band["lower"], result.target_band["upper"]
    within = bool(actual_future_level.between(lower, upper).all())
    return {
        "n": int(len(actual_future_level.dropna())),
        "actual_within_band": within,
        "actual_min": float(actual_future_level.min()),
        "actual_max": float(actual_future_level.max()),
        "note": (
            "판정 시점 이후 실제 관측치가 그때 쓴 목표범위 안에 머물렀는지만 본다 — "
            "추천이 실제로 반영됐는지는 이 함수가 알 수 없다(운영 기록과 별도 대조 필요)."
        ),
    }


def target_achievement_rate(backtest_df: pd.DataFrame) -> dict:
    """추천 제어 시뮬레이션 상의 "목표치 달성률"(2026-09-11 사용자 요청 —
    모델 후보 비교 지표 4번) — `schedule.py --mode dev`가 만드는 백테스트
    결과(`_cycle_result_row`가 만든 origin당 한 행, `achievable` 컬럼 필요)
    에서 계산한다.

    `recommend_for_band()`의 achievable은 이미 두 경우를 다 포함한다:
    (a) 원래부터 목표범위 안(action="none", achievable=True로 표시됨),
    (b) 범위를 벗어날 것으로 예상됐지만 레버 조정으로 다시 범위 안에 넣을
    수 있는 경우(achievable=True). 반대로 achievable=False는 "레버를
    search_max까지 써도 목표를 못 채운다"는 뜻이다. 그래서 achievable=True
    비율 자체가 "이 예측 모델(O7/Q7)을 갖고 이 레버/게인으로 목표수위를
    달성할 수 있었던 사이클의 비율"이 된다 — 8개 예측 모델 후보를 Stage1
    성능(MAE/RMSE/...)뿐 아니라 "그 예측으로 실제 제어가 얼마나 잘 되는가"
    까지 비교하려는 목적이다(Stage1 지표가 좋아도 Stage2/3 결과가 나쁠 수
    있고, 그 반대도 가능 — 이 지표가 그 괴리를 드러낸다).

    backtest_df가 비어있거나 `achievable` 컬럼이 없으면 n=0/nan을 돌려준다.
    """
    if len(backtest_df) == 0 or "achievable" not in backtest_df.columns:
        return {"n": 0, "achieved": 0, "achievement_rate": float("nan")}
    n = len(backtest_df)
    achieved = int((backtest_df["achievable"] == True).sum())  # noqa: E712 - pandas bool 컬럼과의 명시적 비교
    return {"n": n, "achieved": achieved, "achievement_rate": achieved / n}


def h7_forecast_accuracy(results: list["CycleResult"], actuals: list[pd.Series]) -> pd.DataFrame:
    """Stage2 H7 예측 정확도(2026-09-11 요구사항 3번) — 여러 사이클의
    `CycleResult.h7_forecast`(개입 없이 뒀을 때의 baseline 궤적, delta=0)를
    같은 시점 실제 관측 H7과 나란히 쌓아서 `metrics.per_horizon_metrics`/
    `summarize_by_target`을 그대로 재사용한다 - Stage1(O7/Q7) 평가와 같은
    지표 체계(MAE/RMSE/MAPE/SMAPE/R2/skill_vs_persistence)를 Stage2에도
    똑같이 적용해서 "예측 모델(O7/Q7)이 바뀌면 H7 정확도가 실제로 얼마나
    바뀌는지"를 공정하게 비교할 수 있게 한다.

    `results`/`actuals`는 같은 길이여야 하고, `actuals[i]`는 `results[i]`의
    origin 이후 horizon 구간 실제 H7 관측치(인덱스가 시간순, 길이가
    `results[i].h7_forecast`와 같아야 함)다 - 길이가 안 맞거나 결측이 있는
    사이클은 건너뛴다(짧은 데이터 구간 끝부분 등에서 실측이 모자랄 수 있음).

    persistence baseline은 각 사이클의 `level0`(origin 시점 실측 H7)을
    horizon 내내 그대로 쓴 것 - Stage1 평가의 persistence_forecast와 같은
    발상이다.
    """
    y_true_rows, y_pred_rows, y_persist_rows = [], [], []
    for result, actual in zip(results, actuals):
        pred = result.h7_forecast
        actual_clean = actual.dropna()
        if len(actual_clean) != len(pred) or len(pred) == 0:
            continue
        y_true_rows.append(actual_clean.to_numpy())
        y_pred_rows.append(pred.to_numpy())
        y_persist_rows.append(np.full(len(pred), result.level0))

    if not y_true_rows:
        return pd.DataFrame(columns=["target", "method", "MAE", "RMSE", "MAPE_%", "SMAPE_%", "R2", "n"])

    y_true = np.stack(y_true_rows)[:, :, None]
    preds = {"model": np.stack(y_pred_rows)[:, :, None], "persistence": np.stack(y_persist_rows)[:, :, None]}

    rows = []
    for method, y_pred in preds.items():
        df = per_horizon_metrics(y_true, y_pred, ["H7"])
        df["method"] = method
        rows.append(df)
    report = pd.concat(rows, ignore_index=True)

    # skill_vs_persistence = 1 - MAE(model)/MAE(persistence) (metrics.py의 다른
    # skill_vs_* 정의와 같은 공식) - horizon_step별로 짝을 맞춰 계산한다.
    persist_mae = report[report["method"] == "persistence"].set_index("horizon_step")["MAE"]
    model_rows = report[report["method"] == "model"].copy()
    model_rows["skill_vs_persistence"] = 1 - (model_rows["MAE"] / model_rows["horizon_step"].map(persist_mae))

    return summarize_by_target(model_rows)
