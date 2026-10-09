"""설정 로딩.

기존 코드는 window_size, step_topredict 등이 노트북 셀 여기저기에
전역 변수로 흩어져 있어서 학습/추론 간에 값이 어긋나기 쉬웠다
(예: main_guns_v1.py 의 step_topredict=5 주석 "모델 자체 예측 시간 = 5분
but 사용은 1분"). 여기서는 학습에 필요한 모든 하이퍼파라미터/경로를
YAML 설정 파일 하나로 모으고, 학습 산출물(체크포인트)에도 그대로
저장해서 추론 코드가 같은 설정을 강제로 재사용하도록 한다.
"""
from __future__ import annotations

import dataclasses
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .sql_safety import validate_sql_identifier

_ENV_VAR_RE = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")
_REDACTED = "***REDACTED***"
_SECRET_FIELDS = ("db_password", "db_user", "db_host")


def _expand_env(value: str | None) -> str | None:
    """"${VAR_NAME}" 형태면 환경변수 값으로 치환한다.

    DB 비밀번호 등을 YAML에 평문으로 적지 않고 환경변수로 주입할 수 있게 하기 위함.
    """
    if value is None:
        return None
    m = _ENV_VAR_RE.match(value)
    if not m:
        return value
    var_name = m.group(1)
    if var_name not in os.environ:
        raise ValueError(f"환경변수 {var_name}가 설정되어 있지 않습니다 (설정값: {value!r}).")
    return os.environ[var_name]


