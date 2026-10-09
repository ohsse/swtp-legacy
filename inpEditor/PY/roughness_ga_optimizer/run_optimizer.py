from __future__ import annotations

import argparse
import json
import logging
import math
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from db import DbConfig, DbManager
from groups import load_inp_tag_groups, load_year_groups
from models import (
    attach_observed_values,
    attach_observed_values_by_result_time,
    attach_demand_values,
    build_inp_path,
    get_next_revision_no,
    get_optimization_request,
    insert_inp_revision_record,
    load_analysis_pressure_points_from_option_snap,
    load_demand_points_from_option_snap,
    load_visual_points,
    make_revision_stored_name,
    resolve_revision_inp_path,
    resolve_observation_timestamp,
    update_current_revision,
)
from opt_history import OptimizationHistoryUpdater
from optimizer import (
    GaConfig,
    MultiplierConfig,
    RoughnessConfig,
    RoughnessGaOptimizer,
    flow_cmh_to_si,
    write_inp,
)


logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def parse_optional_timestamp(value) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return parse_timestamp(text)


def parse_comparison_times(value) -> list[int]:
    if not value:
        return []
    return sorted(int(time_sec) for time_sec in value)


def setup_logging(output_dir: Path, run_id: str) -> None:
    log_path = output_dir / f"optimizer_{run_id}.log"
    warnings.filterwarnings("ignore", message="Not all curves were used.*")
    logging.getLogger("wntr.epanet.io").setLevel(logging.ERROR)
    logging.getLogger("wntr.epanet.toolkit").setLevel(logging.ERROR)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        ],
    )
    logger.info("log_file=%s", log_path.resolve())


def build_pressure_flow_comparison(
    baseline_pressure: pd.DataFrame,
    optimized_pressure: pd.DataFrame,
    baseline_flow: pd.DataFrame,
    optimized_flow: pd.DataFrame,
) -> pd.DataFrame:
    pressure = _merge_metric_comparison(
        baseline_pressure,
        optimized_pressure,
        id_column="node_id",
        measured_column="실측압력",
        baseline_column="기존압력분석",
        optimized_column="GA후압력분석",
        baseline_error_column="기존압력오차율(%)",
        optimized_error_column="GA압력오차율(%)",
    )
    flow = _merge_metric_comparison(
        baseline_flow,
        optimized_flow,
        id_column="link_id",
        measured_column="실측유량",
        baseline_column="기존유량분석",
        optimized_column="GA후유량분석",
        baseline_error_column="기존유량오차율(%)",
        optimized_error_column="GA유량오차율(%)",
    )

    if pressure.empty:
        merged = flow
    elif flow.empty:
        merged = pressure
    else:
        merge_keys = ["지점명"]
        if "해석시간(초)" in pressure.columns or "해석시간(초)" in flow.columns:
            merge_keys = ["해석시간(초)", *merge_keys]
        merged = pressure.merge(flow, on=merge_keys, how="outer")

    ordered_columns = [
        "해석시간(초)",
        "지점명",
        "실측압력",
        "기존압력분석",
        "GA후압력분석",
        "기존압력오차율(%)",
        "GA압력오차율(%)",
        "실측유량",
        "기존유량분석",
        "GA후유량분석",
        "기존유량오차율(%)",
        "GA유량오차율(%)",
    ]
    return merged[[column for column in ordered_columns if column in merged.columns]]


