"""데이터 준비 단계 — DB에서 필요한 구간만 받아, 학습 때와 동일한 리샘플/
짧은 결측 보정(`resample_and_flag_gaps`)을 적용한 DataFrame을 만든다.

이 저장소는 패키지로 설치돼 있지 않으므로(`pyproject.toml` 없음), `src/`를
`sys.path`에 올려서 `deepems`를 임포트한다 — `tests/`와 같은 관례.

`analyze.load_full_raw()`는 전체 이력(수 년치)을 통째로 읽어서 학습/EDA용으로는
맞지만, 실시간/백테스트에서 매 사이클(또는 매 origin)마다 그렇게 하면 DB
왕복이 너무 크다. 여기서는 `db_source.load_raw_frame_db()`(태그 목록 + 기간을
주면 그대로 받아오는 기존 함수)를 재사용하되, 필요한 태그만(Stage1 feature_cols
+ 호출부가 추가로 요구하는 컬럼) 추려서 조회량을 줄인다.

**오프라인(로컬) 캐시는 강제로 끈다(2026-09-14)**: `DataConfig.cache_dir`의
기본값이 `"./Data"`라서, 아무 config나 그대로 쓰면 `db_source.
load_raw_frame_db()`가 지난 달 데이터를 태그별로 `{cache_dir}/{태그명}/
{YYYY-MM}.pkl.gz`에 자동으로 로컬 저장한다 — 이건 `analyze.load_full_raw()`
가 수 년치 이력을 반복 조회하는 학습/EDA 용도로 만든 것이지, 이 모듈(실시간
사이클/백테스트, 매번 최근 며칠~몇 주 구간만 조회)에는 맞지 않는다. 운영
서버에서 `schedule.py`를 계속 돌리면 새 달이 지날 때마다 로컬 디스크에
캐시가 정리 없이 계속 쌓이는 부작용이 있었다(사용자 지적, 실측이 아니라
설계 검토로 발견). `fetch_window()`가 조회 직전에 `cfg.data.cache_dir`을
`None`으로 강제해서, 이 모듈을 거치는 모든 조회(dev/dev-server/prod
전부)는 caller의 config 설정과 무관하게 항상 로컬 캐시 없이 DB에서 직접
받는다 — 원본 `cfg` 객체는 손대지 않고 복사본만 바꾼다(dataclasses.replace).
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from deepems.config import Config  # noqa: E402
from deepems.data import add_lever_change_features, add_time_features, combine_max_columns, resample_and_flag_gaps  # noqa: E402
from deepems.db_source import load_raw_frame_db  # noqa: E402
from deepems.taglist import combine_max, feature_vars, filter_excluded, load_taglist  # noqa: E402


def tags_to_fetch(cfg: Config, extra_cols: list[str]):
    """Stage1 feature_cols + extra_cols(레버/목표 컬럼 등 feature_cols에 없을 수
    있는 컬럼)를 합친 뒤, `combine_max_columns`로 묶이는 이름(예: H7)이 필요하면
    그 원본 태그들(H7_1/H7_2)을 조회 대상에 넣는다. 반환값은 `load_taglist`가
    돌려주는 원본(병합 전) `TagInfo` 목록의 부분집합이다.
    """
    tags_raw = load_taglist(cfg.data.taglist_path, cfg.data.sheet, cfg.data.mode)
    tags_raw = filter_excluded(tags_raw, cfg.data.exclude_vars)
    tags_combined = combine_max(tags_raw, cfg.data.combine_max_columns)
    needed = set(feature_vars(tags_combined)) | set(extra_cols)

    combine_groups = cfg.data.combine_max_columns
    raw_needed_vars: set[str] = set()
    for v in needed:
        raw_needed_vars.update(combine_groups.get(v, [v]))
    return [t for t in tags_raw if t.var_name in raw_needed_vars]


def fetch_window(cfg: Config, extra_cols: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """[start, end) 구간만 DB에서 받아 filled DataFrame을 돌려준다.

    실시간 사이클(`analysis.run_cycle`)과 백테스트(`schedule.py --mode dev`)
    둘 다 이 함수 하나로 처리한다 — 차이는 그냥 어떤 [start, end)를 주느냐뿐이다.
    """
    tags = tags_to_fetch(cfg, extra_cols)
    if not tags:
        raise ValueError(f"조회할 태그가 없습니다(extra_cols={extra_cols}가 taglist에 없을 수 있음).")

    # cache_dir은 캐지 않는다(모듈 docstring의 "오프라인(로컬) 캐시는 강제로
    # 끈다" 참고) - 원본 cfg.data는 그대로 두고 복사본만 cache_dir=None으로 바꿔 쓴다.
    data_cfg_no_cache = dataclasses.replace(cfg.data, cache_dir=None)
    raw = load_raw_frame_db(tags, data_cfg_no_cache, start.isoformat(), end.isoformat())
    raw = combine_max_columns(raw, cfg.data.combine_max_columns)

    filled, _valid_mask = resample_and_flag_gaps(
        raw, cfg.data.freq, cfg.data.ffill_limit_minutes, linear_interp_columns=cfg.data.linear_interp_columns
    )
    if cfg.data.time_features:
        # Stage1 모델이 hour_sin/hour_cos 등을 feature_cols에 포함해 학습됐다면
        # (analyze.load_full_raw와 동일하게) 여기서도 넣어줘야 한다 — 안 넣으면
        # infer.predict_next_horizon이 art.feature_cols로 이 DataFrame을 인덱싱할
        # 때 "not in index"로 실패한다(2026-09-11 dev 백테스트 실측으로 발견 —
        # 169개 origin 전부가 이 이유로 건너뛰어졌었다).
        filled = add_time_features(filled, cfg.data.time_features)
    if cfg.data.lever_diff_columns:
        # pipeline.prepare_data()의 학습 경로와 같은 자리에서 같은 처리를
        # 한다 - 안 넣으면 lever_diff feature로 학습된 Stage1 모델이
        # 여기서도 "not in index"로 실패한다(위 time_features와 같은
        # 이유, 2026-09-14 dev 백테스트 실측으로 발견).
        filled = add_lever_change_features(filled, cfg.data.lever_diff_columns, cfg.data.lever_diff_steps)
    return filled


def fetch_recent_window(cfg: Config, extra_cols: list[str], lookback_days: float, end: pd.Timestamp) -> pd.DataFrame:
    """실시간(운영)용 — `end` 시점 기준 최근 `lookback_days`일만 받는다."""
    start = end - pd.Timedelta(days=lookback_days)
    return fetch_window(cfg, extra_cols, start, end)


# 조회 분할 시 짧은 구간에 더 얹는 여유(분). 필요한 최소 길이는
# feature_lookback_minutes()의 공식이 정확히 주지만, 경계 한두 칸에서 결과가
# 갈리는 걸 막는 안전폭이다(2026-09-28 실측: 최소 400분·여유 포함 460분 모두
# 22일 조회와 20/20 origin 완전 일치).
FEATURE_LOOKBACK_MARGIN_MINUTES = 60.0


def feature_lookback_minutes(cfg: Config, window_size: int) -> float:
    """Stage1 입력 윈도우를 22일 조회 때와 **비트 단위로 같게** 만들기 위해
    필요한 최소 조회 길이(분) + 여유.

    `fetch_window()`의 처리 중 조회 시작점에 영향받는 것은 셋뿐이다:
    - 입력 윈도우 자체 `window_size` 스텝
    - `add_lever_change_features`의 `diff(max(lever_diff_steps))` - 앞쪽에
      과거가 없으면 0으로 채우므로(data.py) 조회가 짧으면 값이 달라진다
    - `resample_and_flag_gaps`의 ffill/선형보간(`ffill_limit_minutes`) -
      그만큼 앞의 실측을 끌어다 쓴다
    목표범위(21일)는 이 조회가 아니라 `fetch_level_history()`가 따로 받는다.

    2026-09-28 군산 개발서버 실측(1분 모델, window 360 / diff 30 / ffill 10):
    360분만 받으면 20개 origin 전부 레버 변화량 입력이 달라졌고(Q_GunS_diff30
    최대 386 차이), 400분 이상이면 입력·유효판정·origin·목표범위·잔차 feature가
    전부 일치했다.
    """
    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0
    diff_steps = max(cfg.data.lever_diff_steps) if cfg.data.lever_diff_columns and cfg.data.lever_diff_steps else 0
    return (window_size + diff_steps) * freq_minutes + cfg.data.ffill_limit_minutes + FEATURE_LOOKBACK_MARGIN_MINUTES


def fetch_level_history(cfg: Config, level_col: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """목표범위(`recommend.compute_target_band`) 계산 전용 — `level_col`(H7)
    하나만 [start, end) 구간으로 받아 `fetch_window()`와 같은 처리(combine_max
    → 리샘플 → ffill/보간)를 거친 시계열을 돌려준다.

    나눠 받는 이유: 사이클에서 21일 이력이 필요한 건 목표범위 하나뿐인데,
    예전에는 이것 때문에 모든 태그(약 29개)를 22일치씩 매 사이클 받았다. 1분
    주기에서는 그게 매분 약 85만 행이다. 이 함수는 H7 원본 태그(H7_1/H7_2)만
    받으므로 조회량이 태그 수만큼 줄어든다.

    처리는 컬럼별로 독립이라(resample 평균·ffill·보간 모두 컬럼 단위) 다른
    태그와 함께 받든 따로 받든 같은 값이 나온다 — `feature_lookback_minutes()`
    docstring의 실측 참고.
    """
    wanted = set(cfg.data.combine_max_columns.get(level_col, [level_col]))
    tags_raw = filter_excluded(load_taglist(cfg.data.taglist_path, cfg.data.sheet, cfg.data.mode), cfg.data.exclude_vars)
    tags = [t for t in tags_raw if t.var_name in wanted]
    if not tags:
        raise ValueError(f"목표범위용 {level_col} 태그를 taglist에서 찾지 못했습니다.")
    data_cfg_no_cache = dataclasses.replace(cfg.data, cache_dir=None)
    raw = load_raw_frame_db(tags, data_cfg_no_cache, start.isoformat(), end.isoformat())
    raw = combine_max_columns(raw, cfg.data.combine_max_columns)
    filled, _ = resample_and_flag_gaps(
        raw, cfg.data.freq, cfg.data.ffill_limit_minutes, linear_interp_columns=cfg.data.linear_interp_columns
    )
    return filled[level_col]
