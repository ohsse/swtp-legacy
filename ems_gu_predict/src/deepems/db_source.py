"""운영 DB(TB_RAWDATA)에서 직접 학습용 raw 데이터를 가져오는 경로.

기존 main_guns_v1.py의 get_db_df()/open_db()와 같은 테이블·컬럼 구조
(TS, TAGNAME, VALUE)를 그대로 대량 조회용으로 확장한 버전이다.
CSV 경로(data.load_raw_frame)와 정확히 같은 형태
(index=Datetime, columns=변수명)의 DataFrame을 반환하므로,
pipeline.prepare_data는 source 설정만 보고 둘 중 하나를 부르면 된다.

비밀번호는 이 모듈에 절대 하드코딩하지 않는다 — Config.db_connection_params()가
기존 connections.json을 재사용하거나 환경변수로 치환된 값을 준다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

from .config import DataConfig
from .db_ssl import ssl_connect_args
from .taglist import TagInfo


def build_engine(conn_params: dict) -> Engine:
    url = (
        f"mysql+pymysql://{conn_params['user']}:{conn_params['password']}"
        f"@{conn_params['host']}:{conn_params.get('port', 3306)}/{conn_params['db']}"
    )
    # ssl_ca 등이 접속정보에 있으면 TLS로 연결한다(db_ssl.py 참고) — 없으면
    # 기존과 동일하게 평문 연결(하위호환).
    return create_engine(url, pool_pre_ping=True, connect_args=ssl_connect_args(conn_params))


def month_start(ts: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(year=ts.year, month=ts.month, day=1)


def month_range(start: pd.Timestamp, end: pd.Timestamp) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """[start, end)를 달력 월 단위 [그 달 1일, 다음 달 1일) 구간 목록으로 쪼갠다.

    캐시 파일 하나 = 달 하나가 되도록 하기 위한 경계다. 요청 범위가 어느 달의
    중간에서 시작/끝나도, 그 달 전체를 캐시 단위로 잡는다 — fetch_tag_series가
    최종적으로 실제 요청 구간으로 다시 잘라서 돌려준다.
    """
    if end <= start:
        return []
    months = []
    cur = month_start(start)
    while cur < end:
        nxt = cur + pd.DateOffset(months=1)
        months.append((cur, nxt))
        cur = nxt
    return months


def _cache_path(cache_dir: str, tag_name: str, m_start: pd.Timestamp) -> Path:
    return Path(cache_dir) / tag_name / f"{m_start:%Y-%m}.pkl.gz"


def _read_cache(path: Path) -> pd.Series | None:
    if not path.exists():
        return None
    try:
        return pd.read_pickle(path, compression="gzip")
    except Exception as e:  # 캐시 파일이 손상됐으면 무시하고 DB에서 다시 받는다
        print(f"    (캐시 파일 {path} 손상됨, 무시하고 다시 조회: {e})")
        return None


def _write_cache(path: Path, series: pd.Series) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    series.to_pickle(path, compression="gzip")


def _fetch_month_from_db(engine: Engine, query, tag_name: str, m_start: pd.Timestamp, m_end: pd.Timestamp) -> pd.Series:
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"tag": tag_name, "start": m_start, "end": m_end})
    df["dt"] = pd.to_datetime(df["dt"])
    # TB_RAWDATA.VALUE는 varchar 컬럼이다(실제 dev DB로 확인함) — 그대로 두면
    # object dtype으로 남아 뒤의 resample().mean() 등 수치 연산이 전부 깨진다.
    # 숫자로 못 바꾸는 값(빈 문자열, 통신 오류 코드 등)은 결측으로 처리한다 —
    # data.resample_and_flag_gaps가 짧은 결측은 채우고, 긴 결측은 구간을 끊는다.
    df["val"] = pd.to_numeric(df["val"], errors="coerce")
    df = df.dropna(subset=["dt"]).drop_duplicates(subset=["dt"]).set_index("dt").sort_index()
    return df["val"]


def fetch_tag_series(
    engine: Engine,
    tag_name: str,
    data_cfg: DataConfig,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.Series:
    """[start_date, end_date) 구간의 태그 값을 달력 월 단위로 나눠서 가져온다.

    data_cfg.cache_dir가 설정돼 있으면, 이미 끝난(지난) 달은 로컬 gzip pickle
    캐시(Data/<태그명>/<YYYY-MM>.pkl.gz)를 먼저 확인하고, 없으면 DB에서 받아와
    캐시에 남긴다. 아직 진행 중인 달(현재 시각이 그 달 안에 있는 경우)은 캐시를
    쓰지 않고 항상 DB에서 새로 가져온다 — 그 달의 나머지 데이터가 계속
    쌓이는 중이라 캐시하면 오래된 부분 데이터가 영구히 남기 때문이다.
    """
    query = text(
        f"""
        SELECT {data_cfg.db_ts_col} AS dt, {data_cfg.db_value_col} AS val
        FROM {data_cfg.db_table}
        WHERE {data_cfg.db_tagname_col} = :tag
          AND {data_cfg.db_ts_col} >= :start
          AND {data_cfg.db_ts_col} < :end
        ORDER BY {data_cfg.db_ts_col} ASC
        """
    )

    now = pd.Timestamp.now()
    parts: list[pd.Series] = []
    for m_start, m_end in month_range(start_date, end_date):
        is_past_month = m_end <= now
        cache_path = _cache_path(data_cfg.cache_dir, tag_name, m_start) if data_cfg.cache_dir else None

        cached = _read_cache(cache_path) if (cache_path and is_past_month) else None
        if cached is not None:
            parts.append(cached)
            continue

        month_series = _fetch_month_from_db(engine, query, tag_name, m_start, m_end)
        if cache_path and is_past_month:
            _write_cache(cache_path, month_series)
        parts.append(month_series)

    full = pd.concat(parts) if parts else pd.Series(dtype=float)
    # 캐시는 달 전체를 담고 있으므로, 실제 요청한 [start_date, end_date) 구간으로 다시 자른다.
    full = full.loc[(full.index >= start_date) & (full.index < end_date)]
    return full.sort_index()


def fetch_tags_batch(
    engine: Engine, tag_names: list[str], data_cfg: DataConfig, start_date: pd.Timestamp, end_date: pd.Timestamp,
) -> pd.DataFrame:
    """여러 태그를 한 번의 SQL 쿼리(`TAGNAME IN (...)`)로 한꺼번에 가져온다
    (2026-09-14, 사용자 요청 - "가져올 태그들을 미리 정렬한 후 한꺼번에
    load"). `fetch_tag_series`가 태그 하나당 쿼리 하나씩 순차 조회하는 것과
    달리 DB 왕복이 1번으로 줄어든다 - 짧은 구간을 매 사이클 반복 조회하는
    운영 경로(`preprocess.fetch_window`)에서 체감 속도 차이가 크다.

    캐시(`cache_dir`)는 안 쓴다 - 운영 경로는 애초에 `preprocess.
    fetch_window()`가 `cache_dir`을 강제로 `None`으로 덮어써서 캐시를
    안 쓰기로 이미 정해져 있다(2026-09-14, "왜 오프라인으로 저장되게
    했지" 항목 참고). 월 단위 캐시가 필요한 학습 경로(수 년치 반복 조회)는
    여전히 `fetch_tag_series`(태그별 캐시 파일)를 쓴다 - `load_raw_frame_db`
    참고.

    태그명을 정렬해서 쿼리하면(`ORDER BY`가 아니라 `IN` 절 안의 순서) 실행
    계획 자체는 안 달라지지만, 결과 파싱/디버깅 시 태그 순서가 항상
    일정해서 재현 가능하다는 부수 효과가 있다.
    """
    sorted_tags = sorted(set(tag_names))
    if not sorted_tags:
        return pd.DataFrame()

    query = text(
        f"""
        SELECT {data_cfg.db_ts_col} AS dt, {data_cfg.db_tagname_col} AS tag, {data_cfg.db_value_col} AS val
        FROM {data_cfg.db_table}
        WHERE {data_cfg.db_tagname_col} IN :tags
          AND {data_cfg.db_ts_col} >= :start
          AND {data_cfg.db_ts_col} < :end
        ORDER BY {data_cfg.db_ts_col} ASC
        """
    ).bindparams(bindparam("tags", expanding=True))

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"tags": sorted_tags, "start": start_date, "end": end_date})
    df["dt"] = pd.to_datetime(df["dt"])
    # TB_RAWDATA.VALUE는 varchar 컬럼이다(fetch_tag_series와 같은 이유) -
    # 숫자로 못 바꾸는 값은 결측 처리.
    df["val"] = pd.to_numeric(df["val"], errors="coerce")
    df = df.dropna(subset=["dt"]).drop_duplicates(subset=["dt", "tag"])
    pivot = df.pivot(index="dt", columns="tag", values="val")
    # 조회 기간에 값이 하나도 없는 태그는 pivot 결과에 컬럼 자체가 안
    # 생기므로, reindex로 요청한 태그 전부를(전부 NaN이라도) 컬럼으로 채워
    # 넣는다 - 호출부(load_raw_frame_db)가 태그 누락을 몰라도 되게.
    pivot = pivot.reindex(columns=sorted_tags)
    return pivot.sort_index()


def load_raw_frame_db(
    tags: list[TagInfo],
    data_cfg: DataConfig,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    """CSV 경로의 load_raw_frame()과 동일한 형태(index=Datetime, columns=변수명)를 DB에서 만든다.

    `data_cfg.cache_dir`이 설정돼 있으면(학습/EDA 경로) 태그별 월 단위
    캐시가 있는 `fetch_tag_series`로 태그마다 순차 조회한다. 캐시가 없으면
    (`cache_dir=None` - 운영 경로, `preprocess.fetch_window`가 항상 이
    상태로 강제함) `fetch_tags_batch`로 태그 전체를 한 번에 조회한다 -
    짧은 구간만 반복 조회하는 운영 경로에서는 캐시보다 쿼리 왕복 횟수를
    줄이는 게 더 효과적이다.
    """
    if not start_date:
        raise ValueError("data.source='db'일 때는 data.start_date를 반드시 지정해야 합니다 (전체 테이블 스캔 방지).")
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) if end_date else pd.Timestamp.now()

    engine = build_engine(data_cfg.db_connection_params())
    try:
        if data_cfg.cache_dir:
            series_list = []
            for tag in tags:
                print(f"  [db] {tag.var_name} ({tag.tag_name}) 조회 중 ...")
                s = fetch_tag_series(engine, tag.tag_name, data_cfg, start_ts, end_ts)
                s.name = tag.var_name
                series_list.append(s)
            df = pd.concat(series_list, axis=1)
        else:
            tag_name_to_var = {t.tag_name: t.var_name for t in tags}
            print(f"  [db] {len(tags)}개 태그 한꺼번에 조회 중 (정렬됨) ...")
            raw = fetch_tags_batch(engine, list(tag_name_to_var), data_cfg, start_ts, end_ts)
            df = raw.rename(columns=tag_name_to_var)
            df = df.reindex(columns=[t.var_name for t in tags])
    finally:
        engine.dispose()

    return df.sort_index()
