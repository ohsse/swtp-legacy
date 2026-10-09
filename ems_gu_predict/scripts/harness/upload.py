"""추천 결과를 DB에 적재하는 부분 — 원본 데이터를 "읽는" 접속정보
(`configs/db_connections.json`, `deepems.config.DataConfig`)와는 완전히
다른 파일(`configs/db_upload_connections.json`)에서 접속정보를 읽는다.

보안 근거: 읽기 전용 분석 코드(`preprocess.py`)가 실수로 쓰기 권한이 있는
계정 정보를 로드할 일이 없고, 반대로 이 업로드 경로가 원본 DB 자격증명을
알 필요도 없다 — 운영 DB 팀이 결과 적재용 계정을 아예 별도로 발급하는
경우에도 그대로 맞는 구조다. `dev` 모드(`schedule.py`)는 이 모듈 자체를
import하지 않는다 — 그래서 dev 모드를 아무리 잘못 돌려도 업로드
자격증명이 로드될 일 자체가 없다(코드 경로로 강제).

`configs/db_upload_connections.json` 구조(`db_connections.json`과 같은
{environment: {connection_key: {...}}} 2단계 구조를 재사용,
`configs/db_upload_connections.example.json` 참고):

    {"dev-server": {"<key>": {host, port, user, password, db, table}},
     "prod":       {"<key>": {host, port, user, password, db, table}}}

`dev-server`/`prod` 두 environment만 다루고 `local`은 없다 — 업로드는
"진짜로 DB에 쓰는" 기능이라 로컬 스텁 없이 dev-server(테스트용 서버)부터
시작하는 게 맞다는 전제(dev 모드는 애초에 업로드를 안 한다).

**업로드 대상 테이블(`tb_ctr_tnk_rst`, 2026-09-28 스키마 변경)**: 처음엔
(DSTRB_ID, PRDCT_VALUE, RGSTR_TIME) 좁은 스키마로 레버 추천값만 올렸는데,
"비고=='target'인 모든 태그가 예측/추천돼야 한다" + "horizon별 값을
컬럼으로 나눠 담는다"는 요청으로 wide 스키마로 바꿨고(2026-09-14),
1분 주기 전환(2026-09-28, 개발사 요구)으로 horizon 컬럼이 1/5/15/30분만
남았다:

    DSTRB_ID VARCHAR(100), RGSTR_TIME DATETIME,
    PRDCT_VALUE FLOAT,                          -- 레거시 소비자용(아래 참고)
    VALUE_1min, VALUE_5min, VALUE_15min, VALUE_30min (전부 FLOAT)
    PRIMARY KEY (DSTRB_ID, RGSTR_TIME)

- **`PRDCT_VALUE`는 반드시 같이 채운다**(2026-09-16, 2026-09-28 재적용).
  wide 스키마로 바꾸면서 이 컬럼을 안 쓰게 됐지만, 컬럼 자체는 운영
  테이블에 그대로 남아 있고 **읽는 쪽이 둘이나 된다**:
    * 군산 PRE 관망해석 — `epa/epanet_gunsan/main_epa_gs.py:644`가
      `SELECT DSTRB_ID, PRDCT_VALUE, RGSTR_TIME`으로 EPANET 수요를 가져온다.
    * BE 운전현황 화면 — `be/.../sqlmapper/mysql/drvn_mssql.xml:465,485,643`
      (예측 ID 목록은 `application-gu.properties`의 `dstrb.prdct.dstrbId`).
  그런데 아래 `upload_target_forecasts()`는 `REPLACE INTO`(= DELETE 후
  INSERT)라, 컬럼 목록에서 빼면 매 사이클 기본값(레거시 DDL 기준 0)으로
  덮인다 - 예외도 경고도 없이 두 소비자가 동시에 0을 읽게 된다. 그래서
  "안 쓰는 컬럼을 그냥 두는" 선택지가 없다.
  어느 지평을 복사할지는 접속정보의 `prdct_value_from`으로 정한다(기본
  `"VALUE_1min"` - 1분 주기 전환 후 "가장 가까운 예측값"). 레거시 컬럼이
  아예 없는 DB를 대비해 `null`이면 컬럼을 통째로 뺀다. 지평 선택을 코드가
  아니라 접속정보에 둔 이유는, 그게 "이 테이블을 누가 어떻게 읽는가"가
  사이트마다 갈리는 값이기 때문이다(테이블명이 이미 거기 있는 것과 같은 이유).

이전 스키마의 `VALUE_10min`/`VALUE_1h`~`VALUE_6h`는 **폐기**됐다
(5분 주기 + 6시간 horizon 시절 컬럼). 폐기 컬럼을 실제로 DROP할지,
과거 데이터 보존을 위해 남겨둘지는 운영 판단이다 - 남겨두면 이 코드는
그 컬럼을 건드리지 않으므로(INSERT 목록에 없음) NULL로 남는다.

- `DSTRB_ID` = `"{var_name}_Predict"`(예: `"O7_Predict"`, `"Q_GunS_Predict"`).
  Stage1 NN의 target_cols(taglist 비고=='target'인 모든 태그) 전체가
  대상이다. H3/H7처럼 여러 원본 태그(H3_1/H3_2, H7_1/H7_2)를 대표값
  하나로 묶어 예측하는 경우, 그 대표 예측값을 각 원본 태그의
  `{var_name}_Predict`에 그대로 복사한다(따로 예측 안 하므로).
- `RGSTR_TIME` = 그 예측이 나온 사이클의 origin 시각(현재 시각) - 위
  4개 VALUE_* 컬럼이 각각 그 시점 기준 1분/5분/15분/30분 후 예측값이다
  (horizon을 행이 아니라 컬럼으로 담는다 - 예전엔 스텝마다 한 행이었음).
  값 위치는 `_value_at_offset()`이 config의 freq로 계산하므로, 5분 freq
  모델을 그대로 쓰면 `VALUE_1min`은 뽑을 스텝이 없어 None이 된다(1분
  컬럼을 채우려면 1분 freq로 학습한 모델이 필요 -
  `configs/gu_db_1min_h30.yaml`).
- **Q_GunS는 예외** - 원시 NN 예측이 아니라 "그 시점의 추천값"(Stage3가
  추천한 `delta_lever`를 더한 값)을 담는다. Q_GunS가 유일한 레버라(밸브
  V2/V4는 2026-09-14부터 Stage3 추천 대상에서 빠짐 -
  `taglist.CONTROLLABLE_LEVERS` 참고) `used_lever`는 항상 Q_GunS다.
  `action="conflict"`처럼 단일 delta_lever가 없는 사이클은 delta_lever=0
  (원시 예측 그대로)으로 안전하게 대체한다.
- H7은 Stage1 NN 원시 예측 대신 Stage2 하이브리드(`CycleResult.
  h7_forecast`, 물리+GBR 잔차보정)를 쓴다 - 더 정확하다고 판단해서
  이미 그렇게 설계된 값이다(`docs/forecast_recommendation_pipeline.md`
  참고).

**주의**: 이 테이블은 코드가 만들지도, 바꾸지도 않는다 - 운영 DB에 이미
있는 `tb_ctr_tnk_rst`를 위 스키마에 맞게 DBA/운영이 직접 준비해야 한다
(2026-09-15, 테이블 생성 코드(`ensure_table`)는 자동 마이그레이션도
못 해주면서 혼란만 준다는 판단으로 제거). 2026-09-28 스키마 변경 때도
같은 원칙을 유지한다 - **CREATE/ALTER/DROP TABLE을 실행하는 코드는 이
저장소에 넣지 않는다**. 1분 주기 전환에 필요한 DDL은 운영에서 직접
실행할 것:

    ALTER TABLE tb_ctr_tnk_rst ADD COLUMN VALUE_1min FLOAT NULL,
                               ADD COLUMN VALUE_15min FLOAT NULL;
    -- 폐기 컬럼(VALUE_10min, VALUE_1h~VALUE_6h)은 과거 데이터 보존
    -- 여부를 판단해 운영에서 결정(그대로 두면 NULL로 남음).
    -- PRDCT_VALUE 는 지우지 말 것(위 레거시 소비자 참고).
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from deepems.config import _expand_env  # noqa: E402  (환경변수 ${VAR} 치환 재사용)
from deepems.db_ssl import ssl_connect_args  # noqa: E402
from deepems.sql_safety import validate_sql_identifier  # noqa: E402

ALLOWED_ENVIRONMENTS = ("dev-server", "prod")

# RGSTR_TIME(사이클 origin) 기준 각 VALUE_* 컬럼이 몇 분 후 예측값인지.
# dict 순서 = INSERT 컬럼 순서로도 그대로 쓴다.
#
# 2026-09-28: 1분 주기/30분 horizon 전환(개발사 요구)으로 1h~6h 컬럼을
# 폐기하고 1/5/15/30분만 남겼다 - `configs/gu_db_1min_h30.yaml` 참고.
# **운영 DB 테이블 변경은 이 코드가 하지 않는다**(아래 모듈 docstring의
# 주의 참고) - DBA/운영이 직접 ALTER해야 한다.
HORIZON_OFFSET_MINUTES: dict[str, int] = {
    "VALUE_1min": 1, "VALUE_5min": 5, "VALUE_15min": 15, "VALUE_30min": 30,
}

# 레거시 소비자(EPANET PRE·BE 운전현황)가 읽는 단일 컬럼과, 거기에 복사할
# 기본 지평. 접속정보에 prdct_value_from이 없으면 이 값을 쓴다 - 1분 주기
# 전환(2026-09-28) 후 "지금 대비 바로 다음 스텝"은 VALUE_1min이다.
LEGACY_VALUE_COLUMN = "PRDCT_VALUE"
DEFAULT_PRDCT_VALUE_FROM = "VALUE_1min"


@dataclasses.dataclass
class UploadConfig:
    host: str
    port: int
    user: str
    password: str
    db: str
    table: str
    # 레거시 PRDCT_VALUE 컬럼에 복사할 지평(HORIZON_OFFSET_MINUTES의 키).
    # None이면 그 컬럼을 INSERT에서 뺀다 — 컬럼이 없는 DB용 탈출구다.
    prdct_value_from: str | None = DEFAULT_PRDCT_VALUE_FROM
    # TLS(db_ssl.py 참고) — connections.json에 ssl_ca 등이 없으면 전부 None/True
    # 기본값이라 평문 연결(하위호환). prod에서는 ssl_ca 지정을 강하게 권장.
    ssl_ca: str | None = None
    ssl_cert: str | None = None
    ssl_key: str | None = None
    ssl_verify_identity: bool = True


def load_upload_config(conn_path: str, environment: str, connection_key: str) -> UploadConfig:
    if environment not in ALLOWED_ENVIRONMENTS:
        raise ValueError(
            f"업로드 environment는 {ALLOWED_ENVIRONMENTS} 중 하나여야 합니다: {environment!r} "
            "(dev 모드는 업로드 자체를 하지 않습니다 — schedule.py --mode dev 참고)"
        )
    path = Path(conn_path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path}가 없습니다. 이 파일은 비밀번호가 들어있어 git에 커밋하지 않으므로 직접 만들어야 합니다. "
            f"configs/db_upload_connections.example.json을 복사해서 실제 접속정보로 채우세요."
        )
    all_conn = json.loads(path.read_text(encoding="utf-8"))
    envs = {k: v for k, v in all_conn.items() if not k.startswith("_")}
    if environment not in envs:
        raise KeyError(f"{conn_path}에 environment '{environment}'가 없습니다. 사용 가능: {list(envs.keys())}")
    env_conns = {k: v for k, v in envs[environment].items() if not k.startswith("_")}
    if connection_key not in env_conns:
        raise KeyError(
            f"{conn_path}의 '{environment}' 환경에 '{connection_key}' 키가 없습니다. "
            f"사용 가능: {list(env_conns.keys())}"
        )
    raw = env_conns[connection_key]
    # table은 REPLACE INTO/CREATE TABLE에 파라미터 바인딩 없이 f-string으로
    # 직접 끼워 넣는다(SQL 식별자라 바인드 불가) — 접속정보 파일이 손상/변조돼도
    # SQL injection으로 이어지지 않도록 여기서 검증한다(sql_safety.py 참고).
    table = validate_sql_identifier(raw.get("table", "tb_ctr_tnk_rst"), "table")
    # 명시적 null은 "그 컬럼을 쓰지 않는다"는 뜻이라 기본값과 구분해서 살린다
    # (dict.get의 기본값은 키가 없을 때만 적용되므로 그대로 쓰면 된다).
    prdct_value_from = raw.get("prdct_value_from", DEFAULT_PRDCT_VALUE_FROM)
    if prdct_value_from is not None and prdct_value_from not in HORIZON_OFFSET_MINUTES:
        raise ValueError(
            f"prdct_value_from은 {list(HORIZON_OFFSET_MINUTES)} 중 하나이거나 null이어야 합니다: "
            f"{prdct_value_from!r} ({conn_path}의 '{environment}'.'{connection_key}')"
        )
    return UploadConfig(
        host=_expand_env(raw["host"]), port=int(raw.get("port", 3306)), user=_expand_env(raw["user"]),
        password=_expand_env(raw["password"]), db=_expand_env(raw["db"]), table=table,
        prdct_value_from=prdct_value_from,
        ssl_ca=_expand_env(raw.get("ssl_ca")), ssl_cert=_expand_env(raw.get("ssl_cert")),
        ssl_key=_expand_env(raw.get("ssl_key")), ssl_verify_identity=bool(raw.get("ssl_verify_identity", True)),
    )


def build_upload_engine(cfg: UploadConfig) -> Engine:
    url = f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.db}"
    conn_params = {"ssl_ca": cfg.ssl_ca, "ssl_cert": cfg.ssl_cert, "ssl_key": cfg.ssl_key, "ssl_verify_identity": cfg.ssl_verify_identity}
    return create_engine(url, pool_pre_ping=True, connect_args=ssl_connect_args(conn_params))


def _value_at_offset(series: pd.Series, origin: pd.Timestamp, offset_minutes: int, freq_minutes: float) -> float | None:
    """`series`(index가 origin 이후 미래 시각인 예측 궤적)에서 origin 기준
    `offset_minutes` 후 시점의 값을 뽑는다. 인덱스가 정확히 그 시각을 갖고
    있다고 가정하지 않고, freq 기준 스텝 위치를 계산해 안전하게 접근한다
    (`round`로 반올림 - freq가 5분 배수가 아닌 offset과 안 맞아떨어지는
    경우를 대비). 범위를 벗어나면(horizon이 그 offset보다 짧음) None."""
    if len(series) == 0 or freq_minutes <= 0:
        return None
    pos = round(offset_minutes / freq_minutes) - 1  # series[0]은 origin+freq 시점(첫 예측 스텝)
    if pos < 0 or pos >= len(series):
        return None
    value = series.iloc[pos]
    return None if pd.isna(value) else float(value)


def build_target_forecast_rows(
    origin: pd.Timestamp,
    forecast: pd.DataFrame,
    h7_forecast: pd.Series,
    level_col: str,
    used_lever: str,
    delta_lever: float | None,
    freq_minutes: float,
    combine_max_columns: dict[str, list[str]],
    observed_at_origin: pd.Series | None = None,
    persistence_max_offset_minutes: float = 0.0,
    persistence_exempt_targets: tuple[str, ...] = (),
    prdct_value_from: str | None = DEFAULT_PRDCT_VALUE_FROM,
) -> list[dict]:
    """한 사이클의 모든 target 예측을 `tb_ctr_tnk_rst` wide 스키마 행으로
    만든다(2026-09-14 요구사항: "비고=='target'인 모든 태그는 예측/추천돼야
    한다"). `forecast.columns`(Stage1 NN의 target_cols 전체)를 순회하며:

    - `level_col`(H7)은 원시 NN 예측 대신 `h7_forecast`(Stage2 하이브리드)를 쓴다.
    - `used_lever`(현재 Q_GunS 하나뿐 - `taglist.CONTROLLABLE_LEVERS` 참고)는
      원시 예측에 `delta_lever`(Stage3 추천 조정값)를 더한 "추천값"을 쓴다.
      `delta_lever`가 None이면(예: action="conflict") 0으로 대체한다
      (단일 추천값이 없다는 뜻이라, 안전하게 원시 예측 그대로 담는다).
    - 나머지 target은 Stage1 NN 원시 예측 그대로.

    H3/H7처럼 `combine_max_columns`로 여러 원본 태그를 대표값 하나로 묶은
    target은, 그 대표 예측값을 원본 태그 각각의 `{tag}_Predict`에 복사한다
    (따로 예측하지 않으므로 - 2026-09-14 사용자 확인).

    **짧은 offset은 persistence로 대체(2026-09-28, 1분 주기 전환)**:
    `observed_at_origin`(origin 시점 실측값, 보통 `filled.iloc[-1]`)을 주면,
    offset이 `persistence_max_offset_minutes` 이하인 컬럼은 모델 예측 대신
    그 실측값(= "직전값 유지" persistence)을 담는다. 근거는 실측이다 - 1분
    모델 학습 결과에서 **1분 시점은 23개 target 중 2개만 모델이 persistence를
    이겼다**(`docs/DEVNOTES.md` 2026-09-28 항목). 1분 앞은 "값이 그대로
    유지된다"가 거의 정답이라 모델이 이길 여지가 거의 없다.
    `persistence_exempt_targets`에 넣은 target은 이 대체에서 빼서 모델
    예측을 그대로 쓴다(예: H3는 1분 시점에도 skill이 +0.047~+0.099로 세 번의
    학습에서 일관되게 양수였다).

    부수 효과: 5분 freq 모델을 그대로 쓰는 경우에도 `VALUE_1min`이 None 대신
    실측값으로 채워진다(그 모델은 1분 앞 예측 스텝 자체가 없어 원래 None).

    기본값(`observed_at_origin=None`, 임계값 0)에서는 이 로직이 전혀 개입하지
    않으므로 기존 동작과 100% 동일하다.

    `prdct_value_from`이 지평 컬럼명이면 그 값(위 persistence 대체까지
    반영된 최종값)을 레거시 `PRDCT_VALUE`에도 복사한다(모듈 docstring 참고 -
    REPLACE INTO라 빼면 0으로 덮인다). None이면 키 자체를 넣지 않고, 그러면
    `upload_target_forecasts()`도 컬럼 목록에서 자동으로 뺀다.
    """
    delta = float(delta_lever) if delta_lever is not None else 0.0
    origin_py = origin.to_pydatetime()
    exempt = set(persistence_exempt_targets)
    rows = []
    for target_col in forecast.columns:
        if target_col == level_col:
            series = h7_forecast
        elif target_col == used_lever:
            series = forecast[target_col] + delta
        else:
            series = forecast[target_col]

        # 짧은 offset은 persistence(origin 실측값)로 대체 - 위 docstring 참고.
        # used_lever는 컬럼 의미가 "그 시점의 추천값"이라, persistence 기반에도
        # 같은 delta_lever를 더해야 의미가 유지된다("현재값 + 추천 조정폭").
        persistence_base = None
        if (
            observed_at_origin is not None
            and target_col not in exempt
            and target_col in observed_at_origin.index
        ):
            observed = observed_at_origin[target_col]
            if pd.notna(observed):
                persistence_base = float(observed) + (delta if target_col == used_lever else 0.0)

        values = {}
        for col, offset in HORIZON_OFFSET_MINUTES.items():
            if persistence_base is not None and offset <= persistence_max_offset_minutes:
                values[col] = persistence_base
            else:
                values[col] = _value_at_offset(series, origin, offset, freq_minutes)
        if prdct_value_from is not None:
            values[LEGACY_VALUE_COLUMN] = values[prdct_value_from]
        for tag in combine_max_columns.get(target_col, [target_col]):
            rows.append({"DSTRB_ID": f"{tag}_Predict", "RGSTR_TIME": origin_py, **values})
    return rows


def upload_target_forecasts(engine: Engine, table: str, rows: list[dict]) -> int:
    """`build_target_forecast_rows()`가 만든 행들을 한 번에 `REPLACE INTO`한다
    - 같은 (DSTRB_ID, RGSTR_TIME)으로 재실행(재시도/백필)해도 중복 없이
    최신값으로 덮어써지도록 REPLACE INTO(MariaDB/MySQL)를 쓴다. 반환값은
    실제로 쓴 행 수(빈 목록이면 0, engine을 아예 안 건드림).

    컬럼 목록은 넘어온 행의 키에서 그대로 끌어낸다 - 여기서 따로 조립하면
    `build_target_forecast_rows()`의 `prdct_value_from` 설정과 어긋났을 때
    바인딩 오류로만 드러나기 때문이다(단일 진실원은 행 딕셔너리)."""
    table = validate_sql_identifier(table, "table")  # 이 함수를 직접 호출하는 경로도 방어(defense in depth)
    if not rows:
        return 0
    cols = ["DSTRB_ID", "RGSTR_TIME", *HORIZON_OFFSET_MINUTES.keys()]
    if LEGACY_VALUE_COLUMN in rows[0]:
        cols.append(LEGACY_VALUE_COLUMN)
    # executemany는 모든 행이 같은 바인드 키를 가져야 한다. 행마다 키가 다르면
    # 드라이버 단에서 엉뚱한 오류가 나므로 여기서 먼저 잡는다.
    expected = set(cols)
    for i, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                f"행 {i}의 컬럼 구성이 다릅니다: {sorted(set(row) ^ expected)} "
                "(build_target_forecast_rows가 만든 행을 그대로 넘겨야 합니다)"
            )
    placeholders = ", ".join(f":{c}" for c in cols)
    stmt = text(f"REPLACE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})")
    with engine.begin() as conn:
        conn.execute(stmt, rows)
    return len(rows)
