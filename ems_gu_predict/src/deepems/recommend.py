"""Stage 3: 목표수위 대비 부족 예상 시 조작 가능한 레버(정수장 송수 유량
Q_GunS, 밸브 개도 V2/V4) 조정 추천.

레버는 taglist.CONTROLLABLE_LEVERS(["Q_GunS", "V2", "V4"])에서만 고를 것 —
P_GunS/P_Ham/P2/P4/P5/P6 같은 압력 태그는 이 함수들에 넣지 않는다. 2026-09-11
사용자 확인: 압력은 펌프/밸브 조작의 "결과"로 측정되는 값이지 운영자가
직접 설정(제어)하는 값이 아니다. estimate_gain()/compare_lever_gains() 등은
어떤 컬럼이든 받아주지만(통계적으로만 판단), 그 컬럼이 실제로 조작
가능한지는 함수가 몰라서 강제로 막지 못한다 - 호출부가
taglist.CONTROLLABLE_LEVERS를 기준으로 lever_cols/lever_gains를 구성해야
한다.

Stage 1(residual_model.py로 보정한 O7 수요 예측)과 Stage 2(mass_balance.py
물리 시뮬레이션 + residual_model.py GBR 잔차보정 = H7 예측)의 결과물을
"what-if 시뮬레이터"로 재사용한다 - 미래 H7이 목표 수위 밑으로 떨어질 것으로
예상되면, 레버 하나를 지금부터 horizon 내내 얼마나 더 조정해야 막을 수
있는지를 이분탐색으로 찾는다.

레버가 여러 개인 이유(2026-09-10 추가): 처음엔 정수장 유량(Q_GunS) 하나만
다뤘는데, 실제 운영에서는 밸브(V2=지방산단, V4=국가산단 개도)도 조작
대상이다. 이 모듈의 함수들은 애초에 "어떤 변수 하나가 Q7에 선형으로
얼마나 반영되는가"만 알면 동작하므로 Q_GunS에 국한되지 않는다 - estimate_gain()
/compare_lever_gains()로 후보 레버 여러 개의 게인을 한 번에 비교하고,
recommend_across_levers()로 레버별 추천을 나란히 낼 수 있다.

경로: 레버 조정 -> (거의 즉시, path-lag 분석 실측: Q_GunS의 경우 0~5분) Q7
(오식도 유입) 변화 -> (물리 시뮬레이션, mass_balance.simulate_level) H7 변화.
밸브(V2/V4)는 Q_GunS와 달리 오식도까지의 실측 전달 지연을 따로 확인하지
않았다 - 동시 회귀를 쓰는 게 정당한지는 레버별로 다를 수 있다는 뜻이니,
compare_lever_gains()의 r_squared가 낮은 레버는 신중하게 봐야 한다(특히
V4-H7 관계는 이전 밸브 분석에서 상관 0.02로 사실상 노이즈였다 - taglist/
GU_network_topology.md "밸브 분석" 참고. V4가 Q7에 미치는 영향 자체는 여기서
다시 추정하지만, 그 결과의 신뢰도를 판단할 때 이 배경을 염두에 둘 것).

목표수위 정의(2026-09-11 추가): target_level을 고정값으로 임의로 정하지
않는다 - compute_target_band()로 "최근 3주간 이 저수지가 실제로 오갔던
범위"(H7의 1~3사분위수, Q1~Q3)를 하한/상한으로 삼는다. 미래 H7이 Q1보다
낮아질 것 같으면(recommend_min_intervention) 레버를 올리고, Q3보다
높아질 것 같으면(recommend_max_intervention) 레버를 내린다 - 그 사이면
개입하지 않는다. recommend_for_band()가 이 판단을 한 번에 처리한다.

인과관계 경고 (실제 반영 전 반드시 고려할 것): estimate_gain()이 추정하는
"레버 1단위 증가가 Q7에 얼마나 반영되는가"는 관측 데이터의 상관관계(동시
회귀)일 뿐, "그 레버를 의도적으로 올려보고 Q7이 실제로 얼마나 바뀌었는지"
기록한 개입 실험 데이터로 검증한 인과관계가 아니다. 이 모듈은 운영자
의사결정을 보조하는 "이렇게 하면 이 정도 효과가 있을 것으로 추정된다"는
시뮬레이션 도구로 쓰는 걸 전제로 하며, 검증 없이 자동 폐루프 제어로 바로
연결하는 건 권장하지 않는다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .mass_balance import simulate_level


def estimate_gain(cause: pd.Series, effect: pd.Series) -> dict:
    """동시(lag=0) 선형회귀(effect = gain * cause + intercept)로, cause(레버)
    1단위 증가가 effect(보통 Q7)에 평균적으로 얼마나 반영되는지 추정한다.

    절편을 두는 이유: Q7은 Q_GunS 하나만의 함수가 아니라(예: 함열가압장
    Q_Ham도 같은 개정분기를 거쳐 국가산단/군산관말을 통해 Q7에 합류함 -
    taglist.REFERENCE_NETWORK_EDGES 참고), cause=0이어도 effect가 0이 아닌 게
    정상이다 —
    mass_balance.calibrate_area(질량보존 방정식이라 절편이 물리적으로 있을
    이유가 없음)와는 성격이 다르다.

    동시(lag=0) 회귀를 쓰는 근거: Q_GunS->Q7 경로는 이전 지연시간 분석
    (analyze.ccf_for_pairs 실측, docs/GU_network_topology.md "데이터
    기반 검증" 참고)에서 0~5분 이내로 사실상 즉시 반영된다고 이미 확인했다.
    다른 레버(밸브 등)도 같은 가정을 쓰지만, 그 레버까지 지연시간을 따로
    확인한 건 아니므로 결과(특히 r_squared)를 신중하게 해석할 것 - 모듈
    docstring 참고.

    n<2거나 cause 분산이 0이면 전부 nan을 돌려준다.
    """
    mask = cause.notna() & effect.notna()
    x, y = cause[mask].to_numpy(dtype=float), effect[mask].to_numpy(dtype=float)
    if len(x) < 2 or x.std() == 0:
        return {"gain": float("nan"), "intercept": float("nan"), "r_squared": float("nan"), "n": len(x)}
    gain, intercept = np.polyfit(x, y, deg=1)
    pred = gain * x + intercept
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"gain": float(gain), "intercept": float(intercept), "r_squared": r_squared, "n": len(x)}


def compare_lever_gains(df: pd.DataFrame, lever_cols: list[str], effect_col: str) -> pd.DataFrame:
    """lever_cols(예: ["Q_GunS", "P_GunS", "V2", "V4"]) 각각과 effect_col(보통
    "Q7") 사이의 게인을 estimate_gain()으로 한 번에 계산해서 비교표를
    만든다 - |r_squared| 내림차순으로 정렬해서, 어느 레버가 그나마 신뢰할
    만한 설명력을 갖는지 한눈에 보이게 한다. gain이 0 이하거나 nan인
    레버는 recommend_across_levers()가 못 쓰므로(레버를 올렸는데 effect가
    안 오르거나 방향이 반대) usable 컬럼으로 표시한다.

    std 컬럼(각 레버의 표준편차, df[col].std())도 같이 낸다 - 레버마다
    단위가 다른 문제(압력/밸브 개도/유량) 때문에 recommend_across_levers()의
    delta_lever(필요 조정량) 절대값만으로는 레버를 공정하게 비교할 수 없다.
    이 표의 {lever: std} 매핑을 recommend_across_levers(lever_stds=...)에
    그대로 넘기면 "평소 변동폭의 몇 배를 조정해야 하는가" 기준으로 비교할
    수 있다.
    """
    rows = []
    for col in lever_cols:
        if col not in df.columns:
            continue
        result = estimate_gain(df[col], df[effect_col])
        rows.append(
            {
                "lever": col, "gain": result["gain"], "intercept": result["intercept"],
                "r_squared": result["r_squared"], "n": result["n"], "std": float(df[col].std()),
                "usable": np.isfinite(result["gain"]) and result["gain"] > 0,
            }
        )
    out = pd.DataFrame(rows, columns=["lever", "gain", "intercept", "r_squared", "n", "std", "usable"])
    if len(out):
        out = out.reindex(out["r_squared"].abs().sort_values(ascending=False).index).reset_index(drop=True)
    return out


def lever_has_room(
    current_value: float, direction: str, min_value: float | None, max_value: float | None, margin: float = 0.0,
) -> bool:
    """"지금 이 레버를 그 방향으로 더 조작할 여유가 있는가"를 판단한다
    (2026-09-14, "V2를 증가/감소로 쓸 수 있는지부터 판단"하는 요청에
    대응). 밸브 개도처럼 물리적 상한/하한이 있는 레버(taglist.
    LEVER_PHYSICAL_BOUNDS)는, 이미 그 끝에 붙어있으면 그 방향으로는
    사실상 더 조작할 수 없다 - 예: V2가 이미 0(완전히 닫힘)에 가까우면
    `direction="lower"`(더 내리는 방향)는 쓸 수 없다.

    - `direction="raise"`: `current_value`가 `max_value`(있으면) - `margin`
      보다 작아야 여유 있음. `max_value`가 None이면(물리적 상한을 모르는
      레버, 예: Q_GunS) 항상 여유 있음으로 본다.
    - `direction="lower"`: 대칭적으로 `min_value` + `margin`보다 커야 함.

    `direction`이 "raise"/"lower"가 아니면(예: 방향이 아직 안 정해졌거나
    both_violated인 경우) `ValueError`를 낸다 - 호출부가 방향을 먼저
    정하고 불러야 한다는 뜻이다.
    """
    if direction == "raise":
        return True if max_value is None else current_value < max_value - margin
    if direction == "lower":
        return True if min_value is None else current_value > min_value + margin
    raise ValueError(f"direction은 'raise' 또는 'lower'여야 합니다: {direction!r}")


def simulate_h7_with_intervention(
    level0: float,
    o7_forecast: pd.Series,
    q7_forecast: pd.Series,
    delta_lever: float,
    gain: float,
    area_m2: float,
    freq_minutes: float,
    residual_model=None,
    residual_features: np.ndarray | list[float] | None = None,
) -> pd.Series:
    """delta_lever만큼 레버(Q_GunS, 밸브 개도 등 - gain은 그 레버 기준으로 추정된
    값이어야 함)를 지금부터 horizon 내내 일정하게 조정했다고 가정하고(가장
    단순한 개입 형태 - 시간에 따라 다르게 조정하는 건 다음 버전), 조정된
    Q7(= q7_forecast + gain*delta_lever)로 H7 궤적을 시뮬레이션한다.

    residual_model/residual_features를 둘 다 주면 residual_model.py의 GBR
    잔차보정도 한 번 더해준다 - 다만 그 feature(recent_dH 등)는 "지금(개입
    시작 시점) 이전"의 실제 과거 데이터로 계산된 값이라 delta_lever와 무관하게
    고정이다(개입이 과거를 바꾸지는 않으므로). 즉 이 잔차보정값은 "물리
    모델이 평소 얼마나 치우치는 경향이 있는지"를 horizon 전체에 한 번(상수로)
    반영하는 근사다 - delta_lever가 커질수록 이 근사의 오차도 커질 수 있다는
    한계가 있다(residual_model이 큰 개입 시나리오를 학습해본 적이 없으므로).
    """
    adjusted_q7 = q7_forecast + gain * delta_lever
    sim = simulate_level(level0, adjusted_q7, o7_forecast, area_m2, freq_minutes)
    if residual_model is not None and residual_features is not None:
        predicted_residual = float(residual_model.predict(np.asarray(residual_features, dtype=float).reshape(1, -1))[0])
        sim = sim + predicted_residual
    return sim


def recommend_min_intervention(
    level0: float,
    o7_forecast: pd.Series,
    q7_forecast: pd.Series,
    target_level: float,
    gain: float,
    area_m2: float,
    freq_minutes: float,
    residual_model=None,
    residual_features: np.ndarray | list[float] | None = None,
    search_max: float = 2000.0,
    tolerance: float = 1.0,
    lever_name: str = "lever",
) -> dict:
    """horizon 내내 H7이 target_level 밑으로 안 내려가게 하는, lever_name
    레버의 최소 delta_lever를 이분탐색으로 찾는다 - H7이 오르기만 하면 되는
    게 아니라 horizon 전체(특히 최저점)가 기준을 넘어야 하므로, 시뮬레이션한
    궤적의 최솟값을 본다.

    delta_lever=0(개입 안 함)일 때 이미 target_level 이상이면 개입이
    필요 없다는 뜻으로 achievable=True, delta_lever=0.0을 돌려준다.
    search_max까지 올려도 여전히 부족하면(이 레버 하나만으로는 이 부족을
    못 막는 상황 - 예: 상류 경로 용량 한계, 또는 gain 추정이 너무 작음)
    achievable=False로 표시한다 - 이땐 다른 레버를 같이 고려하거나
    search_max를 늘려야 한다는 신호다(recommend_across_levers 참고).

    gain<=0(회귀가 실패했거나 방향이 이상한 경우)이면 이 방법 자체가
    성립하지 않으므로 ValueError를 낸다 - 레버를 올렸는데 Q7이 안 오르거나
    줄어드는 관계로는 "얼마나 올려야 하는지" 자체를 정의할 수 없다.
    """
    if not np.isfinite(gain) or gain <= 0:
        raise ValueError(f"gain은 0보다 큰 유한값이어야 합니다({lever_name}를 올리면 Q7도 올라야 함): {gain!r}")

    def min_level(delta: float) -> float:
        sim = simulate_h7_with_intervention(
            level0, o7_forecast, q7_forecast, delta, gain, area_m2, freq_minutes, residual_model, residual_features
        )
        return float(sim.min())

    baseline_min = min_level(0.0)
    if baseline_min >= target_level:
        return {"lever": lever_name, "delta_lever": 0.0, "achievable": True, "min_level": baseline_min, "note": "개입 불필요 - 이미 목표수위 이상"}

    max_min = min_level(search_max)
    if max_min < target_level:
        # delta_lever=None(2026-09-14 수정) - 예전엔 search_max를 그대로
        # 담았는데, 그건 "정답"이 아니라 "여기까지 시도해봤는데도 안 됐다"는
        # 실패 신호일 뿐이라 델타값처럼 보이면 오해를 산다(사용자 지적:
        # "상한으로 채워도 목표를 못 채운다면 그건 상한으로 설정하는게?").
        # achievable=False와 함께 None을 주면 호출부가 "추천할 단일 값이
        # 없다"는 걸 명확히 알 수 있다(예: upload.build_target_forecast_rows
        # 가 이 경우 원시 예측 그대로 올리도록 이미 그렇게 처리돼 있음).
        return {
            "lever": lever_name, "delta_lever": None, "achievable": False, "min_level": max_min,
            "note": f"search_max({search_max})까지 올려도 목표수위 미달 - 이 레버 단독으로는 부족할 수 있음",
        }

    lo, hi = 0.0, search_max
    while hi - lo > tolerance:
        mid = (lo + hi) / 2.0
        if min_level(mid) >= target_level:
            hi = mid
        else:
            lo = mid
    return {"lever": lever_name, "delta_lever": hi, "achievable": True, "min_level": min_level(hi), "note": "이분탐색으로 최소 조정값 산출"}


def recommend_across_levers(
    level0: float,
    o7_forecast: pd.Series,
    q7_forecast: pd.Series,
    target_level: float,
    lever_gains: dict[str, float],
    area_m2: float,
    freq_minutes: float,
    residual_model=None,
    residual_features: np.ndarray | list[float] | None = None,
    search_max: float = 2000.0,
    tolerance: float = 1.0,
    lever_stds: dict[str, float] | None = None,
) -> pd.DataFrame:
    """lever_gains(예: compare_lever_gains()가 낸 표에서 뽑은 {"Q_GunS": 0.42,
    "V4": 0.1, ...})에 있는 레버 각각에 대해 recommend_min_intervention을
    독립적으로(레버를 하나만 쓴다고 가정하고) 돌려서 결과를 한 표로
    모은다 - 운영자가 "정수장을 올릴지 밸브를 조일지" 레버별 필요 조정량을
    나란히 비교하는 용도다. 여러 레버를 동시에 조합해서 최적화하는 건
    이 함수 범위 밖이다(레버 간 상호작용/우선순위는 운영 판단이 필요해
    여기서 자동으로 정하지 않는다).

    gain<=0인 레버(usable=False, compare_lever_gains 참고)는 조용히
    건너뛴다 - 애초에 그 레버로는 개입을 정의할 수 없으므로.

    lever_stds(신규, 선택 - 보통 df[lever].std()로 구한 값들): 레버마다
    단위가 완전히 다르다(압력 kPa, 밸브 개도 %, 유량 m^3/h 등)는 문제가
    있다 - delta_lever의 절대 크기만 비교하면 "숫자가 작아 보이는" 레버가
    실은 평소 변동폭 대비 훨씬 큰 조정을 요구하는 경우를 놓친다(실측: P_GunS
    delta=0.61이 V2 delta=13.4보다 작아 보이지만, P_GunS 표준편차 대비로는
    훨씬 큰 조정일 수 있다). lever_stds를 주면 delta_lever_in_stds(=
    delta_lever / 그 레버의 표준편차, "평소 변동의 몇 배만큼 조정해야
    하는가")를 추가로 계산해서 그 기준으로 정렬한다 - 표준편차 정보가
    없는 레버는 delta_lever_in_stds가 nan이 되고, 정렬에서 맨 뒤로 밀린다
    (nan을 무한대 취급). lever_stds를 안 주면(기본) 예전처럼 delta_lever
    원값으로만 정렬한다 - 이땐 위 단위 문제를 호출부가 직접 감안해야 한다.
    """
    rows = []
    for lever_name, gain in lever_gains.items():
        if not np.isfinite(gain) or gain <= 0:
            continue
        result = recommend_min_intervention(
            level0, o7_forecast, q7_forecast, target_level, gain, area_m2, freq_minutes,
            residual_model, residual_features, search_max, tolerance, lever_name=lever_name,
        )
        if lever_stds is not None:
            std = lever_stds.get(lever_name)
            result["delta_lever_in_stds"] = result["delta_lever"] / std if std else float("nan")
        rows.append(result)
    cols = ["lever", "delta_lever", "achievable", "min_level", "note"]
    if lever_stds is not None:
        cols.append("delta_lever_in_stds")
    out = pd.DataFrame(rows, columns=cols)
    if len(out):
        if lever_stds is not None:
            # nan(표준편차 정보 없음)은 맨 뒤로 - "비교 기준이 없으면 우선순위를
            # 못 매기니 일단 뒤로 미룬다"는 뜻으로, 무한대로 채워 오름차순 정렬에서
            # 자연스럽게 마지막에 오게 한다.
            sort_key = out["delta_lever_in_stds"].fillna(np.inf)
            out = out.assign(_sort_key=sort_key).sort_values(
                ["achievable", "_sort_key"], ascending=[False, True]
            ).drop(columns="_sort_key").reset_index(drop=True)
        else:
            # achievable한 것 중 delta_lever(필요 조정폭) 원값이 작은 레버를
            # 위로 - 단위가 다른 레버가 섞여 있으면 이 정렬이 공정하지 않을
            # 수 있다는 한계는 위 lever_stds 설명 참고.
            out = out.sort_values(["achievable", "delta_lever"], ascending=[False, True]).reset_index(drop=True)
    return out


def recommend_joint_intervention(
    level0: float,
    o7_forecast: pd.Series,
    q7_forecast: pd.Series,
    target_level: float,
    lever_gains: dict[str, float],
    lever_stds: dict[str, float],
    area_m2: float,
    freq_minutes: float,
    residual_model=None,
    residual_features: np.ndarray | list[float] | None = None,
    q7_boost_search_max: float = 5000.0,
    tolerance: float = 1.0,
) -> dict:
    """레버 여러 개를 동시에 "조금씩" 조정해서 target_level을 맞춘다 —
    recommend_across_levers()처럼 레버 하나만 쓴다고 가정하는 대신, 부담을
    레버들에 나눠서 "전체적으로 가장 적게 손대는" 조합을 찾는다.

    수학적 근거: Q7에 대한 물리 시뮬레이션(mass_balance.simulate_level)은
    Q7 입력에 대해 선형이라(오일러 적분은 선형 연산), 레버 i를 delta_i만큼
    조정했을 때 Q7 총 증가분은 오직 sum_i(gain_i * delta_i)에만 의존한다 —
    "어느 레버로 그 증가분을 만들었는지"는 물리 시뮬레이션 결과에 영향을
    주지 않는다(잔차보정도 delta에 무관하게 고정값이라 마찬가지 —
    simulate_h7_with_intervention 참고). 그래서 문제가 두 단계로 정확히
    분리된다:

    1) "Q7을 총 얼마나 올려야 목표수위를 만족하는가"(required_boost)를
       구한다 - 레버가 무엇이든 상관없이 gain=1인 가상의 레버로
       recommend_min_intervention을 한 번 돌리면 된다(정확히 Q7 자체를
       올리는 것과 같으므로).
    2) required_boost = sum_i(gain_i * delta_i)라는 제약 아래, "부담"을
       sum_i (delta_i / std_i)^2 (레버마다 자기 평소 변동폭 대비 상대적
       부담, recommend_across_levers의 정규화와 같은 발상)로 정의하고
       이걸 최소화하는 delta_i를 라그랑주 승수법으로 닫힌 형태로 구한다:

           delta_i = required_boost * gain_i * std_i^2 / sum_j(gain_j^2 * std_j^2)

       (증명: u_i = delta_i/std_i로 치환하면 "min sum(u_i^2) s.t.
       sum_i(gain_i*std_i*u_i) = required_boost"라는 표준 최소노름 문제가
       되고, 그 해는 제약식의 계수 벡터 c_i=gain_i*std_i에 비례한다:
       u_i = required_boost * c_i / sum(c_j^2).)

    즉 게인이 크고(레버 하나로 Q7을 많이 움직일 수 있고) 평소 변동폭도
    넓은(그만큼 움직여도 "평소와 크게 다르지 않은") 레버일수록 더 많이
    떠맡는다 - 직관과 일치한다.

    recommend_across_levers()와의 차이: 그쪽은 "레버 하나만 쓴다면 각각
    얼마나 필요한가"를 나열해서 운영자가 그 중 고르게 하는 것이고, 이
    함수는 "여러 레버를 동시에 나눠 쓴다면 부담을 어떻게 배분하는 게
    최적인가"를 계산한다 - 한 레버를 크게 움직이는 것보다 여러 레버를
    조금씩 나눠 움직이는 걸 선호하는 운영 방침이라면 이쪽이 맞다.

    gain<=0인 레버는 recommend_across_levers()와 마찬가지로 조용히
    제외한다. std가 없거나(lever_stds에 없음) 0 이하인 레버도 제외한다
    (표준편차로 나누는 계산이라 필수).

    반환: {"required_boost": ..., "achievable": ..., "allocations":
    {lever: delta}, "note": ...}. achievable=False면(gain=1 가상 레버로도
    q7_boost_search_max 안에서 목표를 못 채운 것 - 애초에 이 레버 집합
    전체로는 안 되거나 area_m2/시나리오 자체가 감당이 안 되는 상황)
    allocations는 빈 dict를 돌려준다.
    """
    usable = {
        name: gain for name, gain in lever_gains.items()
        if np.isfinite(gain) and gain > 0 and lever_stds.get(name, 0) and lever_stds[name] > 0
    }
    if not usable:
        return {"required_boost": float("nan"), "achievable": False, "allocations": {}, "note": "쓸 수 있는 레버가 없음(gain<=0 또는 std 없음)"}

    boost_result = recommend_min_intervention(
        level0, o7_forecast, q7_forecast, target_level, gain=1.0,
        area_m2=area_m2, freq_minutes=freq_minutes,
        residual_model=residual_model, residual_features=residual_features,
        search_max=q7_boost_search_max, tolerance=tolerance, lever_name="Q7(가상)",
    )
    required_boost = boost_result["delta_lever"]
    if not boost_result["achievable"]:
        return {
            "required_boost": required_boost, "achievable": False, "allocations": {},
            "note": f"Q7을 {q7_boost_search_max}만큼 올려도 목표수위 미달 - 레버 배분과 무관하게 이 상황 자체가 해결 불가",
        }

    weights = {name: gain * (lever_stds[name] ** 2) for name, gain in usable.items()}
    denom = sum(gain * weights[name] for name, gain in usable.items())  # sum(gain_i^2 * std_i^2)
    allocations = {name: required_boost * weights[name] / denom for name in usable}

    return {
        "required_boost": required_boost, "achievable": True, "allocations": allocations,
        "note": "최소노름(정규화된 부담 제곱합 최소화)으로 배분",
    }


def compute_target_band(
    level: pd.Series, now: pd.Timestamp, window_days: float = 21,
    lower_quantile: float = 0.25, upper_quantile: float = 0.75,
) -> dict:
    """target_level을 고정값으로 임의로 정하는 대신(2026-09-11 이전 데모가
    이렇게 했었다 - "현재수위-0.05m" 같은 근거 없는 값), "최근 window_days일간
    이 저수지가 실제로 오갔던 범위"를 기준으로 삼는다.

    now 시점 기준 최근 window_days일(기본 3주)의 level 값에서 `lower_quantile`
    분위수(기본 0.25, 1사분위수/Q1)를 하한, `upper_quantile` 분위수(기본 0.75,
    3사분위수/Q3)를 상한으로 쓴다 - 사분위수를 쓰는 이유는 min/max보다
    극단치(센서 글리치 등)에 덜 흔들리기 때문이다. 이 구간을 "최근 3주간
    정상적으로 오갔던 범위"로 보고, 미래 예측이 이 범위를 벗어날 것 같을
    때만 개입한다(recommend_for_band 참고) - 범위 안에서는 개입하지 않는다.

    분위수를 넓히면(예: 0.15/0.85) 그만큼 "정상"으로 인정하는 폭이 넓어져서
    개입 빈도가 줄고, 좁히면(예: 0.35/0.65) 더 자주 개입하게 된다 -
    운영 방침에 따라 얼마나 보수적으로 개입할지 조정하는 손잡이다.

    now 이후의 미래 데이터는 절대 안 섞이게, level.loc[now - window_days :
    now]만 쓴다(미래를 안 봐야 "지금 시점에 실제로 쓸 수 있는 기준"이 된다).

    lower_quantile >= upper_quantile이면 하한이 상한보다 높거나 같아지는
    모순된 범위가 나오므로 ValueError.
    """
    if lower_quantile >= upper_quantile:
        raise ValueError(
            f"lower_quantile({lower_quantile})은 upper_quantile({upper_quantile})보다 작아야 합니다."
        )
    window_start = now - pd.Timedelta(days=window_days)
    window = level.loc[window_start:now].dropna()
    if len(window) == 0:
        return {"lower": float("nan"), "upper": float("nan"), "n": 0, "window_start": window_start, "window_end": now}
    return {
        "lower": float(window.quantile(lower_quantile)), "upper": float(window.quantile(upper_quantile)),
        "n": len(window), "window_start": window_start, "window_end": now,
    }


def compute_target_band_by_hour(
    level: pd.Series, hour: int, now: pd.Timestamp | None = None, window_days: float | None = 21,
    lower_quantile: float = 0.25, upper_quantile: float = 0.75,
) -> dict:
    """compute_target_band()과 같은 발상(최근 실측 분포의 사분위수를 "정상
    범위"로 삼음)이지만, **시간대(hour)별로 따로** 계산한다 -
    docs/network_control_simulation_design.md 규칙2/3("나운배수지 목표는
    3.5~4.3m 정도지만 시간별로 다름")에 대응한다. 실제로도
    `scripts/network_app`의 "탱크별 관측된 패턴 - 시간대별 목표범위"에서
    이미 확인된 패턴이다(예: 오식도 지 대부분이 낮/저녁 시간대의
    25~75%ile 범위가 서로 다름) - 여기서는 그 계산을 백엔드(Python)
    쪽에서도 그대로 재현한다.

    `now`와 `window_days`를 둘 다 주면(기본) compute_target_band()처럼
    "최근 window_days일" 구간으로 먼저 제한한 뒤 그중 `hour` 시간대만
    골라 분위수를 낸다. 둘 중 하나라도 None이면 **전체 이력**에서 그
    시간대만 골라 계산한다(network_app JS의 hourlyBand()와 정확히 같은
    범위 - 앱이 만든 표와 수치를 맞춰볼 때는 이 모드를 쓸 것).

    lower_quantile >= upper_quantile이거나 hour가 0~23을 벗어나면
    ValueError(compute_target_band와 같은 이유 - 모순된 범위/입력을 조용히
    받아들이지 않는다).
    """
    if lower_quantile >= upper_quantile:
        raise ValueError(
            f"lower_quantile({lower_quantile})은 upper_quantile({upper_quantile})보다 작아야 합니다."
        )
    if not (0 <= hour <= 23):
        raise ValueError(f"hour는 0~23이어야 합니다: {hour!r}")

    scoped = level
    window_start = None
    if now is not None and window_days is not None:
        window_start = now - pd.Timedelta(days=window_days)
        scoped = level.loc[window_start:now]

    by_hour = scoped[scoped.index.hour == hour].dropna()
    if len(by_hour) == 0:
        return {
            "lower": float("nan"), "upper": float("nan"), "n": 0, "hour": hour,
            "window_start": window_start, "window_end": now,
        }
    return {
        "lower": float(by_hour.quantile(lower_quantile)), "upper": float(by_hour.quantile(upper_quantile)),
        "n": len(by_hour), "hour": hour, "window_start": window_start, "window_end": now,
    }


def recommend_max_intervention(
    level0: float,
    o7_forecast: pd.Series,
    q7_forecast: pd.Series,
    target_level: float,
    gain: float,
    area_m2: float,
    freq_minutes: float,
    residual_model=None,
    residual_features: np.ndarray | list[float] | None = None,
    search_max: float = 2000.0,
    tolerance: float = 1.0,
    lever_name: str = "lever",
) -> dict:
    """recommend_min_intervention()의 반대 방향 - horizon 내내 H7이
    target_level(상한)을 넘지 않게 하는, 크기가 가장 작은(0에 가장 가까운)
    delta_lever(<=0, 레버를 "내리는" 방향)를 이분탐색으로 찾는다.

    레버를 올리면(delta_lever>0) Q7이 늘어 수위가 오르므로, 상한을 넘지
    않게 막으려면 반대로 레버를 내려야(delta_lever<0) 한다 - Q_GunS를
    줄이거나 V2 밸브를 닫는 것에 해당한다.

    delta_lever=0(개입 안 함)일 때 이미 target_level 이하면 개입 불필요.
    search_max만큼 낮춰도 여전히 초과하면 achievable=False.
    """
    if not np.isfinite(gain) or gain <= 0:
        raise ValueError(f"gain은 0보다 큰 유한값이어야 합니다({lever_name}를 내리면 Q7도 줄어야 함): {gain!r}")

    def max_level(delta: float) -> float:
        sim = simulate_h7_with_intervention(
            level0, o7_forecast, q7_forecast, delta, gain, area_m2, freq_minutes, residual_model, residual_features
        )
        return float(sim.max())

    baseline_max = max_level(0.0)
    if baseline_max <= target_level:
        return {"lever": lever_name, "delta_lever": 0.0, "achievable": True, "max_level": baseline_max, "note": "개입 불필요 - 이미 목표수위 이하"}

    extreme_max = max_level(-search_max)
    if extreme_max > target_level:
        # delta_lever=None(2026-09-14 수정) - recommend_min_intervention과
        # 같은 이유(위 주석 참고): search_max에 막혀 못 채운 경우 그 상한값을
        # 델타처럼 보이게 담지 않는다.
        return {
            "lever": lever_name, "delta_lever": None, "achievable": False, "max_level": extreme_max,
            "note": f"-{search_max}만큼 낮춰도 목표수위 초과 - 이 레버 단독으로는 부족할 수 있음",
        }

    lo, hi = -search_max, 0.0  # lo: 확인된 feasible(하한 쪽), hi: infeasible(개입 안 한 상태)
    while hi - lo > tolerance:
        mid = (lo + hi) / 2.0
        if max_level(mid) <= target_level:
            lo = mid
        else:
            hi = mid
    return {"lever": lever_name, "delta_lever": lo, "achievable": True, "max_level": max_level(lo), "note": "이분탐색으로 최소 크기(하향) 조정값 산출"}


def recommend_for_band(
    level0: float,
    o7_forecast: pd.Series,
    q7_forecast: pd.Series,
    lower_target: float,
    upper_target: float,
    gain: float,
    area_m2: float,
    freq_minutes: float,
    residual_model=None,
    residual_features: np.ndarray | list[float] | None = None,
    search_max: float = 2000.0,
    tolerance: float = 1.0,
    lever_name: str = "lever",
) -> dict:
    """compute_target_band()가 낸 [lower_target, upper_target] 범위(최근
    3주 Q1~Q3) 기준으로, 개입 없이 뒀을 때 미래 H7 궤적이 그 범위를 벗어날지
    확인하고, 벗어난다면(어느 쪽이든) 그 방향에 맞는 개입을 찾는다:

    - 궤적 최솟값이 lower_target보다 낮아질 것으로 예상되면
      recommend_min_intervention()으로 올리는 개입을 찾는다.
    - 궤적 최댓값이 upper_target보다 높아질 것으로 예상되면
      recommend_max_intervention()으로 내리는 개입을 찾는다.
    - 범위 안에 머무르면 개입하지 않는다(사용자 지정: "그 사이엔 제어X").
    - 양쪽 다 벗어날 것으로 예상되면(예: horizon 초반엔 급락, 후반엔 급등)
      상수 하나로 두 방향을 동시에 만족시킬 수 없으므로 둘 다 계산해서
      보여주되 both_violated=True로 표시한다 - 이 경우는 시간에 따라
      다르게 조정하는 개입이 필요하다는 뜻이고, 이 함수(상수 개입 전제)의
      범위를 벗어난다(recommend.py 모듈 docstring의 한계 참고).
    """
    baseline = simulate_h7_with_intervention(level0, o7_forecast, q7_forecast, 0.0, gain, area_m2, freq_minutes, residual_model, residual_features)
    below = float(baseline.min()) < lower_target
    above = float(baseline.max()) > upper_target

    if not below and not above:
        return {
            "lever": lever_name, "action": "none", "delta_lever": 0.0, "achievable": True,
            "baseline_min": float(baseline.min()), "baseline_max": float(baseline.max()),
            "note": f"예측 궤적이 정상범위[{lower_target:.4f}, {upper_target:.4f}] 안에 머무름 - 개입 불필요",
        }

    result = {"baseline_min": float(baseline.min()), "baseline_max": float(baseline.max())}
    if below:
        raise_result = recommend_min_intervention(
            level0, o7_forecast, q7_forecast, lower_target, gain, area_m2, freq_minutes,
            residual_model, residual_features, search_max, tolerance, lever_name,
        )
        result["raise"] = raise_result
    if above:
        lower_result = recommend_max_intervention(
            level0, o7_forecast, q7_forecast, upper_target, gain, area_m2, freq_minutes,
            residual_model, residual_features, search_max, tolerance, lever_name,
        )
        result["lower"] = lower_result

    if below and above:
        result.update({"lever": lever_name, "action": "conflict", "achievable": False, "both_violated": True,
                        "note": "궤적이 하한/상한을 둘 다 벗어날 것으로 예상 - 상수 개입 하나로는 해결 불가(raise/lower 결과를 각각 참고)"})
    elif below:
        result.update({"lever": lever_name, "action": "raise", "delta_lever": raise_result["delta_lever"],
                        "achievable": raise_result["achievable"], "note": "하한 미달 예상 - 레버를 올리는 개입 추천"})
    else:
        result.update({"lever": lever_name, "action": "lower", "delta_lever": lower_result["delta_lever"],
                        "achievable": lower_result["achievable"], "note": "상한 초과 예상 - 레버를 내리는 개입 추천"})
    return result


# ── H3(나운배수지)용 반응형(시뮬레이션 없는) 제어 (2026-09-11 추가, 실험적) ──
#
# 위쪽 함수들(recommend_for_band 등)은 전부 mass_balance.simulate_level로
# horizon 내내 궤적을 시뮬레이션한다는 전제다 - Q_in/Q_out을 둘 다 알아야
# 하는 방식이다. H3(나운배수지)는 유출 태그 자체가 없어서(taglist/
# GU_network_topology.md, mass_balance.py 모듈 docstring 참고) 이 전제가
# 성립하지 않는다.
#
# 실측으로 확인한 것(2026-09-11): H3 "레벨" 자체는 Q2(유입)와 거의 무관하다
# (lag=0 r²=0.03, lag을 12시간까지 옮겨도 0.001~0.03 - 사실상 노이즈).
# 반면 H3의 "변화량"(예: ΔH3(30분) = H3(t+30분) - H3(t))은 Q2(t)와 뚜렷한
# 관계가 있다(r²=0.15) - 물리적으로 당연하다, dH/dt가 유입량에 관계있는
# 거지 H(누적값) 자체가 아니다. 참고로 V2(밸브개도)는 레벨 기준으로는
# r²=0.127로 그럴듯해 보였지만 변화량 기준으로는 r²=0.008로 사라졌다 —
# 계절/시간대 트렌드가 같이 움직이는 가짜 상관이었다는 뜻(진짜 레버 효과는
# Q2 쪽에 있다).
#
# 그래서 H3는 "몇 시간 앞을 미리 시뮬레이션"하는 대신(Stage1의 리드타임
# 확보라는 존재 이유를 포기하는 셈), 매 제어 주기(cycle_minutes, 보통 운영
# 사이클 주기 - 예: 5분)마다 "지금 레벨이 목표범위를 벗어났는가"만 보고
# 그 자리에서 바로 레버를 조정하는 반응형(순수 피드백) 제어로 다룬다.
# recommend_for_band()류와 나란히 쓸 수 있게 이름/반환 형태를 최대한
# 맞췄지만, "예측 없이 지금 상태만 본다"는 점이 본질적으로 다르다.


def estimate_rate_gain(cause: pd.Series, level: pd.Series, step_steps: int) -> dict:
    """레벨(level)이 step_steps 스텝 뒤까지 얼마나 변하는지(delta =
    level.shift(-step_steps) - level)를 cause에 대해 lag-0 선형회귀한다:
    delta = gain * cause + intercept.

    estimate_gain(cause, delta_series)와 계산은 완전히 같지만, "지금 원본
    레벨이 아니라 그 변화량을 본다"는 프레이밍을 함수 이름/시그니처로
    명시하기 위해 따로 뒀다 - 위 섹션 설명 참고(H3는 레벨 자체보다 변화량이
    cause와 관계가 훨씬 뚜렷했다).

    반환값의 "gain"은 cause 1단위가 step_steps 스텝 동안 level을 얼마나
    움직이는지다. mass_balance의 물리적 게인(1/면적)과 달리, 미계측
    유출/기타 효과를 절편과 잔차가 암묵적으로 흡수한 "경험적" 게인이다 —
    calibrate_area()가 절편을 일부러 안 두는 것과 반대로, 여기서는
    estimate_gain()과 마찬가지로 절편을 둔다(그 흡수 역할을 절편이 하도록).

    step_steps < 1이면 ValueError.
    """
    if step_steps < 1:
        raise ValueError(f"step_steps는 1 이상이어야 합니다: {step_steps!r}")
    delta = level.shift(-step_steps) - level
    return estimate_gain(cause, delta)


def recommend_reactive_adjustment(
    level_now: float,
    lower_target: float,
    upper_target: float,
    rate_gain: float,
    step_minutes: float,
    cycle_minutes: float,
    current_lever_value: float | None = None,
    max_delta_lever: float | None = None,
    damping: float = 1.0,
    lever_name: str = "lever",
) -> dict:
    """시뮬레이션 없이, "지금 레벨이 목표범위를 벗어났으면 그 즉시 레버를
    얼마나 조정할지"만 계산하는 반응형(순수 피드백) 제어기 - 위 섹션 설명
    참고. recommend_for_band()와 근본적으로 다른 전제: 그쪽은 Stage1의
    O7/Q7 예측을 horizon 내내 반영해 몇 시간 전에 미리 조치하지만, 이
    함수는 그런 예측이 아예 없다(리드타임을 포기하는 대신, 매 제어 주기
    (cycle_minutes)마다 반복 호출돼 "지금" 상태로 다시 계산되는 걸
    전제한다 - 한 번 계산하고 몇 시간 방치하는 용도가 아니다).

    - `rate_gain`: estimate_rate_gain()의 결과 dict의 "gain" - cause 1단위가
      `step_minutes` 동안 level을 얼마나 움직이는지.
    - `cycle_minutes`: 이 함수가 실제로 반복 호출되는 주기(예: 운영
      스케줄러가 5분마다 돈다면 5). `rate_gain`을 `step_minutes` 기준에서
      `cycle_minutes` 기준으로 선형 환산해서 쓴다(변화량이 시간에 비례한다는
      1차 근사 - step_minutes와 cycle_minutes가 크게 다르면 근사가
      나빠질 수 있으니 되도록 비슷한 스케일로 맞춰 쓸 것).
    - `damping`(0~1, 기본 1.0): 목표범위 경계까지의 거리(gap)를 한 주기 안에
      전부 메우려 하면(1.0) 게인 추정 오차/노이즈에 취약해 과도조정
      (overshoot)·진동할 수 있다 - 작게 주면 그 비율만큼만 메운다(예: 0.5면
      이번 주기엔 gap의 절반만 조정).
    - `max_delta_lever`: 한 주기에 허용하는 최대 조정폭(레버 급변 방지) —
      넘으면 그 한도로 클리핑하고 note에 남긴다(recommend_min_intervention
      의 achievable=False와 달리, 여기선 "못 한다"가 아니라 "천천히
      따라간다"는 뜻이라 클리핑 후에도 정상 결과로 돌려준다).
    - `current_lever_value`를 주면 `target_lever_value`(= 그 값 +
      delta_lever)도 같이 돌려준다 - 운영자가 "몇 %로 맞추라"를 바로 보게.

    rate_gain이 0이거나 유한하지 않으면(레버를 올렸는데 반대로 움직이는
    관계로는 "얼마나"를 정의할 수 없음) ValueError.
    """
    if not np.isfinite(rate_gain) or rate_gain == 0:
        raise ValueError(f"rate_gain은 0이 아닌 유한값이어야 합니다({lever_name}): {rate_gain!r}")

    if lower_target <= level_now <= upper_target:
        return {
            "lever": lever_name, "action": "none", "delta_lever": 0.0,
            "note": f"현재수위가 정상범위[{lower_target:.4f}, {upper_target:.4f}] 안 - 개입 불필요",
        }

    if level_now < lower_target:
        gap = (lower_target - level_now) * damping
        action = "raise"
    else:
        gap = (upper_target - level_now) * damping  # level_now > upper_target이므로 음수
        action = "lower"

    rate_gain_per_minute = rate_gain / step_minutes
    delta_lever = gap / (rate_gain_per_minute * cycle_minutes)

    clipped = False
    if max_delta_lever is not None and abs(delta_lever) > max_delta_lever:
        delta_lever = float(np.sign(delta_lever) * max_delta_lever)
        clipped = True

    result = {
        "lever": lever_name, "action": action, "delta_lever": float(delta_lever),
        "note": (
            f"{'하한' if action == 'raise' else '상한'} 위반 - 이번 주기({cycle_minutes:.0f}분)에 "
            + (f"조정 한도({max_delta_lever})로 제한됨" if clipped else f"갭의 {damping * 100:.0f}%만큼 조정")
        ),
    }
    if current_lever_value is not None:
        result["target_lever_value"] = float(current_lever_value + delta_lever)
    return result


def recommend_h3_valve_adjustment(
    h3: pd.Series,
    valve: pd.Series,
    now: pd.Timestamp,
    freq_minutes: float,
    step_minutes: float,
    cycle_minutes: float,
    window_days: float | None = 21,
    lower_quantile: float = 0.25,
    upper_quantile: float = 0.75,
    current_lever_value: float | None = None,
    max_delta_lever: float | None = None,
    damping: float = 1.0,
    lever_name: str = "V2",
    min_r_squared: float | None = None,
) -> dict:
    """나운배수지 수위(H3)를 그 시각(`now`)의 "시간대별 정상범위" 안에
    유지하기 위해 밸브(기본 지방산단밸브 V2, `lever_name`으로 다른 밸브도
    가능)를 얼마나 조정할지 규칙기반으로 정한다 -
    docs/network_control_simulation_design.md 규칙2/3 대응:
    - 규칙2: 수위가 너무 높아지면(상한 초과 예상) 밸브를 줄여 유입을 낮게 유지.
    - 규칙3: 수위가 낮아지면(하한 미달 예상) 밸브를 열어 유입을 다시 높임.

    "정확한 기준은 모름"(사용자 명시)이라 목표범위·게인 둘 다 하드코딩된
    상수가 아니라 실측 데이터에서 추정한다. 아래 세 함수를 조합한 얇은
    오케스트레이션일 뿐, 새 통계 로직은 없다:

    1. `compute_target_band_by_hour` - `now.hour` 시간대의 최근
       `window_days`일 실측 분포에서 [lower_quantile, upper_quantile]
       범위를 "정상 목표범위"로 삼는다(시간대별로 다르다는 요구사항).
    2. `estimate_rate_gain` - 밸브가 `step_minutes` 동안 H3를 얼마나
       움직이는지(경험적 게인)를 lag-0 회귀로 추정한다.
    3. `recommend_reactive_adjustment` - 지금 H3가 그 범위를 벗어났으면
       이번 제어주기(`cycle_minutes`)에 밸브를 얼마나 바꿀지 계산한다.

    목표범위를 계산할 데이터가 부족하거나(band n=0) 게인 추정이
    실패/역방향이면(밸브를 열었는데 H3가 안 오르거나 내려가는 관계로는
    "얼마나"를 정의할 수 없음) `action="unavailable"`로 개입하지 않는다 -
    recommend_reactive_adjustment처럼 예외를 던지는 대신, 이 함수는 매
    제어 주기 자동으로 반복 호출되는 걸 전제하므로 잘못된 방향으로
    개입하느니 "이번 주기는 보류"가 더 안전하다.

    `min_r_squared`를 넣으면 게인 추정의 **설명력 자체**도 게이트로 건다 -
    `gain > 0`이어도 `r_squared`가 이 값 미만이면(레버가 통계적으로 거의
    무관하다는 뜻) `action="unavailable"`로 보류한다. 상류로 갈수록(예:
    Q_GunS처럼 여러 갈래로 흩어지는 총량 레버) 방향은 맞아도 설명력이
    잡음 수준(r²≈0.001~0.002)인 경우가 있어서, gain 부호만으로는 걸러지지
    않는 "약하지만 우연히 양수인 게인"을 이 문턱으로 추가로 막는다
    (2026-09-21, 사용자가 "Q_GunS를 약한 신호로만 참고" 요청한 데 대응).
    """
    band = compute_target_band_by_hour(
        h3, now.hour, now=now, window_days=window_days,
        lower_quantile=lower_quantile, upper_quantile=upper_quantile,
    )
    if band["n"] == 0 or not np.isfinite(band["lower"]) or not np.isfinite(band["upper"]):
        return {
            "lever": lever_name, "action": "unavailable", "delta_lever": 0.0,
            "note": f"{now.hour}시 목표범위를 계산할 데이터가 부족함(n={band['n']})",
            "band": band,
        }

    step_steps = max(1, round(step_minutes / freq_minutes))
    rate = estimate_rate_gain(valve, h3, step_steps)
    if not np.isfinite(rate["gain"]) or rate["gain"] <= 0:
        return {
            "lever": lever_name, "action": "unavailable", "delta_lever": 0.0,
            "note": f"밸브→H3 게인 추정 실패/방향 이상(gain={rate['gain']!r}) - 개입 보류",
            "band": band, "rate_gain": rate,
        }
    if min_r_squared is not None and (not np.isfinite(rate["r_squared"]) or rate["r_squared"] < min_r_squared):
        return {
            "lever": lever_name, "action": "unavailable", "delta_lever": 0.0,
            "note": f"게인 추정 신뢰도가 낮음(r²={rate['r_squared']!r} < {min_r_squared}) - 개입 보류",
            "band": band, "rate_gain": rate,
        }

    level_now = h3.asof(now)
    if level_now is None or (isinstance(level_now, float) and not np.isfinite(level_now)):
        return {
            "lever": lever_name, "action": "unavailable", "delta_lever": 0.0,
            "note": f"{now} 시점의 H3 실측값이 없음", "band": band, "rate_gain": rate,
        }

    result = recommend_reactive_adjustment(
        level_now=float(level_now), lower_target=band["lower"], upper_target=band["upper"],
        rate_gain=rate["gain"], step_minutes=step_minutes, cycle_minutes=cycle_minutes,
        current_lever_value=current_lever_value, max_delta_lever=max_delta_lever,
        damping=damping, lever_name=lever_name,
    )
    result["band"] = band
    result["rate_gain"] = rate
    return result


def solve_valve_opening_for_target_flow(
    upstream_flow: float, target_flow: float, min_pct: float = 0.0, max_pct: float = 100.0,
) -> float | None:
    """전단(들어오는) 유량이 `upstream_flow`일 때, 후단(나가는) 유량을
    `target_flow`로 만들려면 밸브 개도(0~100%)를 얼마로 둬야 하는지
    역산한다 - `scripts/network_app`의 밸브 자동계산 규칙("후단 = 전단 ×
    개도/100", index.html의 resolveEdgeArray 참고)을 거꾸로 푼 것뿐이다:
    개도 = target_flow / upstream_flow × 100.

    `upstream_flow`가 0이거나 유한하지 않으면, 또는 필요한 개도가 음수면
    (반대 방향 유량을 요구 - 이 밸브 하나로는 못 만듦) `None`을 돌려준다 -
    "이 조건에서는 이 밸브만으로 그 목표를 만들 수 없다"는 뜻으로, 호출부가
    조용히 이상한 값(0으로 나누기, 음수 개도)을 쓰지 않게 막는다. 계산된
    개도가 [min_pct, max_pct] 밖이면 그 경계로 clip한다(완전히 열거나
    닫아도 부족/과함을 뜻하지만, 밸브 자체는 그 이상 조작할 수 없으므로).
    """
    if upstream_flow == 0 or not np.isfinite(upstream_flow):
        return None
    pct = target_flow / upstream_flow * 100.0
    if pct < 0:
        return None
    return float(np.clip(pct, min_pct, max_pct))


def recommend_h3_v4_adjustment(
    h3: pd.Series,
    q2: pd.Series,
    q4: pd.Series,
    v4: pd.Series,
    upstream_flow: pd.Series,
    now: pd.Timestamp,
    freq_minutes: float,
    step_minutes: float,
    cycle_minutes: float,
    window_days: float | None = 21,
    lower_quantile: float = 0.25,
    upper_quantile: float = 0.75,
    max_delta_q2: float | None = None,
    damping: float = 1.0,
    valve_min_pct: float = 0.0,
    valve_max_pct: float = 100.0,
) -> dict:
    """`recommend_h3_valve_adjustment()`를 실제로 쓸 수 있게 다듬은
    버전 - **제어 레버는 V2(지방산단밸브)가 아니라 V4(국가산단밸브)다**
    (2026-09-21 사용자 정정: "나운배수지 유입유량을 제어하는건
    국가산단밸브" - `docs/GU_network_topology.md`상 V2는 나운으로 가는
    지방산단 라인에 직접 물려 있는 밸브지만, 개정분기에서 지방산단/
    국가산단 두 라인으로 갈라지는 구조상 **국가산단밸브(V4)를 줄이면
    그만큼 지방산단 쪽(Q2, 즉 나운 유입)으로 유량이 더 흘러가는 간접
    효과로 제어한다**(V2 직접 제어가 아니라 형제 분기 밸브를 통한
    보존법칙 기반 간접 제어). 2026-09-21 실측 검증에서도 V2(밸브 개도)
    자체는 H3 변화량과 거의 무관했다(r²≈0.0000, 5분~3시간 전 구간
    전부) - 이 정정과 일치하는 결과다. 반면 **Q2(지방산단 유량, 실제로
    나운배수지에 들어가는 유입량 그 자체)는 뚜렷한 관계가 있다
    (r²≈0.17, 약 50분 horizon에서 최대)**(물리적으로도 당연 - Q2가
    사실상 H3의 "유입유량"이므로, H7-Q7 관계와 같은 구조).

    그래서 이 함수는 세 단계로 계산한다:
      1) `recommend_h3_valve_adjustment(h3, valve=q2, ...)`로 "Q2를
         얼마나 바꿔야 목표범위를 지키는가"(delta_q2)를 구한다(위 실측
         근거로 Q2를 목표 삼음).
      2) 개정분기에서의 보존법칙으로 "Q4를 얼마나 바꿔야 하는가"를
         구한다 - Q2를 delta_q2만큼 올리려면(내리려면) 형제 분기인
         Q4를 그만큼 내려야(올려야) 한다는 뜻이므로 `delta_q4 =
         -delta_q2`(부호 반전 - 이게 "간접 제어"의 핵심).
      3) 그 목표 Q4를, **지금 이 순간의 전단 유량(upstream_flow, V4로
         들어가기 전 유량)**을 근거로 `solve_valve_opening_for_target_
         flow()`를 이용해 "V4를 몇 %로 돌려야 하는가"(v4_target)로
         변환한다.

    운영자가 실제로 조작하는 건 V4이므로, 최종 추천(`lever`/`delta_lever`)은
    **항상 V4 opening 기준**으로 돌려준다 - Q2/Q4는 중간 계산값일 뿐이고
    `q2_delta`/`q2_now`/`q2_target`/`q4_now`/`q4_target` 키로 참고용으로
    같이 남긴다.

    1단계 결과가 `action`이 "none"(개입 불필요) 또는 "unavailable"(밴드/
    게인 추정 실패)이면 그대로 돌려준다(V4 변환 자체가 필요 없거나 의미
    없음). 3단계에서 전단 유량이 0/결측이거나 필요한 개도가 음수면(이
    밸브 하나로는 그 Q4 목표를 못 만듦) `action`을 "unavailable"로
    바꾼다.
    """
    result = recommend_h3_valve_adjustment(
        h3, q2, now=now, freq_minutes=freq_minutes, step_minutes=step_minutes,
        cycle_minutes=cycle_minutes, window_days=window_days,
        lower_quantile=lower_quantile, upper_quantile=upper_quantile,
        max_delta_lever=max_delta_q2, damping=damping, lever_name="Q2",
    )
    result["lever"] = "V4"  # 중간 계산은 Q2 기준이지만, 최종 사용자 표시/조작 대상은 V4.
    if result["action"] in ("none", "unavailable"):
        return result

    delta_q2 = result["delta_lever"]
    delta_q4 = -delta_q2  # 개정분기 보존법칙: Q2를 올리려면(내리려면) 형제 분기 Q4를 내려야(올려야) 함.
    q2_now = q2.asof(now)
    q4_now = q4.asof(now)
    v4_now = v4.asof(now)
    upstream_now = upstream_flow.asof(now)
    values_ok = all(
        v is not None and np.isfinite(v) for v in (q2_now, q4_now, v4_now, upstream_now)
    )
    if not values_ok:
        result["action"] = "unavailable"
        result["note"] = result["note"] + " (V4 변환에 필요한 실측값 부족)"
        return result

    q4_target = float(q4_now) + delta_q4
    v4_target = solve_valve_opening_for_target_flow(float(upstream_now), q4_target, valve_min_pct, valve_max_pct)

    result["q2_delta"] = delta_q2
    result["q2_now"] = float(q2_now)
    result["q2_target"] = float(q2_now) + delta_q2
    result["q4_delta"] = delta_q4
    result["q4_now"] = float(q4_now)
    result["q4_target"] = q4_target
    result["v4_now"] = float(v4_now)
    if v4_target is None:
        result["action"] = "unavailable"
        result["v4_target"] = None
        result["delta_lever"] = None
        result["note"] = result["note"] + " (전단 유량 0 또는 반대방향 요구라 V4로는 이 목표를 못 만듦)"
    else:
        result["v4_target"] = v4_target
        result["delta_lever"] = v4_target - float(v4_now)  # 최종 델타는 V4(%) 기준으로 덮어씀
    return result


def recommend_h3_qguns_adjustment(
    h3: pd.Series,
    q_guns: pd.Series,
    now: pd.Timestamp,
    freq_minutes: float,
    step_minutes: float,
    cycle_minutes: float,
    window_days: float | None = 21,
    lower_quantile: float = 0.25,
    upper_quantile: float = 0.75,
    current_lever_value: float | None = None,
    max_delta_lever: float | None = None,
    damping: float = 1.0,
    min_r_squared: float = 0.05,
) -> dict:
    """"V2는 건드리지 않고, 대신 Q_GunS(군산정수장 송수유량)를 조절해서
    나운배수지(H3)를 관리한다"는 가정으로 만든 정책 함수(2026-09-21 사용자
    요청).

    **실측 검증 결과(2026-09-21, Data/ 캐시 1분 간격, 2022~2026, n≈190만) -
    이 레버는 신뢰할 만한 게인을 못 찾는다.** `estimate_rate_gain(Q_GunS,
    H3, step)`의 r²가 5분~6시간 전 구간 전부에서 **0.0004~0.0023**(60분
    horizon에서 최대 0.0023)로 잡음 수준이다 - 비교로 Q2→H3는 같은 조건에서
    60분에 r²≈0.166까지 나온다. 원인도 확인함: Q_GunS(총 송수량) 자체가
    Q2(지방산단 유량)에 주는 영향도 전 구간 r²≤0.0016, 레벨 상관 0.10에
    불과하다 - Q_GunS는 개정분기에서 지방산단(→나운)뿐 아니라 국가산단/
    내초도분기/지평선산단까지 여러 갈래로 갈라진 뒤라, 총 생산량을 올려도
    그 증분이 정확히 나운 쪽으로 간다는 보장이 없다(Q2처럼 나운행 유량
    그 자체가 아니라 훨씬 상류의 총량 레버이기 때문).

    그래서 이 함수는 `recommend_h3_valve_adjustment(h3, valve=q_guns, ...,
    lever_name="Q_GunS", min_r_squared=min_r_squared)`를 그대로 감싼
    얇은 래퍼일 뿐이다 - Q_GunS는 V2/V4처럼 개도를 유량으로 환산하는
    중간 단계가 필요 없다(그 자체가 이미 실제 유량이라 추천값도 바로
    "Q_GunS를 몇 ㎥/h 만큼 바꿔라"로 나온다). 다만 위 검증 결과 때문에
    `min_r_squared` 기본값을 0.05로 걸어뒀다 - 실측 r²가 이보다 훨씬
    낮으므로(≤0.0023), **기본 설정으로는 거의 항상 `action="unavailable"`
    을 돌려준다** - "약한 신호로만 참고하고 실제 개입은 하지 않는" 보수적
    정책을 의도한 대로 구현한 것이다. 그래도 강제로 써보고 싶으면
    `min_r_squared=0`(또는 더 낮은 값)으로 게이트를 풀 수 있지만, 그 경우
    나오는 추천값은 통계적으로 사실상 무작위에 가깝다는 점을 유의해야 한다.
    """
    result = recommend_h3_valve_adjustment(
        h3, q_guns, now=now, freq_minutes=freq_minutes, step_minutes=step_minutes,
        cycle_minutes=cycle_minutes, window_days=window_days,
        lower_quantile=lower_quantile, upper_quantile=upper_quantile,
        current_lever_value=current_lever_value, max_delta_lever=max_delta_lever,
        damping=damping, lever_name="Q_GunS", min_r_squared=min_r_squared,
    )
    return result
