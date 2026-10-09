"""예측 모델 후보(Ridge/Lasso/XGBoost/LightGBM 등)를 위한 공용 인터페이스와
저장/불러오기 — attn-Transformer/attn-LSTM(신경망, `src/deepems/model.py`)과
달리 sklearn 스타일 회귀기라서, 시퀀스 윈도우([N, window_size, n_features])를
평평하게 펴서([N, window_size*n_features]) 넣고 horizon*n_targets개 값을
예측한다.

이 저장소는 패키지로 설치돼 있지 않으므로(`pyproject.toml` 없음), `src/`를
`sys.path`에 올려서 `deepems`를 임포트한다 — `tests/`와 같은 관례.

**GPU(2026-09-11 추가)**: XGBoost는 `device="cuda"`로 실제 GPU 학습을 쓴다
(이 환경에 RTX 5070 Ti가 있음, `torch.cuda.is_available()`로 감지). LightGBM은
pip으로 설치되는 일반 wheel이 보통 GPU(OpenCL/CUDA) 없이 빌드돼 있어서
`device="gpu"`를 그냥 켜면 fit 시점에 에러가 난다 — 그래서 GPU로 시도해보고
실패하면 CPU로 자동 재시도하며, 실제로 어느 쪽으로 돌았는지를 반환값에
정직하게 남긴다(`fit_candidate`가 돌려주는 `(model, used_gpu)` 참고 —
"GPU를 켰다고 주장했지만 사실 CPU였다"를 감추지 않기 위함). Ridge/Lasso는
sklearn 구현 자체가 CPU 전용이라 GPU를 쓸 방법이 없다 — 이건 이 저장소의
문제가 아니라 sklearn의 근본적인 한계다.
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# sklearn이 다중출력을 자체 지원하는 모델 — MultiOutputRegressor로 감싸면
# 출력(horizon*n_targets, 보통 100개 이상) 개수만큼 같은 크기의 선형계를
# 하나씩 따로 풀어서 극도로 느려진다(실측: gu_db_noq8_h6 config, 6048
# feature, 144 출력에서 20분 넘게 걸리다 중단 — Ridge closed-form 해가
# feature 수의 세제곱에 비례하는데 그걸 144번 반복했기 때문). 네이티브
# 다중출력은 행렬 분해를 한 번만 해서 압도적으로 빠르다. dlinear/informer는
# sklearn이 아니라 PyTorch 신경망이지만 fit() 한 번으로 모든 target/horizon을
# 동시에 출력하므로 같은 "한 번에 다중출력" 경로를 그대로 쓴다.
NATIVE_MULTIOUTPUT_MODELS = {"ridge", "lasso", "dlinear", "informer"}


def gpu_available() -> bool:
    """이 환경에 CUDA GPU가 있는지 — torch가 이미 이 환경에서 검증된 CUDA
    감지 수단이라 재사용한다(src/deepems/train.py의 resolve_device와 같은
    방식)."""
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _make_ridge(**kwargs):
    from sklearn.linear_model import Ridge

    return Ridge(alpha=kwargs.get("alpha", 1.0), random_state=42)


def _make_lasso(**kwargs):
    from sklearn.linear_model import Lasso

    return Lasso(alpha=kwargs.get("alpha", 0.01), random_state=42, max_iter=5000)


def _make_xgboost(use_gpu: bool, **kwargs):
    from xgboost import XGBRegressor

    return XGBRegressor(
        n_estimators=kwargs.get("n_estimators", 200), max_depth=kwargs.get("max_depth", 4),
        learning_rate=kwargs.get("learning_rate", 0.05), subsample=kwargs.get("subsample", 0.8),
        colsample_bytree=kwargs.get("colsample_bytree", 0.8), random_state=42,
        tree_method="hist", device=("cuda" if use_gpu else "cpu"),
    )


def _make_lightgbm(use_gpu: bool, **kwargs):
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        n_estimators=kwargs.get("n_estimators", 200), max_depth=kwargs.get("max_depth", 4),
        learning_rate=kwargs.get("learning_rate", 0.05), subsample=kwargs.get("subsample", 0.8),
        colsample_bytree=kwargs.get("colsample_bytree", 0.8), n_jobs=(1 if use_gpu else -1),
        random_state=42, verbose=-1, device=("gpu" if use_gpu else "cpu"),
    )


_SEQ_MODEL_REQUIRED_KWARGS = ("window_size", "n_features", "feature_target_idx", "horizon", "n_targets")


def _make_dlinear(**kwargs):
    from dlinear_model import DLinearRegressor

    missing = [k for k in _SEQ_MODEL_REQUIRED_KWARGS if k not in kwargs]
    if missing:
        raise ValueError(f"dlinear에는 {missing}가 model_kwargs로 필요합니다(train_candidates.train_one 참고).")
    return DLinearRegressor(
        window_size=kwargs["window_size"], n_features=kwargs["n_features"],
        feature_target_idx=kwargs["feature_target_idx"], horizon=kwargs["horizon"],
        n_targets=kwargs["n_targets"], kernel_size=kwargs.get("kernel_size", 25),
        lr=kwargs.get("lr", 1e-3), epochs=kwargs.get("epochs", 100), patience=kwargs.get("patience", 10),
    )


def _make_informer(**kwargs):
    from informer_model import InformerRegressor

    missing = [k for k in _SEQ_MODEL_REQUIRED_KWARGS if k not in kwargs]
    if missing:
        raise ValueError(f"informer에는 {missing}가 model_kwargs로 필요합니다(train_candidates.train_one 참고).")
    return InformerRegressor(
        window_size=kwargs["window_size"], n_features=kwargs["n_features"],
        feature_target_idx=kwargs["feature_target_idx"], horizon=kwargs["horizon"],
        n_targets=kwargs["n_targets"], label_len=kwargs.get("label_len"),
        d_model=kwargs.get("d_model", 64), n_heads=kwargs.get("n_heads", 4),
        e_layers=kwargs.get("e_layers", 2), d_layers=kwargs.get("d_layers", 1),
        lr=kwargs.get("lr", 1e-3), epochs=kwargs.get("epochs", 100), patience=kwargs.get("patience", 10),
    )


# 새 후보를 추가하려면 여기 한 줄만 더하면 된다 — train_candidates.py의
# --model 선택지, 저장 폴더 이름(scripts/models/<key>_*)에 그대로 쓰인다.
MODEL_FACTORIES = {
    "ridge": _make_ridge,
    "lasso": _make_lasso,
    "xgboost": _make_xgboost,
    "lightgbm": _make_lightgbm,
    "dlinear": _make_dlinear,
    "informer": _make_informer,
}
# GPU device 인자를 받는(=_make_xgboost/_make_lightgbm처럼 use_gpu 위치인자가
# 있는) 팩토리만 표시 — ridge/lasso는 GPU 자체가 없어서 안 받는다. dlinear/
# informer는 NATIVE_MULTIOUTPUT_MODELS 경로(자체 .fit에서 GPU 여부를 직접
# 결정)라 여기엔 안 넣는다 - fit_candidate가 GPU device 인자를 주입하는
# 대상이 아니라는 뜻.
GPU_CAPABLE_MODELS = {"xgboost", "lightgbm"}


def flatten_windows(X: np.ndarray, y: np.ndarray, target_idx: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """`windows.WindowSet`의 X([N, window_size, n_features])/y([N, horizon,
    n_targets_all])를 sklearn 회귀기가 받는 2D 형태로 편다.

    X는 그냥 평평하게(window_size*n_features), y는 `target_idx`로 필요한
    target만 골라(예: O7/Q7 2개) horizon*len(target_idx)로 편다 — 신경망은
    12개 target을 한 번에 joint로 학습하지만, 이 후보 모델들은 그렇게
    많은 출력을 다루면 너무 느려지므로 O7/Q7처럼 필요한 것만 추린다.

    되돌리려면(예측 후 실제 형태로 복원) `unflatten_predictions()`을 쓴다.
    """
    n = X.shape[0]
    x_flat = X.reshape(n, -1)
    y_flat = y[:, :, target_idx].reshape(n, -1)
    return x_flat, y_flat


def unflatten_predictions(y_flat: np.ndarray, horizon: int, n_targets: int) -> np.ndarray:
    """`flatten_windows`가 편 것과 반대 방향 — 예측 결과를 [N, horizon, n_targets]로 복원."""
    n = y_flat.shape[0]
    return y_flat.reshape(n, horizon, n_targets)


def fit_candidate(model_type: str, x_train: np.ndarray, y_train: np.ndarray, use_gpu: bool | None = None, **model_kwargs):
    """`model_type`(MODEL_FACTORIES의 키)에 맞는 모델을 만들어
    `x_train`([N, window_size*n_features]) -> `y_train`([N, horizon*n_targets])
    를 학습한다.

    - `ridge`/`lasso`: sklearn 네이티브 다중출력으로 한 번에 학습(빠름,
      GPU 없음 — sklearn 자체가 CPU 전용).
    - `xgboost`/`lightgbm`: `MultiOutputRegressor`로 감싸 출력별로 개별
      트리 앙상블을 학습한다(두 라이브러리 다 진짜 다중출력 회귀를
      지원하지 않음). `use_gpu`(기본 None=자동 감지, `gpu_available()`)가
      True면 GPU로 시도하고, LightGBM은 GPU 미지원 빌드일 수 있어 실패하면
      CPU로 자동 재시도한다.

    반환값은 `(model, used_gpu: bool)` — 실제로 GPU를 썼는지 호출부가
    확인할 수 있게(로그/모델 설명에 정직하게 남기기 위함, 모듈 docstring
    참고).
    """
    if model_type not in MODEL_FACTORIES:
        raise ValueError(f"model_type은 {sorted(MODEL_FACTORIES)} 중 하나여야 합니다: {model_type!r}")

    if model_type in NATIVE_MULTIOUTPUT_MODELS:
        model = MODEL_FACTORIES[model_type](**model_kwargs)
        model.fit(x_train, y_train)
        # ridge/lasso는 sklearn이라 GPU 자체가 없어 항상 False. dlinear는
        # PyTorch라 실제로 GPU를 썼으면 fit()이 used_gpu_ 속성을 남긴다 -
        # 없으면(=ridge/lasso) False로 정직하게 처리.
        return model, bool(getattr(model, "used_gpu_", False))

    want_gpu = gpu_available() if use_gpu is None else use_gpu
    from sklearn.multioutput import MultiOutputRegressor

    if model_type == "lightgbm" and want_gpu:
        # LightGBM은 GPU 지원 여부가 빌드에 달려있어 미리 확실히 알 방법이
        # 마땅치 않다 — 작게 한 번 시도해보고 실패하면(대부분 pip 기본
        # wheel이 이 경우) CPU로 바로 넘어간다.
        try:
            probe = MODEL_FACTORIES[model_type](use_gpu=True, **model_kwargs)
            probe.fit(x_train[:8], y_train[:8])
        except Exception:
            want_gpu = False

    base = MODEL_FACTORIES[model_type](use_gpu=want_gpu, **model_kwargs)
    # GPU 사용 시 여러 프로세스가 같은 GPU 컨텍스트를 동시에 두고 경합하는 걸
    # 피하려고 순차 실행(n_jobs=1), CPU면 코어 수만큼 병렬화.
    model = MultiOutputRegressor(base, n_jobs=(1 if want_gpu else -1))
    model.fit(x_train, y_train)
    return model, want_gpu


@dataclasses.dataclass
class CandidateModelMeta:
    """`save_candidate_model`이 model_card.md/meta.json에 같이 남기는 설명 —
    "학습완료된 모델은 설명과 함께 저장"이라는 요구사항에 대응한다. 나중에
    이 폴더만 보고도(코드를 다시 안 읽어도) 무슨 모델인지, 뭘로 학습했는지,
    성능이 어땠는지 알 수 있어야 한다는 게 목표다."""

    model_type: str
    cfg_path: str
    target_cols: list[str]
    feature_cols: list[str]
    window_size: int
    horizon: int
    freq: str
    n_train_windows: int
    n_test_windows: int
    trained_at: str
    model_kwargs: dict
    test_metrics_summary: list[dict]  # metrics.summarize_by_target(...).to_dict("records")
    used_gpu: bool = False
    note: str = ""


def save_candidate_model(model, pipeline, meta: CandidateModelMeta, out_dir: str) -> Path:
    """`out_dir`(예: scripts/models/ridge_gu_db_noq8_h6)에 model.joblib(학습된
    모델), pipeline.joblib(스케일 역변환에 필요한 FeaturePipeline),
    meta.json(구조화된 설명), MODEL_CARD.md(사람이 바로 읽는 설명) 네 파일을
    만든다. 폴더가 없으면 만든다."""
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, path / "model.joblib")
    joblib.dump(pipeline, path / "pipeline.joblib")
    (path / "meta.json").write_text(json.dumps(dataclasses.asdict(meta), ensure_ascii=False, indent=2), encoding="utf-8")
    (path / "MODEL_CARD.md").write_text(_render_model_card(meta), encoding="utf-8")
    return path


def load_candidate_model(model_dir: str):
    """`save_candidate_model`이 만든 폴더에서 (model, pipeline, meta)를 그대로 불러온다."""
    path = Path(model_dir)
    model = joblib.load(path / "model.joblib")
    pipeline = joblib.load(path / "pipeline.joblib")
    meta_dict = json.loads((path / "meta.json").read_text(encoding="utf-8"))
    meta = CandidateModelMeta(**meta_dict)
    return model, pipeline, meta


def _render_model_card(meta: CandidateModelMeta) -> str:
    lines = [
        f"# {meta.model_type} 예측 모델 후보",
        "",
        f"- 학습 config: `{meta.cfg_path}`",
        f"- target: {', '.join(meta.target_cols)}",
        f"- feature 수: {len(meta.feature_cols)}, window_size: {meta.window_size}, horizon: {meta.horizon} ({meta.freq})",
        f"- 학습 윈도우 수: {meta.n_train_windows}, 테스트 윈도우 수: {meta.n_test_windows}",
        f"- 학습 시각: {meta.trained_at}",
        f"- GPU 사용: {'예' if meta.used_gpu else '아니오'}",
        f"- 하이퍼파라미터: `{meta.model_kwargs}`",
    ]
    if meta.note:
        lines.append(f"- 비고: {meta.note}")
    lines.append("")
    lines.append("## 테스트 성능 (target별, horizon 전체 평균)")
    lines.append("")
    if meta.test_metrics_summary:
        cols = [c for c in meta.test_metrics_summary[0].keys()]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * len(cols))
        for row in meta.test_metrics_summary:
            lines.append("| " + " | ".join(f"{row[c]:.4f}" if isinstance(row[c], float) else str(row[c]) for c in cols) + " |")
    else:
        lines.append("(평가 결과 없음)")
    return "\n".join(lines) + "\n"
