"""예측 모델 두 가지: 기존 AttnLSTMForecaster(호환용)와,
분석 결과를 반영해 새로 설계한 AttnTransformerResidualForecaster(기본값).

## 왜 다시 설계했나 (근거: analysis/*/autocorrelation.csv, runs/gunsan_db/test_report.csv)

1. **naive(persistence)가 이례적으로 강한 baseline이다.** 이 프로젝트의 모든
   타깃은 lag_1min 자기상관이 대체로 0.95~0.999 (analyze.py의 EDA 결과) —
   즉 "1분 뒤 값 = 지금 값"이라는 가정만으로도 이미 거의 정답에 가깝다.
   실제로 gunsan_db를 AttnLSTMForecaster(기존 구조)로 학습해서 평가해보니
   `skill_vs_persistence`가 Q_GunS -0.09~-0.27, P_GunS -0.52~-1.18로,
   **59 epoch을 학습하고도(조기종료, val_loss는 3~5 epoch 만에 수렴) 그냥
   직전 값을 쓰는 것보다 못했다.** val_loss가 초반에 이미 거의 다 떨어지고
   그 뒤로 거의 안 줄었다는 것은 undertraining이 아니라 이 구조·목적함수
   조합의 한계라는 뜻이다.
2. **원인으로 의심되는 구조적 문제**: 기존 모델은 절대값을 처음부터 직접
   회귀한다. 초기화 시점의 예측은 사실상 무작위이고, "그냥 마지막 값을
   반복하면 이미 거의 다 맞는다"는 아주 강한 사전 지식을 architecture
   차원에서 전혀 활용하지 않는다 — 학습이 그 지식을 매 스텝 gradient로
   재발견해야 한다.
3. **대응**: 모델이 절대값이 아니라 persistence 예측값 대비 "변화량(Δ)"만
   예측하도록 바꿨다 (`AttnTransformerResidualForecaster`). Δ 회귀 head의
   마지막 Linear 층을 0으로 초기화해서, **학습 시작 시점의 예측이 정확히
   persistence와 같다** — 즉 skill_vs_persistence가 애초에 0(동점)에서
   출발하고, 그 뒤로는 오직 "이 상황에서 얼마나 벗어날지"만 학습하면 된다.
   구조적으로 persistence보다 나쁜 상태로 수렴할 이유가 없다.
4. Attention은 self-attention 인코더(nn.TransformerEncoder, 여러 head)로
   바꿨다 — 기존의 단일 query Luong-attention보다 어떤 과거 시점 조합이
   지금 상황과 비슷한지를 더 유연하게 표현할 수 있다. 짧은 고정 길이
   윈도우(60분)라 학습형 위치 임베딩을 쓴다.
"""
from __future__ import annotations

import torch
import torch.nn as nn


# --------------------------------------------------------------------------
# 기존 모델 (호환용으로 남겨둠 — model.type: attn_lstm)
# --------------------------------------------------------------------------

class TemporalAttention(nn.Module):
    """마지막 hidden state를 query로, 인코더 전체 출력을 key/value로 쓰는
    Luong-style attention."""

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.proj = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, encoder_outputs: torch.Tensor, query: torch.Tensor):
        scores = torch.bmm(encoder_outputs, self.proj(query).unsqueeze(2)).squeeze(2)
        weights = torch.softmax(scores, dim=1)
        context = torch.bmm(weights.unsqueeze(1), encoder_outputs).squeeze(1)
        return context, weights


