"""후보 모델(Ridge/Lasso/XGBoost/LightGBM/D-Linear/Informer) 예측 결과를
비교/시각화한다 - `scripts/models/*/meta.json`(train_candidates.py가 저장한
test_metrics_summary)을 모아 모델 간 성능을 그래프로 비교하고, 원하면 실제
DB 데이터로 한 윈도우의 예측 궤적을 실측과 겹쳐 그린다.

데이터 집계 함수(`load_model_cards`/`build_skill_comparison_table`)는
`meta.json`만 읽으면 되므로 DB 없이 합성 파일로 단위테스트한다
(`tests/test_visualize_candidates.py`). 실제 그래프 렌더링(`plot_*`)과
실측 궤적 조회(`load_prediction_trajectory`, DB 필요)는 CLI로만 확인한다
(다른 DB 의존 스크립트와 같은 원칙).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def load_model_cards(models_dir: str = "scripts/models") -> pd.DataFrame:
    """`models_dir` 아래 각 `<name>/meta.json`을 읽어 한 행 = (모델 폴더,
    target, method) 조합인 긴 형식(long-form) DataFrame으로 모은다.

    폴더 이름 규칙(`train_candidates.py`가 저장하는 `<model_type>_<cfg_name>_
    <target1-target2>`)에서 `model_type`을 다시 뽑는 대신, `meta.json`
    안의 `model_type` 필드를 그대로 신뢰한다(폴더명은 사람이 읽기 위한
    것일 뿐 데이터 소스가 아니어야 함 - 나중에 명명 규칙이 바뀌어도 이
    함수는 안 깨짐).

    `meta.json`이 없거나 `test_metrics_summary`가 비어있는 폴더는 조용히
    건너뛴다(아직 평가 전 모델이거나 다른 용도의 폴더일 수 있음).
    """
    rows = []
    base = Path(models_dir)
    if not base.exists():
        return pd.DataFrame()

    for model_dir in sorted(base.iterdir()):
        meta_path = model_dir / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for record in meta.get("test_metrics_summary", []):
            rows.append({
                "model_dir": model_dir.name, "model_type": meta.get("model_type", "?"),
                "cfg_path": meta.get("cfg_path", ""), "used_gpu": meta.get("used_gpu", False),
                **record,
            })
    return pd.DataFrame(rows)


def build_skill_comparison_table(cards: pd.DataFrame, target: str | None = None) -> pd.DataFrame:
    """`load_model_cards()` 결과에서 target별 skill_vs_persistence를
    model_type 기준 내림차순(가장 좋은 모델이 위)으로 정렬한 요약 테이블을
    만든다. `target`을 주면 그 target 하나만 필터링한다."""
    if len(cards) == 0:
        return pd.DataFrame(columns=["target", "model_type", "skill_vs_persistence", "R2", "MAE"])
    df = cards[cards["method"] == "model"] if "method" in cards.columns else cards
    if target is not None:
        df = df[df["target"] == target]
    cols = [c for c in ["target", "model_type", "skill_vs_persistence", "R2", "MAE", "RMSE", "MAPE_%", "SMAPE_%"] if c in df.columns]
    return df[cols].sort_values(["target", "skill_vs_persistence"], ascending=[True, False]).reset_index(drop=True)


def plot_skill_comparison(cards: pd.DataFrame, out_path: str, targets: list[str] | None = None) -> None:
    """target별로 model_type을 skill_vs_persistence 기준 가로 막대그래프로
    비교한다(0을 넘으면 persistence baseline보다 낫다는 뜻이라, 0에 기준선을
    그어 한눈에 보이게 한다)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = cards[cards["method"] == "model"] if "method" in cards.columns else cards
    if targets is not None:
        df = df[df["target"].isin(targets)]
    target_list = sorted(df["target"].unique())
    if not target_list:
        raise ValueError("그릴 데이터가 없습니다(cards가 비어있거나 targets 필터에 걸리는 게 없음).")

    fig, axes = plt.subplots(1, len(target_list), figsize=(6 * len(target_list), 4), squeeze=False)
    for ax, target in zip(axes[0], target_list):
        sub = df[df["target"] == target].sort_values("skill_vs_persistence")
        colors = ["#4c72b0" if v >= 0 else "#c44e52" for v in sub["skill_vs_persistence"]]
        ax.barh(sub["model_type"], sub["skill_vs_persistence"], color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title(f"{target} skill vs persistence")
        ax.set_xlabel("skill_vs_persistence (1 - MAE_model/MAE_persistence)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def load_prediction_trajectory(model_dir: str, window_idx: int = 0) -> dict:
    """저장된 후보 모델을 불러와 실제 test 구간 하나(window_idx번째 윈도우)의
    예측 궤적과 실측을 실제 단위로 돌려준다 - DB 접속이 필요하다(meta.json의
    cfg_path로 다시 prepare_data를 돌리므로). 반환값:
    {"target_cols": [...], "y_true": [horizon, n_targets], "y_pred": [horizon, n_targets], "origin_ts": Timestamp}
    """
    from candidate_models import flatten_windows, load_candidate_model, unflatten_predictions
    from deepems.config import Config
    from deepems.pipeline import prepare_data

    model, pipeline, meta = load_candidate_model(model_dir)
    cfg = Config.from_yaml(meta.cfg_path)
    prepared = prepare_data(cfg)
    target_col_idx = [prepared.target_cols.index(t) for t in meta.target_cols]
    test_ws = prepared.windows["test"]
    if window_idx >= len(test_ws.X):
        raise ValueError(f"window_idx({window_idx})가 test 윈도우 수({len(test_ws.X)})보다 큽니다.")

    x_flat, y_flat = flatten_windows(test_ws.X[window_idx : window_idx + 1], test_ws.y[window_idx : window_idx + 1], target_col_idx)
    y_pred_scaled = unflatten_predictions(model.predict(x_flat), meta.horizon, len(meta.target_cols))[0]
    y_true_scaled = unflatten_predictions(y_flat, meta.horizon, len(meta.target_cols))[0]

    y_pred = np.empty_like(y_pred_scaled)
    y_true = np.empty_like(y_pred_scaled)
    for t, col in enumerate(meta.target_cols):
        y_pred[:, t] = pipeline.inverse_transform_col(col, y_pred_scaled[:, t])
        y_true[:, t] = pipeline.inverse_transform_col(col, y_true_scaled[:, t])

    return {
        "target_cols": meta.target_cols, "y_true": y_true, "y_pred": y_pred,
        "origin_ts": pd.Timestamp(test_ws.origin_ts[window_idx]),
    }


def plot_prediction_trajectory(trajectory: dict, out_path: str, model_label: str = "model") -> None:
    """`load_prediction_trajectory()` 결과를 target별로 예측 vs 실측 선그래프로 그린다."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    target_cols = trajectory["target_cols"]
    horizon = trajectory["y_true"].shape[0]
    fig, axes = plt.subplots(len(target_cols), 1, figsize=(8, 3 * len(target_cols)), squeeze=False)
    for i, target in enumerate(target_cols):
        ax = axes[i][0]
        ax.plot(range(1, horizon + 1), trajectory["y_true"][:, i], label="actual", color="black", linewidth=1.5)
        ax.plot(range(1, horizon + 1), trajectory["y_pred"][:, i], label=model_label, color="#c44e52", linestyle="--")
        ax.set_title(f"{target} (origin={trajectory['origin_ts']})")
        ax.set_xlabel("horizon step")
        ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="후보 모델 예측 결과 비교/시각화")
    parser.add_argument("--models-dir", default="scripts/models")
    parser.add_argument("--out-dir", default="analysis_demo")
    parser.add_argument("--targets", default=None, help="쉼표로 구분(생략하면 저장된 모든 target)")
    parser.add_argument("--trajectory-model-dir", default=None, help="예측 궤적도 그릴 모델 폴더(예: scripts/models/informer_gunS_db_noq8_h6_O7-Q7) - 생략하면 궤적 그래프는 건너뜀(DB 필요)")
    parser.add_argument("--trajectory-window-idx", type=int, default=0)
    args = parser.parse_args(argv)

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    cards = load_model_cards(args.models_dir)
    if len(cards) == 0:
        print(f"[경고] {args.models_dir}에서 읽을 수 있는 모델 카드가 없습니다.")
        return

    targets = [t.strip() for t in args.targets.split(",")] if args.targets else None
    table = build_skill_comparison_table(cards, target=None)
    print(table.to_string(index=False))

    skill_out = str(Path(args.out_dir) / "candidate_skill_comparison.png")
    plot_skill_comparison(cards, skill_out, targets=targets)
    print(f"저장: {skill_out}")

    if args.trajectory_model_dir:
        trajectory = load_prediction_trajectory(args.trajectory_model_dir, window_idx=args.trajectory_window_idx)
        model_type = Path(args.trajectory_model_dir).name
        traj_out = str(Path(args.out_dir) / f"prediction_trajectory_{model_type}.png")
        plot_prediction_trajectory(trajectory, traj_out, model_label=model_type)
        print(f"저장: {traj_out}")


if __name__ == "__main__":
    main()
