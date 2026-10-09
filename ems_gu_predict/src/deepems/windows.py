"""연속 구간(segment) 안에서만 슬라이딩 윈도우를 만든다.

기존 to_sequences_x/y (두 학습 노트북에 동일하게 존재)는 DataFrame
행 순서로만 자르기 때문에, 결측으로 빠진 행이 있어도 그 앞뒤를
그대로 이어붙여 "60분 윈도우"라고 취급했다. 여기서는 data.py의
find_segments()가 돌려주는, 실제로 시간이 끊기지 않은 구간
안에서만 윈도우를 만든다.

또한 출력 시퀀스 길이를 horizon(예: 5)으로 고정한다. 기존 모델은
window_size(60) 길이 전체를 출력하고 앞부분(window_size-horizon)은
패딩(0 또는 10)으로 채운 뒤 마지막 horizon개만 취했는데, 한 노트북은
이 패딩을 마스킹 없이 그대로 MSE에 포함시켜 학습 신호를 희석시켰다.
여기서는 애초에 필요한 horizon 길이만 예측/학습하므로 그런 문제가
구조적으로 없다.
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


@dataclasses.dataclass
class WindowSet:
    X: np.ndarray  # [N, window_size, n_features]
    y: np.ndarray  # [N, horizon, n_targets]
    origin_ts: np.ndarray  # [N] 예측 시작 시점(=입력 마지막 시각) 타임스탬프


def make_windows(
    df: pd.DataFrame,
    segments: list[tuple[int, int]],
    feature_cols: list[str],
    target_cols: list[str],
    window_size: int,
    horizon: int,
    stride: int,
) -> WindowSet:
    values = df[feature_cols].to_numpy(dtype=np.float32)
    target_values = df[target_cols].to_numpy(dtype=np.float32)
    index = df.index

    xs, ys, ts = [], [], []
    for seg_start, seg_end in segments:
        seg_len = seg_end - seg_start
        max_i = seg_len - window_size - horizon
        for i in range(0, max_i + 1, stride):
            a = seg_start + i
            b = a + window_size
            c = b + horizon
            xs.append(values[a:b])
            ys.append(target_values[b:c])
            ts.append(index[b - 1])

    if not xs:
        return WindowSet(
            X=np.empty((0, window_size, len(feature_cols)), dtype=np.float32),
            y=np.empty((0, horizon, len(target_cols)), dtype=np.float32),
            origin_ts=np.empty((0,), dtype="datetime64[ns]"),
        )

    return WindowSet(
        X=np.stack(xs),
        y=np.stack(ys),
        origin_ts=np.array(ts, dtype="datetime64[ns]"),
    )


def compute_time_decay_weights(
    origin_ts: np.ndarray,
    halflife_days: float,
    reference_ts: np.datetime64 | None = None,
) -> np.ndarray:
    """오래된 윈도우일수록 가중치를 지수적으로 낮춘다(잘라내지는 않음).

    2026-08 국가산단밸브 제어 방식 변경(고정 개방 -> 수위 연동 조절,
    docs/model_results.md 참고) 이후로 옛날 데이터의 제어 정책 자체가
    달라져서, 전체 기간을 그대로 동일 가중치로 학습하면 지금과 다른
    정책의 패턴을 같은 비중으로 배우게 된다. 구간을 아예 잘라내면
    학습 윈도우 수가 40219 -> 수천 개로 급감해 과적합 위험이 커지므로,
    자르는 대신 `weight = 0.5 ** (age_days / halflife_days)`로 최근
    데이터의 비중만 높인다 - `reference_ts`(기본 origin_ts 중 최댓값)로부터
    `halflife_days`가 지날 때마다 가중치가 절반이 된다.
    """
    if reference_ts is None:
        reference_ts = origin_ts.max()
    age_days = (reference_ts - origin_ts) / np.timedelta64(1, "D")
    age_days = np.clip(age_days, 0, None)
    return np.power(0.5, age_days / halflife_days).astype(np.float32)


class WindowDataset(Dataset):
    def __init__(self, ws: WindowSet, sample_weight: np.ndarray | None = None):
        self.X = torch.from_numpy(ws.X)
        self.y = torch.from_numpy(ws.y)
        if sample_weight is None:
            sample_weight = np.ones(len(ws.X), dtype=np.float32)
        self.w = torch.from_numpy(np.asarray(sample_weight, dtype=np.float32))

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.y[idx], self.w[idx]
