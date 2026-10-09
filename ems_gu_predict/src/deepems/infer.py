"""운영 추론에서 학습과 동일한 전처리를 강제하기 위한 얇은 래퍼.

기존 main_guns_v1.py의 Predict_1min_test()는:
  - DB에서 LIMIT 60으로 최근 60행을 가져와 실제 타임스탬프 확인 없이
    "60분 윈도우"로 취급했고,
  - 결측은 testset.fillna(testset.mean())으로 채웠다 — 학습 때는
    dropna()로 결측 구간을 아예 버렸으므로, 학습이 한 번도 보지
    못한 형태의 입력을 운영에서 모델에 넣는 셈이었다.

여기서는 학습 산출물(FeaturePipeline, meta.json)을 그대로 불러와
같은 리샘플링·결측 처리·스케일링 함수를 재사용하고, 시간이 실제로
연속인지 확인해 아니면 예외를 던진다 (조용히 잘못된 예측을 내보내는
대신, 무엇이 문제인지 알 수 있게).
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from .config import ModelConfig
from .data import FeaturePipeline, resample_and_flag_gaps
from .model import build_model


@dataclasses.dataclass
class LoadedArtifacts:
    cfg: dict  # train.py가 저장한 config.json (dict) — 학습 때 쓴 값 그대로 재사용
    model: torch.nn.Module
    pipeline: FeaturePipeline
    feature_cols: list[str]
    target_cols: list[str]
    device: str


def load_artifacts(run_dir: str, device: str = "cpu") -> LoadedArtifacts:
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    cfg_dict = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))

    pipeline: FeaturePipeline = joblib.load(run_dir / "feature_pipeline.joblib")

    # build_model은 train.py와 공유하는 단일 조립 함수라, 학습 때 쓴 구조(model.type
    # 포함)와 여기서 재구성하는 구조가 어긋날 수 없다.
    model = build_model(
        ModelConfig(**cfg_dict["model"]),
        horizon=cfg_dict["window"]["horizon"],
        window_size=cfg_dict["window"]["window_size"],
        input_dim=len(meta["feature_cols"]),
        n_targets=len(meta["target_cols"]),
        target_idx=meta["target_idx"],
    )
    model.load_state_dict(torch.load(run_dir / "model.pt", map_location=device))
    model.to(device).eval()

    return LoadedArtifacts(
        cfg=cfg_dict,
        model=model,
        pipeline=pipeline,
        feature_cols=meta["feature_cols"],
        target_cols=meta["target_cols"],
        device=device,
    )


@torch.no_grad()
def predict_next_horizon(art: LoadedArtifacts, raw_recent: pd.DataFrame) -> pd.DataFrame:
    """raw_recent: 학습에 쓰인 feature_cols를 컬럼으로 갖는, 시간순 정렬된
    최근 원시 데이터 (예: DB에서 가져온 최근 N분). freq 그리드로 리샘플링/
    짧은 결측 보정을 거친 뒤, 정확히 window_size분 연속 데이터가 있어야
    예측한다 — 아니면 예외를 던진다 (기존 코드처럼 평균으로 조용히
    메꾸고 넘어가지 않는다).
    """
    cfg = art.cfg
    window_size = cfg["window"]["window_size"]
    horizon = cfg["window"]["horizon"]

    filled, valid_mask = resample_and_flag_gaps(
        raw_recent[art.feature_cols], cfg["data"]["freq"], cfg["data"]["ffill_limit_minutes"]
    )
    if len(filled) < window_size:
        raise ValueError(f"입력 데이터가 {len(filled)}분뿐입니다 (window_size={window_size}분 필요).")

    tail = filled.iloc[-window_size:]
    tail_valid = valid_mask.iloc[-window_size:]
    if not tail_valid.all():
        bad = tail.index[~tail_valid.to_numpy()]
        raise ValueError(
            f"최근 {window_size}분 안에 결측/불연속 구간이 있어 예측을 건너뜁니다: {list(bad)}"
        )

    scaled = art.pipeline.transform(tail, clip=False)  # 운영 입력은 test와 동일하게 clip하지 않는다.
    x = scaled[art.feature_cols].to_numpy(dtype=np.float32)[None, :, :]
    pred_scaled = art.model(torch.from_numpy(x).to(art.device)).cpu().numpy()[0]  # [horizon, n_targets]

    origin = tail.index[-1]
    freq_delta = pd.Timedelta(cfg["data"]["freq"])
    out = {}
    for t, col in enumerate(art.target_cols):
        out[col] = art.pipeline.inverse_transform_col(col, pred_scaled[:, t])
    idx = [origin + (k + 1) * freq_delta for k in range(horizon)]
    return pd.DataFrame(out, index=idx)
