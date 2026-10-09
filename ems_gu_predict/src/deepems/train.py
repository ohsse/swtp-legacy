"""학습 엔트리포인트.

python -m deepems.train --config configs/gunsan.yaml
python -m deepems.train --config configs/gunsan_db.yaml --model-type attn_lstm   # 다른 모델로 비교 실험
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import random
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from torch.utils.data import DataLoader

from .baselines import compute_inverse_persistence_weights
from .config import Config
from .evaluate import evaluate_test_split
from .model import MODEL_TYPES, build_model
from .pipeline import prepare_data
from .windows import WindowDataset, compute_time_decay_weights


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def resolve_device(name: str) -> str:
    """"auto"면 GPU(cuda -> mps 순)를 먼저 쓰고, 없을 때만 cpu로 내려간다.

    attn_transformer_residual(self-attention, model.py 참고)은 행렬 연산이
    많아 CPU보다 GPU에서 훨씬 빠르다 — 그래서 이 프로젝트는 "auto"를 그냥
    조용히 cpu로 떨어뜨리지 않고, 실제로 어떤 장치를 왜 골랐는지 항상
    로그로 남긴다 (GPU가 있는데 못 잡고 있는 상황을 바로 알 수 있게).
    특정 장치를 강제하려면 config의 train.device나 CLI `--device`로
    "cuda"/"cuda:0"/"mps"/"cpu"를 직접 지정하면 된다.
    """
    if name != "auto":
        print(f"  device: {name} (명시적으로 지정됨)")
        return name
    if torch.cuda.is_available():
        print(f"  device: cuda ({torch.cuda.get_device_name(0)})")
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        print("  device: mps (Apple GPU)")
        return "mps"
    print(
        "  device: cpu (GPU(cuda/mps)를 지원하는 PyTorch/드라이버가 감지되지 않았습니다. "
        "GPU를 쓰려면 CUDA 지원 PyTorch를 설치하거나 --device로 직접 지정하세요.)"
    )
    return "cpu"


def run_epoch(model, loader, device, optimizer=None, target_weights: torch.Tensor | None = None) -> float:
    is_train = optimizer is not None
    model.train(is_train)
    total_loss, total_n = 0.0, 0
    for xb, yb, wb in loader:
        xb, yb, wb = xb.to(device), yb.to(device), wb.to(device)
        with torch.set_grad_enabled(is_train):
            pred = model(xb)
            sq_err = (pred - yb) ** 2  # [B, horizon, n_targets]
            if target_weights is not None:
                sq_err = sq_err * target_weights.view(1, 1, -1)
            # 샘플(윈도우)별로 먼저 평균낸 뒤 sample weight로 가중 평균 -
            # 오래된 윈도우(wb가 작음)의 기여를 줄인다(compute_time_decay_weights).
            per_sample = sq_err.mean(dim=(1, 2))
            loss = (per_sample * wb).sum() / wb.sum().clamp_min(1e-8)
            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        total_loss += loss.item() * xb.size(0)
        total_n += xb.size(0)
    return total_loss / max(total_n, 1)


def train(cfg: Config) -> Path:
    set_seed(cfg.train.seed)
    device = resolve_device(cfg.train.device)
    out_dir = Path(cfg.output.dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] 데이터 준비 중 (device={device}) ...")
    data = prepare_data(cfg)
    for split in ("train", "val", "test"):
        n = len(data.windows[split].X)
        print(f"  - {split}: {n}개 시퀀스")
        if n == 0:
            raise ValueError(f"{split} split에 시퀀스가 0개입니다. 설정(min_segment_minutes, purge_minutes, 기간)을 확인하세요.")

    train_sample_weight = None
    if cfg.train.sample_time_decay_halflife_days is not None:
        train_sample_weight = compute_time_decay_weights(
            data.windows["train"].origin_ts, halflife_days=cfg.train.sample_time_decay_halflife_days,
        )
        print(f"  time-decay sample weight: halflife={cfg.train.sample_time_decay_halflife_days}일, "
              f"train 윈도우 가중치 범위 [{train_sample_weight.min():.4f}, {train_sample_weight.max():.4f}]")
    # val은 학습 신호에 안 쓰이고 early-stopping 판단 기준이라, 지금 시점
    # 성능을 그대로 보기 위해 시간 가중치를 걸지 않는다(전부 1).
    train_loader = DataLoader(
        WindowDataset(data.windows["train"], sample_weight=train_sample_weight),
        batch_size=cfg.train.batch_size, shuffle=True, drop_last=True,
    )
    val_loader = DataLoader(WindowDataset(data.windows["val"]), batch_size=cfg.train.batch_size, shuffle=False)

    model = build_model(
        cfg.model, horizon=cfg.window.horizon, window_size=cfg.window.window_size,
        input_dim=len(data.feature_cols), n_targets=len(data.target_cols), target_idx=data.target_idx,
    ).to(device)
    print(f"  model.type = {cfg.model.type} ({sum(p.numel() for p in model.parameters()):,} params)")
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.train.lr, weight_decay=cfg.train.weight_decay)

    target_weights = None
    if cfg.train.target_loss_weighting == "inverse_persistence_mae":
        w = compute_inverse_persistence_weights(
            data.windows["train"].X, data.windows["train"].y, data.target_idx,
            max_weight=cfg.train.target_loss_weight_cap,
        )
        target_weights = torch.tensor(w, device=device)
        print(f"  target loss weights (inverse persistence MAE, cap={cfg.train.target_loss_weight_cap}): "
              f"{dict(zip(data.target_cols, w.round(3).tolist()))}")

    print("[2/4] 학습 시작 ...")
    best_val = float("inf")
    best_state = None
    patience_left = cfg.train.patience
    history = []
    for epoch in range(1, cfg.train.epochs + 1):
        t0 = time.time()
        train_loss = run_epoch(model, train_loader, device, optimizer, target_weights=target_weights)
        val_loss = run_epoch(model, val_loader, device, optimizer=None, target_weights=target_weights)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        print(f"  epoch {epoch:4d} | train_loss {train_loss:.6f} | val_loss {val_loss:.6f} | {time.time()-t0:.1f}s")

        if val_loss < best_val - 1e-6:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = cfg.train.patience
        else:
            patience_left -= 1
            if patience_left <= 0:
                print(f"  early stopping at epoch {epoch} (best val_loss={best_val:.6f})")
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    print("[3/4] 산출물 저장 중 ...")
    torch.save(model.state_dict(), out_dir / "model.pt")
    joblib.dump(data.pipeline, out_dir / "feature_pipeline.joblib")
    # to_dict()는 기본적으로 DB 접속정보(host/user/password)를 가린다 — 학습 산출물
    # (runs/*/config.json)은 결과 공유·backup 과정에서 밖으로 나갈 수 있으므로 평문 비밀번호를 남기지 않는다.
    (out_dir / "config.json").write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    meta = {
        "feature_cols": data.feature_cols,
        "target_cols": data.target_cols,
        "target_idx": data.target_idx,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[4/4] Test set에서 baseline 대비 평가 중 ...")
    report = evaluate_test_split(cfg, data, model, device)
    report.to_csv(out_dir / "test_report.csv", index=False, encoding="utf-8-sig")
    print(report.to_string(index=False))
    print(f"\n산출물 저장 위치: {out_dir.resolve()}")
    return out_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--model-type", choices=MODEL_TYPES, default=None,
        help="config의 model.type을 덮어씀 (같은 데이터로 다른 모델 구조를 바로 비교 학습할 때 사용). "
        "지정하면 output.dir에 _<model-type>이 자동으로 붙어 기존 결과를 덮어쓰지 않음.",
    )
    parser.add_argument("--out-dir", default=None, help="output.dir을 직접 지정 (자동 접미사보다 우선)")
    parser.add_argument(
        "--device", default=None,
        help="config의 train.device를 덮어씀 (auto/cuda/cuda:0/mps/cpu). "
        "기본(auto)은 GPU(cuda -> mps)를 먼저 찾고 없으면 cpu로 내려간다. GPU가 있는데 안 잡히면 "
        "이 옵션으로 명시해서 원인을 좁힐 수 있다.",
    )
    args = parser.parse_args()
    cfg = Config.from_yaml(args.config)

    if args.model_type:
        cfg = dataclasses.replace(cfg, model=dataclasses.replace(cfg.model, type=args.model_type))
        if args.out_dir is None:
            cfg = dataclasses.replace(cfg, output=dataclasses.replace(cfg.output, dir=f"{cfg.output.dir}_{args.model_type}"))
    if args.out_dir:
        cfg = dataclasses.replace(cfg, output=dataclasses.replace(cfg.output, dir=args.out_dir))
    if args.device:
        cfg = dataclasses.replace(cfg, train=dataclasses.replace(cfg.train, device=args.device))

    train(cfg)


if __name__ == "__main__":
    main()
