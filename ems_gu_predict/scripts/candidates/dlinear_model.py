"""D-Linear(Zeng et al. 2022, "Are Transformers Effective for Time Series
Forecasting?") 후보 모델 - candidate_models.py의 다른 후보(Ridge/Lasso/
XGBoost/LightGBM)와 같은 sklearn 스타일 fit(X, y)/predict(X) 인터페이스를
갖는 얇은 PyTorch 래퍼(DLinearRegressor)로 구현한다.

원 논문의 핵심 아이디어: 시계열을 이동평균으로 뽑은 추세(trend)와 그
나머지(seasonal)로 분해한 뒤, 각각을 독립된 Linear(window_size -> horizon)
층 하나로만 예측해서 더한다. 어텐션/RNN 없이 채널별 선형층 두 개뿐이라
학습이 매우 빠르고(attn-Transformer 대비 파라미터 수가 수백 배 적음),
논문에서도 여러 벤치마크에서 당시 SOTA 트랜스포머 계열을 능가해 화제가
됐다 - 여기서는 그 결과가 이 저수지 데이터에도 재현되는지 실측 비교가
목적이다.

target(O7/Q7)마다 서로 다른 물리량이라 가중치를 공유하지 않고
채널별(individual) Linear를 따로 둔다(원 논문의 individual=True 설정).
입력은 그 target 자신의 과거값만 쓴다(DLinear는 원래 univariate-per-channel
모델 - 다른 태그를 cross-attention으로 참고하는 attn-Transformer와는
설계가 다르다는 점이 이 비교의 핵심 관전 포인트).
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# torch는 이 저장소 전체(src/deepems/model.py 등)에서 이미 하드 의존성이라
# 여기서도 최상위에서 바로 임포트한다. 아래 두 클래스를 모듈 최상위에 둬야
# joblib pickling이 가능하다 - 함수/메서드 안에 지역 정의된 클래스는
# "it's not found as <module>.<func>.<locals>.<Class>" 에러로 저장이
# 실패한다(2026-09-11 실측, tests/test_candidate_models.py의 _FakePipeline과
# 같은 원인).


class _MovingAvgDecomp(nn.Module):
    """AvgPool1d 기반 이동평균으로 trend/seasonal 분해. 양 끝을 replicate
    패딩해서 길이를 window_size로 유지한다(원 논문의 series_decomp 구현과 동일)."""

    def __init__(self, kernel_size: int):
        super().__init__()
        self.kernel_size = kernel_size
        self.avg = nn.AvgPool1d(kernel_size=kernel_size, stride=1, padding=0)

    def forward(self, x):
        # x: [N, window_size, n_targets]
        pad_left = (self.kernel_size - 1) // 2
        pad_right = self.kernel_size - 1 - pad_left
        x_t = x.permute(0, 2, 1)  # [N, n_targets, window_size]
        x_padded = F.pad(x_t, (pad_left, pad_right), mode="replicate")
        trend = self.avg(x_padded)  # [N, n_targets, window_size]
        trend = trend.permute(0, 2, 1)  # [N, window_size, n_targets]
        seasonal = x - trend
        return seasonal, trend


class _DLinearNet(nn.Module):
    def __init__(self, window_size: int, horizon: int, n_targets: int, kernel_size: int = 25):
        super().__init__()
        self.decomp = _MovingAvgDecomp(kernel_size)
        self.n_targets = n_targets
        self.seasonal_linear = nn.ModuleList([nn.Linear(window_size, horizon) for _ in range(n_targets)])
        self.trend_linear = nn.ModuleList([nn.Linear(window_size, horizon) for _ in range(n_targets)])

    def forward(self, x):
        # x: [N, window_size, n_targets] -> out: [N, horizon, n_targets]
        seasonal, trend = self.decomp(x)
        outs = []
        for t in range(self.n_targets):
            s_out = self.seasonal_linear[t](seasonal[:, :, t])  # [N, horizon]
            tr_out = self.trend_linear[t](trend[:, :, t])
            outs.append(s_out + tr_out)
        return torch.stack(outs, dim=-1)  # [N, horizon, n_targets]


class DLinearRegressor:
    """sklearn 스타일 fit(x_flat, y_flat)/predict(x_flat) - x_flat/y_flat은
    candidate_models.flatten_windows()가 편 2D 배열([N, window_size*n_features],
    [N, horizon*n_targets])을 그대로 받는다. 내부에서 원래 3D 형태로 복원한
    뒤, feature_target_idx로 target 자신의 과거값 채널만 뽑아 신경망에 넣는다.

    GPU: torch.cuda.is_available()이면 학습(fit)을 GPU에서 돈다 - D-Linear는
    파라미터가 아주 적어 GPU 이점이 크지 않을 수 있지만, 실제로 썼는지는
    `used_gpu_`에 정직하게 남긴다(모듈 docstring의 설계 원칙과 동일). 저장은
    joblib pickling이 CUDA 텐서에서 깨지는 걸 피하려고 항상 CPU 가중치로
    한다 - 추론도 CPU에서 하는데, D-Linear는 계산량이 워낙 작아(선형층 2개)
    실질적인 속도 차이가 없다.
    """

    def __init__(
        self, window_size: int, n_features: int, feature_target_idx: list[int], horizon: int, n_targets: int,
        kernel_size: int = 25, lr: float = 1e-3, epochs: int = 100, patience: int = 10, batch_size: int = 256,
        use_gpu: bool | None = None,
    ):
        self.window_size = window_size
        self.n_features = n_features
        self.feature_target_idx = feature_target_idx
        self.horizon = horizon
        self.n_targets = n_targets
        self.kernel_size = kernel_size
        self.lr = lr
        self.epochs = epochs
        self.patience = patience
        self.batch_size = batch_size
        self.use_gpu = use_gpu
        self.used_gpu_ = False
        self.net_ = None

    def _to_3d_inputs(self, x_flat: np.ndarray) -> np.ndarray:
        n = x_flat.shape[0]
        x3 = x_flat.reshape(n, self.window_size, self.n_features)
        return x3[:, :, self.feature_target_idx]

    def fit(self, x_flat: np.ndarray, y_flat: np.ndarray) -> "DLinearRegressor":
        from candidate_models import gpu_available  # 지연 임포트: candidate_models가 dlinear_model을 임포트하는 순환을 피함

        n = x_flat.shape[0]
        x3 = self._to_3d_inputs(x_flat)
        y3 = y_flat.reshape(n, self.horizon, self.n_targets)

        want_gpu = gpu_available() if self.use_gpu is None else self.use_gpu
        device = "cuda" if want_gpu else "cpu"
        self.used_gpu_ = want_gpu

        # 시간순 데이터라 순서가 섞여 있어도(flatten_windows/max_train_windows
        # 서브샘플 단계에서 이미 섞였을 수 있음) 여기서 다시 무작위로
        # train/val을 나눈다 - 조기종료용 내부 검증셋(train.py의 val split과
        # 같은 역할, 별도 val 인자를 안 받는 sklearn 인터페이스라 fit() 안에서
        # 직접 떼어낸다).
        rng = np.random.RandomState(42)
        idx = rng.permutation(n)
        n_val = max(1, int(n * 0.1))
        val_idx, train_idx = idx[:n_val], idx[n_val:]

        net = _DLinearNet(self.window_size, self.horizon, self.n_targets, kernel_size=self.kernel_size)
        net = net.to(device)
        optimizer = torch.optim.Adam(net.parameters(), lr=self.lr)

        x_train_t = torch.tensor(x3[train_idx], dtype=torch.float32, device=device)
        y_train_t = torch.tensor(y3[train_idx], dtype=torch.float32, device=device)
        x_val_t = torch.tensor(x3[val_idx], dtype=torch.float32, device=device)
        y_val_t = torch.tensor(y3[val_idx], dtype=torch.float32, device=device)

        best_val, best_state, patience_left = float("inf"), None, self.patience
        for _epoch in range(self.epochs):
            net.train()
            perm = torch.randperm(len(x_train_t), device=device)
            for i in range(0, len(x_train_t), self.batch_size):
                batch_idx = perm[i : i + self.batch_size]
                optimizer.zero_grad()
                pred = net(x_train_t[batch_idx])
                loss = F.mse_loss(pred, y_train_t[batch_idx])
                loss.backward()
                optimizer.step()

            net.eval()
            with torch.no_grad():
                val_loss = F.mse_loss(net(x_val_t), y_val_t).item()
            if val_loss < best_val - 1e-9:
                best_val = val_loss
                best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}
                patience_left = self.patience
            else:
                patience_left -= 1
                if patience_left <= 0:
                    break

        if best_state is not None:
            net.load_state_dict(best_state)
        # CPU로 내려서 저장(joblib pickling이 CUDA 텐서와 얽히는 문제를
        # 피함) - predict()도 항상 CPU에서 돈다(모듈 docstring 참고).
        self.net_ = net.to("cpu")
        return self

    def predict(self, x_flat: np.ndarray) -> np.ndarray:
        if self.net_ is None:
            raise RuntimeError("fit() 전에는 predict()를 호출할 수 없습니다.")
        n = x_flat.shape[0]
        x3 = self._to_3d_inputs(x_flat)
        self.net_.eval()
        preds = []
        with torch.no_grad():
            x_t = torch.tensor(x3, dtype=torch.float32)
            for i in range(0, n, 512):
                preds.append(self.net_(x_t[i : i + 512]).numpy())
        out = np.concatenate(preds, axis=0) if preds else np.empty((0, self.horizon, self.n_targets), dtype=np.float32)
        return out.reshape(n, -1)