@dataclasses.dataclass
class DataConfig:
    taglist_path: str
    sheet: str = "gunsan"
    mode: str = "BOTH"  # FLUX / PRES / BOTH
    freq: str = "1min"
    start_date: str | None = "2021-01-01"
    end_date: str | None = None
    ffill_limit_minutes: int = 2
    # 값이 이 분(minute) 이상 정확히 고정되면 결측처럼 취급해 학습에서 제외한다
    # (센서/통신 고장으로 마지막 값이 반복 기록되는 경우 — data.stuck_run_mask 참고).
    # None이면 비활성화. 실제 물리 신호가 몇 시간씩 완전히 안 변하는 경우는
    # 드물어서 기본값(360분=6시간)은 정상적인 짧은 무변화 구간까지 잘못
    # 잘라내지 않으면서도, dev DB에서 실제 발견된 몇 달짜리 고착은 확실히 잡는다.
    stuck_value_min_minutes: int | None = 360
    # stuck_value_min_minutes로 감지된 고정 구간을(그 태그가 있는) 전체 행을
    # 무효 처리하는 대신, 여기 적힌 변수명(var_name)에 대해서만 그 구간의 값을
    # 해당 컬럼의 중앙값으로 대체(imputation)한다. feature_cols == target_cols인
    # joint 모델(GU 시트)에서는 태그 하나(P6)가 몇 달간 고정되면 그 기간
    # 나머지 태그 전부가 학습에서 통째로 빠지기 때문에 만든 옵션이다 — P6
    # 자체를 그 기간에 정확히 맞힐 순 없어도, 중앙값이라는 "그럴듯한 상수"로
    # 채워서 나머지 태그들의 그 기간 데이터는 살린다 (data.impute_stuck_values 참고).
    stuck_value_impute_columns: list[str] = dataclasses.field(default_factory=list)
    # stuck_value_impute_columns를 어떻게 채울지: "median"(기본, 위 설명대로
    # 고정 구간 전체를 하나의 상수로 채움) 또는 "linear"(고정 구간 시작 직전
    # 마지막 실측값과 끝난 직후 첫 실측값을 직선으로 이어서 채움).
    # "median"의 문제(2026-09-10 실측으로 확인): 고정 구간이 아주 길면(P6가
    # 9.5개월 가까이 고정됐던 사례) 그 기간 내내 완전히 평평한 "가짜 상수"
    # 구간이 생겨서, 평가 시 skill_vs_persistence 같은 지표가 왜곡된다(모델이
    # 그 구간에 합리적인 미세 변동을 예측해도, 정답 자체가 인위적으로 평평해서
    # 실제보다 나쁜 점수를 받는 것처럼 보임). "linear"는 원래 변동폭이 좁은
    # 태그(P6: 4.26~4.36)에서 이 문제를 크게 줄여준다 — 완전히 정확하진 않아도
    # 상수보다는 훨씬 그럴듯한 추세를 준다. 고정 구간이 데이터 맨 앞/뒤에
    # 걸려 한쪽 끝값이 없으면(예: 측정 시작부터 고정) "linear"를 쓰더라도 그
    # 구간만 자동으로 median으로 대체된다(data.impute_stuck_values 참고).
    stuck_value_impute_method: str = "median"
    # 변수명(var_name) -> 이 날짜 이전 데이터는 무시(NaN 처리)한다. 센서가 뒤늦게
    # 설치돼서 그 전엔 값이 없거나 의미 없는 값(0 근처 노이즈 등)만 있는 태그에
    # 쓴다 — 예: Q8(891-365-FRI-8802)은 2025-03-27 이전엔 -10~30 사이를 맴도는
    # 노이즈뿐이다가 그날부터 실제 유량(수백 단위)이 찍히기 시작했다. AND 조건인
    # valid_mask 특성상 이 필드를 안 쓰고 그냥 data.start_date를 늦추면 다른 모든
    # 태그의 그 이전 데이터까지 같이 버려지므로, 이 태그 하나만 시작일을 늦추는
    # 용도로 쓴다 (data.apply_column_start_dates 참고).
    column_start_dates: dict[str, str] = dataclasses.field(default_factory=dict)
    # 태그리스트에서 읽은 변수 중 여기 적힌 변수명(var_name)은 feature/target에서
    # 아예 뺀다. Q8처럼 그 변수만 최근 데이터만 있는 태그를 넣으면(설령
    # column_start_dates로 그 태그 자체는 살려도) joint 모델 전체의 유효 구간이
    # 그 태그의 시작일 이후로 짧아진다 — "Q8 포함 버전"과 "Q8 제외(그래서 전체
    # 기간을 다 쓰는) 버전"을 별도 config로 두고 싶을 때 이 필드로 나눈다
    # (taglist.filter_excluded 참고).
    exclude_vars: list[str] = dataclasses.field(default_factory=list)
    # exclude_vars와 달리 **예측 대상(target)에서만** 빼고 입력 feature로는
    # 그대로 남긴다 (2026-09-28 추가). taglist의 role=="target"을 config
    # 단위로 "이 학습에서는 예측까지 하진 않는다"로 내리는 수단이다 - taglist
    # 엑셀의 role을 고치면 그 태그를 쓰는 **모든** config가 같이 바뀌는데,
    # "1분 모델에서만 빼고 기존 5분 모델은 그대로 두고 싶다" 같은 경우가
    # 있어서 config-local 수단이 필요했다.
    #
    # 쓰는 이유(실측): 손실 가중치가 `inverse_persistence_mae`(1/persistence
    # MAE)라, 느리게 변해서 persistence로 이미 잘 맞는 신호가 가중치를 크게
    # 먹는다. 1분 모델 첫 학습에서 오식도 개별 수위(H7_3~H7_8)와 고장 센서
    # (P6)가 전체 가중치의 62%를 가져가고 정작 제어에 쓰는 H3(0.29)/O7(0.07)이
    # 밀렸다. `docs/network_control_simulation_design.md` §5(규칙5)도 이미
    # "오식도 개별 8개는 예측 대상에서 빼고 요약값만 입력으로 쓴다"고 정해둔
    # 방향이라 그에 맞춘다.
    #
    # **업로드 영향**: 여기 넣은 변수는 `{var}_Predict` 행이 더는 안 올라간다
    # (upload.build_target_forecast_rows가 target_cols만 돌므로).
    target_exclude_vars: list[str] = dataclasses.field(default_factory=list)
    # {새 변수명: [원본 변수명들]} — 지정된 변수들을(raw, 리샘플 전 원본 해상도
    # 기준) 결측이 아닌 값들의 최댓값으로 합쳐 새 변수 하나로 만들고, 원본은
    # feature/target에서 뺀다. H3_1/H3_2, H7_1/H7_2처럼 같은 지점의 서로 다른
    # 두 수위 센서가 사실상 중복 신호일 때(상관계수 0.98 이상,
    # analysis/GU_db/near_duplicate_features.csv) "둘 다 따로 넣지 말고 큰 쪽을
    # 대표값으로" 쓰기 위함이다 (data.combine_max_columns, taglist.combine_max 참고).
    combine_max_columns: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    # 여기 적힌 변수명(var_name)은 결측 구간을 ffill(직전값 유지) 대신 linear
    # interpolation(선형 보간)으로 채운다. 압력처럼 값이 시간에 따라 매끄럽게
    # 변하는 신호는, 결측 동안 값이 "계단식으로 멈춰있었다"고 가정하는 ffill보다
    # 두 관측치 사이를 직선으로 잇는 편이 더 그럴듯하다. ffill_limit_minutes와
    # 같은 한도(그 이상 길게 비면 안 채우고 valid_mask에서 제외)를 그대로
    # 공유한다 — resample_and_flag_gaps 참고.
    linear_interp_columns: list[str] = dataclasses.field(default_factory=list)
    # 시각(index)에서 결정적으로 계산되는 주기적 시간 feature를 입력에 추가한다
    # (target으로는 쓰이지 않고 feature_cols에만 더해진다). 실측(analyze.py
    # --acf-max-lag-minutes 10080으로 7일치까지 확인)으로, 거의 모든 target이
    # 24시간(및 그 배수)에서 자기상관 국소 피크를 보였다 — 일간 주기성이
    # 뚜렷하다는 뜻이다(analysis/GU_db/periodicities.csv). 그 근처에 7일(주간)
    # 주기 피크는 뚜렷하게 나타나지 않았으므로 dow_sin/dow_cos(요일)는 넣지
    # 않는다 — 근거 없이 넣지 않는다는 원칙. 사용 가능한 이름은
    # data._TIME_FEATURE_FNS 참고 (hour_sin/hour_cos/dow_sin/dow_cos/
    # month_sin/month_cos).
    time_features: list[str] = dataclasses.field(default_factory=list)

    # 레버 태그(V2/V4/Q_GunS 등)의 diff(변화량)를 별도 feature로 추가한다
    # (`{col}_diff{step}`, data.add_lever_change_features 참고). 2026-09-11
    # 실측: 후보 모델 8종이 전부 Q7의 급격한 낙폭을 놓쳤는데, 그 구간이
    # V2 밸브 조작 시점과 정확히 일치했다 - 원시 레버값만으로는 "지금 막
    # 움직이기 시작했다"는 신호가 암묵적이라, 명시적 diff feature로
    # 모델이 조작 감지를 더 쉽게 하도록 시도한다. 빈 리스트면(기본)
    # 아무 feature도 추가되지 않아 기존 config와 완전히 동일하게 동작.
    lever_diff_columns: list[str] = dataclasses.field(default_factory=list)
    lever_diff_steps: list[int] = dataclasses.field(default_factory=lambda: [1, 3, 6])

    # source: "csv" (기존 Rawdata/*.csv 파일) 또는 "db" (운영 DB에서 직접 조회)
    source: str = "csv"

    # --- source: csv ---
    rawdata_dir: str | None = None
    raw_filename_template: str = "GSSCADA.{tag}.F_CV.csv"

    # --- source: db ---
    # main_guns_v1.py와 동일하게 태그별 raw 값을 담은 TB_RAWDATA(TS, TAGNAME, VALUE)
    # 형태의 테이블에서 조회한다. 접속정보는 두 가지 방식 중 하나로 준다:
    #   1) db_connections_path + db_environment + db_connection_key : configs/ 폴더의
    #      db_connections.json(비밀번호 포함, git 제외)에서 "실제서버(prod)/개발서버(dev)/
    #      로컬서버(local)" 환경별로 분리해둔 접속정보를 읽는다. 자세한 파일 구조는
    #      configs/db_connections.example.json 참고.
    #   2) db_host/db_port/db_user/db_password/db_name : 직접 지정. 비밀번호는
    #      YAML에 평문으로 적지 말고 "${환경변수명}" 형태로 적으면 실행 시
    #      해당 환경변수 값으로 치환된다.
    db_connections_path: str | None = None
    # 실제서버(prod) / 개발서버(dev) / 로컬서버(local). 잘못 지정해도 조용히
    # 다른 서버로 붙지 않도록, connections.json에 없는 값이면 바로 에러를 낸다.
    # 기본값을 "local"로 둔 것도 실수로 운영(prod) DB에 붙는 사고를 막기 위함이다.
    db_environment: str = "local"
    db_connection_key: str | None = None
    db_host: str | None = None
    db_port: int = 3306
    db_user: str | None = None
    db_password: str | None = None
    db_name: str | None = None
    # DB 연결에 TLS를 켠다(db_ssl.py 참고) — db_connections_path 방식이면
    # json의 해당 연결 항목에 ssl_ca 등을 직접 적으면 되므로 보통 이 필드들은
    # 인라인 접속정보(db_host 등)를 쓸 때만 필요하다. 전부 비워두면(기본)
    # 지금까지처럼 평문 연결(하위호환) — 원격 DB라면 최소 ssl_ca 지정을 권장.
    db_ssl_ca: str | None = None
    db_ssl_cert: str | None = None
    db_ssl_key: str | None = None
    db_ssl_verify_identity: bool = True
    db_table: str = "TB_RAWDATA"
    db_ts_col: str = "TS"
    db_tagname_col: str = "TAGNAME"
    db_value_col: str = "VALUE"
    # 태그별로 달력 월 단위(YYYY-MM)로 쪼개서 DB를 조회하고, 이미 끝난(지난) 달은
    # {cache_dir}/{태그명}/{YYYY-MM}.pkl.gz 로 gzip-압축된 pickle 캐시를 남긴다.
    # 여러 시트가 태그를 공유하거나(gj/nw/osd는 gunsan과 태그가 겹침) 같은 분석을
    # 반복 실행할 때 DB 왕복을 크게 줄인다. 아직 안 끝난 이번 달은 매번 새로
    # 가져온다(과거 달만 캐시 — 진행 중인 달을 캐시하면 그 달의 나머지 데이터가
    # 영영 안 채워진 채로 남는다). None으로 두면 캐시를 끈다.
    cache_dir: str | None = "./Data"

    def __post_init__(self) -> None:
        if self.source not in ("csv", "db"):
            raise ValueError(f"data.source는 'csv' 또는 'db'여야 합니다: {self.source!r}")

        self.db_user = _expand_env(self.db_user)
        self.db_password = _expand_env(self.db_password)
        self.db_host = _expand_env(self.db_host)

        if self.source == "csv":
            if not self.rawdata_dir:
                raise ValueError("data.source='csv'이면 data.rawdata_dir을 지정해야 합니다.")
        elif self.source == "db":
            has_file_ref = bool(self.db_connections_path and self.db_connection_key)
            has_inline = bool(self.db_host and self.db_user and self.db_name)
            if not (has_file_ref or has_inline):
                raise ValueError(
                    "data.source='db'이면 (db_connections_path + db_connection_key) 또는 "
                    "(db_host + db_user + db_password + db_name)을 지정해야 합니다."
                )
            # db_table/db_ts_col/db_tagname_col/db_value_col은 db_source.py가
            # 파라미터 바인딩이 아니라 SQL 문자열에 직접 끼워 넣는다(식별자는
            # 바인드 파라미터로 못 넘김) — config 파일이 손상/변조됐을 때 SQL
            # injection으로 이어지지 않도록 여기서 미리 검증한다(sql_safety.py 참고).
            for field_name in ("db_table", "db_ts_col", "db_tagname_col", "db_value_col"):
                validate_sql_identifier(getattr(self, field_name), f"data.{field_name}")

    def db_connection_params(self) -> dict:
        """pymysql.connect(**params) / SQLAlchemy 접속 문자열에 쓸 dict를 반환.

        connections.json 방식이 우선이고, 없으면 인라인 값을 쓴다. connections.json은
        {환경(prod/dev/local): {연결키: {host, port, user, password, db}}} 형태의
        2단계 구조다 — db_environment로 서버를, db_connection_key로 그 안의 접속
        항목을 고른다. 둘 중 하나라도 파일에 없으면 (실수로 엉뚱한 서버에 붙는 대신)
        바로 에러를 낸다.
        """
        import json

        if self.db_connections_path and self.db_connection_key:
            conn_path = Path(self.db_connections_path)
            if not conn_path.exists():
                raise FileNotFoundError(
                    f"{conn_path}가 없습니다. 이 파일은 비밀번호가 들어있어 git에 커밋하지 않으므로,"
                    f" 직접 만들어야 합니다. configs/db_connections.example.json을 복사해서"
                    f" 실제 접속정보로 채우세요."
                )
            all_conn = json.loads(conn_path.read_text(encoding="utf-8"))
            envs = {k: v for k, v in all_conn.items() if not k.startswith("_")}
            if self.db_environment not in envs:
                raise KeyError(
                    f"{self.db_connections_path}에 environment '{self.db_environment}'가 없습니다. "
                    f"사용 가능한 environment: {list(envs.keys())}"
                )
            env_conns = {k: v for k, v in envs[self.db_environment].items() if not k.startswith("_")}
            if self.db_connection_key not in env_conns:
                raise KeyError(
                    f"{self.db_connections_path}의 '{self.db_environment}' 환경에 "
                    f"'{self.db_connection_key}' 키가 없습니다. "
                    f"사용 가능한 키: {list(env_conns.keys())}"
                )
            params = dict(env_conns[self.db_connection_key])
        else:
            params = {
                "host": self.db_host,
                "port": self.db_port,
                "user": self.db_user,
                "password": self.db_password,
                "db": self.db_name,
                "ssl_ca": self.db_ssl_ca,
                "ssl_cert": self.db_ssl_cert,
                "ssl_key": self.db_ssl_key,
                "ssl_verify_identity": self.db_ssl_verify_identity,
            }
        return params


