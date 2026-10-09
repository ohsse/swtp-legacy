"""Stage2(H7 예측 정확도) + Stage3(추천 제어 시뮬레이션 목표치 달성률) 평가
CLI - 2026-09-11 요구사항 3번(H7 예측 정확도)/4번(목표치 달성률)에 대응한다.

`schedule.py --mode dev`와 같은 원리(실시간 대기 없이 과거 구간을 origin별로
훑는 백테스트)지만, 결과 CSV 저장에 그치지 않고 각 사이클의 실제 이후 H7
관측치까지 같이 받아서 `analysis.h7_forecast_accuracy`(Stage2)와
`analysis.target_achievement_rate`(Stage3)를 계산해 화면에 바로 보여준다.

DB/모델 파일이 필요해 단위테스트 대상은 아니다(schedule.py의 run_dev_backtest
와 같은 이유) - 로직 자체(`analysis.h7_forecast_accuracy`/
`target_achievement_rate`)는 `tests/test_scripts_analysis.py`에서 합성
데이터로 이미 검증한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import analysis  # noqa: E402
import preprocess  # noqa: E402
import train  # noqa: E402
from deepems.config import Config  # noqa: E402
from deepems.infer import load_artifacts  # noqa: E402
from logging_setup import get_logger  # noqa: E402
from schedule import _extra_cols, _lookback_days, resolve_source_environment  # noqa: E402


def run_eval(args) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    logger = get_logger("eval", args.log_dir)
    cfg = Config.from_yaml(args.source_cfg)
    cfg.data.db_environment = resolve_source_environment("dev", args.source_db_environment)
    art = load_artifacts(args.stage1_run_dir, device=args.device)
    offline = train.load_offline_artifacts(args.offline_artifacts)
    freq_minutes = pd.Timedelta(cfg.data.freq).total_seconds() / 60.0
    lookback = _lookback_days(args, art, cfg)
    horizon = art.cfg["window"]["horizon"]
    extra_cols = _extra_cols(offline)

    origins = pd.date_range(args.backtest_start, args.backtest_end, freq=f"{args.stride_minutes}min")
    logger.info(
        "[eval] Stage2/3 평가 시작: %d개 origin (%s ~ %s, %s분 간격)",
        len(origins), args.backtest_start, args.backtest_end, args.stride_minutes,
    )

    rows, results, actuals = [], [], []
    for origin in origins:
        try:
            filled = preprocess.fetch_window(cfg, extra_cols, origin - pd.Timedelta(days=lookback), origin)
            result = analysis.run_cycle(
                art, offline, filled, freq_minutes, band_window_days=args.band_window_days,
                band_lower_quantile=args.band_lower_quantile, band_upper_quantile=args.band_upper_quantile,
                search_max_stds=args.search_max_stds,
            )
            # h7_forecast_accuracy가 필요로 하는 "이 origin 이후 실제 H7"을
            # origin~origin+horizon*freq 구간으로 별도 조회한다(백테스트라
            # 이미 과거 구간이라 실측값이 존재함). fetch_window(origin, end)가
            # 돌려주는 구간이 [origin, end)에 더 가깝게 한 스텝 짧게 나와서
            # (2026-09-11 실측: horizon*freq만큼 요청했는데 정확히 horizon개만
            # 나오고 origin 자신의 행이 그중 하나를 차지함) horizon+1스텝을
            # 요청해 origin 행을 버리고도 정확히 horizon개가 남게 한다.
            future_end = origin + pd.Timedelta(minutes=(horizon + 1) * freq_minutes)
            future = preprocess.fetch_window(cfg, extra_cols, origin, future_end)
            actual_h7 = future[offline.level_col].iloc[1 : horizon + 1]  # origin 시점 자신은 제외
        except Exception as e:  # noqa: BLE001 - 평가는 한 origin이 실패해도 계속 진행해야 함
            logger.warning("[eval] %s 건너뜀: %s", origin, e)
            continue
        results.append(result)
        actuals.append(actual_h7)
        rows.append({
            "origin": result.origin, "level0": result.level0, "lever": result.used_lever,
            "action": result.recommendation.get("action"), "achievable": result.recommendation.get("achievable"),
        })

    backtest_df = pd.DataFrame(rows)
    h7_report = analysis.h7_forecast_accuracy(results, actuals)
    achievement = analysis.target_achievement_rate(backtest_df)

    logger.info("[eval] %d/%d개 origin 처리됨.", len(rows), len(origins))
    print("\n===== Stage2: H7 예측 정확도 =====")
    print(h7_report.to_string(index=False) if len(h7_report) else "(집계할 사이클 없음)")
    print("\n===== Stage3: 목표치 달성률 =====")
    print(f"n={achievement['n']}, achieved={achievement['achieved']}, rate={achievement['achievement_rate']:.4f}")

    if args.out_csv and len(backtest_df):
        backtest_df.to_csv(args.out_csv, index=False)
        logger.info("[eval] 백테스트 결과 저장: %s", args.out_csv)
    if args.h7_report_csv and len(h7_report):
        h7_report.to_csv(args.h7_report_csv, index=False)
        logger.info("[eval] H7 정확도 리포트 저장: %s", args.h7_report_csv)

    return backtest_df, h7_report, achievement


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Stage2(H7 정확도) + Stage3(목표치 달성률) 백테스트 평가")
    parser.add_argument("--stage1-run-dir", required=True, help="예: ./runs/gu_db_noq8_h6")
    parser.add_argument("--source-cfg", required=True, help="예: configs/gu_db_noq8_h6.yaml")
    parser.add_argument("--offline-artifacts", required=True, help="train.py가 저장한 .joblib 경로")
    parser.add_argument("--backtest-start", required=True)
    parser.add_argument("--backtest-end", required=True)
    parser.add_argument("--stride-minutes", type=int, default=30)
    parser.add_argument("--band-window-days", type=float, default=21.0)
    parser.add_argument("--band-lower-quantile", type=float, default=0.25)
    parser.add_argument("--band-upper-quantile", type=float, default=0.75)
    parser.add_argument("--search-max-stds", type=float, default=10.0)
    parser.add_argument("--source-db-environment", default=None)
    parser.add_argument("--lookback-days", type=float, default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--out-csv", default=None, help="사이클별 backtest 결과 저장 경로(선택)")
    parser.add_argument("--h7-report-csv", default=None, help="H7 정확도 리포트 저장 경로(선택)")
    args = parser.parse_args(argv)

    run_eval(args)


if __name__ == "__main__":
    main()
