#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""군산 SI 관망해석: SI 수요량과 운영자 지정 펌프 조합으로 EPANET 0초 해석을 수행한다.

기본 실행 예:
    python epanet_si_gunsan.py --pump-comb "1,3" --pump-hz "1:55,3:52"

특정 시각:
    python epanet_si_gunsan.py --ts "2026-09-02 11:29:00" --pump-comb "1,3"

동작 원칙(v.26.09.11)
  * 수요/공급량은 TB_EPA_SIM_RESV_FLOW의 NODE_ID / FLOW_RATE / UPDT_TIME을 사용한다.
  * FLOW_RATE는 m3/h로 해석하고 WNTR Demand 입력 시 m3/s로 변환한다.
  * 함열가압장은 공급 지점이므로 FLOW_RATE의 양수 크기에 코드에서 음수 부호를 적용한다.
  * --ts 생략 시 TB_EPA_SIM_RESV_FLOW의 최신 UPDT_TIME을 기준시각으로 사용한다.
  * 펌프 운전 조합은 --pump-comb로 운영자가 직접 지정한다. 선택하지 않은 펌프는 CLOSED.
  * 선택 펌프의 Hz는 --pump-hz 값이 우선이며, 미지정 시 같은 기준시각의 실제 Hz 태그를 사용한다.
  * 기본 펌프 성능곡선 기준은 60 Hz이며 상대속도 = 적용 Hz / 기준 Hz.
  * 국가산단/지방산단 밸브 처리, INP 한글 ID 변환, CMH 단위 처리 등은 검증된 MO snapshot 로직을 유지한다.
  * DDA, duration=0의 단일시점 해석이다.
  * 결과 DB 저장은 기본 ON이며 TB_FP_SI_VAL / TB_FR_SI_VAL / TB_TOT_ALG에 FLG='si'로 저장한다.
    DB 저장 없이 파일 결과만 확인하려면 --no-save-db를 사용한다.
  * 실행 결과 파일은 logs/si_YYYYMMDD.txt 일 단위 요약 로그만 누적한다.
    EPANET 계산용 임시 INP/RPT/BIN은 실행 후 삭제한다.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
import tempfile
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_TS = None 
DEFAULT_INP_VALUE_UNIT = "CMH"  # 단위: m3/h
SCRIPT_DIR = Path(__file__).resolve().parent


NODE_META = [
    ("14", "891-365-PRI-9010", None),
    ("28", None, "891-365-FRI-8851"),
    ("Bkj-1460", "891-365-PRI-8301", None),
    ("Bks-2496", "891-365-PRI-4000", None),
    ("개정", "891-365-PRI-8700", None),
    ("국가산단", "891-365-PRI-8601", None),
    ("군산관말", "891-365-PRI-8800", None),
    ("군장에너지", None, "891-365-FRI-8802"),
    ("나운(배)", None, "891-365-FRI-8601"),
    ("덕암", "701-367-PRI-9322", None),
    ("신관", "701-367-PRI-9160", None),
    ("오식도(배)공업", None, "891-365-FRI-8652"),
    ("옥석", "701-367-PRI-9300", None),
    ("함열가압장", None, "740-914-FRI-1001"),
]

# 사용자 제공 TB_LINK_GRP 매핑: (LINK_ID, 유량 태그, 설명)
LINK_META = [
    ("45", "891-365-FRI-8950", "군산(정) 송수 유량"),
    ("62", "891-365-FRI-8850", "군산(정) 장항산단 유출 유량순시"),
    ("88", "891-365-FRI-8602", "군산(정) 국가산단분기 1200mm 순시유량"),
    ("Bks-1984", "891-365-FRI-8800", "군산(정) 군산관말 유량"),
    ("103", "891-365-FRI-8303", "내초도분기 공업 순시유량(통신)"),
    ("16", "891-365-FRI-9010", "군산(정) 최호장군(공) 유량(통신)"),
]

# (INP 펌프 ID, 가동 태그, 주파수 태그)
PUMPS = [
    ("군산(정)1", "891-365-PMB-4017", "891-365-SPI-4000"),
    ("군산(정)2", "891-365-PMB-4022", "891-365-SPI-4001"),
    ("군산(정)3", "891-365-PMB-4027", "891-365-SPI-4002"),
    ("군산(정)4", "891-365-PMB-4032", "891-365-SPI-4003"),
]
DEMAND_SIGN = {"함열가압장": -1.0}

# TAGNAME은 기존 891-365 접두부를 포함한 DB 이름을 사용한다.
VALVE_META = {
    "국가산단밸브": {"opening": "891-365-POI-8601", "flow": "891-365-FRI-8602",
                    "upstream_pressure": "891-365-PRI-8601", "downstream_pressure": "891-365-PRI-8603",
                    "upstream_node": "Bks-2361", "downstream_node": "16"},
    "지방산단밸브": {"opening": "891-365-POI-8600", "flow": "891-365-FRI-8601",
                    "upstream_pressure": "891-365-PRI-8600", "downstream_pressure": None,
                    "upstream_node": "13", "downstream_node": "17"},
}
DEFAULT_VALVE_MODEL = SCRIPT_DIR / "gunsan_valve_model.json"


LOG_DIR = SCRIPT_DIR / "logs"
PROCESS_STARTED = time.perf_counter()


def append_daily_log(
    mode: str,
    status: str,
    target_ts=None,
    elapsed_sec: Optional[float] = None,
    reason=None,
) -> Path:
    now = datetime.now()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{mode.lower()}_{now:%Y%m%d}.txt"

    target_text = "-" if target_ts is None else str(target_ts)
    fields = [
        f"[{now:%Y-%m-%d %H:%M:%S}]",
        status.upper(),
        f"MODE={mode.upper()}",
        f"TARGET_TS={target_text}",
    ]
    if elapsed_sec is not None:
        fields.append(f"ELAPSED={elapsed_sec:.3f}s")
    if reason is not None:
        reason_text = " ".join(str(reason).splitlines()).strip()
        fields.append(f"REASON={reason_text or '-'}")

    with path.open("a", encoding="utf-8") as stream:
        stream.write(" | ".join(fields) + "\n")
    return path