@dataclasses.dataclass
class WindowConfig:
    window_size: int = 60
    horizon: int = 5
    stride: int = 5
    # val/test에 쓸 stride. None이면 horizon을 쓴다(=예측 구간이 겹치지도 비지도
    # 않는 기본 관례). train과 다른 값을 주는 이유: window_size를 늘리면서
    # stride를 촘촘하게(예: 1) 두면 train 데이터 증강에는 도움이 되지만, 그
    # 촘촘한 stride를 val/test에도 그대로 쓰면 서로 거의 똑같은(window_size가
    # 클수록 겹침 비율이 더 커짐) 윈도우를 수만 번 평가하는 셈이 되어 실제
    # 다양성 없이 지표만 안정적으로/부풀려 보일 수 있다. train만 촘촘하게
    # 증강하고 평가는 정직하게 하려면 이 값을 horizon과 같게(기본값) 두면 된다.
    eval_stride: int | None = None
    # 윈도우+호라이즌보다 충분히 길어야 최소 1개 시퀀스를 만들 수 있다.
    min_segment_minutes: int = 200


@dataclasses.dataclass
class SplitConfig:
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    # 분할 경계 양쪽에서 겹치는 슬라이딩 윈도우로 정보가 새지 않도록
    # 잘라내는 여유 구간(분). window_size + horizon 이상으로 둔다.
    purge_minutes: int = 65


