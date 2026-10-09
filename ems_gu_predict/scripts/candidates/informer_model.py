"""Informer(Zhou et al. 2021, "Informer: Beyond Efficient Transformer for
Long Sequence Time-Series Forecasting") 후보 모델 - dlinear_model.py와 같은
패턴으로, candidate_models.py의 sklearn 스타일 fit(X, y)/predict(X) 인터페이스를
갖는 PyTorch 래퍼(InformerRegressor)로 구현한다.

**원본 대비 단순화한 부분 (정직하게 명시)**: 원 논문의 핵심 기여인
ProbSparse self-attention은 인코더 시퀀스 길이가 수천~수만일 때(장기
시계열) top-u개 쿼리만 골라 attention을 근사해서 O(L logL)로 낮추는
기법이다. 이 저장소의 window_size(288, 24시간)는 그 정도로 길지 않아
표준 nn.MultiheadAttention(O(L^2), L=288이면 완전히 감당 가능한 크기)를
그대로 쓴다 - 즉 "ProbSparse 없는 Informer"다. 대신 Informer의 또 다른
핵심 요소인 **인코더 distilling**(Conv1d+MaxPool1d로 레이어마다 시퀀스
길이를 절반으로 줄여 계산량/과적합을 동시에 줄이는 구조)과 **생성형
디코더**(디코더 입력에 최근 실측값(label_len) + 0으로 채운 예측
구간(horizon)을 이어붙여 한 번의 forward로 horizon 전체를 예측 -
attn-LSTM/GRU 계열의 순차적 autoregressive 디코딩보다 빠르고 오차
누적이 없다)는 그대로 구현했다. 8종 후보 비교에서 "진짜 순수
Transformer 인코더-디코더 구조가 이 데이터에 맞는지"를 attn-Transformer
(다른 설계, model.py 참고)와는 별개로 확인하는 게 이 모델의 목적이다.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn

# torch는 이 저장소 전체의 하드 의존성이라 최상위에서 바로 임포트한다.
# 아래 클래스들은 dlinear_model.py와 같은 이유(joblib pickling)로 반드시
# 모듈 최상위에 둔다 - 함수/메서드 안에 지역 정의하면 "it's not found as
# <module>.<func>.<locals>.<Class>"로 저장이 실패한다(2026-09-11
# _DLinearNet에서 실측).


class _PositionalEncoding(nn.Module):
    """표준 sinusoidal positional encoding - 학습 파라미터 없음."""

    def __init__(self, d_model: int, max_len: int = 2000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term[: pe[:, 1::2].shape[1]])
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, x):
        # x: [N, L, d_model]
        return x + self.pe[:, : x.size(1)]


class _DistilConv(nn.Module):
    """Informer의 인코더 distilling 층 - Conv1d + ELU + MaxPool1d(stride=2)로
    시퀀스 길이를 대략 절반으로 줄인다. padding=1/kernel=3/stride=2 조합은
    입력 길이가 1이어도 출력이 최소 1은 나오므로(floor((L-1)/2)+1) 아주 짧은
    윈도우(단위테스트용 합성 데이터 포함)에서도 길이가 0으로 붕괴하지 않는다."""

    def __init__(self, d_model: int):
        super().__init__()
        self.conv = nn.Conv1d(d_model, d_model, kernel_size=3, padding=1)
        self.norm = nn.BatchNorm1d(d_model)
        self.activation = nn.ELU()
        self.pool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

    def forward(self, x):
        # x: [N, L, d_model] -> [N, ceil(L/2), d_model]
        x = x.transpose(1, 2)  # [N, d_model, L]
        x = self.pool(self.activation(self.norm(self.conv(x))))
        return x.transpose(1, 2)


class _InformerNet(nn.Module):
    def __init__(
        self, n_targets: int, horizon: int, label_len: int,
        d_model: int = 64, n_heads: int = 4, e_layers: int = 2, d_layers: int = 1,
        d_ff: int = 128, dropout: float = 0.1,
    ):
        super().__init__()
        self.horizon = horizon
        self.label_len = label_len

        self.enc_embed = nn.Linear(n_targets, d_model)
        self.dec_embed = nn.Linear(n_targets, d_model)
        self.pos_enc = _PositionalEncoding(d_model)

        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff, dropout=dropout,
            activation="gelu", batch_first=True,
        )
        self.enc_layers = nn.ModuleList([enc_layer.__class__(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff, dropout=dropout,
            activation="gelu", batch_first=True,
        ) for _ in range(e_layers)])
        # distilling: 레이어 사이(e_layers-1개)에 conv로 시퀀스 길이를 줄인다(원 논문 그대로)
        self.distil_layers = nn.ModuleList([_DistilConv(d_model) for _ in range(max(0, e_layers - 1))])

        dec_layer = nn.TransformerDecoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff, dropout=dropout,
            activation="gelu", batch_first=True,
        )
        self.dec_layers = nn.ModuleList([dec_layer.__class__(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff, dropout=dropout,
            activation="gelu", batch_first=True,
        ) for _ in range(d_layers)])

        self.out_proj = nn.Linear(d_model, n_targets)

    def forward(self, x_enc, x_dec_known):
        # x_enc: [N, window_size, n_targets] (인코더 입력, 과거 전체)
        # x_dec_known: [N, label_len, n_targets] (디코더 입력 중 실측 구간 - 최근 label_len 스텝)
        n = x_enc.size(0)
        device = x_enc.device

        enc = self.pos_enc(self.enc_embed(x_enc))
        for i, layer in enumerate(self.enc_layers):
            enc = layer(enc)
            if i < len(self.distil_layers):
                enc = self.distil_layers[i](enc)

        zeros = torch.zeros(n, self.horizon, x_dec_known.size(-1), device=device, dtype=x_dec_known.dtype)
        dec_in = torch.cat([x_dec_known, zeros], dim=1)  # [N, label_len+horizon, n_targets]
        dec = self.pos_enc(self.dec_embed(dec_in))

        causal_mask = nn.Transformer.generate_square_subsequent_mask(dec.size(1)).to(device)
        for layer in self.dec_layers:
            dec = layer(dec, enc, tgt_mask=causal_mask)

        out = self.out_proj(dec)  # [N, label_len+horizon, n_targets]
        return out[:, -self.horizon :, :]  # 예측 구간만 반환


class InformerRegressor:
    """sklearn 스타일 fit(x_flat, y_flat)/predict(x_flat) - dlinear_model.
    DLinearRegressor와 같은 계약(입력/출력 shape, GPU 처리, CPU pickling)을
    따른다. x_flat/y_flat은 candidate_models.flatten_windows()가 편 2D
    배열이고, 내부에서 3D로 복원한 뒤 feature_target_idx로 target 자신의
    과거값 채널만 뽑아 신경망에 넣는다(D-Linear와 동일하게 univariate-
    per-channel 입력 - attn-Transformer처럼 21개 feature 전체를 cross-
    attention으로 참고하지 않는다. 공정 비교를 위해 D-Linear와 입력 조건을
    맞췄다)."""

    def __init__(
        self, window_size: int, n_features: int, feature_target_idx: list[int], horizon: int, n_targets: int,
        label_len: int | None = None, d_model: int = 64, n_heads: int = 4, e_layers: int = 2, d_layers: int = 1,
        d_ff: int = 128, dropout: float = 0.1, lr: float = 1e-3, epochs: int = 100, patience: int = 10,
        batch_size: int = 128, use_gpu: bool | None = None,
    ):
        self.window_size = window_size
        self.n_features = n_features
        self.feature_target_idx = feature_target_idx
        self.horizon = horizon
        self.n_targets = n_targets
        # label_len: 디코더에 실측값으로 넣어줄 최근 구간 길이 - 너무 짧으면
        # 디코더가 참고할 맥락이 없고, window_size보다 길 수는 없다.
        self.label_len = label_len if label_len is not None else max(1, min(48, window_size // 2))
        self.d_model = d_model
        self.n_heads = n_heads
        self.e_layers = e_layers
        self.d_layers = d_layers
        self.d_ff = d_ff
        self.dropout = dropout
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

    def _build_net(self) -> _InformerNet:
        return _InformerNet(
            n_targets=self.n_targets, horizon=self.horizon, label_len=self.label_len,
            d_model=self.d_model, n_heads=self.n_heads, e_layers=self.e_layers, d_layers=self.d_layers,
            d_ff=self.d_ff, dropout=self.dropout,
        )

    def fit(self, x_flat: np.ndarray, y_flat: np.ndarray) -> "InformerRegressor":
        from candidate_models import gpu_available  # 지연 임포트: 순환 임포트 회피

        n = x_flat.shape[0]
        x3 = self._to_3d_inputs(x_flat)  # [N, window_size, n_targets]
        y3 = y_flat.reshape(n, self.horizon, self.n_targets)
        dec_known = x3[:, -self.label_len :, :]  # 디코더 입력의 실측 구간

        want_gpu = gpu_available() if self.use_gpu is None else self.use_gpu
        device = "cuda" if want_gpu else "cpu"
        self.used_gpu_ = want_gpu

        rng = np.random.RandomState(42)
        idx = rng.permutation(n)
        n_val = max(1, int(n * 0.1))
        val_idx, train_idx = idx[:n_val], idx[n_val:]

        net = self._build_net().to(device)
        optimizer = torch.optim.Adam(net.parameters(), lr=self.lr)

        x_enc_train = torch.tensor(x3[train_idx], dtype=torch.float32, device=device)
        dec_train = torch.tensor(dec_known[train_idx], dtype=torch.float32, device=device)
        y_train_t = torch.tensor(y3[train_idx], dtype=torch.float32, device=device)
        x_enc_val = torch.tensor(x3[val_idx], dtype=torch.float32, device=device)
        dec_val = torch.tensor(dec_known[val_idx], dtype=torch.float32, device=device)
        y_val_t = torch.tensor(y3[val_idx], dtype=torch.float32, device=device)

        best_val, best_state, patience_left = float("inf"), None, self.patience
        for _epoch in range(self.epochs):
            net.train()
            perm = torch.randperm(len(x_enc_train), device=device)
            for i in range(0, len(x_enc_train), self.batch_size):
                b = perm[i : i + self.batch_size]
                optimizer.zero_grad()
                pred = net(x_enc_train[b], dec_train[b])
                loss = torch.nn.functional.mse_loss(pred, y_train_t[b])
                loss.backward()
                optimizer.step()

            net.eval()
            with torch.no_grad():
                val_loss = torch.nn.functional.mse_loss(net(x_enc_val, dec_val), y_val_t).item()
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
        # CPU로 내려서 저장(joblib pickling이 CUDA 텐서와 얽히는 문제를 피함,
        # dlinear_model.DLinearRegressor와 같은 이유) - predict()도 항상 CPU.
        self.net_ = net.to("cpu")
        return self

    def predict(self, x_flat: np.ndarray) -> np.ndarray:
        if self.net_ is None:
            raise RuntimeError("fit() 전에는 predict()를 호출할 수 없습니다.")
        n = x_flat.shape[0]
        x3 = self._to_3d_inputs(x_flat)
        dec_known = x3[:, -self.label_len :, :]
        self.net_.eval()
        preds = []
        with torch.no_grad():
            x_enc_t = torch.tensor(x3, dtype=torch.float32)
            dec_t = torch.tensor(dec_known, dtype=torch.float32)
            for i in range(0, n, 256):
                preds.append(self.net_(x_enc_t[i : i + 256], dec_t[i : i + 256]).numpy())
        out = np.concatenate(preds, axis=0) if preds else np.empty((0, self.horizon, self.n_targets), dtype=np.float32)
        return out.reshape(n, -1)
