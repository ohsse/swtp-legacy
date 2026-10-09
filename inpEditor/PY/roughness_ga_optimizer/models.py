from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Optional
import uuid

from db import DbManager


@dataclass
class ObservationPoint:
    mapping_id: Optional[int]
    location_name: str
    pressure_node_id: Optional[str]
    flow_link_id: Optional[str]
    pressure_tag: Optional[str]
    flow_tag: Optional[str]
    observed_pressure: Optional[float] = None
    observed_flow: Optional[float] = None
    observed_pressure_by_time: dict[int, float] | None = None
    observed_flow_by_time: dict[int, float] | None = None


@dataclass
class DemandPoint:
    mapping_id: Optional[int]
    node_id: str
    tag_no: str
    data_type: str = "FLOW"
    observed_value: Optional[float] = None


@dataclass
class InpFileInfo:
    inp_file_id: str
    original_file_name: str
    stored_file_name: str
    file_extension: str
    file_size: Optional[int]


@dataclass
class OptimizationRequest:
    hist_id: int
    inp_file_id: str
    prev_rev_no: int
    rev_no: Optional[int]
    option_snap: dict[str, Any]
    original_file_name: str = ""


@dataclass
class InpRevisionInfo:
    inp_file_id: str
    rev_no: int
    stored_file_name: str
    file_size: int
    file_hash: Optional[str]
    work_type: str


def get_inp_file_info(db: DbManager, inp_file_id: str) -> InpFileInfo:
    """inp_file_m에서 선택한 INP 파일의 실제 저장 파일명을 조회합니다."""

    sql = """
        SELECT inp_file_id, orgnl_file_nm, stor_file_nm, file_xtns, file_sz
        FROM inp_file_m
        WHERE inp_file_id = %s
    """
    row = db.fetchone(sql, (inp_file_id,))
    if not row:
        raise ValueError(f"inp_file_m에서 inp_file_id를 찾지 못했습니다: {inp_file_id}")

    return InpFileInfo(
        inp_file_id=row["inp_file_id"],
        original_file_name=row.get("orgnl_file_nm") or "",
        stored_file_name=row.get("stor_file_nm") or "",
        file_extension=row.get("file_xtns") or "",
        file_size=row.get("file_sz"),
    )


def build_inp_path(inp_base_dir: str, stored_file_name: str) -> str:
    """INP 저장 기준 폴더와 저장 파일명을 실제 파일 경로로 조합합니다."""

    return str(Path(inp_base_dir) / stored_file_name)


def parse_json_object(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"mappings": parsed}
    raise ValueError("설정 스냅샷(option_snap)은 JSON 객체 또는 매핑 목록이어야 합니다.")


def get_optimization_request(db: DbManager, hist_id: int | str) -> OptimizationRequest:
    """Read the Java-created optimization history row."""

    sql = """
        SELECT
            h.hist_id,
            h.inp_file_id,
            h.prev_rev_no,
            h.rev_no,
            h.option_snap,
            m.orgnl_file_nm
        FROM inp_file_opt_h h
        LEFT JOIN inp_file_m m ON m.inp_file_id = h.inp_file_id
        WHERE h.hist_id = %s
    """
    row = db.fetchone(sql, (hist_id,))
    if not row:
        raise ValueError(f"최적화 이력 정보를 찾지 못했습니다. hist_id={hist_id}")
    if row.get("prev_rev_no") is None:
        raise ValueError(f"원본 리비전번호(prev_rev_no)가 없습니다. hist_id={hist_id}")

    return OptimizationRequest(
        hist_id=int(row["hist_id"]),
        inp_file_id=row["inp_file_id"],
        prev_rev_no=int(row["prev_rev_no"]),
        rev_no=None if row.get("rev_no") is None else int(row["rev_no"]),
        option_snap=parse_json_object(row.get("option_snap")),
        original_file_name=row.get("orgnl_file_nm") or "",
    )