@dataclasses.dataclass
class OutlierConfig:
    enabled: bool = True
    lower_quantile: float = 0.01
    upper_quantile: float = 0.99
    # test 구간은 절대 clip하지 않는다 (실제 이상상황 성능을 보기 위해).
    apply_to_splits: tuple[str, ...] = ("train", "val")
    # 컬럼별로 다른 (lower_q, upper_q)를 쓰고 싶을 때. 여기 없는 컬럼은 위
    # lower_quantile/upper_quantile을 그대로 쓴다.
    #
    # 왜 필요한가 (analyze.py 결과로 실제로 드러난 사례, osd 시트 P6):
    # 정상 작동 범위가 아주 좁은(예: 4.2~4.3) 압력 신호는, 전역 0.01/0.99
    # quantile clip이 2년치 데이터 중 약 2%(수만 행)를 정상 범위 안의 값인데도
    # 잘라내 버린다. 그 결과 clip 후 자기상관이 clip 전보다 오히려 낮아졌다
    # (raw 0.994 -> robust_clipped 0.858, lag_1min). 반대로 진짜 이상치가 섞인
    # 컬럼(예: gunsan 시트 Q_GunSnS)은 같은 0.01/0.99 clip이 자기상관을 0.01에서
    # 0.999로 크게 끌어올렸다. 즉 "이 clip이 도움이 되는지"는 컬럼마다 다르며,
    # autocorrelation.csv의 raw vs robust_clipped를 비교하면 판단할 수 있다:
    # robust_clipped가 raw보다 낮으면 그 컬럼은 clip 범위를 넓히거나(예: 0.001/0.999)
    # 꺼야 한다.
    column_overrides: dict[str, tuple[float, float]] = dataclasses.field(default_factory=dict)
    # "minmax"(기본, 기존 동작 그대로) | "robust"(median/IQR) | "standard"
    # (평균/표준편차). Q_GunS처럼 운영자가 갑자기 크게 바꾸는 값(8/3 저수위
    # 사태 등, docs/model_results.md §4)은 quantile clip을 걸어도 남은 값의
    # 분포가 여전히 한쪽으로 치우칠 수 있는데, RobustScaler는 이상치 자체에
    # 덜 끌려가는 median/IQR 기준이라 이런 컬럼에 더 안정적이다 -
    # docs/network_control_simulation_design.md 규칙11 대응.
    scaler_type: str = "minmax"
    # 컬럼별로 scaler_type을 다르게 쓰고 싶을 때(위 column_overrides와 같은
    # 패턴) - 여기 없는 컬럼은 위 scaler_type을 그대로 쓴다.
    column_scaler_overrides: dict[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        valid = ("minmax", "robust", "standard")
        if self.scaler_type not in valid:
            raise ValueError(f"outlier.scaler_type은 {valid} 중 하나여야 합니다: {self.scaler_type!r}")
        bad = {k: v for k, v in self.column_scaler_overrides.items() if v not in valid}
        if bad:
            raise ValueError(f"outlier.column_scaler_overrides 값은 {valid} 중 하나여야 합니다: {bad}")


@dataclasses.dataclass
class ModelConfig:
    # attn_transformer_residual(기본, model.py 상단 docstring 참고) | attn_lstm(기존 구조, 호환용)
    type: str = "attn_transformer_residual"
    dropout: float = 0.1
    non_negative_output: bool = True

    # --- type: attn_lstm 전용 ---
    encoder_hidden: int = 64

    # --- type: attn_transformer_residual 전용 ---
    d_model: int = 64          # nhead로 나누어떨어져야 함
    nhead: int = 4
    num_encoder_layers: int = 2
    dim_feedforward: int = 128

    # --- 공통 (decoder head 크기) ---
    decoder_hidden: int = 32


@dataclasses.dataclass
class TrainConfig:
    batch_size: int = 256
    epochs: int = 200
    patience: int = 15
    lr: float = 1e-3
    weight_decay: float = 0.0
    seed: int = 42
    # "auto"는 GPU를 기본으로 쓴다 — cuda 있으면 cuda, 없으면 mps(Apple GPU),
    # 그마저 없으면 cpu (train.resolve_device). attn_transformer_residual처럼
    # self-attention 연산이 많은 모델은 GPU에서 훨씬 빠르다. 특정 장치를
    # 강제하려면 "cuda"/"cuda:0"/"mps"/"cpu"를 직접 적거나 CLI --device 사용.
    device: str = "auto"
    val_check_batches: int | None = None
    # "none" | "inverse_persistence_mae". target이 여러 개(특히 예측 난이도가
    # 서로 크게 다른 경우 — 예: 태그리스트를 GU 시트 하나로 합쳐 24개 target을
    # 한 모델로 예측하는 경우)일 때, 단순 평균 MSE는 원래 잡음이 크고 예측이
    # 어려운(persistence MAE가 큰) target의 자연히 더 큰 오차값이 손실을
    # 지배해서, 상대적으로 깨끗한 target의 미세한 개선 신호가 묻힐 수 있다.
    # "inverse_persistence_mae"는 train 구간에서 각 target의 persistence
    # (직전값 유지) MAE를 미리 계산해 그 역수(평균 1로 정규화, 어려운 target은
    # 낮게·쉬운 target은 높게)를 손실 가중치로 쓴다 —
    # baselines.compute_inverse_persistence_weights 참고.
    target_loss_weighting: str = "none"
    # target_loss_weighting="inverse_persistence_mae"일 때, 정규화된(평균 1)
    # 가중치의 상한. persistence MAE가 극히 작은 target(예: 장기 고정 구간을
    # 중앙값으로 채운 태그, 또는 원래도 거의 완벽하게 매끄러운 신호)은 가중치가
    # 나머지 target보다 10배 이상 커질 수 있고, 실제로 그 상태로 학습하면 그
    # target들이 손실을 독식해 skill_vs_persistence가 오히려 크게 나빠지는
    # 현상이 gu_db.yaml 실측(P6/H7, 가중치 6.58/5.19)으로 확인됐다 —
    # baselines.compute_inverse_persistence_weights 참고. None이면 상한 없음.
    target_loss_weight_cap: float | None = 3.0
    # 오래된 학습 윈도우일수록 손실 가중치를 지수적으로 낮춘다(구간을 잘라내진
    # 않음) — weight = 0.5 ** (age_days / 이 값). None이면 끔(모든 윈도우
    # 동일 가중치). 예: 60이면 60일 전 데이터는 가중치 0.5, 120일 전은 0.25.
    # 2026-08 국가산단밸브 제어 방식 변경(고정 개방 -> 수위 연동 조절,
    # docs/model_results.md 참고)처럼 운영 정책 자체가 바뀐 뒤, 옛날 데이터를
    # 통으로 잘라내면 학습 윈도우가 급감해 과적합 위험이 커지는 대신 이걸로
    # "최근 데이터 위주로 학습하되 옛날 데이터도 완전히 버리지는 않기"를
    # 절충한다. windows.compute_time_decay_weights 참고.
    sample_time_decay_halflife_days: float | None = None

    def __post_init__(self) -> None:
        if self.target_loss_weighting not in ("none", "inverse_persistence_mae"):
            raise ValueError(
                f"train.target_loss_weighting은 'none' 또는 'inverse_persistence_mae'여야 합니다: "
                f"{self.target_loss_weighting!r}"
            )
        if self.target_loss_weight_cap is not None and self.target_loss_weight_cap <= 1.0:
            raise ValueError(
                f"train.target_loss_weight_cap은 1.0보다 커야 합니다(평균이 1로 정규화되므로 "
                f"1.0 이하면 사실상 모든 target이 같은 가중치로 눌립니다): {self.target_loss_weight_cap!r}"
            )
        if self.sample_time_decay_halflife_days is not None and self.sample_time_decay_halflife_days <= 0:
            raise ValueError(
                f"train.sample_time_decay_halflife_days는 0보다 커야 합니다: "
                f"{self.sample_time_decay_halflife_days!r}"
            )


@dataclasses.dataclass
class OutputConfig:
    dir: str = "./runs/gunsan"
    # deepems.analyze 결과 저장 위치. 학습 산출물(runs/)과 섞이지 않도록 별도 폴더에 둔다.
    # "{sheet}"는 data.sheet 값으로 치환된다 (다른 시트로 돌려도 서로 안 겹치도록).
    analysis_dir: str = "./analysis/{sheet}"


@dataclasses.dataclass
class Config:
    data: DataConfig
    window: WindowConfig
    split: SplitConfig
    outlier: OutlierConfig
    model: ModelConfig
    train: TrainConfig
    output: OutputConfig

    @staticmethod
    def from_yaml(path: str | Path) -> "Config":
        raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return Config(
            data=DataConfig(**raw.get("data", {})),
            window=WindowConfig(**raw.get("window", {})),
            split=SplitConfig(**raw.get("split", {})),
            outlier=OutlierConfig(**raw.get("outlier", {})),
            model=ModelConfig(**raw.get("model", {})),
            train=TrainConfig(**raw.get("train", {})),
            output=OutputConfig(**raw.get("output", {})),
        )

    def to_dict(self, redact_secrets: bool = True) -> dict:
        """dict로 직렬화. 기본적으로 DB 접속정보(host/user/password)를 가린다.

        __post_init__에서 환경변수/connections.json이 이미 실제 값으로
        치환/보관되어 있기 때문에, redact_secrets=False 없이 이 dict를
        그대로 파일(runs/*/config.json 등)에 쓰면 평문 비밀번호가
        디스크에 남는다. train.py는 항상 기본값(True)으로 저장한다 —
        infer.py는 model/window 설정만 쓰고 DB 접속정보는 필요 없다.
        """
        d = dataclasses.asdict(self)
        if redact_secrets:
            for field in _SECRET_FIELDS:
                if d["data"].get(field):
                    d["data"][field] = _REDACTED
        return d
