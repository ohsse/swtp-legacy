from __future__ import annotations

import argparse
import json
import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import wntr
from wntr.epanet.util import FlowUnits, HydParam, from_si, to_si

from config_path import resolve_config_path
from db import DbConfig, DbManager
from models import (
    ObservationPoint,
    attach_observed_values,
    build_inp_path,
    load_observation_points,
    resolve_observation_timestamp,
)
from optimizer import make_wntr_readable_inp, run_epanet


logger = logging.getLogger(__name__)


@dataclass
class MonitoringFile:
    inp_file_id: str
    original_file_name: str
    rev_no: int
    stored_file_name: str
    inp_path: str


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def parse_timestamp(value) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)


def setup_logging(output_dir: Path, run_id: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"monitor_{run_id}.log"
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


def load_monitoring_files(db: DbManager, inp_base_dir: str) -> list[MonitoringFile]:
    sql = """
        SELECT
            m.inp_file_id,
            m.orgnl_file_nm,
            m.curr_rev_no,
            r.stor_file_nm
        FROM inp_file_m m
        JOIN inp_file_rev_h r
          ON r.inp_file_id = m.inp_file_id
         AND r.rev_no = m.curr_rev_no
        WHERE COALESCE(m.mntr_yn, 'N') = 'Y'
        ORDER BY m.rgst_dttm, m.inp_file_id
    """
    rows = db.fetchall(sql)
    files: list[MonitoringFile] = []
    for row in rows:
        stored_file_name = row.get("stor_file_nm") or ""
        inp_path = build_inp_path(inp_base_dir, stored_file_name)
        files.append(
            MonitoringFile(
                inp_file_id=row["inp_file_id"],
                original_file_name=row.get("orgnl_file_nm") or "",
                rev_no=int(row["curr_rev_no"]),
                stored_file_name=stored_file_name,
                inp_path=inp_path,
            )
        )
    return files


def load_network(inp_path: str) -> wntr.network.WaterNetworkModel:
    readable_path = make_wntr_readable_inp(inp_path)
    wn = wntr.network.WaterNetworkModel(readable_path)
    wn.options.time.duration = 0
    return wn


def apply_measured_flow_as_demand(
    wn: wntr.network.WaterNetworkModel,
    points: list[ObservationPoint],
    raw_flow_unit: FlowUnits,
) -> list[str]:
    skipped: list[str] = []
    for point in points:
        if point.observed_flow is None:
            continue
        if not point.pressure_node_id:
            skipped.append(f"{point.location_name}: junction_id empty")
            continue
        if point.pressure_node_id not in wn.junction_name_list:
            skipped.append(f"{point.location_name}: junction not found ({point.pressure_node_id})")
            continue

        demand_si = to_si(raw_flow_unit, float(point.observed_flow), HydParam.Flow)
        junction = wn.get_node(point.pressure_node_id)
        demand_list = getattr(junction, "demand_timeseries_list", None)
        if demand_list and len(demand_list) > 0:
            demand_list[0].base_value = demand_si
        else:
            junction.add_demand(base=demand_si, pattern=None, category="MeasuredFlow")
    return skipped


def error_rate(measured: Optional[float], simulated: Optional[float]) -> Optional[float]:
    if measured is None or simulated is None:
        return None
    if float(measured) == 0.0:
        return None
    return (float(simulated) - float(measured)) / float(measured) * 100.0


def build_monitor_rows(
    monitoring_file: MonitoringFile,
    ts: datetime,
    points: list[ObservationPoint],
    results,
    pressure_compare_scale: float,
    raw_flow_unit: FlowUnits,
) -> list[tuple]:
    pressure_row = results.node["pressure"].iloc[0]
    flow_row = results.link["flowrate"].iloc[0]

    rows: list[tuple] = []
    for point in points:
        if point.pressure_node_id:
            simulated_pressure = None
            if point.pressure_node_id in pressure_row.index:
                simulated_pressure = float(pressure_row[point.pressure_node_id]) * pressure_compare_scale
            rows.append(
                (
                    monitoring_file.inp_file_id,
                    monitoring_file.rev_no,
                    ts,
                    point.mapping_id,
                    point.location_name,
                    point.pressure_node_id,
                    point.flow_link_id,
                    "PRESSURE",
                    point.observed_pressure,
                    simulated_pressure,
                    error_rate(point.observed_pressure, simulated_pressure),
                )
            )

        if point.flow_link_id:
            simulated_flow = None
            if point.flow_link_id in flow_row.index:
                simulated_flow = from_si(
                    raw_flow_unit,
                    float(flow_row[point.flow_link_id]),
                    HydParam.Flow,
                )
            rows.append(
                (
                    monitoring_file.inp_file_id,
                    monitoring_file.rev_no,
                    ts,
                    point.mapping_id,
                    point.location_name,
                    point.pressure_node_id,
                    point.flow_link_id,
                    "FLOW",
                    point.observed_flow,
                    simulated_flow,
                    error_rate(point.observed_flow, simulated_flow),
                )
            )
    return rows


def insert_monitor_rows(db: DbManager, rows: list[tuple]) -> int:
    if not rows:
        return 0
    sql = """
        INSERT INTO inp_motrn_i (
            inp_file_id,
            rev_no,
            measure_dttm,
            mapping_id,
            point_nm,
            junction_id,
            pipe_id,
            data_type,
            measure_value,
            anal_value,
            error_rate
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    return db.executemany(sql, rows)


def run_monitoring(config: dict) -> dict:
    db = DbManager(DbConfig(**config["db"]))
    try:
        target_ts = parse_timestamp(config.get("monitor_target_timestamp"))
        fallback_sec = int(config.get("fallback_sec", 600))
        inp_base_dir = config["inp_base_dir"]
        pressure_compare_scale = float(config.get("pressure_compare_scale", 0.1))
        raw_flow_unit = getattr(FlowUnits, str(config.get("raw_flow_unit", "CMH")).upper())

        monitoring_files = load_monitoring_files(db, inp_base_dir)
        logger.info("monitoring_file_count=%s", len(monitoring_files))

        total_rows = 0
        processed = 0
        failed: list[dict] = []
        for monitoring_file in monitoring_files:
            try:
                path = Path(monitoring_file.inp_path)
                if not path.exists():
                    raise FileNotFoundError(f"INP file not found: {path}")

                points = load_observation_points(
                    db,
                    monitoring_file.inp_file_id,
                    only_display=True,
                    only_analysis=False,
                )
                ts = resolve_observation_timestamp(db, points, target_ts)
                if ts is None:
                    raise ValueError("TB_RAWDATA monitoring timestamp not found.")

                points = attach_observed_values(db, points, ts, fallback_sec=fallback_sec)
                wn = load_network(str(path))
                skipped = apply_measured_flow_as_demand(wn, points, raw_flow_unit)
                for item in skipped:
                    logger.warning("demand_injection_skipped inp_file_id=%s %s", monitoring_file.inp_file_id, item)

                results = run_epanet(wn)
                rows = build_monitor_rows(
                    monitoring_file=monitoring_file,
                    ts=ts,
                    points=points,
                    results=results,
                    pressure_compare_scale=pressure_compare_scale,
                    raw_flow_unit=raw_flow_unit,
                )
                inserted = insert_monitor_rows(db, rows)
                db.commit()

                total_rows += inserted
                processed += 1
                logger.info(
                    "monitoring_done inp_file_id=%s rev_no=%s ts=%s rows=%s",
                    monitoring_file.inp_file_id,
                    monitoring_file.rev_no,
                    ts,
                    inserted,
                )
            except Exception as exc:
                db.conn.rollback()
                failed.append(
                    {
                        "inp_file_id": monitoring_file.inp_file_id,
                        "rev_no": monitoring_file.rev_no,
                        "error": str(exc),
                    }
                )
                logger.exception(
                    "monitoring_failed inp_file_id=%s rev_no=%s",
                    monitoring_file.inp_file_id,
                    monitoring_file.rev_no,
                )

        return {
            "processed": processed,
            "failed": failed,
            "insertedRows": total_rows,
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EPANET monitoring once.")
    # 미지정 시 api_server 와 같은 규약(APP_CONFIG)으로 경로를 정한다.
    parser.add_argument("--config", default=None, help="config JSON path (기본값: APP_CONFIG)")
    parser.add_argument("--target-ts", default=None, help="override monitoring timestamp")
    args = parser.parse_args()

    config = load_config(args.config or str(resolve_config_path()))
    if args.target_ts:
        config["monitor_target_timestamp"] = args.target_ts

    output_dir = Path(config.get("output_dir", "outputs"))
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(output_dir, run_id)

    result = run_monitoring(config)
    logger.info("monitoring_result=%s", json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
