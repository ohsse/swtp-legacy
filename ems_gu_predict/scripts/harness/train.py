"""Stage2/3 "학습"(통계적 아티팩트 재계산) — 저수지 면적 역산, 레버 게인
추정, 잔차보정 모델 학습.

Stage1(O7/Q7 수요 예측 신경망)은 `src/deepems/train.py`가 이미 담당한다 —
이 스크립트는 그것과 다른 대상이다. 여기서 만드는 값들은 전체 이력을 훑어야
해서 느리지만, 값 자체는 며칠~몇 주 안에 크게 안 바뀌므로 실시간 사이클마다
다시 계산하지 않고 하루~한 주 주기로만(예: cron) 재실행해 파일(`joblib`)로
저장해두는 용도다. `analysis.py`가 이 파일을 불러와 매 사이클마다 재사용한다.

`docs/forecast_recommendation_pipeline.md`의 Stage 2(2-1/2-2)/Stage 3(3-1)에서
검증한 알고리즘(`mass_balance.calibrate_area`, `recommend.compare_lever_gains`,
`residual_model.fit_residual_model`)을 그대로 호출한다 — 새 알고리즘은 없다.
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from deepems.analyze import clip_series, load_full_raw  # noqa: E402
from deepems.config import Config  # noqa: E402
from deepems.mass_balance import REFERENCE_RESERVOIR_AREAS_M2, calibrate_area  # noqa: E402
from deepems.recommend import compare_lever_gains  # noqa: E402
from deepems.residual_model import build_residual_dataset, fit_residual_model  # noqa: E402
from deepems.taglist import CONTROLLABLE_LEVERS  # noqa: E402


@dataclasses.dataclass
class OfflineArtifacts:
    """`fit_offline_artifacts()`가 만들고 `analysis.run_cycle()`이 소비하는,
    매 사이클 다시 계산할 필요 없는 값들의 묶음."""

    area_m2: float
    lever_gains: dict[str, float]
    lever_stds: dict[str, float]
    residual_model: object | None
    trend_window_steps: int
    fitted_at: pd.Timestamp
    level_col: str
    inflow_col: str
    outflow_col: str


# `python scripts/train.py`로 직접 실행하면 이 파일이 "__main__" 모듈로 로드되어,
# 여기서 정의한 OfflineArtifacts의 __module__이 "__main__"으로 pickle된다 — 그러면
# 나중에 다른 진입점(예: schedule.py가 `import train; train.OfflineArtifacts`로
# unpickle)에서 "Can't get attribute 'OfflineArtifacts' on <module '__main__'>"
# 오류가 난다(2026-09-11 실측으로 발견). __module__을 실제 모듈 이름으로
# 고정해서, CLI로 직접 돌리든 다른 모듈이 import해서 쓰든 항상 같은 pickle
# 호환성을 갖게 한다.
OfflineArtifacts.__module__ = "train"


def fit_offline_artifacts(
    cfg_path: str,
    level_col: str = "H7",
    inflow_col: str = "Q7",
    outflow_col: str = "O7",
    effect_col: str = "Q7",
    residual_horizon_steps: int | None = None,
    residual_trend_window_steps: int | None = None,
    residual_stride: int | None = None,
    residual_model_type: str = "gbr",
    residual_min_rows: int = 20,
    out_path: str | None = None,
) -> OfflineArtifacts:
    """전체 이력(cfg_path가 가리키는 config의 source/기간 그대로)을 한 번 훑어
    면적/레버게인/잔차모델을 만든다.

    - `area_m2`: `calibrate_area()`로 역산. 역산이 실패하면(nan/0 이하 —
      데이터가 부족하거나 변화가 전혀 없는 경우) `mass_balance.
      REFERENCE_RESERVOIR_AREAS_M2`의 실측값으로 대체한다(level_col이
      거기 없으면 그대로 nan — 호출부가 알아채도록 감추지 않는다).
    - `lever_gains`/`lever_stds`: `taglist.CONTROLLABLE_LEVERS`로 후보를
      제한하고(압력 태그 등은 애초에 넣지 않음), `compare_lever_gains()`의
      `usable`(gain>0 and finite) 레버만 남긴다.
    - `residual_model`: 데이터가 `residual_min_rows`보다 적으면(예: 짧은
      기간만 조회한 config) 학습을 건너뛰고 None을 둔다.

    `residual_horizon_steps`/`residual_trend_window_steps`는 **스텝 단위**라
    config의 freq가 바뀌면 물리적 의미가 달라진다 - 그래서 None(기본)이면
    config에서 파생한다(2026-09-28, 1분 주기 전환 대응):
    - `residual_horizon_steps` = `cfg.window.horizon`(Stage1과 같은 예측
      구간을 보정 대상으로 삼는 게 맞으므로)
    - `residual_trend_window_steps` = 60분 / freq_minutes("최근 1시간 추세"
      라는 원래 의도를 freq와 무관하게 유지)
    - `residual_stride` = 5분 / freq_minutes(잔차 학습 origin 간격을 5분으로
      유지). `build_residual_dataset`의 기본 stride=1은 5분 격자에서 "5분마다
      origin 하나"였는데, 1분 격자에서 그대로 두면 origin이 5배(전체 이력
      190만 개)로 늘어난다 - 파이썬 루프라 그만큼 느려지는데 연속된 1분
      origin은 사실상 중복이라 얻는 게 없다.

    기존 5분 config(`gu_db_noq8_h6.yaml`, horizon 72)에서는 이 공식들이
    각각 72 / 12 / 1을 주므로 예전 하드코딩 기본값과 **결과가 완전히 같다**
    (하위호환). 명시적으로 값을 주면 그대로 쓴다.
    """
    cfg = Config.from_yaml(cfg_path)
    data = load_full_raw(cfg)
    df = data.filled.where(data.valid_mask)

    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0
    if residual_horizon_steps is None:
        residual_horizon_steps = int(cfg.window.horizon)
    if residual_trend_window_steps is None:
        residual_trend_window_steps = max(1, round(60.0 / freq_minutes))
    if residual_stride is None:
        residual_stride = max(1, round(5.0 / freq_minutes))

    area_info = calibrate_area(df[level_col], df[inflow_col], df[outflow_col], freq_minutes)
    area_m2 = area_info["fitted_area_m2"]
    if not np.isfinite(area_m2) or area_m2 <= 0:
        area_m2 = REFERENCE_RESERVOIR_AREAS_M2.get(level_col, float("nan"))

    lo, hi = cfg.outlier.lower_quantile, cfg.outlier.upper_quantile
    clip_cols = [c for c in [*CONTROLLABLE_LEVERS, effect_col] if c in df.columns]
    clipped = pd.DataFrame({c: clip_series(df[c], lo, hi) for c in clip_cols})
    lever_cols = [c for c in CONTROLLABLE_LEVERS if c in clipped.columns and c != effect_col]
    gain_table = compare_lever_gains(clipped, lever_cols, effect_col)
    usable = gain_table[gain_table["usable"]] if len(gain_table) else gain_table
    lever_gains = {r["lever"]: float(r["gain"]) for _, r in usable.iterrows()}
    lever_stds = {r["lever"]: float(r["std"]) for _, r in usable.iterrows()}

    dataset = build_residual_dataset(
        df[level_col], df[inflow_col], df[outflow_col], area_m2, freq_minutes,
        residual_horizon_steps, stride=residual_stride, trend_window_steps=residual_trend_window_steps,
    )
    residual_model = (
        fit_residual_model(dataset, model_type=residual_model_type) if len(dataset) >= residual_min_rows else None
    )

    artifacts = OfflineArtifacts(
        area_m2=float(area_m2), lever_gains=lever_gains, lever_stds=lever_stds,
        residual_model=residual_model, trend_window_steps=residual_trend_window_steps,
        fitted_at=pd.Timestamp.now(), level_col=level_col, inflow_col=inflow_col, outflow_col=outflow_col,
    )
    if out_path:
        save_offline_artifacts(artifacts, out_path)
    return artifacts


def save_offline_artifacts(artifacts: OfflineArtifacts, out_path: str) -> None:
    """`out_path`의 부모 디렉터리(예: `models/`)가 아직 없으면 만들고 저장한다
    — 기본 저장 위치(`models/`)를 매번 미리 만들어둘 필요 없게 하기 위함."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, out_path)