def get_inp_revision_info(
    db: DbManager,
    inp_file_id: str,
    rev_no: int,
) -> InpRevisionInfo:
    """Find the exact INP revision to use."""

    sql = """
        SELECT inp_file_id, rev_no, stor_file_nm, file_sz, file_hash, work_type
        FROM inp_file_rev_h
        WHERE inp_file_id = %s
          AND rev_no = %s
    """
    row = db.fetchone(sql, (inp_file_id, rev_no))
    if not row:
        raise ValueError(
            f"INP 리비전 정보를 찾지 못했습니다. inp_file_id={inp_file_id}, rev_no={rev_no}"
        )
    return InpRevisionInfo(
        inp_file_id=row["inp_file_id"],
        rev_no=int(row["rev_no"]),
        stored_file_name=row["stor_file_nm"],
        file_size=int(row["file_sz"]),
        file_hash=row.get("file_hash"),
        work_type=row["work_type"],
    )


def resolve_revision_inp_path(
    db: DbManager,
    inp_file_id: str,
    rev_no: int,
    inp_base_dir: str,
) -> str:
    revision = get_inp_revision_info(db, inp_file_id, rev_no)
    path = Path(build_inp_path(inp_base_dir, revision.stored_file_name))
    if not path.exists():
        raise FileNotFoundError(f"INP 리비전 파일을 찾지 못했습니다: {path}")
    return str(path)


def resolve_inp_path(db: DbManager, inp_file_id: str, inp_base_dir: str) -> str:
    """
    화면에서 받은 inp_file_id를 실제 INP 파일 경로로 변환합니다.

    DB:
        inp_file_m.stor_file_nm

    파일 경로:
        {inp_base_dir}/{stor_file_nm}

    주의:
        inp_base_dir는 이 파이썬 프로세스가 직접 접근 가능한 경로여야 합니다.

        운영환경에서는 이 코드가 localhost 서버에서 실행된다고 보고
        서버 로컬 절대경로를 사용합니다.

        예:
            D:/inp_simulator

        개발 PC에서 직접 실행할 때만 별도 테스트 경로로 바꾸면 됩니다.
    """

    info = get_inp_file_info(db, inp_file_id)
    if not info.stored_file_name:
        raise ValueError(f"저장 파일명이 비어 있습니다: {inp_file_id}")

    path = Path(build_inp_path(inp_base_dir, info.stored_file_name))
    if not path.exists():
        raise FileNotFoundError(f"INP 파일을 찾지 못했습니다: {path}")

    return str(path)


def file_sha256(path: str) -> str:
    """파일 내용을 SHA-256 해시로 계산합니다."""

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_optimized_inp_names(source_info: InpFileInfo) -> tuple[str, str, str]:
    """
    최적화 INP용 새 ID, 화면 표시용 원본 파일명, 실제 저장 파일명을 만듭니다.

    반환:
        new_inp_file_id
        original_file_name_for_db
        stored_file_name_for_disk
    """

    new_id = str(uuid.uuid4())
    source_name = source_info.original_file_name or source_info.stored_file_name or "optimized.inp"
    stem = Path(source_name).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    display_name = f"{stem}_roughness_optimized_{timestamp}.inp"
    stored_name = f"{new_id}.inp"
    return new_id, display_name, stored_name


def insert_inp_file_record(
    db: DbManager,
    inp_file_id: str,
    original_file_name: str,
    stored_file_name: str,
    file_path: str,
) -> None:
    """생성된 최적화 INP 파일을 inp_file_m에 등록합니다."""

    path = Path(file_path)
    sql = """
        INSERT INTO inp_file_m
            (inp_file_id, orgnl_file_nm, stor_file_nm, file_xtns, file_sz, file_hash, rgst_dttm, mdf_dttm)
        VALUES
            (%s, %s, %s, %s, %s, %s, NOW(6), NOW(6))
    """
    db.executemany(
        sql,
        [
            (
                inp_file_id,
                original_file_name,
                stored_file_name,
                "inp",
                path.stat().st_size,
                file_sha256(str(path)),
            )
        ],
    )


