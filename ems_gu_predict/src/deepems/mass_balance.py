"""저수지 수위(H)를 유입/유출 유량의 질량보존(연속 방정식)으로 예측하는
물리 기반 모듈 — Stage 2(H7 등 수위 target)를 순수 데이터 기반 블랙박스
대신 "물리 법칙 + (나중에 붙일) ML 잔차 보정" 하이브리드로 다루기 위한
기초 조각이다.

핵심 방정식:
    dH/dt = (유입량 - 유출량) / A      (A: 저수지 수면적)

이 방정식이 매력적인 이유는 한 번도 안 겪어본 유입량(예: Stage 3가 제안하는
"정수장 유량을 이만큼 올리면"이라는 가상 시나리오)에도 안전하게 외삽할 수
있다는 점이다 — 데이터로 학습한 블랙박스는 학습 분포 밖 입력에서 무슨 값을
내놓을지 보장이 없지만, 질량보존은 물리 법칙이라 입력 범위와 무관하게 항상
성립한다.

단위 주의: 이 저장소의 유량 태그(FRI 계열)가 정확히 어떤 시간 단위(m^3/h,
m^3/day 등)로 기록되는지 taglist에 명시돼 있지 않다. simulate_level()/
calibrate_area()는 "유량 * (freq_minutes/60)"을 시간당->해당 스텝 부피로
가정한다(즉 유량 단위가 시간당(/h)이라고 가정) — 이 가정이 맞는지는
calibrate_area()가 REFERENCE_RESERVOIR_AREAS_M2(사용자가 알려준 실측 면적)와
비교해서 검증한다. 크게 벗어나면 단위 가정이 틀렸거나(예: 실제로는 m^3/day),
계측되지 않는 유입/유출(누수, 월류, 나운배수지처럼 유출 태그 자체가 없는
경우)이 있다는 신호로 해석해야 한다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import skill_score

# 사용자가 알려준 실측 저수지 수면적(2026-09-10) — REFERENCE_NETWORK_EDGES/
# REFERENCE_SAME_SITE_GROUPS(taglist.py)와 같은 성격의 "실측으로 알려진 참고값"
# 이다. 데이터에서 역산한 값(calibrate_area)과 이 값을 나란히 비교해 단위/
# 계측누락 여부를 가늠하는 기준선으로 쓴다 — 시뮬레이션에 직접 넣을 A로도
# 우선 이 값을 쓴다(달리 근거가 없으면).
REFERENCE_RESERVOIR_AREAS_M2: dict[str, float] = {
    "H3": 2000.0,  # 나운배수지 (주의: 유출 태그가 없어 calibrate_area로 검증 불가 — 아래 docstring 참고)
    "H7": 6000.0,  # 오식도배수지 (Q7=유입, O7=유출 둘 다 있어 calibrate_area로 검증 가능)
}


def simulate_level(
    level0: float, inflow: pd.Series, outflow: pd.Series, area_m2: float, freq_minutes: float,
) -> pd.Series:
    """level0(시작 수위)에서 inflow/outflow(그 다음 스텝들의 유량, inflow와
    같은 인덱스를 outflow도 가져야 함)를 오일러 적분해서 수위 궤적을 만든다.

    반환 시리즈의 인덱스는 inflow와 같다 — result.iloc[0]은 "첫 스텝이 지난
    뒤"의 수위(= level0 + 그 스텝 동안의 변화량)다. 즉 level0 자체는 결과에
    포함되지 않는다(호출부가 이미 알고 있는 시작점이므로).

    inflow/outflow에 NaN이 있으면 그 스텝의 변화량도 NaN이 되고, 그 이후
    전부 NaN으로 오염된다 — 결측 구간을 포함한 장기 시뮬레이션은 호출부가
    미리 걸러야 한다(backtest_multistep이 이렇게 한다). pandas Series의
    기본 cumsum()은 NaN을 "그 자리만 NaN, 누적합엔 기여 없음(skipna)"으로
    처리해서 이후 값이 도로 복구돼버리므로(예: [1, nan, 1].cumsum() ==
    [1, nan, 2]) 일부러 안 쓴다 — 물리적으로 "그 스텝에 무슨 일이 있었는지
    모르면 그 이후 수위도 모른다"가 맞는 가정이라, numpy 배열 기반으로
    직접 계산해 NaN이 한 번 나오면 그 뒤로 전부 NaN이 되게 한다.
    """
    dt_hours = freq_minutes / 60.0
    delta_h = (inflow - outflow) * dt_hours / area_m2
    cum = np.cumsum(delta_h.to_numpy(dtype=float))
    return pd.Series(level0 + cum, index=delta_h.index)


def calibrate_area(
    level: pd.Series, inflow: pd.Series, outflow: pd.Series, freq_minutes: float,
) -> dict:
    """실측 수위 변화량(dH = level.diff())과 실측 유량 불균형((inflow-outflow)
    * dt_hours)의 관계를 절편 없는 최소자승으로 맞춰(dH = slope * imbalance,
    이론상 slope = 1/A), "데이터가 암시하는" 유효 면적을 역산한다.

    절편을 안 두는 이유: 질량보존 방정식 자체에 상수항이 있을 물리적 이유가
    없다(imbalance=0이면 dH도 0이어야 한다) — 절편을 허용하면 그 항이 실제로는
    "계측 안 되는 일정한 누수/증발"을 흡수해버려서, slope(=면적 추정)가
    왜곡된다.

    fitted_area_m2를 REFERENCE_RESERVOIR_AREAS_M2의 실측값과 비교하는 게
    이 함수의 핵심 용도다:
    - 비율이 1에 가까우면: 유량 단위 가정(시간당)이 맞고, 두 태그(inflow/
      outflow)가 그 수위 변화를 거의 다 설명한다는 뜻 — 물리 모델을 믿고
      써도 된다는 신호.
    - 비율이 크게 벗어나면(예: 24배 근처): 유량이 실제로는 m^3/day 같은
      다른 시간 단위일 가능성.
    - r_squared가 낮으면(단위는 맞아 보여도): 계측 안 되는 유입/유출이나
      센서 잡음이 상당하다는 뜻 — 오식도배수지 체인이 CCF에서도 약하게
      나온 것과 같은 맥락(저수조 완충).

    n<2거나 imbalance 분산이 0이면(변화가 전혀 없는 상수 구간 등)
    fitted_area_m2=nan을 돌려준다.
    """
    dt_hours = freq_minutes / 60.0
    dh = level.diff()
    imbalance = (inflow - outflow) * dt_hours
    mask = dh.notna() & imbalance.notna()
    dh, imbalance = dh[mask].to_numpy(dtype=float), imbalance[mask].to_numpy(dtype=float)
    denom = float(np.dot(imbalance, imbalance))
    if len(dh) < 2 or denom == 0.0:
        return {"fitted_area_m2": float("nan"), "slope": float("nan"), "r_squared": float("nan"), "n": len(dh)}

    slope = float(np.dot(imbalance, dh) / denom)  # dH = slope * imbalance
    fitted_area_m2 = 1.0 / slope if slope != 0 else float("inf")

    predicted_dh = slope * imbalance
    ss_res = float(np.sum((dh - predicted_dh) ** 2))
    ss_tot = float(np.sum((dh - dh.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {"fitted_area_m2": fitted_area_m2, "slope": slope, "r_squared": r_squared, "n": len(dh)}


def backtest_multistep(
    level: pd.Series, inflow: pd.Series, outflow: pd.Series, area_m2: float, freq_minutes: float,
    horizon_steps: int, stride: int = 1,
) -> pd.DataFrame:
    """실제 미래 유입/유출을 안다고 가정한 상태에서(예측 오차가 아니라 "물리
    방정식 자체가 horizon_steps만큼 앞을 얼마나 정확히 맞히는지"만 따로 보기
    위해 — Stage 1(유입/유출 예측)의 오차와 이 방정식의 오차를 분리한다),
    여러 시작점(origin)에서 horizon_steps만큼 앞으로 시뮬레이션하고 실제
    수위와 비교한다.

    stride: origin을 몇 스텝씩 옮겨가며 반복할지 — 1이면 전체를 다 훑지만
    (인접 origin끼리 window가 거의 겹쳐 중복이 심함) 데이터가 길면 느리다.
    horizon_steps보다 작게 두면 여전히 겹치지만, 이 함수는 평가용이라 학습
    데이터 누수 문제는 없다(윈도우 겹침이 문제되는 건 학습/평가 분리 때뿐).

    구간에 결측(NaN)이 하나라도 있으면 그 origin은 건너뛴다(조용히). 반환
    DataFrame이 비어있을 수 있다(전부 결측 등) — summarize_backtest()가
    그 경우 nan을 돌려주므로 호출부에서 따로 len() 체크 안 해도 된다.
    """
    idx = level.index
    n = len(idx)
    rows = []
    for start in range(0, n - horizon_steps, stride):
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
        sim = simulate_level(level0, inflow_win, outflow_win, area_m2, freq_minutes)
        rows.append(
            {
                "origin": idx[start], "target_time": idx[end],
                "actual": float(actual), "simulated": float(sim.iloc[-1]), "persistence": float(level0),
            }
        )
    return pd.DataFrame(rows, columns=["origin", "target_time", "actual", "simulated", "persistence"])


def summarize_backtest(backtest: pd.DataFrame) -> dict:
    """backtest_multistep() 결과를 MAE/skill_vs_persistence 하나로 요약한다.
    metrics.skill_score와 같은 정의(1 - model_mae/baseline_mae)를 그대로
    써서, evaluate.py의 ML 모델 skill_vs_persistence와 직접 비교 가능하게
    한다 — "물리 모델이 ML 모델보다 이 target에서 얼마나 더/덜 나은가"를
    같은 척도로 볼 수 있다.

    backtest가 비어있으면(결측이 너무 많아 유효 origin이 하나도 없는 경우)
    전부 nan을 돌려준다.
    """
    if len(backtest) == 0:
        return {"n": 0, "mae_simulated": float("nan"), "mae_persistence": float("nan"), "skill_vs_persistence": float("nan")}
    mae_sim = float(np.mean(np.abs(backtest["actual"] - backtest["simulated"])))
    mae_pers = float(np.mean(np.abs(backtest["actual"] - backtest["persistence"])))
    return {
        "n": len(backtest), "mae_simulated": mae_sim, "mae_persistence": mae_pers,
        "skill_vs_persistence": skill_score(mae_sim, mae_pers),
    }