def _merge_metric_comparison(
    baseline: pd.DataFrame,
    optimized: pd.DataFrame,
    id_column: str,
    measured_column: str,
    baseline_column: str,
    optimized_column: str,
    baseline_error_column: str,
    optimized_error_column: str,
) -> pd.DataFrame:
    if baseline.empty or optimized.empty:
        return pd.DataFrame()

    key_columns = ["location_name", id_column]
    if "analysis_time_sec" in baseline.columns or "analysis_time_sec" in optimized.columns:
        key_columns = ["analysis_time_sec", *key_columns]
    baseline_cols = key_columns + ["measured", "simulated", "error_rate_pct"]
    optimized_cols = key_columns + ["simulated", "error_rate_pct"]

    merged = baseline[baseline_cols].merge(
        optimized[optimized_cols],
        on=key_columns,
        how="outer",
        suffixes=("_baseline", "_optimized"),
    )
    return (
        merged.rename(
            columns={
                "location_name": "지점명",
                "measured": measured_column,
                "simulated_baseline": baseline_column,
                "simulated_optimized": optimized_column,
                "error_rate_pct_baseline": baseline_error_column,
                "error_rate_pct_optimized": optimized_error_column,
            }
        )
        .rename(columns={"analysis_time_sec": "해석시간(초)"})
        .drop(columns=[id_column], errors="ignore")
    )

def write_csv_safely(df: pd.DataFrame, path: Path) -> Path:
    """
    Write a CSV file.

    On Windows, Excel often locks an opened CSV. In that case, keep the run from
    failing by writing a timestamped fallback file.
    """

    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        df.to_csv(fallback_path, index=False, encoding="utf-8-sig")
        logger.warning(
            "CSV file is locked, so wrote fallback file. locked=%s fallback=%s",
            path,
            fallback_path,
        )
        return fallback_path