def get_next_revision_no(db: DbManager, inp_file_id: str) -> int:
    sql = """
        SELECT COALESCE(MAX(rev_no), -1) + 1 AS next_rev_no
        FROM inp_file_rev_h
        WHERE inp_file_id = %s
    """
    row = db.fetchone(sql, (inp_file_id,))
    return int(row["next_rev_no"])


def make_revision_stored_name(inp_file_id: str, rev_no: int) -> str:
    return f"{inp_file_id}_r{rev_no}.inp"


def insert_inp_revision_record(
    db: DbManager,
    inp_file_id: str,
    rev_no: int,
    stored_file_name: str,
    file_path: str,
    work_type: str = "OPTIMIZE",
) -> None:
    path = Path(file_path)
    sql = """
        INSERT INTO inp_file_rev_h
            (inp_file_id, rev_no, stor_file_nm, file_sz, file_hash, work_type, rgst_dttm)
        VALUES
            (%s, %s, %s, %s, %s, %s, NOW(6))
    """
    db.execute(
        sql,
        (
            inp_file_id,
            rev_no,
            stored_file_name,
            path.stat().st_size,
            file_sha256(str(path)),
            work_type,
        ),
    )


def update_current_revision(db: DbManager, inp_file_id: str, rev_no: int) -> None:
    sql = """
        UPDATE inp_file_m
        SET curr_rev_no = %s,
            mdf_dttm = NOW(6)
        WHERE inp_file_id = %s
    """
    db.execute(sql, (rev_no, inp_file_id))


def load_observation_points(
    db: DbManager,
    inp_file_id: str,
    only_display: bool = False,
    only_analysis: bool = True,
) -> list[ObservationPoint]:
    """Load display/comparison points from inp_vis_mapping."""

    conditions = ["inp_file_id = %s"]
    params: list[object] = [inp_file_id]
    if only_display:
        conditions.append("COALESCE(disp_yn, 'Y') = 'Y'")
    del only_analysis

    sql = f"""
        SELECT
            mapping_id,
            point_nm,
            junction_id,
            pipe_id,
            pressure_tag_no,
            flow_tag_no
        FROM inp_vis_mapping
        WHERE {" AND ".join(conditions)}
        ORDER BY COALESCE(sort_ord, 999999), mapping_id
    """
    rows = db.fetchall(sql, tuple(params))

    return [
        ObservationPoint(
            mapping_id=row.get("mapping_id"),
            location_name=row.get("point_nm") or "",
            pressure_node_id=row.get("junction_id") or None,
            flow_link_id=row.get("pipe_id") or None,
            pressure_tag=row.get("pressure_tag_no") or None,
            flow_tag=row.get("flow_tag_no") or None,
        )
        for row in rows
    ]


def load_visual_points(
    db: DbManager,
    inp_file_id: str,
    only_display: bool = True,
) -> list[ObservationPoint]:
    return load_observation_points(
        db=db,
        inp_file_id=inp_file_id,
        only_display=only_display,
        only_analysis=False,
    )


def load_analysis_pressure_points(
    db: DbManager,
    inp_file_id: str,
    only_analysis: bool = True,
) -> list[ObservationPoint]:
    """Load pressure points used by the GA objective from inp_anal_mapping."""

    conditions = [
        "inp_file_id = %s",
        "UPPER(data_type) = 'PRESSURE'",
        "tag_no IS NOT NULL",
        "tag_no <> ''",
        "node_id IS NOT NULL",
        "node_id <> ''",
    ]
    params: list[object] = [inp_file_id]
    if only_analysis:
        conditions.append("COALESCE(anal_yn, 'Y') = 'Y'")

    sql = f"""
        SELECT mapping_id, node_id, tag_no
        FROM inp_anal_mapping
        WHERE {" AND ".join(conditions)}
        ORDER BY mapping_id
    """
    rows = db.fetchall(sql, tuple(params))
    return [
        ObservationPoint(
            mapping_id=row.get("mapping_id"),
            location_name=row.get("node_id") or "",
            pressure_node_id=row.get("node_id") or None,
            flow_link_id=None,
            pressure_tag=row.get("tag_no") or None,
            flow_tag=None,
        )
        for row in rows
    ]


