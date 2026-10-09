"""학습/평가 결과 시각화.

runs/<run>/의 학습 산출물(training_history.json, test_report.csv, meta.json)
만으로 그래프를 만든다 — train.py가 이미 baseline(persistence 등) 대비
skill_score까지 test_report.csv에 계산해뒀으므로(evaluate.py 참고), 여기서는
그 숫자를 보기 좋게 그리기만 한다. 모델을 다시 불러오거나 DB에 다시 붙지
않으므로 빠르다.

python -m deepems.visualize --run-dir runs/gu_db
python -m deepems.visualize --run-dir runs/gu_db --clean          # 기존 그래프 지우고 새로
python -m deepems.visualize --run-dir runs/gu_db --with-predictions  # 실제 예측 시계열도 추가 (모델/데이터 다시 로딩 — 느릴 수 있음)
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
from pathlib import Path

import pandas as pd

from .plotting import get_plt, small_multiples_grid


@dataclasses.dataclass
class RunArtifacts:
    run_dir: Path
    history: pd.DataFrame  # epoch, train_loss, val_loss
    report: pd.DataFrame  # test_report.csv 그대로
    meta: dict
    config: dict


def load_run(run_dir: str | Path) -> RunArtifacts:
    run_dir = Path(run_dir)
    history_path = run_dir / "training_history.json"
    report_path = run_dir / "test_report.csv"
    meta_path = run_dir / "meta.json"
    config_path = run_dir / "config.json"
    for p in (history_path, report_path, meta_path, config_path):
        if not p.exists():
            raise FileNotFoundError(
                f"{p}가 없습니다 (train.py로 끝까지 학습한 run 폴더가 맞는지 확인하세요)."
            )
    return RunArtifacts(
        run_dir=run_dir,
        history=pd.DataFrame(json.loads(history_path.read_text(encoding="utf-8"))),
        report=pd.read_csv(report_path),
        meta=json.loads(meta_path.read_text(encoding="utf-8")),
        config=json.loads(config_path.read_text(encoding="utf-8")),
    )


# --------------------------------------------------------------------------
# 그래프
# --------------------------------------------------------------------------

def plot_training_curve(history: pd.DataFrame, out_dir: Path) -> Path:
    """train/val loss 곡선 + early stopping이 실제로 버린(과적합 시작 이후) 구간 표시.

    train.py는 val_loss가 가장 낮았던 epoch의 가중치를 최종 모델로 저장한다
    (best_state) — 그 이후 epoch은 학습 곡선에는 남아있지만 실제 산출물에는
    반영되지 않은, "더 돌려봤지만 과적합만 된" 구간이다. 그 사실을 그래프에서
    바로 보이게 표시한다.
    """
    plt = get_plt()
    best_row = history.loc[history["val_loss"].idxmin()]
    best_epoch, best_val = best_row["epoch"], best_row["val_loss"]
    last_epoch = history["epoch"].max()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(history["epoch"], history["train_loss"], label="train_loss", color="steelblue")
    ax.plot(history["epoch"], history["val_loss"], label="val_loss", color="darkorange")
    if last_epoch > best_epoch:
        ax.axvspan(best_epoch, last_epoch, color="gray", alpha=0.12, label="early stopping으로 버려진 구간")
    ax.axvline(best_epoch, color="gray", linestyle="--", linewidth=1)
    ax.scatter([best_epoch], [best_val], color="darkorange", zorder=3, s=40)
    ax.annotate(
        f"best epoch {int(best_epoch)}\n(val_loss={best_val:.5f})",
        (best_epoch, best_val), textcoords="offset points", xytext=(10, 12), fontsize=9,
    )
    ax.set_xlabel("epoch")
    ax.set_ylabel("loss (스케일된 [0,1] 공간 기준 MSE)")
    ax.set_title("학습 곡선")
    ax.legend()
    fig.tight_layout()
    path = out_dir / "training_curve.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_skill_by_target(report: pd.DataFrame, out_dir: Path, baseline: str = "persistence") -> Path | None:
    """target별 skill_vs_<baseline>(horizon 평균)을 가로 막대로, 나쁜 순 -> 좋은 순으로.

    evaluate.py가 추가한 skill_vs_<baseline>_active(정답이 그 윈도우의 horizon
    내내 상수였던 구간 — 장기 고정 구간을 중앙값으로 채운 태그가 test와 겹치면
    발생 — 을 뺀 실질 skill) 컬럼이 있으면, 그 구간이 실제로 섞인 target에만
    ◆ 마커로 같이 표시한다. 두 값이 크게 다르면(P6 실측 사례: 전체 -0.75,
    실질 -0.19) 막대 색만 보고 "이 target은 못한다"고 오판하지 않도록 하기
    위함이다.
    """
    plt = get_plt()
    model = report[report["method"] == "model"]
    col = f"skill_vs_{baseline}"
    if col not in model.columns or model[col].isna().all():
        return None
    active_col = f"{col}_active"
    has_active = active_col in model.columns and not model[active_col].isna().all()

    agg = model.groupby("target")[col].mean().sort_values()
    targets = list(agg.index)

    fig, ax = plt.subplots(figsize=(7, 0.38 * len(targets) + 1.5))
    colors = ["seagreen" if v > 0 else "crimson" for v in agg.values]
    ax.barh(targets, agg.values, color=colors)
    ax.axvline(0, color="gray", linewidth=0.8)

    if has_active:
        n_by_t = model.groupby("target")["n"].first()
        n_active_by_t = model.groupby("target")["n_active"].first()
        agg_active = model.groupby("target")[active_col].mean()
        contaminated = [t for t in targets if n_active_by_t.get(t, n_by_t.get(t, 0)) < n_by_t.get(t, 0)]
        if contaminated:
            ax.scatter(
                [agg_active[t] for t in contaminated], contaminated,
                color="black", marker="D", s=28, zorder=3, label="고정 구간 제외 실질 skill",
            )
            ax.legend(loc="lower right", fontsize=8)

    ax.set_xlabel(f"skill_vs_{baseline} (horizon 평균, >0: baseline보다 나음)")
    ax.set_title(f"target별 skill_vs_{baseline}")
    fig.tight_layout()
    path = out_dir / f"skill_by_target_{baseline}.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_mae_by_horizon(report: pd.DataFrame, out_dir: Path, methods: tuple[str, ...] = ("model", "persistence")) -> Path:
    """target마다 서브플롯 하나씩, horizon_step에 따라 MAE(실제 단위)가 어떻게
    커지는지 model과 baseline을 겹쳐서 보여준다 — "얼마나 먼 미래일수록 더
    틀리는지", "model이 어느 horizon부터 baseline에 뒤처지는지"를 한눈에 보기 위함."""
    plt = get_plt()
    targets = sorted(report["target"].unique())
    colors = {"model": "steelblue", "persistence": "gray", "moving_average": "seagreen", "seasonal_naive": "darkorange"}
    fig, axes, nrows, ncols = small_multiples_grid(plt, len(targets), ncols=4, subplot_w=3.2, subplot_h=2.4)
    for i, t in enumerate(targets):
        ax = axes[i // ncols][i % ncols]
        sub = report[report["target"] == t]
        for m in methods:
            msub = sub[sub["method"] == m].sort_values("horizon_step")
            if len(msub):
                ax.plot(msub["horizon_step"], msub["MAE"], marker="o", markersize=3, label=m, color=colors.get(m))
        ax.set_title(t, fontsize=9)
    for j in range(len(targets), nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.suptitle("horizon별 MAE (실제 단위) — model vs baseline", y=1.05)
    fig.legend(handles, labels, loc="upper center", ncol=len(methods), bbox_to_anchor=(0.5, 1.01))
    fig.tight_layout()
    path = out_dir / "mae_by_horizon.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_sample_predictions(
    cfg_dict: dict, run_dir: Path, out_dir: Path,
    targets: list[str] | None = None, n_windows: int = 400, device: str = "cpu",
) -> Path:
    """test 구간 앞부분 n_windows개 윈도우에 대해, horizon=1(가장 가까운 미래)
    예측을 실제 값·persistence와 나란히 잇는다. 모델/데이터를 config.json 기준으로
    다시 불러와야 해서(DB 재조회 포함 가능) 다른 그래프보다 느릴 수 있다 —
    --with-predictions로만 켠다.
    """
    import torch

    from .baselines import persistence_forecast
    from .model import build_model
    from .pipeline import prepare_data

    # config.json은 cfg.to_dict(redact_secrets=True)로 저장돼 db_host/db_user/
    # db_password가 (실제로 값이 있었다면) "***REDACTED***"로 가려져 있다 —
    # gu_db.yaml처럼 db_connections_path+db_connection_key 방식(비밀번호를
    # 인라인으로 안 쓰는 방식)이면 이 필드들이 애초에 비어 있어서 문제없이
    # db_connections.json에서 실제 접속정보를 다시 읽어온다. inline
    # db_host/db_user/db_password를 쓰는 config였다면 여기서 재접속이
    # 막힌다 — 평문 비밀번호를 그대로 저장해두는 것보다 안전한 실패다.
    cfg = _config_from_dict(cfg_dict)
    data = prepare_data(cfg)
    ws = data.windows["test"]
    if len(ws.X) == 0:
        raise ValueError("test split에 윈도우가 없습니다.")

    model = build_model(
        cfg.model, horizon=cfg.window.horizon, window_size=cfg.window.window_size,
        input_dim=len(data.feature_cols), n_targets=len(data.target_cols), target_idx=data.target_idx,
    )
    model.load_state_dict(torch.load(run_dir / "model.pt", map_location=device))
    model.to(device).eval()

    n = min(n_windows, len(ws.X))
    X, y = ws.X[:n], ws.y[:n]
    with torch.no_grad():
        pred_scaled = model(torch.from_numpy(X).to(device)).cpu().numpy()
    persist_scaled = persistence_forecast(X, data.target_idx, cfg.window.horizon)

    if targets is None:
        # 지정 안 하면 target_report 없이도 되도록, 그냥 앞쪽 몇 개(또는 6개까지)를 고른다
        targets = data.target_cols[: min(6, len(data.target_cols))]

    times = pd.to_datetime(ws.origin_ts[:n]) + pd.Timedelta(cfg.data.freq)  # horizon=1 시점

    plt = get_plt()
    fig, axes, nrows, ncols = small_multiples_grid(plt, len(targets), ncols=2, subplot_w=6.0, subplot_h=2.6)
    for i, t in enumerate(targets):
        ti = data.target_cols.index(t)
        ax = axes[i // ncols][i % ncols]
        actual = data.pipeline.inverse_transform_col(t, y[:, 0, ti])
        pred = data.pipeline.inverse_transform_col(t, pred_scaled[:, 0, ti])
        persist = data.pipeline.inverse_transform_col(t, persist_scaled[:, 0, ti])
        ax.plot(times, actual, color="black", linewidth=1.2, label="실제값")
        ax.plot(times, pred, color="steelblue", linewidth=1, alpha=0.85, label="모델 예측(5분 뒤)")
        ax.plot(times, persist, color="gray", linewidth=0.8, alpha=0.6, linestyle="--", label="persistence")
        ax.set_title(t, fontsize=9)
        ax.tick_params(axis="x", rotation=30, labelsize=7)
    for j in range(len(targets), nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.suptitle(f"test 구간 앞부분 예측 vs 실제 (horizon=1, {n}개 윈도우)", y=1.05)
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.01))
    fig.tight_layout()
    path = out_dir / "sample_predictions.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def _config_from_dict(cfg_dict: dict):
    from .config import Config, DataConfig, ModelConfig, OutlierConfig, OutputConfig, SplitConfig, TrainConfig, WindowConfig

    return Config(
        data=DataConfig(**cfg_dict["data"]),
        window=WindowConfig(**cfg_dict["window"]),
        split=SplitConfig(**cfg_dict["split"]),
        outlier=OutlierConfig(**cfg_dict["outlier"]),
        model=ModelConfig(**cfg_dict["model"]),
        train=TrainConfig(**cfg_dict["train"]),
        output=OutputConfig(**cfg_dict["output"]),
    )


# --------------------------------------------------------------------------
# 오케스트레이션
# --------------------------------------------------------------------------

def _write_markdown_summary(out_dir: Path, art: RunArtifacts, plot_paths: list[Path]) -> None:
    model = art.report[art.report["method"] == "model"]
    best_epoch = int(art.history.loc[art.history["val_loss"].idxmin(), "epoch"])
    last_epoch = int(art.history["epoch"].max())

    lines = [
        f"# 학습 결과 시각화 — {art.run_dir.name}",
        "",
        f"- model.type: `{art.config['model']['type']}`",
        f"- epoch: {len(art.history)}회 실행, best epoch {best_epoch}"
        + (f" (그 뒤 {last_epoch - best_epoch}회는 early stopping으로 버려짐)" if last_epoch > best_epoch else ""),
        "",
    ]

    for baseline in ("persistence", "moving_average", "seasonal_naive"):
        col = f"skill_vs_{baseline}"
        if col not in model.columns or model[col].isna().all():
            continue
        agg = model.groupby("target")[col].mean()
        lines += [
            f"## `{baseline}` 대비 (skill_vs_{baseline}, horizon 평균)",
            "",
            f"- 평균: {agg.mean():.4f}, baseline보다 나은 target 비율: {(agg > 0).mean()*100:.1f}%",
            "",
            agg.sort_values().to_frame("skill").reset_index().rename(columns={"index": "target"}).to_markdown(index=False),
            "",
        ]

    if plot_paths:
        lines += ["## 그래프", ""]
        lines += [f"- {p.name}" for p in plot_paths]
    (out_dir / "visualization_report.md").write_text("\n".join(lines), encoding="utf-8")


def run_and_save(
    run_dir: str | Path, out_dir: str | Path | None = None, clean: bool = False, with_predictions: bool = False,
    prediction_targets: list[str] | None = None,
) -> Path:
    run_dir = Path(run_dir)
    out_dir = Path(out_dir) if out_dir else run_dir / "plots"
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] {run_dir} 산출물 로딩 중 ...")
    art = load_run(run_dir)

    print("[2/3] 그래프 저장 중 ...")
    plot_paths = [
        plot_training_curve(art.history, out_dir),
        plot_mae_by_horizon(art.report, out_dir),
    ]
    for baseline in ("persistence", "moving_average", "seasonal_naive"):
        p = plot_skill_by_target(art.report, out_dir, baseline=baseline)
        if p is not None:
            plot_paths.append(p)

    if with_predictions:
        print("[3/3] 예측 시계열 그래프 저장 중 (모델/데이터 재로딩, 시간이 걸릴 수 있음) ...")
        plot_paths.append(
            plot_sample_predictions(art.config, run_dir, out_dir, targets=prediction_targets)
        )
    else:
        print("[3/3] 예측 시계열 그래프 생략 (--with-predictions로 켤 수 있음)")

    _write_markdown_summary(out_dir, art, plot_paths)
    print(f"\n시각화 결과 저장 위치: {out_dir.resolve()}")
    return out_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="train.py 산출물 폴더 (예: runs/gu_db)")
    parser.add_argument("--out-dir", default=None, help="기본은 <run-dir>/plots")
    parser.add_argument("--clean", action="store_true", help="기존 그래프를 먼저 지우고 새로 만든다")
    parser.add_argument(
        "--with-predictions", action="store_true",
        help="test 구간 실제 예측 vs 실제값 시계열도 그린다 (모델/데이터 재로딩 필요, 느릴 수 있음)",
    )
    parser.add_argument(
        "--prediction-targets", default=None,
        help="--with-predictions일 때 그릴 target 이름(콤마 구분, 예: P6,H7). 생략하면 처음 6개",
    )
    args = parser.parse_args()

    targets = args.prediction_targets.split(",") if args.prediction_targets else None
    run_and_save(
        args.run_dir, out_dir=args.out_dir, clean=args.clean,
        with_predictions=args.with_predictions, prediction_targets=targets,
    )


if __name__ == "__main__":
    main()
