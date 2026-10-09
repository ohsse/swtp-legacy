"""예측 모델 후보(Ridge/Lasso/XGBoost/LightGBM, 앞으로 D-Linear/Informer도
추가 예정) 학습 CLI — 기존 attn-Transformer/attn-LSTM과 같은 config/데이터
분할(`deepems.pipeline.prepare_data`)을 그대로 써서 공정하게 비교되게 한다.

학습이 끝나면 `scripts/models/<model_type>_<cfg_이름>/`에 모델(.joblib),
FeaturePipeline(역변환용), 설명(meta.json + MODEL_CARD.md)을 같이 저장한다
(2026-09-11 요구사항: "학습완료된 모델은 설명과 함께 scripts/models에
저장되도록").

이 저장소는 패키지로 설치돼 있지 않으므로(`pyproject.toml` 없음), `src/`를
`sys.path`에 올려서 `deepems`를 임포트한다 — `tests/`와 같은 관례.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from candidate_models import (  # noqa: E402
    CandidateModelMeta,
    MODEL_FACTORIES,
    fit_candidate,
    flatten_windows,
    save_candidate_model,
    unflatten_predictions,
)
from deepems.baselines import persistence_forecast  # noqa: E402
from deepems.config import Config  # noqa: E402
from deepems.metrics import build_comparison_report, summarize_by_target  # noqa: E402
from deepems.pipeline import prepare_data  # noqa: E402


def inverse_transform_targets(pipeline, arr_scaled: np.ndarray, target_cols: list[str]) -> np.ndarray:
    """`arr_scaled`([N, horizon, len(target_cols)], 스케일된 값)를 target별로
    `pipeline.inverse_transform_col`을 적용해 실제 물리 단위로 되돌린다 —
    metrics.py는 항상 실제 단위로 계산해야 한다는 이 저장소의 원칙(모듈
    docstring 참고) 때문에 필수 단계다."""
    n, horizon, n_targets = arr_scaled.shape
    out = np.empty_like(arr_scaled)
    for t, col in enumerate(target_cols):
        flat = arr_scaled[:, :, t].reshape(-1)
        out[:, :, t] = pipeline.inverse_transform_col(col, flat).reshape(n, horizon)
    return out


def train_one(
    cfg_path: str,
    model_type: str,
    targets: list[str],
    out_dir: str = "scripts/models",
    max_train_windows: int | None = None,
    model_kwargs: dict | None = None,
) -> Path:
    model_kwargs = model_kwargs or {}
    cfg = Config.from_yaml(cfg_path)
    prepared = prepare_data(cfg)

    missing = [t for t in targets if t not in prepared.target_cols]
    if missing:
        raise ValueError(f"target_cols에 없는 target입니다: {missing}. 사용 가능: {prepared.target_cols}")
    target_col_idx = [prepared.target_cols.index(t) for t in targets]  # y의 마지막 축(=target_cols) 기준
    feature_col_idx = [prepared.feature_cols.index(t) for t in targets]  # X의 마지막 축(=feature_cols) 기준 (persistence용)

    train_ws, test_ws = prepared.windows["train"], prepared.windows["test"]
    if len(train_ws.X) == 0 or len(test_ws.X) == 0:
        raise ValueError(f"train/test 윈도우가 비어있습니다(train={len(train_ws.X)}, test={len(test_ws.X)}). cfg/기간을 확인할 것.")

    x_train, y_train = flatten_windows(train_ws.X, train_ws.y, target_col_idx)
    x_test, y_test = flatten_windows(test_ws.X, test_ws.y, target_col_idx)

    if max_train_windows and len(x_train) > max_train_windows:
        # 학습 윈도우가 너무 많으면(특히 XGBoost/LightGBM을 MultiOutputRegressor로
        # 감싸면 출력 개수만큼 개별 모델을 fit해서 느려짐) 무작위로 줄인다 —
        # 시간순 데이터라 순서 편향 없이 고르게 뽑히도록 셔플 후 자른다.
        rng = np.random.RandomState(42)
        idx = rng.choice(len(x_train), size=max_train_windows, replace=False)
        x_train, y_train = x_train[idx], y_train[idx]

    # dlinear는 x_flat/y_flat을 3D로 복원해야 해서 window_size/n_features/
    # feature_target_idx가 필요하다(dlinear_model.DLinearRegressor 참고) -
    # 다른 모델(ridge 등)은 **kwargs로 받아서 그냥 무시하므로 항상 넘겨도 안전.
    model_kwargs = {
        **model_kwargs,
        "window_size": cfg.window.window_size, "n_features": len(prepared.feature_cols),
        "feature_target_idx": feature_col_idx, "n_targets": len(targets),
    }

    print(f"[1/4] {model_type} 학습 중 (train={len(x_train)}윈도우, test={len(x_test)}윈도우, target={targets}) ...")
    model, used_gpu = fit_candidate(model_type, x_train, y_train, horizon=cfg.window.horizon, **model_kwargs)
    print(f"  GPU 사용: {used_gpu}")

    print("[2/4] test 예측/평가 중 ...")
    horizon = cfg.window.horizon
    y_pred_scaled = unflatten_predictions(model.predict(x_test), horizon, len(targets))
    y_true_scaled = test_ws.y[:, :, target_col_idx]

    y_pred_real = inverse_transform_targets(prepared.pipeline, y_pred_scaled, targets)
    y_true_real = inverse_transform_targets(prepared.pipeline, y_true_scaled, targets)
    persistence_real = inverse_transform_targets(
        prepared.pipeline, persistence_forecast(test_ws.X, feature_col_idx, horizon), targets
    )

    report = build_comparison_report(y_true_real, {"model": y_pred_real, "persistence": persistence_real}, targets)
    summary = summarize_by_target(report[report["method"] == "model"])
    print(summary.to_string(index=False))

    print("[3/4] 저장 중 ...")
    meta = CandidateModelMeta(
        model_type=model_type, cfg_path=str(cfg_path), target_cols=targets, feature_cols=prepared.feature_cols,
        window_size=cfg.window.window_size, horizon=horizon, freq=cfg.data.freq,
        n_train_windows=len(x_train), n_test_windows=len(x_test),
        trained_at=pd.Timestamp.now().isoformat(), model_kwargs=model_kwargs,
        test_metrics_summary=summary.to_dict("records"), used_gpu=used_gpu,
    )
    # config 파일명 자체(gu_db_noq8_h6.yaml 등)는 taglist 리네임(Q_Gu->Q_GunS,
    # 2026-09-14) 이전부터 쓰이던 이름이라 안 바꾸지만, 저장 폴더명은 그
    # 리네임과 맞춰 "gu_db" -> "gunS_db"로 치환한다(2026-09-14, 사용자 확인 -
    # "모델명을 GU에서 GunS로 수정"). 여기서 치환해두면 cfg 파일명을 바꾸지
    # 않고도 재학습할 때마다 항상 gunS_db* 폴더명이 나온다.
    cfg_name = Path(cfg_path).stem.replace("gu_db", "gunS_db")
    # target을 폴더명에 넣지 않으면 같은 (model_type, cfg) 조합으로 다른
    # target을 학습할 때 서로 덮어쓴다 - 2026-09-11 실측: O7/Q7로 학습한
    # informer_gu_db_noq8_h6를 H3/Q2 학습이 그대로 덮어써서 O7/Q7 모델이
    # 사라졌었다(재학습으로 복구). target_cols가 많아 폴더명이 너무 길어질
    # 수 있어 3개 넘으면 "+N개"로 줄인다.
    target_tag = "-".join(targets) if len(targets) <= 3 else f"{'-'.join(targets[:3])}+{len(targets) - 3}개"
    out_path = save_candidate_model(
        model, prepared.pipeline, meta, str(Path(out_dir) / f"{model_type}_{cfg_name}_{target_tag}")
    )
    print(f"[4/4] 저장 완료: {out_path}")
    return out_path


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="예측 모델 후보(Ridge/Lasso/XGBoost/LightGBM/D-Linear/Informer) 학습")
    parser.add_argument("--cfg", required=True, help="예: configs/gu_db_noq8_h6.yaml (attn-Transformer와 같은 config를 써야 공정 비교)")
    parser.add_argument("--model", required=True, choices=sorted(MODEL_FACTORIES))
    parser.add_argument("--targets", default="O7,Q7", help="쉼표로 구분(기본 O7,Q7, Stage2/3가 실제로 쓰는 target)")
    parser.add_argument("--out-dir", default="scripts/models")
    parser.add_argument("--max-train-windows", type=int, default=None, help="학습 윈도우 수 상한(속도용, 기본 제한 없음)")
    parser.add_argument("--alpha", type=float, default=None, help="ridge/lasso 정규화 강도")
    parser.add_argument("--n-estimators", type=int, default=None, help="xgboost/lightgbm")
    parser.add_argument("--max-depth", type=int, default=None, help="xgboost/lightgbm")
    parser.add_argument("--learning-rate", type=float, default=None, help="xgboost/lightgbm/dlinear/informer(Adam lr)")
    parser.add_argument("--epochs", type=int, default=None, help="dlinear/informer 최대 epoch")
    parser.add_argument("--patience", type=int, default=None, help="dlinear/informer 조기종료 patience")
    parser.add_argument("--label-len", type=int, default=None, help="informer 디코더에 넣을 실측 구간 길이(기본 min(48, window_size//2))")
    parser.add_argument("--d-model", type=int, default=None, help="informer 임베딩 차원")
    parser.add_argument("--e-layers", type=int, default=None, help="informer 인코더 층수")
    args = parser.parse_args(argv)

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    model_kwargs = {
        k: v for k, v in {
            "alpha": args.alpha, "n_estimators": args.n_estimators,
            "max_depth": args.max_depth, "learning_rate": args.learning_rate,
            "lr": args.learning_rate, "epochs": args.epochs, "patience": args.patience,
            "label_len": args.label_len, "d_model": args.d_model, "e_layers": args.e_layers,
        }.items() if v is not None
    }

    train_one(args.cfg, args.model, targets, out_dir=args.out_dir, max_train_windows=args.max_train_windows, model_kwargs=model_kwargs)


if __name__ == "__main__":
    main()