def load_demand_points(
    db: DbManager,
    inp_file_id: str,
    only_analysis: bool = True,
) -> list[DemandPoint]:
    """Load flow tags used as demand overrides from inp_anal_mapping."""

    conditions = [
        "inp_file_id = %s",
        "UPPER(data_type) = 'FLOW'",
        "tag_no IS NOT NULL",
        "tag_no <> ''",
        "node_id IS NOT NULL",
        "node_id <> ''",
    ]
    params: list[object] = [inp_file_id]
    if only_analysis:
        conditions.append("COALESCE(anal_yn, 'Y') = 'Y'")

    sql = f"""
        SELECT mapping_id, node_id, tag_no, data_type
        FROM inp_anal_mapping
        WHERE {" AND ".join(conditions)}
        ORDER BY mapping_id
    """
    rows = db.fetchall(sql, tuple(params))
    return [
        DemandPoint(
            mapping_id=row.get("mapping_id"),
            node_id=str(row.get("node_id")),
            tag_no=str(row.get("tag_no")),
            data_type=str(row.get("data_type") or "FLOW").upper(),
        )
        for row in rows
    ]


def attach_demand_values(
    db: DbManager,
    points: list[DemandPoint],
    ts: datetime,
    fallback_sec: int = 600,
) -> list[DemandPoint]:
    tags = [point.tag_no for point in points if point.tag_no]
    values = fetch_raw_values_near(db, ts, tags, fallback_sec=fallback_sec)
    for point in points:
        point.observed_value = values.get(point.tag_no)
    return points