def sanitize_json_value(value):
    if isinstance(value, dict):
        return {key: sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if pd.isna(value):
        return None
    return value


def make_result_snap_items(
    target_ts: datetime,
    pressure_errors: pd.DataFrame,
    flow_errors: pd.DataFrame,
    comparison_times_sec: list[int],
) -> list[dict]:
    first_result_time = min(comparison_times_sec) if comparison_times_sec else None
    items: list[dict] = []
    items.extend(
        make_metric_snap_items(
            target_ts,
            pressure_errors,
            first_result_time,
            data_type="PRESSURE",
        )
    )
    items.extend(
        make_metric_snap_items(
            target_ts,
            flow_errors,
            first_result_time,
            data_type="FLOW",
        )
    )
    return sanitize_json_value(items)


def make_metric_snap_items(
    target_ts: datetime,
    df: pd.DataFrame,
    first_result_time: int | None,
    data_type: str,
) -> list[dict]:
    if df.empty:
        return []

    items = []
    for row in df.to_dict(orient="records"):
        analysis_time_sec = row.get("analysis_time_sec")
        measure_dttm = target_ts
        if first_result_time is not None and analysis_time_sec is not None:
            measure_dttm = target_ts + timedelta(
                seconds=int(analysis_time_sec) - int(first_result_time)
            )
        items.append(
            {
                "measureDttm": measure_dttm.isoformat(sep=" "),
                "pointNm": row.get("location_name"),
                "dataType": data_type,
                "measureValue": row.get("measured"),
                "analValue": row.get("simulated"),
                "errorRate": row.get("error_rate_pct"),
            }
        )
    return items


def make_result_snapshot(
    target_ts: datetime,
    pressure_errors: pd.DataFrame,
    flow_errors: pd.DataFrame,
    summary: dict,
    comparison_times_sec: list[int],
) -> list[dict]:
    del summary
    return make_result_snap_items(
        target_ts,
        pressure_errors,
        flow_errors,
        comparison_times_sec,
    )


def build_demand_overrides(points) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for point in points:
        if point.observed_value is None:
            continue
        overrides[str(point.node_id)] = flow_cmh_to_si(float(point.observed_value))
    return overrides


def get_publish_optimized_inp_path(
    config: dict,
    opt_request,
    source_inp_info,
    source_inp_path: str,
) -> str:
    publish_config = config.get("publish_optimized_inp") or {}
    if not publish_config or not bool(publish_config.get("enabled", False)):
        return ""

    publish_dir = publish_config.get("dir") or publish_config.get("output_dir")
    if not publish_dir:
        raise ValueError("publish_optimized_inp.enabled=true 이면 dir 값이 필요합니다.")

    file_name = (
        publish_config.get("file_name")
        or (opt_request.original_file_name if opt_request else "")
        or (source_inp_info.original_file_name if source_inp_info else "")
        or Path(source_inp_path).name
        or "optimized.inp"
    )
    safe_file_name = Path(str(file_name)).name
    if not safe_file_name.lower().endswith(".inp"):
        safe_file_name = f"{safe_file_name}.inp"

    target_path = Path(publish_dir) / safe_file_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return str(target_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--hist-id", required=False)
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = Path(config.get("output_dir", "outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(output_dir, run_id)
    logger.info("run_id=%s", run_id)

    hist_id = args.hist_id or config.get("hist_id")
    if not hist_id:
        raise ValueError("hist_id가 필요합니다. inp_file_opt_h 이력 기준으로만 최적화를 실행할 수 있습니다.")

    db_config = DbConfig(**config["db"])
    db = DbManager(db_config)
    history = OptimizationHistoryUpdater(db, hist_id)
    opt_request = None
    try:
        history.mark_running(
            run_id=run_id,
            total_generation=int(config.get("ga", {}).get("generations", GaConfig().generations)),
        )

        opt_request = get_optimization_request(db, hist_id)
        inp_file_id = opt_request.inp_file_id
        inp_path = resolve_revision_inp_path(
            db=db,
            inp_file_id=opt_request.inp_file_id,
            rev_no=opt_request.prev_rev_no,
            inp_base_dir=config["inp_base_dir"],
        )
        logger.info(
            "loaded_optimization_request hist_id=%s inp_file_id=%s prev_rev_no=%s",
            hist_id,
            inp_file_id,
            opt_request.prev_rev_no,
        )
        logger.info("source_inp_path=%s", inp_path)
        analysis_points = load_analysis_pressure_points_from_option_snap(
            opt_request.option_snap,
            only_analysis=True,
        )
        demand_points = load_demand_points_from_option_snap(
            opt_request.option_snap,
            only_analysis=True,
        )
        logger.info(
            "loaded_option_snap_anal_mapping pressure=%s demand=%s hist_id=%s",
            len(analysis_points),
            len(demand_points),
            hist_id,
        )
        visual_points = load_visual_points(
            db,
            inp_file_id=inp_file_id,
            only_display=True,
        )
        if not analysis_points:
            raise ValueError(f"분석에 사용할 압력 매핑 정보가 없습니다. inp_file_id={inp_file_id}")
        logger.info(
            "mapping_counts analysis_pressure=%s demand_flow=%s visual=%s",
            len(analysis_points),
            len(demand_points),
            len(visual_points),
        )
        requested_ts = parse_optional_timestamp(config.get("target_timestamp"))
        comparison_times_sec = parse_comparison_times(config.get("comparison_times_sec"))
        target_ts = resolve_observation_timestamp(
            db,
            analysis_points,
            requested_ts,
            result_times_sec=comparison_times_sec,
        )
        if target_ts is None:
            raise ValueError("TB_RAWDATA에서 실측 기준 시각을 찾지 못했습니다.")
        logger.info("requested_target_timestamp=%s", config.get("target_timestamp"))
        logger.info("resolved_target_timestamp=%s", target_ts)
        if comparison_times_sec:
            logger.info("comparison_times_sec=%s", comparison_times_sec)
            analysis_points = attach_observed_values_by_result_time(
                db,
                analysis_points,
                target_ts,
                comparison_times_sec,
                fallback_sec=int(config.get("fallback_sec", 600)),
            )
            visual_points = attach_observed_values_by_result_time(
                db,
                visual_points,
                target_ts,
                comparison_times_sec,
                fallback_sec=int(config.get("fallback_sec", 600)),
            )
        else:
            analysis_points = attach_observed_values(
                db,
                analysis_points,
                target_ts,
                fallback_sec=int(config.get("fallback_sec", 600)),
            )
            visual_points = attach_observed_values(
                db,
                visual_points,
                target_ts,
                fallback_sec=int(config.get("fallback_sec", 600)),
            )
        demand_points = attach_demand_values(
            db,
            demand_points,
            target_ts,
            fallback_sec=int(config.get("fallback_sec", 600)),
        )
        demand_overrides = build_demand_overrides(demand_points)
        pressure_compare_scale = float(config.get("pressure_compare_scale", 0.1))
        pressure_value_count = (
            sum(
                len(point.observed_pressure_by_time or {})
                for point in analysis_points
            )
            if comparison_times_sec
            else sum(1 for point in analysis_points if point.observed_pressure is not None)
        )
        flow_value_count = (
            sum(1 for point in demand_points if point.observed_value is not None)
        )
        logger.info(
            "analysis_points=%s pressure_values=%s demand_points=%s demand_values=%s demand_override_count=%s visual_points=%s",
            len(analysis_points),
            pressure_value_count,
            len(demand_points),
            flow_value_count,
            len(demand_overrides),
            len(visual_points),
        )

        if config.get("pipe_year_csv"):
            groups = load_year_groups(config["pipe_year_csv"])
        else:
            groups = load_inp_tag_groups(inp_path)
        logger.info(
            "roughness_groups=%s tagged_pipes=%s",
            len(groups),
            sum(len(pipe_ids) for pipe_ids in groups.values()),
        )
        optimizer = RoughnessGaOptimizer(
            inp_path=inp_path,
            groups=groups,
            observations=analysis_points,
            multiplier_config=MultiplierConfig(**config.get("multiplier", {})),
            roughness_config=RoughnessConfig(**config.get("roughness", {})),
            ga_config=GaConfig(**config.get("ga", {})),
            pressure_compare_scale=pressure_compare_scale,
            objective_metric=config.get("objective_metric", "rmse"),
            comparison_times_sec=comparison_times_sec,
            demand_overrides_si=demand_overrides,
            progress_callback=history.update_generation,
        )

        baseline_rmse = optimizer.baseline_rmse()
        logger.info("baseline_rmse=%.6f", baseline_rmse)
        baseline_pressure_errors, baseline_flow_errors = optimizer.build_error_tables(
            optimizer.wn_base,
            observations=visual_points,
        )

        best_multipliers, best_rmse = optimizer.run()
        final_wn = optimizer.final_network()
        improvement = baseline_rmse - best_rmse
        improvement_pct = 0.0 if baseline_rmse == 0 else improvement / baseline_rmse * 100.0

        optimized_inp_file_id = None
        optimized_rev_no = None
        optimized_inp_path = ""
        published_optimized_inp_path = ""
        should_write_optimized_inp = bool(config.get("write_optimized_inp", True)) or bool(hist_id)
        if should_write_optimized_inp and opt_request:
            optimized_rev_no = get_next_revision_no(db, opt_request.inp_file_id)
            stored_name = make_revision_stored_name(opt_request.inp_file_id, optimized_rev_no)
            optimized_inp_path = build_inp_path(
                config.get("optimized_inp_dir", config["inp_base_dir"]),
                stored_name,
            )
            write_inp(final_wn, optimized_inp_path)
            insert_inp_revision_record(
                db=db,
                inp_file_id=opt_request.inp_file_id,
                rev_no=optimized_rev_no,
                stored_file_name=stored_name,
                file_path=optimized_inp_path,
                work_type="OPTIMIZE",
            )
            logger.info(
                "registered_optimized_revision inp_file_id=%s rev_no=%s stored_name=%s",
                opt_request.inp_file_id,
                optimized_rev_no,
                stored_name,
            )
            update_current_revision(db, opt_request.inp_file_id, optimized_rev_no)
            db.commit()
            optimized_inp_file_id = opt_request.inp_file_id
        elif should_write_optimized_inp:
            optimized_inp_path = str(output_dir / "optimized.inp")
            write_inp(final_wn, optimized_inp_path)
        else:
            logger.info("write_optimized_inp=false; optimized INP file was not written.")

        published_optimized_inp_path = get_publish_optimized_inp_path(
            config,
            opt_request=opt_request,
            source_inp_info=None,
            source_inp_path=inp_path,
        )
        if published_optimized_inp_path:
            write_inp(final_wn, published_optimized_inp_path)
            logger.info("published_optimized_inp_path=%s", published_optimized_inp_path)

        pressure_errors, flow_errors = optimizer.build_error_tables(
            final_wn,
            observations=visual_points,
        )
        pipe_change_path = write_csv_safely(
            optimizer.build_pipe_change_table(),
            output_dir / f"관로별_C값_변경_{run_id}.csv",
        )
        comparison_path = write_csv_safely(
            build_pressure_flow_comparison(
                baseline_pressure_errors,
                pressure_errors,
                baseline_flow_errors,
                flow_errors,
            ),
            output_dir / f"압력_비교결과_{run_id}.csv",
        )
        logger.info("pipe_change_csv=%s", pipe_change_path)
        logger.info("comparison_csv=%s", comparison_path)

        prev_result_snap = make_result_snapshot(
            target_ts=target_ts,
            pressure_errors=baseline_pressure_errors,
            flow_errors=baseline_flow_errors,
            comparison_times_sec=comparison_times_sec,
            summary={
                "hist_id": hist_id,
                "inp_file_id": inp_file_id,
                "inp_file_name": opt_request.original_file_name if opt_request else "",
                "prev_rev_no": opt_request.prev_rev_no if opt_request else None,
                "rmse": baseline_rmse,
                "comparison_times_sec": comparison_times_sec,
                "analysis_pressure_count": len(analysis_points),
                "demand_override_count": len(demand_overrides),
                "visual_point_count": len(visual_points),
            },
        )
        result_snap = make_result_snapshot(
            target_ts=target_ts,
            pressure_errors=pressure_errors,
            flow_errors=flow_errors,
            comparison_times_sec=comparison_times_sec,
            summary={
                "hist_id": hist_id,
                "inp_file_id": inp_file_id,
                "inp_file_name": opt_request.original_file_name if opt_request else "",
                "prev_rev_no": opt_request.prev_rev_no if opt_request else None,
                "rev_no": optimized_rev_no,
                "rmse": best_rmse,
                "improvement": improvement,
                "improvement_pct": improvement_pct,
                "comparison_times_sec": comparison_times_sec,
                "optimized_inp_path": optimized_inp_path,
                "published_optimized_inp_path": published_optimized_inp_path,
                "analysis_pressure_count": len(analysis_points),
                "demand_override_count": len(demand_overrides),
                "visual_point_count": len(visual_points),
            },
        )
        history.mark_complete(
            rev_no=optimized_rev_no,
            prev_result_snap=prev_result_snap,
            result_snap=result_snap,
        )

        print(f"baseline_rmse={baseline_rmse:.6f}")
        print(f"best_rmse={best_rmse:.6f}")
        print(f"improvement={improvement:.6f}")
        print(f"improvement_pct={improvement_pct:.2f}")
        print(
            "best_multipliers="
            + json.dumps(best_multipliers, ensure_ascii=False, sort_keys=True)
        )
        print(f"analysis_pressure_count={len(analysis_points)}")
        print(f"demand_override_count={len(demand_overrides)}")
        print(f"visual_point_count={len(visual_points)}")
        print(f"optimized_inp_file_id={optimized_inp_file_id or ''}")
        print(f"optimized_rev_no={optimized_rev_no if optimized_rev_no is not None else ''}")
        print(f"optimized_inp_path={optimized_inp_path}")
        print(f"published_optimized_inp_path={published_optimized_inp_path}")
        print(f"run_id={run_id}")
        print(f"outputs={output_dir.resolve()}")
        logger.info("optimized_inp_path=%s", optimized_inp_path)
        logger.info("published_optimized_inp_path=%s", published_optimized_inp_path)
        logger.info("outputs=%s", output_dir.resolve())
    except Exception as exc:
        logger.exception("optimizer_failed")
        history.mark_error(exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
