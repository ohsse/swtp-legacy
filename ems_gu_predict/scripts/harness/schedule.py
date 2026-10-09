"""실시간 운영 하네스의 메인 진입점 — `preprocess.py`(데이터 준비) +
`train.py`(Stage2/3 아티팩트) + `analysis.py`(Stage1~3 추천) +
`upload.py`(결과 DB 적재)를 세 가지 실행 모드로 배선한다.

**dev/dev-server/prod는 서로 다른 실제 서버다** — 같은 서버를 용도만 다르게
부르는 게 아니라, 각 모드가 물리적으로/운영상으로 분리된 서버에 붙는다는
전제다. 그래서 원본 데이터 읽기 environment(`configs/db_connections.json`)
이름도 모드 이름과 그대로 맞췄다(`DEFAULT_SOURCE_ENVIRONMENT` = identity
매핑) — "dev 모드인데 local DB를 읽는다" 같은 암묵적 대응이 없다.

## 모드

- **`dev`**: 과거 구간(`--backtest-start`~`--backtest-end`)을 `dev` 서버
  데이터로 훑는 백테스트. 실시간 대기(`time.sleep`) 없이 각 origin을
  곧바로 이어서 처리하므로 그 자체로 "시간 가속"이다(실제 5분/30분 간격을
  기다리지 않고 계산이 끝나는 대로 다음 origin으로 넘어간다). **DB
  업로드를 하지 않는다** — `upload.py` 자체를 import하지 않으므로, 이
  모드를 아무리 잘못 실행해도 업로드 자격증명이 로드되거나 실제 DB에
  쓰기가 발생할 수 없다. 결과는 콘솔 출력 + 선택적으로 `--out-csv`에
  저장한다.
- **`dev-server`**: `dev-server` 서버의 실시간 경로(지금 시각 기준)를
  실제로 몇 사이클(`--cycles`, 기본 1) 돌리고, `configs/
  db_upload_connections.json`의 `"dev-server"` environment로 실제
  업로드까지 수행해서 "업로드 코드가 실제로 동작하는지"를 확인하는
  모드다. 운영 DB(`prod`)와 완전히 분리된 테스트용 서버에 붙는다는 전제.
- **`prod`**(기본값): `"prod"` 서버에서 원본 데이터를 읽고 `"prod"`
  environment로 업로드하며, 1분 주기(`--interval-seconds`, 기본 60 —
  2026-09-28 개발사 요구로 5분(300)에서 변경)로
  무한 반복한다. 주기는 **벽시계 경계에 맞춘다** — 사이클이 끝난 시점부터
  60초를 세면 실제 간격이 `60 + 사이클 소요시간`이 되어 조금씩 밀리고,
  밀린 양이 한 주기에 닿는 순간 origin 하나를 건너뛰어 그 시각 예측이 통째로
  빈다. 그래서 `_seconds_until_next_slot`으로 "다음 :00 + `--cycle-lag-seconds`"
  까지만 자고, 조회 구간의 끝도 `floor(freq) + freq`로 못박아 origin이 항상 그
  경계 버킷이 되게 한다(둘 중 하나만 해서는 안 된다 — 자세한 이유는 두 곳의
  주석 참고). origin이 한 주기씩 전진하지 않으면 "격자 어긋남" 경고를 남긴다.
  매 사이클 조회는 **분할**한다(`_fetch_cycle` 참고). 실수로 다른 서버에 붙는 사고를 막기 위해 source/업로드
  environment를 CLI로 덮어쓸 수 없게 이 모드에서만 강제 고정한다. 한
  사이클이 실패해도(DB 순단, 일시적 결측 등) 예외를 콘솔에 로그만 남기고
  루프 자체는 계속 돈다 — 그래야 사람이 없어도 다음 정상 사이클에서
  스스로 복구된다. `--mode`를 아예 생략하면 이 모드로 돈다 — 무인
  운영(cron/서비스)이 기본 용도이므로, 테스트 경로(dev/dev-server)는
  오히려 명시적으로 지정하게 만드는 편이 "실수로 --mode를 안 줬는데
  dev로 조용히 돌아서 운영이 안 됐다" 같은 사고를 막는다.

## 접속정보 파일 분리(보안)

- 원본 데이터를 "읽는" 접속정보: `configs/db_connections.json`
  (`deepems.config.DataConfig`, environment: `dev`/`dev-server`/`prod` —
  세 모드가 각각 같은 이름의 실제 서버에 붙는다).
- 추천 결과를 "쓰는" 접속정보: `configs/db_upload_connections.json`
  (`upload.py`, environment: `dev-server`/`prod`만 — `dev` 모드는 업로드
  자체를 안 하므로 없음).

두 파일은 완전히 분리돼 있고, 어느 쪽도 다른 쪽의 존재를 몰라도 동작한다
(`upload.py` 모듈 docstring 참고) — 읽기 전용 계정과 쓰기 계정을 운영에서
아예 다른 사람이 발급/관리해도 이 구조가 그대로 맞는다.

## 실행 로그

`logging_setup.get_logger(mode, log_dir)`로 모드별 로거를 만들어 콘솔과
`{log_dir}/{mode}.log`(기본 `logs/`, `--log-dir`로 변경 가능)에 동시에
기록한다. 자정마다 자동으로 `{mode}.log.YYYY-MM-DD`로 회전하므로("일별
실행 로그") `prod`처럼 며칠씩 계속 도는 모드도 "오늘 무슨 일이 있었는지"를
날짜별 파일로 바로 찾아볼 수 있다 — 자세한 근거는 `logging_setup.py` 참고.

## 개발 이력

버전/수정사항은 `scripts/DEVNOTES.md`에 기록한다 — 이 스크립트를 바꿀 때마다
같이 갱신할 것.

## 알고리즘

Stage1~3 자체가 실제로 무엇을 계산하는지(각 모드가 결국 호출하는 수식)는
`ALGORITHM.md`에 별도로 정리했다 — 설계 근거/실측치의 원본은 여전히
`docs/forecast_recommendation_pipeline.md`이고, `ALGORITHM.md`는 그중 이
스케줄러가 실제로 실행하는 부분만 추려 빠르게 참고하기 위한 요약이다.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # preprocess/analysis/train/upload를 같은 폴더에서 임포트
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import analysis  # noqa: E402
import preprocess  # noqa: E402
import train  # noqa: E402
from deepems.config import Config  # noqa: E402
from deepems.infer import load_artifacts  # noqa: E402
from logging_setup import get_logger  # noqa: E402

## dev/dev-server/prod는 서로 다른 실제 서버다(같은 서버를 다른 이름으로
# 부르는 게 아님) — 그래서 원본 읽기(`configs/db_connections.json`)의
# environment 이름도 모드 이름과 그대로 맞춘다(로컬 스텁을 기본으로 두지
# 않음). 업로드(`configs/db_upload_connections.json`)는 dev가 애초에
# 업로드를 안 하므로 dev-server/prod 두 environment만 있으면 된다.
DEFAULT_SOURCE_ENVIRONMENT = {"dev": "dev", "dev-server": "dev-server", "prod": "prod"}


def resolve_source_environment(mode: str, override: str | None) -> str:
    """모드별 기본 source DB environment. `prod` 모드는 CLI로 덮어쓸 수 없다
    (실수로 다른 서버 원본 데이터를 운영에 흘려보내는 사고 방지) — override를
    주면 ValueError."""
    if mode == "prod":
        if override:
            raise ValueError("--mode prod에서는 --source-db-environment를 지정할 수 없습니다(항상 'prod' 고정).")
        return "prod"
    return override or DEFAULT_SOURCE_ENVIRONMENT[mode]


def _extra_cols(offline: "train.OfflineArtifacts") -> list[str]:
    return [offline.level_col, offline.inflow_col, offline.outflow_col]


def _lookback_days(args, art, cfg: Config) -> float:
    if args.lookback_days is not None:
        return args.lookback_days
    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0
    window_size = art.cfg["window"]["window_size"]
    return max(args.band_window_days, window_size * freq_minutes / 1440.0) + 1.0


def _fetch_cycle(args, art, cfg: Config, offline, end: pd.Timestamp) -> tuple[pd.DataFrame, pd.Series | None]:
    """한 사이클의 입력을 `end`(배타) 기준으로 받는다. 반환: (filled, level_history).

    기본은 **조회 분할**이다(2026-09-28). 예전에는 목표범위(21일) 하나 때문에
    모든 태그를 22일치씩 매 사이클 받았는데, 1분 주기에서는 매분 약 85만
    행이라 사이클 시간 대부분이 여기서 나갔다. 그래서
    - 전체 태그: Stage1 입력에 필요한 만큼만(`preprocess.feature_lookback_minutes`)
    - `level_col`(H7)만: 목표범위 기간 + 1일(`preprocess.fetch_level_history`)
    로 나눠 받는다. 22일 한 번에 받을 때와 결과가 같다는 건 군산 개발서버
    실데이터로 확인했다(20개 origin 전부 일치 - preprocess 참고).

    `--lookback-days`를 주면 예전처럼 한 번에 받는다(level_history=None) -
    분할에 문제가 생겼을 때 코드 수정 없이 되돌리는 스위치다.
    """
    if args.lookback_days is not None:
        return preprocess.fetch_window(cfg, _extra_cols(offline), end - pd.Timedelta(days=args.lookback_days), end), None
    feature_minutes = preprocess.feature_lookback_minutes(cfg, art.cfg["window"]["window_size"])
    filled = preprocess.fetch_window(cfg, _extra_cols(offline), end - pd.Timedelta(minutes=feature_minutes), end)
    level_history = preprocess.fetch_level_history(
        cfg, offline.level_col, end - pd.Timedelta(days=args.band_window_days + 1.0), end
    )
    return filled, level_history


def _seconds_until_next_slot(interval_seconds: float, lag_seconds: float) -> float:
    """다음 "벽시계 경계 + `lag_seconds`"까지 남은 초.

    `time.sleep(interval_seconds)`를 그냥 쓰면 안 되는 이유: sleep은 사이클이
    *끝난 뒤*부터 세기 시작하므로 실제 주기가 `interval + 사이클 소요시간`이
    되어 매번 조금씩 뒤로 밀린다. 밀린 양이 한 주기에 닿는 순간 버킷 하나를
    통째로 건너뛰고 그 origin의 예측 행이 빈다. 사이클이 10초 걸리면 1분
    주기에서 약 6분마다 1행씩 사라진다. 예외가 아니라 정상 동작이라 로그에
    실패로 남지도 않는다.

    그래서 다음 경계까지만 잔다 — 사이클이 얼마나 걸렸든 항상 같은 초에
    깨어나므로 드리프트가 누적되지 않는다. cron과 같은 타이밍을 얻으면서
    모델·DB 엔진은 프로세스에 그대로 상주시킨다(이 컨테이너는 torch·LightGBM·
    XGBoost·OpenBLAS가 전부 기동 시점에 스레드 풀을 만들어 seccomp/clone3에
    가장 크게 걸리는 서비스라, 매 주기 프로세스를 새로 띄우는 쪽이 더 위험하다).

    "다음 슬롯"은 **지금 이후 가장 가까운** `경계 + lag`다. 예전(HEAD) 식
    `interval - now % interval + lag`는 사이클이 경계를 넘긴 뒤 lag 안에
    끝나면(예: :30에 깨어 40초 걸려 다음 분 :10에 끝남) 이번 분의 :30을
    건너뛰고 다음 분 :30까지 잤다 - 1분 주기에서는 사이클이 lag보다 길어지는
    순간 한 칸씩 빠지므로 여기서 바로잡았다.

    `lag_seconds`는 경계 직후 DB 적재를 기다리는 여유다. 0으로 두고 정확히
    경계에 깨면 그 시각 버킷에 샘플이 아직 없어 origin이 직전 버킷으로
    떨어질 수 있다(run_prod의 window_end 주석 참고).
    """
    now_s = time.time()
    target = (now_s // interval_seconds) * interval_seconds + lag_seconds
    if target <= now_s:
        target += interval_seconds
    return target - now_s


def _persistence_exempt(args) -> tuple[str, ...]:
    """`--persistence-exempt-targets`(쉼표 구분)를 튜플로 파싱. 빈 문자열이면
    빈 튜플(= 아무 target도 예외 없이 persistence 대체 대상)."""
    raw = (args.persistence_exempt_targets or "").strip()
    return tuple(t.strip() for t in raw.split(",") if t.strip())


def _cycle_result_row(result: "analysis.CycleResult") -> dict:
    rec = result.recommendation
    band = result.target_band
    return {
        "origin": result.origin, "level0": result.level0, "lever": result.used_lever,
        "action": rec.get("action"), "delta_lever": rec.get("delta_lever"),
        "achievable": rec.get("achievable"), "note": rec.get("note"),
        # target_band(compute_target_band 결과)도 같이 남긴다 — CSV만 보고도
        # "그 시점 목표범위 대비 실제 레벨이 어디 있었는지"를 재구성할 수 있게
        # (2026-09-11 추가: 백테스트 결과를 그래프로 그릴 때 필요해서 확인함 —
        # 이전엔 action/delta_lever만 있어서 level0을 band와 겹쳐 그릴 수 없었다).
        "band_lower": band.get("lower"), "band_upper": band.get("upper"),
    }


def run_dev_backtest(args) -> pd.DataFrame:
    logger = get_logger("dev", args.log_dir)
    cfg = Config.from_yaml(args.source_cfg)
    cfg.data.db_environment = resolve_source_environment("dev", args.source_db_environment)
    art = load_artifacts(args.stage1_run_dir, device=args.device)
    offline = train.load_offline_artifacts(args.offline_artifacts)
    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0

    # tb_ctr_tnk_rst에 실제로 올라갈 행 모양을 미리 CSV로 보고 싶을 때만
    # upload.py를 불러온다(순수 변환 함수만 씀 - DB 접속정보는 안 건드림,
    # dev 모드가 업로드 자격증명을 로드하지 않는다는 보장은 그대로 유지된다).
    build_target_forecast_rows = None
    if args.tnk_rst_csv:
        import upload  # noqa: E402 - 이 블록 안에서만 필요(위 설명 참고)

        build_target_forecast_rows = upload.build_target_forecast_rows

    origins = pd.date_range(args.backtest_start, args.backtest_end, freq=f"{args.stride_minutes}min")
    logger.info(
        "[dev] 백테스트 시작: %d개 origin (%s ~ %s, %s분 간격, 실시간 대기 없음)",
        len(origins), args.backtest_start, args.backtest_end, args.stride_minutes,
    )

    rows = []
    tnk_rst_rows = []
    for origin in origins:
        try:
            filled, level_history = _fetch_cycle(args, art, cfg, offline, origin)
            result = analysis.run_cycle(
                art, offline, filled, freq_minutes, band_window_days=args.band_window_days,
                band_lower_quantile=args.band_lower_quantile, band_upper_quantile=args.band_upper_quantile,
                search_max_stds=args.search_max_stds, level_history=level_history,
            )
        except Exception as e:  # noqa: BLE001 - 백테스트는 한 origin이 실패해도 계속 진행해야 함
            logger.warning("[dev] %s 건너뜀: %s", origin, e)
            continue
        logger.info(analysis.format_cycle_result(result))
        rows.append(_cycle_result_row(result))

        if args.tnk_rst_csv:
            tnk_rst_rows.extend(build_target_forecast_rows(
                result.origin, result.forecast, result.h7_forecast, offline.level_col,
                result.used_lever, result.recommendation.get("delta_lever"), freq_minutes,
                cfg.data.combine_max_columns,
                observed_at_origin=filled.iloc[-1],
                persistence_max_offset_minutes=args.persistence_max_offset_minutes,
                persistence_exempt_targets=_persistence_exempt(args),
            ))

    out = pd.DataFrame(rows)
    if args.out_csv and len(out):
        out.to_csv(args.out_csv, index=False)
        logger.info("[dev] 결과 저장: %s (%d행)", args.out_csv, len(out))
    if args.tnk_rst_csv:
        # 미리보기에도 PRDCT_VALUE를 넣는다 - 이 컬럼이 prdct_value_from이
        # 가리키는 지평과 같은 값인지는 DB 없이 여기서만 확인할 수 있다.
        tnk_rst_columns = [
            "DSTRB_ID", "RGSTR_TIME",
            *upload.HORIZON_OFFSET_MINUTES.keys(), upload.LEGACY_VALUE_COLUMN,
        ]
        tnk_rst_out = pd.DataFrame(tnk_rst_rows, columns=tnk_rst_columns)
        tnk_rst_out.to_csv(args.tnk_rst_csv, index=False)
        logger.info("[dev] tb_ctr_tnk_rst 업로드 미리보기 저장: %s (%d행, 실제 업로드 없음)", args.tnk_rst_csv, len(tnk_rst_out))
    logger.info("[dev] 완료: %d/%d개 origin 처리됨. DB 업로드는 수행하지 않았습니다.", len(out), len(origins))
    return out


def run_dev_server(args) -> None:
    import upload  # dev 모드는 이 import 자체를 안 타므로 함수 안에서 지역 임포트한다.

    logger = get_logger("dev-server", args.log_dir)
    cfg = Config.from_yaml(args.source_cfg)
    cfg.data.db_environment = resolve_source_environment("dev-server", args.source_db_environment)
    art = load_artifacts(args.stage1_run_dir, device=args.device)
    offline = train.load_offline_artifacts(args.offline_artifacts)
    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0
    freq_delta = pd.Timedelta(cfg.data.freq)

    upload_cfg = upload.load_upload_config(args.upload_connections, "dev-server", args.upload_connection_key)
    engine = upload.build_upload_engine(upload_cfg)
    logger.info(
        "[dev-server] 업로드 대상: %s/%s.%s (PRDCT_VALUE <- %s)",
        upload_cfg.host, upload_cfg.db, upload_cfg.table, upload_cfg.prdct_value_from,
    )

    # prod와 같은 타이밍·격자로 돈다 - dev-server는 "prod 경로가 실제로 도는지"를
    # 확인하는 모드라, 여기만 sleep(interval)이면 드리프트 문제를 여기서 볼 수 없다.
    for i in range(args.cycles):
        cycle_started = time.monotonic()
        now = pd.Timestamp.now()
        window_end = now.floor(cfg.data.freq) + freq_delta  # run_prod의 [격자 고정] 주석 참고
        try:
            filled, level_history = _fetch_cycle(args, art, cfg, offline, window_end)
            result = analysis.run_cycle(
                art, offline, filled, freq_minutes, band_window_days=args.band_window_days,
                band_lower_quantile=args.band_lower_quantile, band_upper_quantile=args.band_upper_quantile,
                search_max_stds=args.search_max_stds, level_history=level_history,
            )
            logger.info(analysis.format_cycle_result(result))
            rows = upload.build_target_forecast_rows(
                result.origin, result.forecast, result.h7_forecast, offline.level_col,
                result.used_lever, result.recommendation.get("delta_lever"), freq_minutes,
                cfg.data.combine_max_columns,
                observed_at_origin=filled.iloc[-1],
                persistence_max_offset_minutes=args.persistence_max_offset_minutes,
                persistence_exempt_targets=_persistence_exempt(args),
                prdct_value_from=upload_cfg.prdct_value_from,
            )
            n_rows = upload.upload_target_forecasts(engine, upload_cfg.table, rows)
            logger.info(
                "[dev-server] 업로드 완료: origin=%s (%d행, %.1f초 소요)",
                result.origin, n_rows, time.monotonic() - cycle_started,
            )
        except Exception:  # noqa: BLE001
            logger.exception("[dev-server] 사이클 실패(%s)", now)
        if i < args.cycles - 1:
            time.sleep(_seconds_until_next_slot(args.interval_seconds, args.cycle_lag_seconds))


def run_prod(args) -> None:
    import upload  # prod 모드에서만 로드 — dev/dev 경로와 업로드 자격증명 로딩을 코드로 분리.

    logger = get_logger("prod", args.log_dir)
    cfg = Config.from_yaml(args.source_cfg)
    cfg.data.db_environment = resolve_source_environment("prod", args.source_db_environment)
    art = load_artifacts(args.stage1_run_dir, device=args.device)
    offline = train.load_offline_artifacts(args.offline_artifacts)
    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0
    freq_delta = pd.Timedelta(cfg.data.freq)
    # 정상일 때 사이클마다 origin이 전진해야 하는 폭. 주기가 모델 freq보다 짧으면
    # (예: 5분 모델을 60초 주기로 돌림) 같은 origin을 여러 번 계산하는 게 정상이라
    # 격자 점검을 끈다(None).
    interval_delta = pd.Timedelta(seconds=args.interval_seconds)
    expected_step = interval_delta if interval_delta >= freq_delta else None

    upload_cfg = upload.load_upload_config(args.upload_connections, "prod", args.upload_connection_key)
    engine = upload.build_upload_engine(upload_cfg)
    logger.info(
        "[prod] %s초 주기(벽시계 경계 +%s초)로 시작합니다. 조회: %s. 업로드 대상: %s/%s.%s (PRDCT_VALUE <- %s)",
        args.interval_seconds, args.cycle_lag_seconds,
        f"단일 {args.lookback_days}일" if args.lookback_days is not None
        else f"분할(입력 {preprocess.feature_lookback_minutes(cfg, art.cfg['window']['window_size']):g}분 + "
             f"{offline.level_col} {args.band_window_days + 1:g}일)",
        upload_cfg.host, upload_cfg.db, upload_cfg.table, upload_cfg.prdct_value_from,
    )

    prev_origin = None
    cycle_count = 0
    while args.max_cycles is None or cycle_count < args.max_cycles:
        cycle_started = time.monotonic()
        now = pd.Timestamp.now()
        # [격자 고정] 조회 구간의 끝을 "지금이 속한 버킷의 끝"으로 못박는다.
        #
        # now를 그대로 넘기면 안 된다. DB 조회는 [start, end)이고(db_source.py의
        # `>= :start AND < :end`), preprocess가 freq로 resample하므로 end의 위치가
        # 마지막 버킷을 가른다(5분 모델 예):
        #   end=10:00:00.15 -> 10:00 버킷(샘플 1개) 생성 -> origin=10:00
        #   end=09:59:59.98 -> 10:00 버킷 없음          -> origin=09:55
        # 즉 경계에 가깝게 깨어날수록 origin이 한 칸씩 튀거나 같은 칸을 두 번
        # 계산한다 — _seconds_until_next_slot으로 타이밍을 정밀하게 맞출수록
        # 이 충돌 확률이 올라가므로, 경계 정렬과 이 floor는 반드시 같이 간다.
        # floor + freq로 두면 now가 버킷 안 어디에 있든 결과가 같다.
        #
        # window_end 자체는 미래 시각이지만 그 구간 데이터가 DB에 없으니 무해하다
        # (resample은 실제 존재하는 데이터까지만 버킷을 만든다).
        window_end = now.floor(cfg.data.freq) + freq_delta
        try:
            filled, level_history = _fetch_cycle(args, art, cfg, offline, window_end)
            result = analysis.run_cycle(
                art, offline, filled, freq_minutes, band_window_days=args.band_window_days,
                band_lower_quantile=args.band_lower_quantile, band_upper_quantile=args.band_upper_quantile,
                search_max_stds=args.search_max_stds, level_history=level_history,
            )
            logger.info(analysis.format_cycle_result(result))
            rows = upload.build_target_forecast_rows(
                result.origin, result.forecast, result.h7_forecast, offline.level_col,
                result.used_lever, result.recommendation.get("delta_lever"), freq_minutes,
                cfg.data.combine_max_columns,
                observed_at_origin=filled.iloc[-1],
                persistence_max_offset_minutes=args.persistence_max_offset_minutes,
                persistence_exempt_targets=_persistence_exempt(args),
                prdct_value_from=upload_cfg.prdct_value_from,
            )
            n_rows = upload.upload_target_forecasts(engine, upload_cfg.table, rows)
            # 소요시간을 같이 남긴다 — 이 값이 interval에 근접하면 다음 경계를
            # 놓치기 시작한다는 뜻이라, 아래 격자 경고가 뜨기 전에 미리 보인다.
            logger.info(
                "[prod] 업로드 완료: origin=%s (%d행, %.1f초 소요)",
                result.origin, n_rows, time.monotonic() - cycle_started,
            )
            # [격자 점검] 정상이라면 origin은 매 사이클 정확히 한 주기만큼 전진한다.
            # 어긋나면 그 사이 origin의 예측 행이 비었다는 뜻이다. 사이클이 주기보다
            # 오래 걸렸거나 DB 적재가 늦어 origin이 직전 버킷으로 떨어진 경우인데,
            # 둘 다 예외가 아니라서 이 경고가 없으면 아무 흔적도 남지 않는다.
            # 채우려면 REPLACE INTO라 재실행으로 덮어쓸 수 있다(upload.upload_target_forecasts).
            if expected_step is not None and prev_origin is not None and result.origin - prev_origin != expected_step:
                logger.warning(
                    "[prod] 격자 어긋남: origin이 %s -> %s (간격 %s, 기대 %s). "
                    "그 사이 구간의 예측이 비었습니다.",
                    prev_origin, result.origin, result.origin - prev_origin, expected_step,
                )
            prev_origin = result.origin
        except Exception:  # noqa: BLE001 - 한 사이클 실패로 스케줄러 전체가 죽으면 안 된다(무인 운영 전제)
            logger.exception("[prod] 사이클 실패(%s) - 다음 주기에 재시도합니다.", now)
        cycle_count += 1
        if args.max_cycles is None or cycle_count < args.max_cycles:
            # 경과시간이 아니라 벽시계 경계를 기준으로 잔다(_seconds_until_next_slot).
            time.sleep(_seconds_until_next_slot(args.interval_seconds, args.cycle_lag_seconds))


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(description="Stage1~3 실시간 추천 스케줄러 (dev/dev-server/prod)")
    # 기본값 prod: 이 스크립트는 무인 운영(cron/서비스)에서 돌아가는 게
    # 기본 용도이므로, --mode를 깜빡 빠뜨려도 dev/dev-server(테스트 경로)가
    # 아니라 실제 운영으로 도는 쪽을 기본으로 둔다 — dev/dev-server를 쓰려면
    # 오히려 명시적으로 --mode를 지정하게 만드는 편이 테스트 실행을 실수로
    # 운영처럼 착각하는 사고를 줄인다(반대 방향 사고인 "실수로 --mode를
    # 안 줬는데 dev로 조용히 돌아서 운영이 안 된 줄 모른다"를 막기 위함).
    parser.add_argument("--mode", default="prod", choices=["dev", "dev-server", "prod"])
    parser.add_argument("--stage1-run-dir", required=True, help="Stage1 학습 산출물 디렉터리 (예: ./runs/gu_db_noq8_h6)")
    parser.add_argument("--source-cfg", required=True, help="원본 데이터 config (예: configs/gu_db_noq8_h6.yaml)")
    parser.add_argument("--offline-artifacts", required=True, help="train.py가 저장한 .joblib 경로")
    parser.add_argument("--band-window-days", type=float, default=21.0)
    parser.add_argument(
        "--band-lower-quantile", type=float, default=0.25,
        help="목표범위 하한 분위수(recommend.compute_target_band, 기본 0.25=Q1)",
    )
    parser.add_argument(
        "--band-upper-quantile", type=float, default=0.75,
        help="목표범위 상한 분위수(기본 0.75=Q3, 넓히면(예: 0.85) 개입 빈도가 줄어든다)",
    )
    parser.add_argument(
        "--search-max-stds", type=float, default=10.0,
        help="레버 조정 탐색 상한 = 그 레버 표준편차 * 이 값(analysis.run_cycle 참고, 기본 10배)",
    )
    parser.add_argument("--device", default="cpu")
    # 짧은 offset 컬럼을 모델 예측 대신 origin 실측값(persistence)으로 채운다 -
    # 2026-09-28 1분 모델 실측 근거: 1분 시점은 23개 target 중 2개만 모델이
    # persistence를 이겼다(docs/DEVNOTES.md 참고). 0으로 주면 이 대체를 끈다.
    parser.add_argument(
        "--persistence-max-offset-minutes", type=float, default=1.0,
        help="이 분 이하 horizon 컬럼(예: VALUE_1min)은 모델 예측 대신 origin 실측값을 올린다(0=끄기, 기본 1)",
    )
    parser.add_argument(
        "--persistence-exempt-targets", default="H3",
        help="위 대체에서 제외할 target(쉼표 구분) - 기본 H3(1분 시점에도 skill이 일관되게 양수였음)",
    )
    parser.add_argument("--source-db-environment", default=None, help="prod 모드에서는 지정 불가(항상 prod 고정)")
    parser.add_argument(
        "--lookback-days", type=float, default=None,
        help="생략하면 조회 분할(전체 태그는 Stage1 입력에 필요한 만큼, 목표범위용 수위만 "
        "band-window-days+1일). 주면 예전처럼 모든 태그를 이 일수만큼 한 번에 받는다(되돌리기용)",
    )
    parser.add_argument("--log-dir", default="logs", help="일별 실행 로그를 저장할 디렉터리(logging_setup.py, 자정마다 자동 회전)")

    # dev(백테스트) 전용
    parser.add_argument("--backtest-start", help="dev 모드 필수 (예: 2025-04-01)")
    parser.add_argument("--backtest-end", help="dev 모드 필수")
    parser.add_argument("--stride-minutes", type=float, default=60.0, help="origin 간격(분)")
    parser.add_argument("--out-csv", help="dev 모드 결과를 저장할 CSV 경로(선택)")
    parser.add_argument(
        "--tnk-rst-csv",
        help="dev 모드에서 tb_ctr_tnk_rst에 업로드'될' 행(DSTRB_ID/RGSTR_TIME/VALUE_1min..VALUE_30min)을 "
        "실제로 DB에 쓰지 않고 CSV로만 저장(선택) - upload.build_target_forecast_rows와 "
        "정확히 같은 변환을 실제 DB 접속 없이 미리 확인하는 용도.",
    )

    # dev-server/prod(업로드) 공용
    parser.add_argument("--upload-connections", default="configs/db_upload_connections.json")
    parser.add_argument("--upload-connection-key", default="maria-ems-db-gs")
    parser.add_argument("--interval-seconds", type=float, default=None, help="dev-server 기본 60초, prod 기본 60초(1분, 2026-09-28 변경 - 그전엔 300초)")
    parser.add_argument(
        "--cycle-lag-seconds", type=float, default=30.0,
        help="벽시계 경계에서 이만큼 늦게 깨어난다(기본 30초). 경계 직후에는 그 시각 버킷에 "
        "원본 샘플이 아직 DB에 없을 수 있어, 그대로 깨면 origin이 직전 버킷으로 떨어진다. "
        "로그에 '격자 어긋남'이 반복되면 늘린다(적재가 느린 현장). --interval-seconds 보다 작아야 한다.",
    )

    # dev-server 전용
    parser.add_argument("--cycles", type=int, default=1, help="dev-server에서 실행할 사이클 수")
    # prod 전용
    parser.add_argument("--max-cycles", type=int, default=None, help="prod 테스트용(생략하면 무한 루프)")

    return parser


def _check_cycle_timing(parser, args) -> None:
    # lag가 주기 이상이면 "다음 슬롯"이 한 주기 뒤로 넘어가 매번 한 칸씩 건너뛴다.
    if not (0 <= args.cycle_lag_seconds < args.interval_seconds):
        parser.error(
            f"--cycle-lag-seconds({args.cycle_lag_seconds})는 0 이상, "
            f"--interval-seconds({args.interval_seconds}) 미만이어야 합니다."
        )


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == "dev":
        if not (args.backtest_start and args.backtest_end):
            parser.error("--mode dev는 --backtest-start/--backtest-end가 필요합니다.")
        run_dev_backtest(args)
    elif args.mode == "dev-server":
        args.interval_seconds = 60.0 if args.interval_seconds is None else args.interval_seconds
        _check_cycle_timing(parser, args)
        run_dev_server(args)
    elif args.mode == "prod":
        # 2026-09-28: 개발사 요구로 운영 분석 주기를 5분(300초) -> 1분(60초)으로
        # 변경(`configs/gu_db_1min_h30.yaml`과 같이 씀). 한 사이클(DB 배치조회 ->
        # Stage1 추론 -> Stage2/3 -> 업로드)이 60초 안에 끝나는지는 실제 운영
        # 서버에서 확인해야 한다 - 넘치면 `--interval-seconds`로 늘릴 것.
        args.interval_seconds = 60.0 if args.interval_seconds is None else args.interval_seconds
        _check_cycle_timing(parser, args)
        run_prod(args)


if __name__ == "__main__":
    main()