class AttnLSTMForecaster(nn.Module):
    def __init__(
        self,
        input_dim: int,
        n_targets: int,
        horizon: int,
        encoder_hidden: int = 64,
        decoder_hidden: int = 32,
        dropout: float = 0.1,
        non_negative_output: bool = True,
    ):
        super().__init__()
        self.horizon = horizon
        self.n_targets = n_targets

        self.encoder = nn.LSTM(input_dim, encoder_hidden, batch_first=True)
        self.attention = TemporalAttention(encoder_hidden)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Sequential(
            nn.Linear(encoder_hidden * 2, decoder_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(decoder_hidden, horizon * n_targets),
        )
        self.output_activation = nn.Softplus() if non_negative_output else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoder_out, (h_n, _) = self.encoder(x)
        last_hidden = h_n[-1]
        context, attn_weights = self.attention(encoder_out, last_hidden)
        combined = self.dropout(torch.cat([last_hidden, context], dim=1))
        out = self.head(combined)
        out = out.view(-1, self.horizon, self.n_targets)
        return self.output_activation(out)


# --------------------------------------------------------------------------
# 신규 모델 (기본값 — model.type: attn_transformer_residual)
# --------------------------------------------------------------------------

class AttentionPooling(nn.Module):
    """학습 가능한 query 하나로 인코더 출력 T개 시점을 요약한다
    (BERT의 [CLS] 토큰과 비슷한 역할). attn_weights를 남겨서 어느 과거
    시점이 예측에 크게 기여했는지 사후 점검할 수 있다."""

    def __init__(self, d_model: int, nhead: int, dropout: float):
        super().__init__()
        self.query = nn.Parameter(torch.zeros(1, 1, d_model))
        self.mha = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)

    def forward(self, encoded: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # encoded: [B, T, d_model]
        b = encoded.size(0)
        query = self.query.expand(b, -1, -1)  # [B, 1, d_model]
        context, attn_weights = self.mha(query, encoded, encoded, need_weights=True)
        return context.squeeze(1), attn_weights.squeeze(1)  # [B, d_model], [B, T]


class AttnTransformerResidualForecaster(nn.Module):
    """self-attention 인코더 + persistence 잔차(Δ) 예측 head.

    forward()가 받는 x는 window_size분의 입력 feature 시퀀스이고,
    target_idx는 그 feature들 중 실제로 예측해야 하는 target의 위치다
    (pipeline.PreparedData.target_idx와 동일한 규약). 마지막 시점의
    target 값(persistence)에 학습된 Δ를 더해서 최종 예측을 만든다.
    """

    def __init__(
        self,
        input_dim: int,
        n_targets: int,
        horizon: int,
        target_idx: list[int],
        d_model: int = 64,
        nhead: int = 4,
        num_encoder_layers: int = 2,
        dim_feedforward: int = 128,
        decoder_hidden: int = 32,
        dropout: float = 0.1,
        non_negative_output: bool = True,
        window_size: int = 60,
    ):
        super().__init__()
        if d_model % nhead != 0:
            raise ValueError(f"d_model({d_model})은 nhead({nhead})로 나누어떨어져야 합니다.")
        self.horizon = horizon
        self.n_targets = n_targets
        self.non_negative_output = non_negative_output
        self.register_buffer("target_idx", torch.tensor(target_idx, dtype=torch.long), persistent=False)

        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_embedding = nn.Parameter(torch.zeros(1, window_size, d_model))
        nn.init.trunc_normal_(self.pos_embedding, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward,
            dropout=dropout, batch_first=True, activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_encoder_layers)
        self.pool = AttentionPooling(d_model, nhead, dropout)

        self.delta_head = nn.Sequential(
            nn.Linear(d_model, decoder_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(decoder_hidden, horizon * n_targets),
        )
        # 마지막 층을 0으로 초기화 -> 학습 시작 시점의 Δ=0 -> 예측이 정확히
        # persistence와 같다. skill_vs_persistence가 0(동점)에서 출발한다.
        nn.init.zeros_(self.delta_head[-1].weight)
        nn.init.zeros_(self.delta_head[-1].bias)

        self._last_attn_weights: torch.Tensor | None = None  # 사후 점검용 (선택)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, input_dim]
        t = x.size(1)
        h = self.input_proj(x) + self.pos_embedding[:, :t, :]
        encoded = self.encoder(h)  # [B, T, d_model]
        context, attn_weights = self.pool(encoded)  # [B, d_model], [B, T]
        self._last_attn_weights = attn_weights.detach()

        delta = self.delta_head(context)  # [B, horizon * n_targets]
        delta = delta.view(-1, self.horizon, self.n_targets)

        persistence = x[:, -1, self.target_idx]  # [B, n_targets] — 마지막 관측값
        persistence = persistence.unsqueeze(1).expand(-1, self.horizon, -1)  # [B, horizon, n_targets]

        out = persistence + delta
        if self.non_negative_output:
            out = torch.clamp(out, min=0.0)
        return out


MODEL_TYPES = ("attn_transformer_residual", "attn_lstm")  # build_model()/CLI --model-type이 고르는 값


def build_model(
    model_cfg, horizon: int, window_size: int, input_dim: int, n_targets: int, target_idx: list[int]
) -> nn.Module:
    """model_cfg.type으로 모델 클래스를 고른다. model_cfg는 config.ModelConfig
    (또는 같은 필드를 가진 아무 객체/dict-unpacked dataclass)면 된다 — 학습
    (train.py)과 추론 재구성(infer.py)이 이 함수 하나를 공유해서 쓰기 때문에,
    학습 때 만든 모델과 나중에 state_dict를 불러올 모델의 구조가 어긋나는
    일이 없다."""
    if model_cfg.type == "attn_transformer_residual":
        return AttnTransformerResidualForecaster(
            input_dim=input_dim, n_targets=n_targets, horizon=horizon,
            target_idx=target_idx, d_model=model_cfg.d_model, nhead=model_cfg.nhead,
            num_encoder_layers=model_cfg.num_encoder_layers, dim_feedforward=model_cfg.dim_feedforward,
            decoder_hidden=model_cfg.decoder_hidden, dropout=model_cfg.dropout,
            non_negative_output=model_cfg.non_negative_output, window_size=window_size,
        )
    if model_cfg.type == "attn_lstm":
        return AttnLSTMForecaster(
            input_dim=input_dim, n_targets=n_targets, horizon=horizon,
            encoder_hidden=model_cfg.encoder_hidden, decoder_hidden=model_cfg.decoder_hidden,
            dropout=model_cfg.dropout, non_negative_output=model_cfg.non_negative_output,
        )
    raise ValueError(f"unknown model.type: {model_cfg.type!r} (attn_lstm | attn_transformer_residual)")