def cli_requested_ts(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        i = argv.index("--ts")
        return argv[i + 1] if i + 1 < len(argv) else None
    except ValueError:
        return None



@dataclass(frozen=True)
class Reading:
    ts: datetime
    value: float


@dataclass
class IdMaps:
    node: Dict[str, str]
    link: Dict[str, str]
    pattern: Dict[str, str]
    curve: Dict[str, str]

    @classmethod
    def from_dict(cls, value: dict) -> "IdMaps":
        return cls(
            node=dict(value.get("node", {})),
            link=dict(value.get("link", {})),
            pattern=dict(value.get("pattern", {})),
            curve=dict(value.get("curve", {})),
        )

    def as_dict(self) -> dict:
        return {"node": self.node, "link": self.link,
                "pattern": self.pattern, "curve": self.curve}

    @property
    def reverse_node(self) -> Dict[str, str]:
        return {safe: original for original, safe in self.node.items()}

    @property
    def reverse_link(self) -> Dict[str, str]:
        return {safe: original for original, safe in self.link.items()}


def _id_is_engine_safe(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,31}", value or ""))


def _definition_ids(lines: List[str]) -> List[str]:
    out = []
    for line in lines:
        words = line.split(";", 1)[0].split()
        if words:
            out.append(words[0])
    return out


def _build_id_maps(sections: dict) -> IdMaps:
    groups = {
        "node": ("JUNCTIONS", "RESERVOIRS", "TANKS"),
        "link": ("PIPES", "PUMPS", "VALVES"),
        "pattern": ("PATTERNS",),
        "curve": ("CURVES",),
    }
    prefixes = {"node": "N", "link": "L", "pattern": "PAT", "curve": "CUR"}
    maps: Dict[str, Dict[str, str]] = {}
    for kind, section_names in groups.items():
        identifiers: List[str] = []
        for name in section_names:
            identifiers.extend(_definition_ids(sections.get(name, [])))
        identifiers = list(dict.fromkeys(identifiers))
        used = set(identifiers)
        result: Dict[str, str] = {}
        counter = 1
        for original in identifiers:
            if _id_is_engine_safe(original):
                result[original] = original
                continue
            while True:
                candidate = f"{prefixes[kind]}{counter:05d}"
                counter += 1
                if candidate not in used and _id_is_engine_safe(candidate):
                    break
            result[original] = candidate
            used.add(candidate)
        maps[kind] = result
    return IdMaps(**maps)


def _rewrite_line_for_engine(line: str, section: str, ids: IdMaps) -> str:
    data, sep, comment = line.partition(";")
    words = data.split()
    if not words:
        return line

    def node(i: int):
        if i < len(words):
            words[i] = ids.node.get(words[i], words[i])

    def link(i: int):
        if i < len(words):
            words[i] = ids.link.get(words[i], words[i])

    def pattern(i: int):
        if i < len(words):
            words[i] = ids.pattern.get(words[i], words[i])

    def curve(i: int):
        if i < len(words):
            words[i] = ids.curve.get(words[i], words[i])

    if section == "JUNCTIONS":
        node(0)
        if len(words) >= 4:
            pattern(3)
    elif section == "RESERVOIRS":
        node(0)
        if len(words) >= 3:
            pattern(2)
    elif section == "TANKS":
        node(0)
        if len(words) >= 8 and words[7] != "*":
            curve(7)
    elif section == "PIPES":
        link(0); node(1); node(2)
    elif section == "PUMPS":
        link(0); node(1); node(2)
        for i, value in enumerate(words[:-1]):
            if value.upper() == "HEAD":
                curve(i + 1)
            elif value.upper() == "PATTERN":
                pattern(i + 1)
    elif section == "VALVES":
        link(0); node(1); node(2)
        if len(words) >= 6 and words[4].upper() == "GPV":
            curve(5)
    elif section == "PATTERNS":
        pattern(0)
    elif section == "CURVES":
        curve(0)
    elif section == "STATUS":
        link(0)
    elif section == "DEMANDS":
        node(0)
        if len(words) >= 3:
            pattern(2)
    elif section in ("EMITTERS", "QUALITY"):
        node(0)
    elif section == "SOURCES":
        node(0)
        if len(words) >= 4:
            pattern(3)
    elif section == "ENERGY":
        if words[0].upper() == "PUMP":
            link(1)
            for i, value in enumerate(words[:-1]):
                if value.upper() == "PATTERN":
                    pattern(i + 1)
                elif value.upper() == "EFFIC":
                    curve(i + 1)
        elif len(words) >= 3 and words[0].upper() == "GLOBAL" and words[1].upper() == "PATTERN":
            pattern(2)
    elif section == "COORDINATES":
        node(0)
    elif section == "VERTICES":
        link(0)
    elif section == "OPTIONS" and words[0].upper() == "PATTERN":
        pattern(1)
    elif section == "MIXING":
        node(0)
    elif section == "REACTIONS":
        if words[0].upper() in ("BULK", "WALL"):
            link(1)
        elif words[0].upper() == "TANK":
            node(1)
    elif section == "REPORT":
        if words[0].upper() in ("NODES", "LINKS") and len(words) > 1 and words[1].upper() not in ("ALL", "NONE"):
            for i in range(1, len(words)):
                (node if words[0].upper() == "NODES" else link)(i)
    elif section == "TAGS":
        if words[0].upper() == "NODE":
            node(1)
        elif words[0].upper() == "LINK":
            link(1)
    elif section in ("CONTROLS", "RULES"):
        for i, value in enumerate(words[:-1]):
            key = value.upper()
            if key in ("NODE", "JUNCTION", "TANK"):
                node(i + 1)
            elif key in ("LINK", "PUMP", "PIPE", "VALVE"):
                link(i + 1)
            elif key == "PATTERN":
                pattern(i + 1)
            elif key in ("HEAD", "CURVE", "GPV"):
                curve(i + 1)

    rebuilt = " ".join(words)
    if sep:
        rebuilt += ";" + comment
    return rebuilt


def _sanitize_sections(sections: dict) -> tuple[dict, IdMaps]:
    ids = _build_id_maps(sections)
    sanitized = {}
    for name, lines in sections.items():
        sanitized[name] = [_rewrite_line_for_engine(line, name, ids) for line in lines]
    return sanitized, ids


def all_tags() -> List[str]:
    tags = [tag for _, fp, fr in NODE_META for tag in (fp, fr) if tag]
    tags += [tag for _, tag, _ in LINK_META]
    tags += [tag for _, run, hz in PUMPS for tag in (run, hz)]
    tags += [meta[key] for meta in VALVE_META.values()
             for key in ("opening", "flow", "upstream_pressure", "downstream_pressure") if meta[key]]
    return sorted(set(tags))


def read_valve_exports(folder: Path, target: datetime, fallback_sec: int) -> tuple:
    tag_set = {meta[k] for meta in VALVE_META.values()
               for k in ("opening", "flow", "upstream_pressure", "downstream_pressure") if meta[k]}
    provided, rows = set(), []
    since = target - timedelta(seconds=fallback_sec)
    if not folder.is_dir():
        raise ValueError(f"밸브 CSV 폴더가 없습니다: {folder}")
    for tag in sorted(tag_set):
        paths = list(folder.glob(f"GSSCADA.{tag}.F_CV*.csv"))
        if len(paths) > 1:
            raise ValueError(f"{tag}: 중복 CSV 중 사용할 파일을 1개만 남겨 주세요.")
        if not paths:
            continue
        provided.add(tag)
        with paths[0].open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.reader(stream):
                if not row:
                    continue
                if len(row) != 3:
                    raise ValueError(f"CSV는 헤더 없는 시각,값,상태 3열이어야 합니다: {paths[0].name}")
                ts = datetime.fromisoformat(row[0])
                if ts.tzinfo is not None:
                    raise ValueError("CSV 시각은 DB와 동일한 현지시각이어야 합니다.")
                if since <= ts <= target:
                    value = row[1] if float(row[2]) == 100 else None
                    rows.append({"TAGNAME": tag, "TS": ts, "VALUE": value})
    if not provided:
        raise ValueError("지정 폴더에 GSSCADA.891-365-*.F_CV*.csv 파일이 없습니다.")
    return select_latest(rows, target, fallback_sec), provided


def load_config(path: Path, key: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cfg = data.get(key) if isinstance(data, dict) else None
    if cfg is None and isinstance(data, dict) and "host" in data:
        cfg = data
    if not isinstance(cfg, dict):
        raise ValueError(f"connections 파일에 접속키 {key!r}가 없습니다.")
    missing = [k for k in ("host", "user", "password") if k not in cfg]
    if missing or not (cfg.get("db") or cfg.get("database")):
        raise ValueError("connections 설정에는 host, user, password, db가 필요합니다.")
    return cfg


def connect_db(cfg: dict):
    import pymysql

    return pymysql.connect(
        host=cfg["host"], port=int(cfg.get("port", 3306)), user=cfg["user"],
        password=cfg["password"], database=cfg.get("db") or cfg["database"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=True, connect_timeout=10, read_timeout=60, write_timeout=60,
    )


def select_latest(rows: list, target: datetime, fallback_sec: int) -> Dict[str, Reading]:
    since = target - timedelta(seconds=fallback_sec)
    wanted = set(all_tags())
    latest: Dict[str, Reading] = {}
    for row in rows:
        tag = str(row["TAGNAME"])
        if tag not in wanted:
            continue
        stamp = row["TS"]
        if not isinstance(stamp, datetime):
            stamp = datetime.fromisoformat(str(stamp))
        if stamp.tzinfo is not None:
            raise ValueError("계측시각은 DB와 동일한 현지시각(시간대 표기 없음)이어야 합니다.")
        if not since <= stamp <= target:
            continue
        try:
            val = float(row["VALUE"])
        except (ValueError, TypeError):
            val = math.nan
        old = latest.get(tag)
        if old is None or stamp > old.ts:
            latest[tag] = Reading(stamp, val)
        elif stamp == old.ts and not (val == old.value or (math.isnan(val) and math.isnan(old.value))):
            raise ValueError(f"동일 태그/시각에 서로 다른 값이 있습니다: {tag}, {stamp}")
    return {tag: r for tag, r in latest.items() if math.isfinite(r.value)}


def fetch_readings(conn, target: datetime, fallback_sec: int) -> Dict[str, Reading]:
    tags = all_tags()
    placeholders = ",".join(["%s"] * len(tags))
    sql = f"""
        SELECT r.TAGNAME AS TAGNAME, r.TS AS TS, r.VALUE AS VALUE
        FROM TB_RAWDATA AS r
        JOIN (
            SELECT TAGNAME, MAX(TS) AS TS
            FROM TB_RAWDATA
            WHERE TS >= %s AND TS <= %s AND TAGNAME IN ({placeholders})
            GROUP BY TAGNAME
        ) AS latest ON r.TAGNAME = latest.TAGNAME AND r.TS = latest.TS
    """
    with conn.cursor() as cur:
        cur.execute(sql, (target - timedelta(seconds=fallback_sec), target, *tags))
        rows = cur.fetchall()
    return select_latest(rows, target, fallback_sec)



def si_raw_tags() -> List[str]:
    tags = [fp for _, fp, _ in NODE_META if fp]
    tags += [fr for _, _, fr in NODE_META if fr]  
    tags += [tag for _, tag, _ in LINK_META]
    tags += [hz for _, _, hz in PUMPS]
    tags += [meta[key] for meta in VALVE_META.values()
             for key in ("opening", "flow", "upstream_pressure", "downstream_pressure")
             if meta.get(key)]
    return sorted(set(tags))


def fetch_readings_for_tags(conn, target: datetime, fallback_sec: int,
                            tags: List[str]) -> Dict[str, Reading]:
    tags = sorted(set(t for t in tags if t))
    if not tags:
        return {}
    placeholders = ",".join(["%s"] * len(tags))
    sql = f"""
        SELECT r.TAGNAME AS TAGNAME, r.TS AS TS, r.VALUE AS VALUE
        FROM TB_RAWDATA AS r
        JOIN (
            SELECT TAGNAME, MAX(TS) AS TS
            FROM TB_RAWDATA
            WHERE TS >= %s AND TS <= %s AND TAGNAME IN ({placeholders})
            GROUP BY TAGNAME
        ) AS latest ON r.TAGNAME = latest.TAGNAME AND r.TS = latest.TS
    """
    with conn.cursor() as cur:
        cur.execute(sql, (target - timedelta(seconds=fallback_sec), target, *tags))
        rows = cur.fetchall()

    latest: Dict[str, Reading] = {}
    for row in rows:
        tag = str(row["TAGNAME"])
        stamp = row["TS"]
        if not isinstance(stamp, datetime):
            stamp = datetime.fromisoformat(str(stamp))
        try:
            value = float(row["VALUE"])
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            latest[tag] = Reading(stamp, value)
    return latest


def pick_latest_si_ts(conn, now_dt: datetime) -> Optional[datetime]:
    sql = """
        SELECT MAX(UPDT_TIME) AS UPDT_TIME
        FROM TB_EPA_SIM_RESV_FLOW
        WHERE UPDT_TIME <= %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (now_dt,))
        row = cur.fetchone()
    return row.get("UPDT_TIME") if row and row.get("UPDT_TIME") else None


def fetch_si_demands(conn, target: datetime, fallback_sec: int) -> Dict[str, dict]:
    since = target - timedelta(seconds=fallback_sec)
    sql = """
        SELECT t.NODE_ID, t.FLOW_RATE, t.UPDT_TIME
        FROM TB_EPA_SIM_RESV_FLOW AS t
        JOIN (
            SELECT NODE_ID, MAX(UPDT_TIME) AS UPDT_TIME
            FROM TB_EPA_SIM_RESV_FLOW
            WHERE UPDT_TIME >= %s
              AND UPDT_TIME <= %s
            GROUP BY NODE_ID
        ) AS latest
          ON t.NODE_ID = latest.NODE_ID
         AND t.UPDT_TIME = latest.UPDT_TIME
        ORDER BY t.NODE_ID
    """
    with conn.cursor() as cur:
        cur.execute(sql, (since, target))
        rows = cur.fetchall()

    out: Dict[str, dict] = {}
    for row in rows:
        nid = str(row["NODE_ID"])
        try:
            q = float(row["FLOW_RATE"])
        except (TypeError, ValueError):
            raise ValueError(f"SI FLOW_RATE가 숫자가 아닙니다: node={nid}, value={row.get('FLOW_RATE')!r}")
        if not math.isfinite(q) or q < 0:
            raise ValueError(f"SI FLOW_RATE는 0 이상의 유한한 m3/h 값이어야 합니다: node={nid}, value={q}")
        if nid in out:
            old = out[nid]
            if not math.isclose(old["FLOW_RATE"], q, rel_tol=0, abs_tol=1e-9):
                raise ValueError(f"동일 NODE_ID/UPDT_TIME에 서로 다른 SI FLOW_RATE가 있습니다: {nid}")
        out[nid] = {
            "FLOW_RATE": q,
            "UPDT_TIME": row["UPDT_TIME"],
        }
    return out


def parse_pump_combination(value: str) -> List[int]:
    if value is None or not str(value).strip():
        raise ValueError('--pump-comb를 지정하세요. 예: --pump-comb "1,3"')
    try:
        nums = sorted(set(int(x.strip()) for x in str(value).split(",") if x.strip()))
    except ValueError as exc:
        raise ValueError('--pump-comb 형식은 "1,3"처럼 펌프 번호 CSV여야 합니다.') from exc
    if not nums:
        raise ValueError("--pump-comb에 최소 1대의 펌프를 지정하세요.")
    invalid = [n for n in nums if n < 1 or n > len(PUMPS)]
    if invalid:
        raise ValueError(f"군산 송수펌프는 1~{len(PUMPS)}호기만 지정할 수 있습니다: {invalid}")
    return nums


def parse_pump_hz(value: Optional[str], selected: List[int]) -> Dict[int, float]:
    if value is None or not str(value).strip():
        return {}
    out: Dict[int, float] = {}
    for item in str(value).split(","):
        item = item.strip()
        if not item:
            continue
        try:
            num_s, hz_s = item.split(":", 1)
            num = int(num_s.strip())
            hz = float(hz_s.strip())
        except Exception as exc:
            raise ValueError('--pump-hz 형식은 "1:55,3:52"처럼 지정하세요.') from exc
        if num < 1 or num > len(PUMPS):
            raise ValueError(f"--pump-hz 펌프 번호는 1~{len(PUMPS)}만 가능합니다: {num}")
        if num not in selected:
            raise ValueError(f"--pump-hz에 지정한 {num}호기는 --pump-comb에 포함되어 있지 않습니다.")
        if not math.isfinite(hz) or not 1.0 <= hz <= 60.0:
            raise ValueError(f"{num}호기 Hz는 1~60 범위여야 합니다: {hz}")
        out[num] = hz
    return out


def validate_si_inputs(si_demands: Dict[str, dict], readings: Dict[str, Reading],
                       selected: List[int], hz_overrides: Dict[int, float]) -> None:
    if not si_demands:
        raise ValueError("TB_EPA_SIM_RESV_FLOW에서 기준시각/fallback 범위의 SI 수요량을 찾지 못했습니다.")

    demand_nodes = {nid for nid, _, fr in NODE_META if fr}
    missing_demands = sorted(demand_nodes - set(si_demands))
    if missing_demands:
        raise ValueError(
            "SI 수요/공급 대상 NODE_ID의 FLOW_RATE가 없습니다: " + ", ".join(missing_demands)
        )

    missing_hz = []
    for num in selected:
        _, _, hz_tag = PUMPS[num - 1]
        if num not in hz_overrides and hz_tag not in readings:
            missing_hz.append(f"{num}호기({hz_tag})")
    if missing_hz:
        raise ValueError(
            "선택 펌프의 Hz가 없습니다. --pump-hz로 지정하거나 TB_RAWDATA를 확인하세요: "
            + ", ".join(missing_hz)
        )


def resolve_input_path(value: Path, label: str, *, directory: bool = False) -> Path:
    value = value.expanduser()
    candidates = [value] if value.is_absolute() else [Path.cwd() / value, SCRIPT_DIR / value]
    checked = []
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in checked:
            continue
        checked.append(candidate)
        exists = candidate.is_dir() if directory else candidate.is_file()
        if exists:
            return candidate
    details = "\n".join(f"  - {path}" for path in checked)
    raise FileNotFoundError(f"{label} 경로를 찾을 수 없습니다. 확인한 경로:\n{details}")


def load_network_model(path: Path):
    import wntr

    try:
        return wntr.network.WaterNetworkModel(str(path))
    except Exception as exc:
        details = traceback.format_exc()
        report = path.parent / "inp_read_error.txt"
        cause = exc.__cause__ or exc.__context__ or exc
        try:
            report.write_text(details, encoding="utf-8")
            report_note = f"상세 오류 파일: {report}"
        except OSError as write_error:
            report_note = f"상세 오류 파일 저장 실패: {write_error}"
        raise RuntimeError(f"INP 읽기에 실패했습니다: {path}\n원인: {cause}\n{report_note}") from exc


def prepare_inp(source: Path, output: Path, inp_value_unit: str) -> dict:
    data = source.read_bytes()
    if b"<EPANET2>" in data[:32] or b"\x00" in data[:256]:
        raise ValueError("바이너리 프로젝트입니다. EPANET의 File > Export > Network로 내보낸 텍스트 INP를 지정하세요.")
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("INP 인코딩을 해석하지 못했습니다. UTF-8 또는 CP949 파일을 사용하세요.")
    sections = {}
    section = None
    for line in text.splitlines():
        match = re.match(r"^\s*\[([^]]+)\]", line)
        if match:
            section = match.group(1).upper()
            sections.setdefault(section, [])
        elif section:
            sections[section].append(line)
    pattern_names = {
        line.split(";", 1)[0].split()[0]
        for line in sections.get("PATTERNS", []) if line.split(";", 1)[0].split()
    }
    if "JUNCTIONS" not in sections or "OPTIONS" not in sections:
        raise ValueError("JUNCTIONS/OPTIONS가 있는 텍스트 INP가 필요합니다.")
    cleaned = []
    removed = []
    original_unit = None
    for line in sections["OPTIONS"]:
        words = line.split(";", 1)[0].split()
        if words and words[0].upper() == "PATTERN":
            if len(words) < 2 or words[1] not in pattern_names:
                removed.append(line.strip())
                continue
        if words and words[0].upper() == "UNITS":
            original_unit = words[1].upper()
            if inp_value_unit != "file":
                line = "Units " + inp_value_unit
        cleaned.append(line)
    if not original_unit:
        raise ValueError("INP의 유량 단위 선언(UNITS)이 없습니다.")
    sections["OPTIONS"] = cleaned
    sections.pop("END", None)
    sections, ids = _sanitize_sections(sections)
    output.write_text("\n\n".join("[" + k + "]\n" + "\n".join(v) for k, v in sections.items()) + "\n\n[END]\n", encoding="utf-8")
    return {"encoding": encoding, "original_unit": original_unit,
            "interpreted_unit": original_unit if inp_value_unit == "file" else inp_value_unit,
            "removed_invalid_options": removed, "id_maps": ids.as_dict()}



def configure_snapshot(wn, readings: Dict[str, Reading], si_demands: Dict[str, dict],
                       selected_pumps: List[int], hz_overrides: Dict[int, float],
                       reference_hz: float, ids: IdMaps,
                       keep_inp_demands: bool = False) -> tuple:
    import wntr

    if not math.isfinite(reference_hz) or reference_hz <= 0:
        raise ValueError("성능곡선 기준 주파수는 양수여야 합니다.")

    for nid, _, _ in NODE_META:
        if ids.node.get(nid, nid) not in wn.junction_name_list:
            raise ValueError(f"등록 노드가 INP의 Junction에 없습니다: {nid}")
    for lid, _, _ in LINK_META:
        if ids.link.get(lid, lid) not in wn.pipe_name_list:
            raise ValueError(f"등록 관로가 INP의 Pipe에 없습니다: {lid}")
    for pid, _, _ in PUMPS:
        if ids.link.get(pid, pid) not in wn.pump_name_list:
            raise ValueError(f"등록 펌프가 INP에 없습니다: {pid}")

    wn.options.hydraulic.demand_model = "DDA"
    wn.options.hydraulic.demand_multiplier = 1.0
    wn.options.hydraulic.pattern = None
    wn.options.time.duration = 0
    wn.options.time.report_start = 0
    wn.options.time.report_timestep = 60
    wn.options.time.hydraulic_timestep = 60
    wn.options.time.pattern_start = 0
    wn.options.time.start_clocktime = 0
    wn.options.time.statistic = "NONE"
    wn.options.quality.parameter = "NONE"

    reverse = ids.reverse_node
    original_inp_demands = {}
    for model_nid, node in wn.junctions():
        base_m3h = sum(d.base_value for d in node.demand_timeseries_list) * 3600.0
        if abs(base_m3h) > 1e-9:
            original_inp_demands[reverse.get(model_nid, model_nid)] = base_m3h
        for demand in node.demand_timeseries_list:
            demand.pattern_name = None
            if not keep_inp_demands:
                demand.base_value = 0.0

    for nid, value in original_inp_demands.items():
        action = "유지" if keep_inp_demands else "제거"
        print(f"[INP] 고정 수요량 {action}: {nid} = {value:,.3f} m3/h")

    for name in list(wn.control_name_list):
        wn.remove_control(name)

    assigned = {}
    for nid, row in si_demands.items():
        model_nid = ids.node.get(nid, nid)
        if model_nid not in wn.junction_name_list:
            print(f"[WARN] SI 수요 NODE_ID가 군산 INP Junction에 없어 제외: {nid}")
            continue

        q_input_m3h = float(row["FLOW_RATE"])
        q_applied_m3h = q_input_m3h * DEMAND_SIGN.get(nid, 1.0)
        node = wn.get_node(model_nid)
        demands = node.demand_timeseries_list
        if not demands:
            node.add_demand(q_applied_m3h / 3600.0, None)
        else:
            demands[0].base_value = q_applied_m3h / 3600.0
            for demand in list(demands)[1:]:
                demand.base_value = 0.0
        assigned[nid] = q_applied_m3h
        kind = "공급(-)" if q_applied_m3h < 0 else "수요(+)"
        print(
            f"[SI DEMAND] {nid}: DB={q_input_m3h:,.3f} m3/h "
            f"-> 적용={q_applied_m3h:,.3f} m3/h [{kind}] "
            f"(UPDT_TIME={row['UPDT_TIME']})"
        )

    selected_set = set(selected_pumps)
    pump_rows = []
    for num, (pid, _run_tag, hz_tag) in enumerate(PUMPS, start=1):
        pump = wn.get_link(ids.link.get(pid, pid))
        running = num in selected_set
        measured_hz = readings[hz_tag].value if hz_tag in readings else None

        if running:
            if num in hz_overrides:
                hz = float(hz_overrides[num])
                hz_source = "argument"
            else:
                hz = float(measured_hz)
                hz_source = "TB_RAWDATA"
            if not 1.0 <= hz <= 60.0:
                raise ValueError(f"{pid} 적용 Hz가 1~60 범위 밖입니다: {hz}")
            speed = hz / reference_hz
        else:
            hz = None
            hz_source = "closed"
            speed = 0.0

        pump.speed_pattern_name = None
        pump.base_speed = speed
        pump.initial_status = (
            wntr.network.LinkStatus.Open if running
            else wntr.network.LinkStatus.Closed
        )

        pump_rows.append({
            "PUMP_ID": pid,
            "PUMP_NO": num,
            "RUN_VALUE": 1 if running else 0,
            "MEASURED_HZ": measured_hz,
            "HZ_VALUE": hz,
            "HZ_SOURCE": hz_source,
            "REFERENCE_HZ": reference_hz,
            "APPLIED_STATUS": "OPEN" if running else "CLOSED",
            "APPLIED_SPEED": speed,
        })
        print(
            f"[SI PUMP] {num}호기 {pid}: "
            f"{'OPEN' if running else 'CLOSED'}, "
            f"적용Hz={hz if hz is not None else '-'}, "
            f"source={hz_source}, 상대속도={speed:.6f}"
        )

    return assigned, pump_rows, original_inp_demands


def pressure_value(value_m: float, unit: str) -> float:
    factors = {"legacy_div10": 0.1, "kgf_cm2": 0.1, "bar": 0.0980665,
               "MPa": 0.00980665, "kPa": 9.80665, "m": 1.0}
    return float(value_m) * factors[unit]


def load_valve_model(path: Path, pressure_unit: str) -> dict:
    if not path.is_file():
        raise ValueError(f"국가산단 보정 파일이 없습니다: {path}. 코드와 gunsan_valve_model.json을 같은 폴더에 놓으세요.")
    model = json.loads(path.read_text(encoding="utf-8-sig"))
    if model.get("schema_version") != 1 or model.get("valve_id") != "국가산단밸브":
        raise ValueError("국가산단 schema_version=1 보정 파일이 필요합니다.")
    factor = pressure_value(1.0, pressure_unit)
    if not math.isclose(float(model["pressure_units_per_head_m"]), factor, rel_tol=1e-8):
        raise ValueError("보정파일과 --pressure-unit의 환산계수가 다릅니다. fit_gunsan_valve.py에서 같은 압력 단위로 다시 보정하세요.")
    points = model.get("points", [])
    if len(points) < 2 or any(not math.isfinite(float(p[k])) for p in points for k in ("opening_pct", "R_SI")):
        raise ValueError("보정곡선의 유효한 점이 2개 이상 필요합니다.")
    if any(p["R_SI"] <= 0 for p in points) or any(b["opening_pct"] <= a["opening_pct"] or b["R_SI"] > a["R_SI"] * (1 + 1e-9)
                                                       for a, b in zip(points, points[1:])):
        raise ValueError("개도율은 증가, R은 양수이며 감소하는 곡선이어야 합니다.")
    for k in ("opening_min_pct", "opening_max_pct", "sensor_dz_m"):
        if not math.isfinite(float(model[k])):
            raise ValueError(f"보정파일 {k}가 유효하지 않습니다.")
    if not 0 < model["opening_min_pct"] <= points[0]["opening_pct"] < points[-1]["opening_pct"] <= model["opening_max_pct"] <= 100:
        raise ValueError("보정파일의 개도율 범위가 잘못되었습니다.")
    return model


def resistance_at_opening(model: dict, opening: float) -> float:
    lo, hi = model["opening_min_pct"], model["opening_max_pct"]
    if not lo <= opening <= hi:
        raise ValueError(f"국가산단 개도율 {opening:.5f}%는 보정 범위 {lo:.5f}~{hi:.5f}% 밖입니다. 추가 자료로 곡선을 보정하세요.")
    points = model["points"]
    if opening <= points[0]["opening_pct"]:
        return float(points[0]["R_SI"])
    if opening >= points[-1]["opening_pct"]:
        return float(points[-1]["R_SI"])
    for a, b in zip(points, points[1:]):
        if a["opening_pct"] <= opening <= b["opening_pct"]:
            t = (opening - a["opening_pct"]) / (b["opening_pct"] - a["opening_pct"])
            return math.exp((1 - t) * math.log(a["R_SI"]) + t * math.log(b["R_SI"]))
    raise ValueError("보정곡선 보간에 실패했습니다.")


def configure_valves(wn, readings, ids: IdMaps, mode: str, model_path: Path,
                     pressure_unit: str, sensor_dz_m: Optional[float], max_skew_sec: int) -> tuple:
    import wntr

    model = load_valve_model(model_path, pressure_unit) if mode == "opening" else None
    if model is not None:
        dz = float(model["sensor_dz_m"])
        if sensor_dz_m is not None and not math.isclose(sensor_dz_m, dz, abs_tol=1e-9):
            raise ValueError("개도율 곡선 적용 시 압력계 높이 차는 보정파일과 같아야 합니다. 곡선을 다시 보정하세요.")
    else:
        dz = sensor_dz_m if sensor_dz_m is not None else 0.0
    if not math.isfinite(dz) or max_skew_sec < 0:
        raise ValueError("압력계 높이 차는 유한한 수치, valve-max-skew-sec는 0 이상이어야 합니다.")
    warnings = []
    rows = []
    for name in VALVE_META:
        if ids.link.get(name, name) not in wn.valve_name_list:
            raise ValueError(f"INP 밸브가 없습니다: {name}")
    def val(tag):
        return readings[tag].value if tag and tag in readings else None
    def ts(tag):
        return readings[tag].ts if tag and tag in readings else None
    if mode in ("opening", "measured"):
        warnings.append(f"밸브 압력 환산={pressure_unit}, 전단-후단 계기 높이 차={dz:g}m. 압력계 사이 구간을 밸브 등가 손실로 적용합니다.")
    for lid, old in list(wn.valves()):
        vid = ids.reverse_link.get(lid, lid)
        meta = VALVE_META.get(vid, {})
        opening = val(meta.get("opening"))
        q, pu, pd = (val(meta.get(k)) for k in ("flow", "upstream_pressure", "downstream_pressure"))
        status = str(old.initial_status).upper()
        r_si, k_equiv, note, sign = None, None, "", 1
        if meta:
            upstream, downstream = (ids.node.get(meta[k], meta[k]) for k in ("upstream_node", "downstream_node"))
            if (old.start_node_name, old.end_node_name) == (upstream, downstream):
                sign = 1
            elif (old.start_node_name, old.end_node_name) == (downstream, upstream):
                sign = -1
            else:
                raise ValueError(f"{vid}의 INP 연결노드가 태그 매핑과 다릅니다. 전·후단 매핑을 확인하세요.")
        measured_dh = None
        measurement_skew = None
        if meta.get("downstream_pressure") and all(val(meta.get(k)) is not None for k in ("flow", "upstream_pressure", "downstream_pressure")):
            stamps = [ts(meta[k]) for k in ("flow", "upstream_pressure", "downstream_pressure")]
            measurement_skew = (max(stamps) - min(stamps)).total_seconds()
            if measurement_skew <= max_skew_sec:
                measured_dh = (pu - pd) / pressure_value(1.0, pressure_unit) + dz
        if mode == "inp":
            note = "INP 설정 유지"
        elif mode == "open" or not meta:
            status = "OPEN"
            old.initial_status = wntr.network.LinkStatus.Open
            note = "전개방 비교 시나리오" if mode == "open" else "사용자 확인: 항상 100% 개방"
        else:
            if opening is None or not 0 <= opening <= 100:
                raise ValueError(f"{vid}: 0~100% 범위의 개도율이 필요합니다 ({meta['opening']}).")
            if opening == 0:
                status = "CLOSED"
                old.initial_status = wntr.network.LinkStatus.Closed
                note = "실측 개도율 0%"
                if q is not None and abs(q) > 100:
                    warnings.append(f"{vid}: 개도율 0%인데 실측 유량이 {q:.3f} m3/h입니다. 상태·계측시각을 확인하세요.")
            elif vid == "지방산단밸브":
                status = "OPEN"
                old.initial_status = wntr.network.LinkStatus.Open
                note = "95~100% 전개방 근사; 후단 압력 및 부분 개방 보정곡선 없음"
            else:
                if mode == "opening":
                    r_si = resistance_at_opening(model, opening)
                    note = "개도율로 등가 R 계산; 곡선 관측기간 내 상태 재현"
                else:
                    if any(v is None for v in (q, pu, pd)) or q <= 0:
                        raise ValueError("measured 모드는 국가산단의 양수 유량과 전·후단 압력이 필요합니다.")
                    stamps = [ts(meta[k]) for k in ("opening", "flow", "upstream_pressure", "downstream_pressure")]
                    if (max(stamps) - min(stamps)).total_seconds() > max_skew_sec:
                        raise ValueError("국가산단 계측 태그 간 시각 차이가 valve-max-skew-sec를 초과했습니다.")
                    if measured_dh is None or measured_dh <= .1:
                        raise ValueError("국가산단 실측 총수두 차가 0.1m 이하여서 신뢰할 수 있는 저항을 계산할 수 없습니다.")
                    r_si = measured_dh / (q / 3600.0) ** 2
                    note = "해당 시점 실측 유량/차압으로 R 계산; 독립 예측 검증 불가"
                # K = 2*g*A_model^2*R. 모델 구경이 바뀌어도 R과 손실은 동일하게 보존된다.
                d = float(old.diameter)
                if not math.isfinite(d) or d <= 0:
                    raise ValueError("TCV 환산에 사용할 모델 구경이 유효하지 않습니다.")
                k_equiv = 2.0 * 9.80665 * (math.pi * d * d / 4.0) ** 2 * r_si
                vertices, tag = list(old.vertices), old.tag
                start, end = old.start_node_name, old.end_node_name
                wn.remove_link(lid)
                wn.add_valve(lid, start, end, diameter=d, valve_type="TCV", minor_loss=0.0,
                             initial_setting=k_equiv, initial_status="ACTIVE")
                new = wn.get_link(lid)
                new.vertices, new.tag = vertices, tag
                status = "ACTIVE"
                warnings.append(f"{vid}: 모델 구경 {d*1000:g}mm 기준 등가 K={k_equiv:.6g}. 실제 구경 확인 전 K/밸브 유속을 현장 값으로 해석하지 마세요.")
        applied = wn.get_link(lid)
        row = {"VALVE_ID": vid, "MODE": mode, "ORIGINAL_TYPE": old.valve_type,
               "APPLIED_TYPE": applied.valve_type, "APPLIED_STATUS": status,
               "OPENING_TAG": meta.get("opening"), "OPENING_PCT": opening, "OPENING_TS": ts(meta.get("opening")),
               "MEASURED_FLOW_M3H": q, "FLOW_TAG": meta.get("flow"), "FLOW_TS": ts(meta.get("flow")),
               "FLOW_TAG_ALSO_DEMAND_NODES": ",".join(nid for nid, _, fr in NODE_META if fr and fr == meta.get("flow")),
               "UPSTREAM_PRESSURE": pu, "UPSTREAM_PRESSURE_TS": ts(meta.get("upstream_pressure")),
               "DOWNSTREAM_PRESSURE": pd, "DOWNSTREAM_PRESSURE_TS": ts(meta.get("downstream_pressure")),
               "PRESSURE_UNIT": pressure_unit, "SENSOR_DZ_M": dz, "MEASURED_HEADLOSS_M": measured_dh,
               "MEASUREMENT_SKEW_SECONDS": measurement_skew, "R_SI": r_si, "EQUIVALENT_TCV_K": k_equiv,
               "MODEL_DIAMETER_MM": float(applied.diameter) * 1000,
               "MEASURED_FLOW_SIGN_TO_INP": sign, "NOTE": note}
        rows.append(row)
        print(f"[VALVE] {vid}: {applied.valve_type} {status}, 개도율={opening}, R={r_si}, {note}")
    return rows, warnings


def apply_pipe_overrides(wn, ids: IdMaps, specifications: list) -> list:
    import wntr
    rows = []
    for text in specifications:
        name, sep, status = text.rpartition("=")
        status = status.upper()
        if not sep or status not in ("OPEN", "CLOSED"):
            raise ValueError("pipe-status 형식은 관로ID=OPEN 또는 관로ID=CLOSED입니다.")
        lid = ids.link.get(name, name)
        if lid not in wn.pipe_name_list:
            raise ValueError(f"변경할 INP 관로가 없습니다: {name}")
        pipe = wn.get_link(lid)
        if pipe.check_valve:
            raise ValueError("체크밸브 관로 상태는 이 옵션으로 변경하지 않습니다.")
        old = str(pipe.initial_status)
        pipe.initial_status = wntr.network.LinkStatus.Open if status == "OPEN" else wntr.network.LinkStatus.Closed
        rows.append({"PIPE_ID": name, "ORIGINAL_STATUS": old, "APPLIED_STATUS": status})
        print(f"[PIPE SCENARIO] {name}: {old} -> {status}")
    return rows


def finish_valve_results(wn, results, ids: IdMaps, rows: list) -> list:
    warnings = []
    heads = results.node["head"].loc[0]
    for row in rows:
        lid = ids.link.get(row["VALVE_ID"], row["VALVE_ID"])
        link = wn.get_link(lid)
        sign = row["MEASURED_FLOW_SIGN_TO_INP"]
        q = float(results.link["flowrate"].loc[0, lid]) * 3600.0 * sign
        row["SIM_FLOW_M3H_MEASURED_DIRECTION"] = q
        row["SIM_HEADLOSS_M_MEASURED_DIRECTION"] = float(heads[link.start_node_name] - heads[link.end_node_name]) * sign
        row["SOLVED_STATUS"] = int(results.link["status"].loc[0, lid])
        measured = row["MEASURED_FLOW_M3H"]
        row["FLOW_ERROR_M3H"] = q - measured if measured is not None else None
        row["FLOW_ERROR_PERCENT"] = 100 * (q - measured) / measured if measured is not None and abs(measured) > 1e-9 else None
        if measured is not None and measured > 100 and (abs(q) < 1.0 or abs(q - measured) / measured > .2):
            message = f"{row['VALVE_ID']}: 실측={measured:.3f}, 해석={q:.6f} m3/h. 관로 개폐 상태와 하류 수요를 확인하세요."
            key = ids.link.get("Bks-1874", "Bks-1874")
            if row["VALVE_ID"] == "국가산단밸브" and key in wn.pipe_name_list and str(wn.get_link(key).initial_status).upper() == "CLOSED":
                message += " 현재 INP에서 Bks-1874가 CLOSED입니다. FRI-8602를 별도 수요로 추가하면 기존 말단 수요와 중복될 수 있습니다."
            if row["VALVE_ID"] == "지방산단밸브" and any(nid == "나운(배)" and fr == row["FLOW_TAG"] for nid, _, fr in NODE_META):
                message += " FRI-8601은 지방산단밸브를 통과해 나운(배)로 유입되는 동일 물량이므로, 나운 수요로 입력한 값과 밸브 유량은 독립 비교값이 아닙니다."
            warnings.append(message)
    return warnings


def write_csv(path: Path, rows: list) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_epanet_snapshot(wn, output: Path):
    import wntr

    result_dir = output.resolve(strict=True)
    previous_dir = Path.cwd()
    try:
        os.chdir(result_dir)
        return wntr.sim.EpanetSimulator(wn).run_sim(
            file_prefix="epanet", version=2.2, convergence_error=True
        )
    finally:
        os.chdir(previous_dir)



def build_results(wn, results, readings, assigned, pump_rows, target: datetime,
                  pressure_unit: str, ids: IdMaps):
    pressure = results.node["pressure"]
    if list(pressure.index) != [0]:
        raise RuntimeError(f"0초 한 시점이어야 합니다. 실제 결과 시점: {list(pressure.index)}")
    p = pressure.loc[0]
    h = results.node["head"].loc[0]
    q = results.link["flowrate"].loc[0]
    demand = results.node["demand"].loc[0]
    if not all(math.isfinite(float(x)) for x in list(p) + list(h) + list(q)):
        raise RuntimeError("해석 결과에 유효하지 않은 수치가 있습니다. epanet.rpt를 확인하세요.")

    def measured(tag):
        return readings[tag].value if tag and tag in readings else None

    def measured_ts(tag):
        return readings[tag].ts.isoformat(sep=" ") if tag and tag in readings else None

    node_rows = []
    for nid, fp, fr in NODE_META:
        model_nid = ids.node.get(nid, nid)
        node_rows.append({
            "RGSTR_TIME": target,
            "NODE_ID": nid,
            "FP_VAL": measured(fp),
            "FP_ALG_RST_VAL": pressure_value(p[model_nid], pressure_unit),
            "PRESSURE_UNIT": pressure_unit,
            "PRESSURE_M": float(p[model_nid]),
            "HEAD_M": float(h[model_nid]),
            "INPUT_DEMAND_M3H": assigned.get(nid, 0.0),
            "ACTUAL_DEMAND_M3H": float(demand[model_nid]) * 3600.0,
            "FP_RAW_TS": measured_ts(fp),
            "FR_RAW_TS": measured_ts(fr),
            "FLG": "si",
        })

    link_rows = []
    for lid, tag, name in LINK_META:
        model_lid = ids.link.get(lid, lid)
        pipe = wn.get_link(model_lid)
        loss = abs(float(h[pipe.start_node_name]) - float(h[pipe.end_node_name]))
        link_rows.append({
            "LINK_ID": lid,
            "HH_LOSS_VAL": loss,
            "RGSTR_TIME": target,
            "LINK_VAL": measured(tag),
            "FLW_ALG_RST_VAL": float(q[model_lid]) * 3600.0,
            "FLOW_UNIT": "m3/h",
            "RAW_TS": measured_ts(tag),
            "FLG": "si",
            "DESCRIPTION": name,
        })

    for row in pump_rows:
        pid = ids.link.get(row["PUMP_ID"], row["PUMP_ID"])
        row["FLOW_M3H"] = float(q[pid]) * 3600.0
        row["SOLVED_STATUS"] = float(results.link["status"].loc[0, pid])

    loss_total = sum(
        abs(float(h[pipe.start_node_name]) - float(h[pipe.end_node_name]))
        for _, pipe in wn.pipes()
    )
    return node_rows, link_rows, pump_rows, loss_total


def write_network_results(output: Path, wn, results, ids: IdMaps) -> None:
    rn, rl = ids.reverse_node, ids.reverse_link
    heads = results.node["head"].loc[0]
    write_csv(output / "all_nodes.csv", [
        {"NODE_ID": rn.get(nid, nid), "TYPE": node.node_type,
         "PRESSURE_M": float(results.node["pressure"].loc[0, nid]),
         "HEAD_M": float(heads[nid]),
         "DEMAND_M3H": float(results.node["demand"].loc[0, nid]) * 3600.0}
        for nid, node in wn.nodes()
    ])
    write_csv(output / "all_links.csv", [
        {"LINK_ID": rl.get(lid, lid), "TYPE": link.link_type,
         "FROM_NODE": rn.get(link.start_node_name, link.start_node_name),
         "TO_NODE": rn.get(link.end_node_name, link.end_node_name),
         "FLOW_M3H": float(results.link["flowrate"].loc[0, lid]) * 3600.0,
         "VELOCITY_M_S": float(results.link["velocity"].loc[0, lid]),
         "HEAD_DIFFERENCE_M": float(heads[link.start_node_name] - heads[link.end_node_name]),
         "STATUS": int(results.link["status"].loc[0, lid])}
        for lid, link in wn.links()
    ])



def save_results_db(conn, node_rows, link_rows, target: datetime, loss_total: float) -> None:
    node_sql = """INSERT INTO TB_FP_SI_VAL
        (RGSTR_TIME, NODE_ID, FP_VAL, FP_ALG_RST_VAL, FLG) VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE FP_VAL=VALUES(FP_VAL), FP_ALG_RST_VAL=VALUES(FP_ALG_RST_VAL)"""
    link_sql = """INSERT INTO TB_FR_SI_VAL
        (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, LINK_VAL, FLW_ALG_RST_VAL, FLG) VALUES (%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE HH_LOSS_VAL=VALUES(HH_LOSS_VAL), LINK_VAL=VALUES(LINK_VAL),
        FLW_ALG_RST_VAL=VALUES(FLW_ALG_RST_VAL)"""
    total_sql = """INSERT INTO TB_TOT_ALG
        (RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL, FLG) VALUES (%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE HH_LOSS_VAL_TOT=VALUES(HH_LOSS_VAL_TOT), FLW_VAL=VALUES(FLW_VAL),
        FP_VAL=VALUES(FP_VAL), FP_ALG_RST_VAL=VALUES(FP_ALG_RST_VAL)"""

    np = next(r for r in node_rows if r["NODE_ID"] == "Bks-2496")
    lq = next(r for r in link_rows if r["LINK_ID"] == "45")

    conn.begin()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                node_sql,
                [tuple(r[k] for k in ("RGSTR_TIME", "NODE_ID", "FP_VAL", "FP_ALG_RST_VAL", "FLG"))
                 for r in node_rows]
            )
            cur.executemany(
                link_sql,
                [tuple(r[k] for k in ("LINK_ID", "HH_LOSS_VAL", "RGSTR_TIME", "LINK_VAL",
                                      "FLW_ALG_RST_VAL", "FLG"))
                 for r in link_rows]
            )
            cur.execute(
                total_sql,
                (target, loss_total, lq["LINK_VAL"], np["FP_VAL"], np["FP_ALG_RST_VAL"], "si")
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise



def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="군산 SI: SI 수요량 + 운영자 펌프 조합/Hz로 EPANET 0초 해석",
        epilog='예: python epanet_si_gunsan.py --pump-comb "1,3" --pump-hz "1:55,3:52"',
    )
    ap.add_argument(
        "--ts",
        default=DEFAULT_TS,
        help="SI 기준시각. 미지정 시 TB_EPA_SIM_RESV_FLOW의 현재시각 이하 최신 UPDT_TIME 사용"
    )
    ap.add_argument("--inp", type=Path, default=SCRIPT_DIR / "epa_model.inp")
    ap.add_argument("--conn", type=Path, default=SCRIPT_DIR / "connections.json")
    ap.add_argument("--conn-key", default="maria-ems-db-gu")
    ap.add_argument(
        "--fallback-sec", type=int, default=600,
        help="SI 수요 및 실측 비교값의 과거 허용 범위(초). 기본 600=10분, 0=정확한 시각만"
    )
    ap.add_argument(
        "--pump-comb", required=True,
        help='가동할 군산 송수펌프 번호 CSV. 예: "1,3"'
    )
    ap.add_argument(
        "--pump-hz", default=None,
        help='선택 펌프 Hz 직접 지정. 예: "1:55,3:52". 미지정 펌프는 해당 시각 TB_RAWDATA Hz 사용'
    )
    ap.add_argument("--reference-hz", type=float, default=60.0,
                    help="INP 펌프 성능곡선 기준 Hz. 기본 60")
    ap.add_argument(
        "--inp-value-unit", choices=["file", "CMH", "CMD"], default=DEFAULT_INP_VALUE_UNIT,
        help="INP 유량 숫자의 실제 단위. 군산 기본 CMH=m3/h"
    )
    ap.add_argument(
        "--pressure-unit",
        choices=["legacy_div10", "kgf_cm2", "bar", "MPa", "kPa", "m"],
        default="legacy_div10"
    )
    ap.add_argument("--output-dir", type=Path, default=SCRIPT_DIR / "results_gunsan_si", help=argparse.SUPPRESS)
    ap.add_argument("--keep-inp-demands", action="store_true",
                    help="기본 제거되는 INP 고정 수요량을 비교 목적으로 유지")
    ap.add_argument("--no-save-db", dest="save_db", action="store_false",
                    help="DB 결과 저장은 생략하고 일 단위 SI 실행 로그만 기록")
    ap.set_defaults(save_db=True)
    ap.add_argument(
        "--raw-csv", type=Path,
        help="선택: 압력/관로유량/밸브/실측Hz를 DB 대신 TAGNAME,TS,VALUE CSV에서 읽음. SI Demand는 DB 사용"
    )
    ap.add_argument(
        "--valve-mode", choices=["opening", "measured", "open", "inp"], default="opening",
        help="opening=개도율 곡선, measured=실측 차압/유량, open=전개방, inp=INP 밸브 유지"
    )
    ap.add_argument("--valve-model", type=Path, default=DEFAULT_VALVE_MODEL)
    ap.add_argument("--valve-csv-dir", type=Path,
                    help="밸브 태그 CSV 폴더. 포함된 태그는 TB_RAWDATA보다 우선")
    ap.add_argument("--valve-sensor-dz-m", type=float,
                    help="전단-후단 압력계 높이차(m). measured 기본 0, opening은 보정파일 값")
    ap.add_argument("--valve-max-skew-sec", type=int, default=60,
                    help="실측 차압 계산 시 밸브 태그 간 최대 시각차(초)")
    ap.add_argument("--pipe-status", action="append", default=[], metavar="PIPE=OPEN|CLOSED",
                    help="명시한 관로만 계산용 상태 변경. 예: Bks-1874=OPEN")
    return ap



def main(argv=None) -> int:
    started = time.perf_counter()
    ap = parser()
    args = ap.parse_args(argv)

    if args.fallback_sec < 0:
        ap.error("--fallback-sec는 0 이상이어야 합니다.")

    selected_pumps = parse_pump_combination(args.pump_comb)
    hz_overrides = parse_pump_hz(args.pump_hz, selected_pumps)

    args.inp = resolve_input_path(args.inp, "INP 파일")
    args.conn = resolve_input_path(args.conn, "connections 파일")
    if args.raw_csv is not None:
        args.raw_csv = resolve_input_path(args.raw_csv, "계측 CSV 파일")
    if args.valve_mode == "opening":
        args.valve_model = resolve_input_path(args.valve_model, "밸브 보정 파일")
    if args.valve_csv_dir is not None:
        args.valve_csv_dir = resolve_input_path(
            args.valve_csv_dir, "밸브 CSV 폴더", directory=True
        )

    try:
        import wntr
    except ImportError as exc:
        raise RuntimeError(
            "필요 패키지 설치: python -m pip install wntr pandas pymysql"
        ) from exc

    conn = connect_db(load_config(args.conn, args.conn_key))
    try:
        if args.ts:
            try:
                target = datetime.fromisoformat(str(args.ts))
            except ValueError:
                ap.error("시각 형식은 YYYY-MM-DD HH:MM:SS입니다.")
        else:
            target = pick_latest_si_ts(conn, datetime.now())
            if target is None:
                raise RuntimeError(
                    "TB_EPA_SIM_RESV_FLOW에서 현재시각 이하의 UPDT_TIME을 찾지 못했습니다."
                )

        if target.tzinfo is not None:
            ap.error("DB와 동일한 현지시각(시간대 표기 없음)을 사용하세요.")

        temp_ctx = tempfile.TemporaryDirectory(prefix="epanet_si_gs_")
        output = Path(temp_ctx.name)

        print(f"[INFO] SI 기준 시각: {target}; 해석 시간: 0초")
        print(f"[INFO] 사용 INP: {args.inp}")
        print(f"[INFO] 접속 설정: {args.conn}; 접속키: {args.conn_key}")
        print(
            "[INFO] 선택 펌프: "
            + ", ".join(f"{n}호기" for n in selected_pumps)
        )
        if hz_overrides:
            print(
                "[INFO] Hz 인자 지정: "
                + ", ".join(f"{n}호기={hz:g}Hz" for n, hz in sorted(hz_overrides.items()))
            )
        else:
            print("[INFO] Hz 인자 미지정 -> 선택 펌프는 TB_RAWDATA의 실제 Hz 사용")

        info = prepare_inp(
            args.inp, output / "normalized_input.inp", args.inp_value_unit
        )
        ids = IdMaps.from_dict(info.pop("id_maps"))

        print(
            f"[INFO] DB/SI 유량=m3/h; "
            f"INP 숫자 해석 단위={info['interpreted_unit']}; "
            f"압력 환산={args.pressure_unit}"
        )
        if info["original_unit"] != info["interpreted_unit"]:
            print(
                f"[INFO] INP 단위 선언 {info['original_unit']} "
                f"-> {info['interpreted_unit']} 교정 "
                "(기존 유량 숫자는 변경하지 않음)"
            )
        if info["removed_invalid_options"]:
            print(
                "[INFO] 잘못된 기본 패턴 옵션 정리: "
                + str(info["removed_invalid_options"])
            )

        wn = load_network_model(output / "normalized_input.inp")

        # 1) 실제 압력/유량/밸브/Hz는 비교 및 현재 상태 반영용
        if args.raw_csv:
            with args.raw_csv.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            readings = select_latest(rows, target, args.fallback_sec)
            wanted = set(si_raw_tags())
            readings = {k: v for k, v in readings.items() if k in wanted}
        else:
            readings = fetch_readings_for_tags(
                conn, target, args.fallback_sec, si_raw_tags()
            )

        si_demands = fetch_si_demands(conn, target, args.fallback_sec)

        valve_csv_tags = []
        if args.valve_csv_dir:
            csv_readings, provided = read_valve_exports(
                args.valve_csv_dir, target, args.fallback_sec
            )
            for tag in provided:
                readings.pop(tag, None)
            readings.update(csv_readings)
            valve_csv_tags = sorted(provided)
            print(
                f"[INFO] 밸브 CSV {len(provided)}개 태그 사용. "
                f"정상값 {len(csv_readings)}개."
            )

        validate_si_inputs(
            si_demands, readings, selected_pumps, hz_overrides
        )

        missing_optional = sorted(set(si_raw_tags()) - set(readings))
        if missing_optional:
            print(
                "[WARN] 미조회 실측 태그(비교용 포함): "
                + ", ".join(missing_optional)
            )

        assigned, pump_rows, original_demands = configure_snapshot(
            wn,
            readings,
            si_demands,
            selected_pumps,
            hz_overrides,
            args.reference_hz,
            ids,
            args.keep_inp_demands,
        )

        pipe_overrides = apply_pipe_overrides(
            wn, ids, args.pipe_status
        )

        valve_rows, valve_assumptions = configure_valves(
            wn,
            readings,
            ids,
            args.valve_mode,
            args.valve_model,
            args.pressure_unit,
            args.valve_sensor_dz_m,
            args.valve_max_skew_sec,
        )
        for message in valve_assumptions:
            print("[WARN] " + message)

        for pid, _, _ in PUMPS:
            pump = wn.get_link(ids.link.get(pid, pid))
            if getattr(pump, "pump_type", None) == "HEAD":
                curve = wn.get_curve(pump.pump_curve_name)
                print(
                    f"[CURVE] {pid}: "
                    + str([
                        (round(q * 3600.0, 3), round(h, 3))
                        for q, h in curve.points
                    ])
                    + " (m3/h, m)"
                )

        results = run_epanet_snapshot(wn, output)

        valve_warnings = finish_valve_results(
            wn, results, ids, valve_rows
        )
        for message in valve_warnings:
            print("[WARN] " + message)

        node_rows, link_rows, pump_rows, loss_total = build_results(
            wn,
            results,
            readings,
            assigned,
            pump_rows,
            target,
            args.pressure_unit,
            ids,
        )

        np = next(r for r in node_rows if r["NODE_ID"] == "Bks-2496")
        lq = next(r for r in link_rows if r["LINK_ID"] == "45")

        solved_pressure = results.node["pressure"].loc[0]
        solved_demand = results.node["demand"].loc[0]
        negative_nodes = [
            ids.reverse_node.get(nid, nid)
            for nid in wn.junction_name_list
            if float(solved_pressure[nid]) < 0
        ]
        negative_demand_nodes = [
            ids.reverse_node.get(nid, nid)
            for nid in wn.junction_name_list
            if float(solved_pressure[nid]) < 0
            and float(solved_demand[nid]) > 1e-9
        ]

        if negative_nodes:
            print(
                f"[WARN] 음압 Junction {len(negative_nodes)}개 "
                f"(양수 수요가 있는 음압 노드 {len(negative_demand_nodes)}개). "
                "수요·펌프조합·Hz·표고·공급수두를 확인하세요."
            )

        for row in pump_rows:
            if row["APPLIED_STATUS"] == "OPEN" and row["SOLVED_STATUS"] == 0:
                print(
                    f"[WARN] {row['PUMP_ID']}: 가동 입력과 달리 "
                    "수리계산에서 폐쇄되었습니다. epanet.rpt를 확인하세요."
                )

        def show(value):
            return "계측값 없음" if value is None else f"{value:,.6f}"

        print(
            f"\n[RESULT] PIPE 45 유량(m3/h): "
            f"실측={show(lq['LINK_VAL'])}, "
            f"SI해석={show(lq['FLW_ALG_RST_VAL'])}"
        )
        print(
            f"[RESULT] NODE Bks-2496 압력({args.pressure_unit}): "
            f"실측={show(np['FP_VAL'])}, "
            f"SI해석={show(np['FP_ALG_RST_VAL'])}"
        )
        print(
            f"[RESULT] NODE Bks-2496 압력 원값="
            f"{np['PRESSURE_M']:.6f} m"
        )

        for row in valve_rows:
            if row["VALVE_ID"] in VALVE_META:
                print(
                    f"[RESULT] VALVE {row['VALVE_ID']} 유량(m3/h, 계측 방향): "
                    f"실측={show(row['MEASURED_FLOW_M3H'])}, "
                    f"SI해석={show(row['SIM_FLOW_M3H_MEASURED_DIRECTION'])}"
                )

        if args.save_db:
            save_results_db(
                conn, node_rows, link_rows, target, loss_total
            )
            print("[OK] SI 결과 DB 저장 완료 (FLG=si)")
        else:
            print("[INFO] --no-save-db: DB 결과 저장 생략")

        elapsed = time.perf_counter() - started
        log_path = append_daily_log("SI", "SUCCESS", target, elapsed)
        print(f"[OK] 군산 SI 한 시점 해석 완료; 로그={log_path}")
        return 0

    finally:
        conn.close()
        if "temp_ctx" in locals():
            temp_ctx.cleanup()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        append_daily_log(
            "SI", "FAIL", cli_requested_ts(),
            time.perf_counter() - PROCESS_STARTED, exc
        )
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
