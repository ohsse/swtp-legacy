"""데이터 로딩부터 (train/val/test) WindowSet까지의 전체 파이프라인.

학습(train.py)과 평가(evaluate.py)가 반드시 이 한 함수를 통해서만
데이터를 준비하도록 해서, 두 경로의 전처리가 어긋나는 일
(기존 코드의 학습 dropna() vs 추론 fillna(mean) 같은)을 원천적으로
막는다. 운영 추론 코드를 붙일 때도 raw DataFrame을 얻은 뒤
FeaturePipeline.transform()을 그대로 재사용해야 한다 (infer.py 참고).
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from .config import Config
from .data import (
    FeaturePipeline,
    add_lever_change_features,
    add_time_features,
    apply_column_start_dates,
    check_feature_coverage,
    combine_max_columns,
    find_segments,
    impute_stuck_values,
    load_raw_frame,
    resample_and_flag_gaps,
    stuck_run_mask,
    time_based_split,
)
from .config import WindowConfig
from .taglist import TagInfo, combine_max, feature_vars, filter_excluded, load_taglist, target_vars
from .windows import WindowSet, make_windows


def stride_for_split(split_name: str, window_cfg: WindowConfig) -> int:
    """train은 window_cfg.stride, val/test는 window_cfg.eval_stride(없으면 horizon)를 쓴다.

    window_size를 늘리면서 train용 stride를 촘촘하게(예: 1) 잡아 데이터를
    증강하는 건 괜찮지만, 그 촘촘한 stride를 val/test에도 그대로 쓰면
    거의 겹치는 윈도우를 반복 평가하게 되어 지표가 실제보다 안정적으로/
    부풀려 보일 수 있다 — 그래서 평가용 stride를 따로 둔다."""
    if split_name == "train":
        return window_cfg.stride
    return window_cfg.eval_stride or window_cfg.horizon


@dataclasses.dataclass
class PreparedData:
    tags: list[TagInfo]
    feature_cols: list[str]
    target_cols: list[str]
    target_idx: list[int]  # feature_cols 안에서 target의 위치
    pipeline: FeaturePipeline
    windows: dict[str, WindowSet]  # "train" / "val" / "test"
    split_frames: dict[str, pd.DataFrame]  # 스케일된, split별 raw(연속) DataFrame (baseline 계산용)


def prepare_data(cfg: Config) -> PreparedData:
    # combine_max_columns(예: H3_1/H3_2 -> H3)로 합쳐질 원본 태그는 DB/CSV에
    # 실제로 존재하는 개별 태그이므로, raw 로딩까지는 병합 전(tags_raw)의
    # 전체 태그 목록을 써야 한다 — 병합 자체는 로딩된 raw DataFrame에서
    # combine_max_columns()가 수행하고, 그 다음에야 tags(따라서 feature_cols/
    # target_cols)를 병합 후 기준으로 다시 만든다.
    tags_raw = load_taglist(cfg.data.taglist_path, cfg.data.sheet, cfg.data.mode)
    tags_raw = filter_excluded(tags_raw, cfg.data.exclude_vars)

    if cfg.data.source == "csv":
        raw = load_raw_frame(
            tags_raw, cfg.data.rawdata_dir, cfg.data.raw_filename_template, cfg.data.start_date, cfg.data.end_date
        )
    elif cfg.data.source == "db":
        from .db_source import load_raw_frame_db  # pymysql/sqlalchemy는 db 경로에서만 필요

        raw = load_raw_frame_db(tags_raw, cfg.data, cfg.data.start_date, cfg.data.end_date)
    else:  # pragma: no cover - DataConfig.__post_init__에서 이미 막힘
        raise ValueError(f"unknown data.source: {cfg.data.source}")

    raw = combine_max_columns(raw, cfg.data.combine_max_columns)
    tags = combine_max(tags_raw, cfg.data.combine_max_columns)
    feature_cols = feature_vars(tags)
    target_cols = target_vars(tags)
    if cfg.data.target_exclude_vars:
        # 예측 대상에서만 빼고 입력 feature로는 남긴다(config.DataConfig.
        # target_exclude_vars 참고). 오타를 조용히 무시하면 "빼려던 target이
        # 그대로 남는" 사고가 되므로, 실제 target이 아닌 이름은 에러로 알린다.
        unknown = [v for v in cfg.data.target_exclude_vars if v not in target_cols]
        if unknown:
            raise ValueError(
                f"target_exclude_vars에 target이 아닌 변수가 있습니다: {unknown} "
                f"(현재 target: {target_cols}). exclude_vars/combine_max_columns로 이미 "
                f"빠진 이름이거나 오타인지 확인할 것."
            )
        target_cols = [c for c in target_cols if c not in set(cfg.data.target_exclude_vars)]
        if not target_cols:
            raise ValueError(f"target_exclude_vars {cfg.data.target_exclude_vars}를 적용하면 target이 하나도 안 남습니다.")
    target_idx = [feature_cols.index(c) for c in target_cols]

    raw = raw[feature_cols]
    raw = apply_column_start_dates(raw, cfg.data.column_start_dates)
    check_feature_coverage(raw)

    filled, valid_mask = resample_and_flag_gaps(
        raw, cfg.data.freq, cfg.data.ffill_limit_minutes, linear_interp_columns=cfg.data.linear_interp_columns
    )

    if cfg.data.stuck_value_min_minutes:
        # 결측(NaN)은 아니지만 센서/통신 고장으로 값이 몇 시간~몇 달씩 고정된
        # 구간도 학습에서 제외한다 (dev DB의 osd 시트 P6에서 실제 발견된 문제 —
        # deepEMS/README.md "DB 분석 기반 재설계" 절 참고). stuck_value_impute_columns에
        # 있는 컬럼은 제외 대신 값으로 대체한다 (joint 모델에서 태그 하나의
        # 장기 고정이 나머지 태그 전부를 끌어내리지 않도록) — median/linear
        # 방식 선택은 stuck_value_impute_method(data.impute_stuck_values 참고).
        raw_grid, _ = resample_and_flag_gaps(raw, cfg.data.freq, ffill_limit_minutes=0)
        if cfg.data.stuck_value_impute_columns:
            filled = impute_stuck_values(
                filled, raw_grid, cfg.data.freq, cfg.data.stuck_value_min_minutes, cfg.data.stuck_value_impute_columns,
                method=cfg.data.stuck_value_impute_method,
            )
        valid_mask = valid_mask & ~stuck_run_mask(
            raw_grid, cfg.data.freq, cfg.data.stuck_value_min_minutes,
            exclude_columns=cfg.data.stuck_value_impute_columns,
        )

    if cfg.data.time_features:
        # 센서 값과 달리 시각에서 결정적으로 계산되므로 결측이 없다 — valid_mask
        # 계산이 다 끝난 filled에 추가한다. feature_cols에만 더해지고
        # target_cols/target_idx(원래 태그들, 앞쪽에 그대로 있음)는 안 바뀐다.
        filled = add_time_features(filled, cfg.data.time_features)
        feature_cols = feature_cols + [f for f in cfg.data.time_features if f not in feature_cols]
        target_idx = [feature_cols.index(c) for c in target_cols]

    if cfg.data.lever_diff_columns:
        # time_features와 같은 자리(valid_mask 계산 이후) - diff로 생기는
        # 맨 앞 NaN은 windowing이 window_size로 흡수한다(add_lever_change_features
        # docstring 참고). feature_cols에만 더해지고 target_cols는 안 바뀐다.
        filled = add_lever_change_features(filled, cfg.data.lever_diff_columns, cfg.data.lever_diff_steps)
        new_cols = [
            f"{c}_diff{s}" for c in cfg.data.lever_diff_columns for s in cfg.data.lever_diff_steps
        ]
        feature_cols = feature_cols + [c for c in new_cols if c not in feature_cols]
        target_idx = [feature_cols.index(c) for c in target_cols]

    ranges = time_based_split(
        filled.index, cfg.split.train_ratio, cfg.split.val_ratio, cfg.split.test_ratio, cfg.split.purge_minutes
    )

    freq_delta = pd.Timedelta(cfg.data.freq)
    min_segment_rows = int(pd.Timedelta(minutes=cfg.window.min_segment_minutes) / freq_delta)
    # 적어도 윈도우 1개는 만들 수 있는 길이보다 짧으면 의미가 없으므로 하한을 강제한다.
    min_rows = max(1, min_segment_rows, cfg.window.window_size + cfg.window.horizon)

    split_slices: dict[str, tuple[pd.Timestamp, pd.Timestamp]] = {
        "train": ranges.train,
        "val": ranges.val,
        "test": ranges.test,
    }

    # 1) train 구간 통계로만 이상치 clip 기준 + 스케일러를 fit한다.
    train_raw = filled.loc[ranges.train[0] : ranges.train[1]]
    train_valid_mask = valid_mask.loc[ranges.train[0] : ranges.train[1]]
    fp = FeaturePipeline(
        feature_cols=feature_cols,
        outlier_enabled=cfg.outlier.enabled,
        lower_q=cfg.outlier.lower_quantile,
        upper_q=cfg.outlier.upper_quantile,
        column_overrides=cfg.outlier.column_overrides,
        scaler_type=cfg.outlier.scaler_type,
        column_scaler_overrides=cfg.outlier.column_scaler_overrides,
    ).fit(train_raw.loc[train_valid_mask])

    windows: dict[str, WindowSet] = {}
    split_frames: dict[str, pd.DataFrame] = {}
    for split_name, (s, e) in split_slices.items():
        split_df = filled.loc[s:e]
        split_valid = valid_mask.loc[s:e]
        clip = split_name in cfg.outlier.apply_to_splits
        scaled = fp.transform(split_df, clip=clip)
        segments = find_segments(split_valid, min_rows=min_rows)
        ws = make_windows(
            scaled,
            segments,
            feature_cols,
            target_cols,
            cfg.window.window_size,
            cfg.window.horizon,
            stride_for_split(split_name, cfg.window),
        )
        windows[split_name] = ws
        split_frames[split_name] = scaled.loc[split_valid]

    return PreparedData(
        tags=tags,
        feature_cols=feature_cols,
        target_cols=target_cols,
        target_idx=target_idx,
        pipeline=fp,
        windows=windows,
        split_frames=split_frames,
    )