def load_offline_artifacts(path: str) -> OfflineArtifacts:
    return joblib.load(path)


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Stage2/3 아티팩트(면적/레버게인/잔차모델) 재계산")
    # window/horizon은 안 쓰고 data: 섹션(freq/resample/결측보정/taglist)만
    # 쓰므로, Stage1에서 실제로 쓰는 config(예: gu_db_noq8_h6.yaml)를 그대로
    # 넘겨도 된다 - data: 섹션이 같은 계열 config끼리는 결과가 동일하다.
    parser.add_argument("--cfg", required=True, help="Stage2/3 config 경로 (예: configs/gu_db_noq8_h6.yaml)")
    # 기본 저장 위치는 models/ 폴더 — Stage1 신경망(./runs/*, src/deepems/train.py가
    # 저장)도 재생성 가능한 학습 산출물이라 이미 .gitignore 대상이고, 여기서
    # 만드는 Stage2/3 아티팩트(.joblib)도 같은 성격이라 별도 디렉터리(models/)에
    # 모아 git에서 제외한다(.gitignore 참고). 폴더가 없으면 자동으로 만든다.
    parser.add_argument("--out", default="models/offline_artifacts.joblib", help="저장할 .joblib 경로")
    parser.add_argument("--level-col", default="H7")
    parser.add_argument("--inflow-col", default="Q7")
    parser.add_argument("--outflow-col", default="O7")
    args = parser.parse_args(argv)

    fit_offline_artifacts(
        args.cfg, level_col=args.level_col, inflow_col=args.inflow_col, outflow_col=args.outflow_col,
        out_path=args.out,
    )
    print(f"저장 완료: {args.out}")


if __name__ == "__main__":
    # OfflineArtifacts.__module__을 "train"으로 고정해뒀는데(위 참고), 이 파일을
    # `python scripts/train.py`로 직접 실행하면 이 실행 중인 모듈은 sys.modules
    # 상에서 "__main__"으로만 등록돼 있고 "train"으로는 없다. 그 상태에서
    # joblib.dump가 "train.OfflineArtifacts"를 검증하려고 `import train`을
    # 새로 시도하면, scripts/가 sys.path에 있어서 이 파일이 처음부터 다시
    # 실행되며 별개의(동일하지 않은) OfflineArtifacts 클래스가 또 만들어지고,
    # pickle이 "it's not the same object" 오류를 낸다(2026-09-11 실측으로 발견).
    # sys.modules["train"]을 지금 실행 중인 모듈 자신으로 미리 등록해두면,
    # 나중에 그 조회가 재실행 없이 같은 객체를 그대로 찾는다.
    sys.modules.setdefault("train", sys.modules["__main__"])
    main()