def load_observation_points_from_option_snap(
    option_snap: dict[str, Any],
    only_analysis: bool = True,
) -> list[ObservationPoint]:
    """Build observation points from the inp_mapping snapshot stored by Java."""

    mappings = option_snap.get("mappings")
    if mappings is None:
        mappings = option_snap.get("inp_mapping")
    if mappings is None:
        mappings = option_snap.get("mapping")
    if mappings is None:
        mappings = []
    if not isinstance(mappings, list):
        raise ValueError("option_snap mappings must be a list.")

    def pick(row: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = row.get(key)
            if value is not None and value != "":
                return value
        return None

    def sort_key(row: dict[str, Any]) -> tuple[int, int]:
        sort_ord = pick(row, "sort_ord", "sortOrd")
        mapping_id = pick(row, "mapping_id", "mappingId")
        try:
            sort_value = int(sort_ord)
        except (TypeError, ValueError):
            sort_value = 999999
        try:
            mapping_value = int(mapping_id)
        except (TypeError, ValueError):
            mapping_value = 999999
        return sort_value, mapping_value

    points: list[ObservationPoint] = []
    for row in sorted(mappings, key=sort_key):
        if not isinstance(row, dict):
            continue
        anal_yn = str(pick(row, "anal_yn", "analYn") or "Y").upper()
        if only_analysis and anal_yn != "Y":
            continue
        mapping_id = pick(row, "mapping_id", "mappingId")
        points.append(
            ObservationPoint(
                mapping_id=None if mapping_id is None else int(mapping_id),
                location_name=pick(row, "point_nm", "pointNm", "location_name") or "",
                pressure_node_id=pick(row, "junction_id", "junctionId"),
                flow_link_id=pick(row, "pipe_id", "pipeId"),
                pressure_tag=pick(row, "pressure_tag_no", "pressureTagNo", "pressure_tag"),
                flow_tag=pick(row, "flow_tag_no", "flowTagNo", "flow_tag"),
            )
        )
    return points


def _option_snap_mappings(option_snap: dict[str, Any]) -> list[dict[str, Any]]:
    mappings = option_snap.get("mappings")
    if mappings is None:
        mappings = option_snap.get("inp_anal_mapping")
    if mappings is None:
        mappings = option_snap.get("inp_mapping")
    if mappings is None:
        mappings = option_snap.get("mapping")
    if mappings is None:
        mappings = []
    if not isinstance(mappings, list):
        raise ValueError("option_snap mappings must be a list.")
    return [row for row in mappings if isinstance(row, dict)]


def _pick_option_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def load_analysis_pressure_points_from_option_snap(
    option_snap: dict[str, Any],
    only_analysis: bool = True,
) -> list[ObservationPoint]:
    """Build GA pressure comparison points from the Java-created inp_anal_mapping snapshot."""

    points: list[ObservationPoint] = []
    for row in _option_snap_mappings(option_snap):
        data_type = str(_pick_option_value(row, "dataType", "data_type") or "").upper()
        if data_type != "PRESSURE":
            continue
        anal_yn = str(_pick_option_value(row, "analYn", "anal_yn") or "Y").upper()
        if only_analysis and anal_yn != "Y":
            continue
        node_id = _pick_option_value(row, "nodeId", "node_id", "junctionId", "junction_id")
        tag_no = _pick_option_value(row, "tagNo", "tag_no", "pressureTagNo", "pressure_tag_no")
        if not node_id or not tag_no:
            continue
        mapping_id = _pick_option_value(row, "mappingId", "mapping_id")
        points.append(
            ObservationPoint(
                mapping_id=None if mapping_id is None else int(mapping_id),
                location_name=str(node_id),
                pressure_node_id=str(node_id),
                flow_link_id=None,
                pressure_tag=str(tag_no),
                flow_tag=None,
            )
        )
    return points


def load_demand_points_from_option_snap(
    option_snap: dict[str, Any],
    only_analysis: bool = True,
) -> list[DemandPoint]:
    """Build demand override points from the Java-created inp_anal_mapping snapshot."""

    points: list[DemandPoint] = []
    for row in _option_snap_mappings(option_snap):
        data_type = str(_pick_option_value(row, "dataType", "data_type") or "").upper()
        if data_type != "FLOW":
            continue
        anal_yn = str(_pick_option_value(row, "analYn", "anal_yn") or "Y").upper()
        if only_analysis and anal_yn != "Y":
            continue
        node_id = _pick_option_value(row, "nodeId", "node_id", "junctionId", "junction_id")
        tag_no = _pick_option_value(row, "tagNo", "tag_no", "flowTagNo", "flow_tag_no")
        if not node_id or not tag_no:
            continue
        mapping_id = _pick_option_value(row, "mappingId", "mapping_id")
        points.append(
            DemandPoint(
                mapping_id=None if mapping_id is None else int(mapping_id),
                node_id=str(node_id),
                tag_no=str(tag_no),
                data_type="FLOW",
            )
        )
    return points


def fetch_raw_values_near(
    db: DbManager,
    ts: datetime,
    tags: list[str],
    fallback_sec: int = 600,
) -> dict[str, float]:
    """
    TB_RAWDATA에서 요청 시각 이전 fallback_sec 안의 가장 최근 값을 가져옵니다.

    EMS_EPA의 fetch_values_by_tag_with_fallback 방식과 같은 목적입니다.
    """

    tags = [tag for tag in tags if tag]
    if not tags:
        return {}

    placeholders = ",".join(["%s"] * len(tags))
    sql = f"""
        SELECT r.TAGNAME, r.VALUE
        FROM TB_RAWDATA r
        JOIN (
            SELECT TAGNAME, MAX(TS) AS TS
            FROM TB_RAWDATA
            WHERE TS <= %s
              AND TS >= DATE_SUB(%s, INTERVAL %s SECOND)
              AND TAGNAME IN ({placeholders})
            GROUP BY TAGNAME
        ) x ON x.TAGNAME = r.TAGNAME AND x.TS = r.TS
    """
    rows = db.fetchall(sql, (ts, ts, fallback_sec, *tags))

    values: dict[str, float] = {}
    for row in rows:
        try:
            values[row["TAGNAME"]] = float(row["VALUE"])
        except (TypeError, ValueError):
            continue
    return values


def get_latest_rawdata_timestamp(db: DbManager) -> Optional[datetime]:
    """
    TB_RAWDATA의 전체 최신 시각을 찾습니다.

    TB_RAWDATA 기본키가 (TS, TAGNAME) 순서라서 전체 MAX(TS)는 TS 인덱스를
    타기 쉽습니다. 이후 태그별 값은 fetch_raw_values_near()에서 해당 시각
    주변의 좁은 시간 범위만 조회합니다.
    """

    row = db.fetchone("SELECT MAX(TS) AS ts FROM TB_RAWDATA")
    if not row:
        return None
    return row.get("ts")


def attach_observed_values(
    db: DbManager,
    points: list[ObservationPoint],
    ts: datetime,
    fallback_sec: int = 600,
) -> list[ObservationPoint]:
    """ObservationPoint에 실측 압력/유량 값을 채웁니다."""

    pressure_tags = [point.pressure_tag for point in points if point.pressure_tag]
    flow_tags = [point.flow_tag for point in points if point.flow_tag]
    values = fetch_raw_values_near(db, ts, pressure_tags + flow_tags, fallback_sec=fallback_sec)

    for point in points:
        if point.pressure_tag:
            point.observed_pressure = values.get(point.pressure_tag)
        if point.flow_tag:
            point.observed_flow = values.get(point.flow_tag)

    return points


def attach_observed_values_by_result_time(
    db: DbManager,
    points: list[ObservationPoint],
    base_ts: datetime,
    result_times_sec: list[int],
    fallback_sec: int = 600,
) -> list[ObservationPoint]:
    """
    Attach observed values for multiple EPANET result times.

    The first EPANET result time is matched to base_ts. Later result times are
    matched by adding their offset from the first result time.
    """

    if not result_times_sec:
        return points

    first_result_time = min(result_times_sec)
    pressure_tags = [point.pressure_tag for point in points if point.pressure_tag]
    flow_tags = [point.flow_tag for point in points if point.flow_tag]
    all_tags = pressure_tags + flow_tags

    for point in points:
        point.observed_pressure_by_time = {}
        point.observed_flow_by_time = {}

    for result_time in result_times_sec:
        observed_ts = base_ts + timedelta(seconds=int(result_time) - first_result_time)
        values = fetch_raw_values_near(
            db,
            observed_ts,
            all_tags,
            fallback_sec=fallback_sec,
        )
        for point in points:
            if point.pressure_tag and point.pressure_tag in values:
                point.observed_pressure_by_time[int(result_time)] = values[point.pressure_tag]
            if point.flow_tag and point.flow_tag in values:
                point.observed_flow_by_time[int(result_time)] = values[point.flow_tag]

    for point in points:
        if point.observed_pressure_by_time:
            point.observed_pressure = point.observed_pressure_by_time.get(first_result_time)
        if point.observed_flow_by_time:
            point.observed_flow = point.observed_flow_by_time.get(first_result_time)

    return points


def resolve_observation_timestamp(
    db: DbManager,
    points: list[ObservationPoint],
    requested_ts: Optional[datetime],
    result_times_sec: list[int] | None = None,
) -> Optional[datetime]:
    """
    사용자가 시각을 지정하면 그 시각을 그대로 사용하고,
    지정하지 않으면 관측 태그 기준 공통 최신 시각을 계산합니다.
    """

    if requested_ts is not None:
        return requested_ts

    latest_ts = get_latest_rawdata_timestamp(db)
    if latest_ts is None:
        return None

    if result_times_sec and len(result_times_sec) > 1:
        span_sec = max(result_times_sec) - min(result_times_sec)
        return latest_ts - timedelta(seconds=int(span_sec))

    return latest_ts
