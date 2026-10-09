#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""군산 CUR(MO 결과 복사) + 수요예측(PRE) → EPANET 관망해석 주기 실행 코드(기본 5분).

기본 실행:
    python main_epa_gs.py

1분 주기 실행 (수요예측 1분 주기에 맞춤, 매분 :45초):
    python main_epa_gs.py --interval-min 1 --schedule-offset-sec 45

과거 예측 결과 1회 테스트:
    python main_epa_gs.py --snapshot --ts "2026-09-11 10:05:00" --no-save-db

설치:
    python -m pip install wntr pandas pymysql

핵심 동작
  * TB_CTR_TNK_RST의 수요예측 결과를 TB_NODE_TAG.DSTRB_Q_ID와 매핑해 EPANET
    NODE_ID의 Demand로 적용한다. 1/5/15/30분 네 Horizon(VALUE_1MIN(또는 PRDCT_VALUE)·
    VALUE_5MIN·VALUE_15MIN·VALUE_30MIN)을 각각 독립 스냅샷으로 해석하고, 결과는
    NODE/LINK 별 한 행에 _1MIN/_5MIN/_15MIN/_30MIN 컬럼으로 wide 저장한다.
    기존 컬럼(FP_ALG_RST_VAL·HH_LOSS_VAL·FLW_ALG_RST_VAL·HH_LOSS_VAL_TOT)에는 1분 결과가 들어간다.
    네 컬럼 중 하나라도 없거나 NULL 이면 그 회차는 SKIP 한다(2026-10-01 벤더 드롭).
  * 현재 코드의 PREDICTION_NODE_IDS에 정의된 노드만 예측 Demand로 적용한다.
  * 28번 노드는 예측값을 사용하지 않고 Demand=0으로 유지한다.
  * 함열가압장은 예측값 대신 TB_RAWDATA의 740-914-FRI-1001 실측값을 사용하며
    관망 공급원이므로 음수 Demand로 적용한다.
  * 펌프 운전상태/Hz 및 밸브 처리는 검증된 군산 MO 로직을 그대로 사용한다.
  * 모든 INP Junction Demand를 먼저 0으로 초기화한 뒤 필요한 값만 덮어쓴다.
  * DDA, duration=0 단일시점 관망해석이다.
  * 운영 LOOP는 01/06/11/16/...분에 실행한다. 실행 슬롯 이전의 가장 최근
    '정상 완료' MO 결과(TB_TOT_ALG·TB_FP_SI_VAL·TB_FR_SI_VAL 에 같은 RGSTR_TIME 이
    있는 것)를 CUR로 복사하고, 같은 실행시각으로 PRE 관망해석 결과를 저장한다.
    최신 MO 가 --mo-max-age-min(기본 10분)보다 오래됐으면 그 회차는 건너뛴다.
  * 주기는 --interval-min(1/2/3/5/10/15, 기본 5), 실행 시점은 --schedule-offset-min
    또는 --schedule-offset-sec 로 바꾼다. 결과시각은 실행 슬롯의 분이다.
    MO 는 5분 격자라 주기를 5분보다 짧게 하면 같은 MO 결과가 여러 번 CUR 로 복사된다.
  * 해당 회차(주기 경계 이후)에 생성된 수요예측 묶음만 PRE 입력으로 사용하며,
    예측 대상의 수행시각 차이는 --prediction-max-skew-sec 이내여야 한다.
  * 한 회차는 단일 스레드로 실행되어 다음 회차와 겹치지 않는다.
  * DB 연결은 예측/실측 조회 시 열고 해석 전에 닫은 뒤, 결과 저장 시 다시 열고
    COMMIT 후 즉시 닫는다. 주기 대기 동안 DB connection을 유지하지 않는다.
  * 해석 후 WNTR/results 객체를 정리하고 gc.collect()를 호출한다.
  * 직전 MO 결과는 TB_FP_VAL / TB_FR_VAL / TB_TOT_ALG에 FLG='CUR'로 복사하고,
    PRE 해석 결과는 같은 테이블에 FLG='PRE'로 저장한다.
  * TB_FP_VAL: 전체 EPANET 노드의 해석 압력(m)
  * TB_FR_VAL: 전체 Pipe의 수두손실(m), 해석 유량(m3/h)
  * TB_TOT_ALG: 전체 Pipe 손실 합계 + 대표노드 Bks-2496의 해석 압력(m)
  * 실측 FP_VAL / LINK_VAL은 사용하지 않는다.
  * TB_LINK_GRP / TB_AVL_GRP는 이번 군산 PRE 해석에서는 사용하지 않는다.
  * DB 저장은 기본 ON. --no-save-db로 DB 결과 저장만 생략할 수 있다.
  * 섀도우 배포용으로 --prediction-table(수요예측 조회 테이블)과
    --result-table-suffix(PRE/CUR 저장 테이블 접미사, 예: _SH)를 바꿀 수 있다.
    MO 원본(TB_TOT_ALG/TB_FP_SI_VAL/TB_FR_SI_VAL, FLG='mo')은 항상 운영 테이블에서 읽는다.
  * 파일 결과는 logs/pre_YYYYMMDD.txt 일 단위 요약 로그만 남긴다.
    EPANET 계산용 임시 INP/RPT/BIN은 시스템 임시폴더에서 실행 후 삭제한다.
"""
from __future__ import annotations

import argparse
import csv
import gc
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


DEFAULT_TS = None  # 예: "2026-09-08 10:00:00"
DEFAULT_INP_VALUE_UNIT = "CMH"  # 군산 INP의 모든 유량 숫자는 m3/h (사용자 확인).
SCRIPT_DIR = Path(__file__).resolve().parent

# (NODE_ID, 압력 태그, 수요/공급 유량 태그). 없는 태그는 None.
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
    """운영용 일 단위 요약 로그. 계정/암호 등 접속정보는 기록하지 않는다."""
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
    """최상위 예외 발생 시 로그에 남길 --ts 문자열을 가능한 범위에서 복원한다."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        i = argv.index("--ts")
        return argv[i + 1] if i + 1 < len(argv) else None
    except ValueError:
        return None


# PRE 수요예측 대상: 아래 PREDICTION_NODE_IDS에 정의된 노드만 예측값을 적용한다.
PREDICTION_NODE_IDS = ("나운(배)", "오식도(배)공업")#("군장에너지", "나운(배)", "오식도(배)공업")
PREDICTION_HORIZONS = (1, 5, 15, 30)
# DB 컬럼명은 대소문자를 구분하지 않고 찾는다. 1분은 기존 PRDCT_VALUE도 허용한다.
PREDICTION_COLUMN_CANDIDATES = {
    1: ("VALUE_1MIN", "PRDCT_VALUE"),
    5: ("VALUE_5MIN",),
    15: ("VALUE_15MIN",),
    30: ("VALUE_30MIN",),
}
ZERO_DEMAND_NODE_IDS = ("28",)
HAMYEOL_NODE_ID = "함열가압장"
HAMYEOL_FLOW_TAG = "740-914-FRI-1001"
REPRESENTATIVE_PRESSURE_NODE = "Bks-2496"
RESULT_FLAG = "PRE"
CUR_FLAG = "CUR"
MO_FLAG = "mo"
# 섀도우 배포용 테이블 전환(2026-09-29). 기본값은 운영 테이블 그대로다.
# 섀도우는 --prediction-table TB_CTR_TNK_RST_SH --result-table-suffix _SH 로
# 섀도우 수요예측을 읽고 TB_FP_VAL_SH / TB_FR_VAL_SH / TB_TOT_ALG_SH 에 쓴다.
# MO 원본 조회는 이 설정과 무관하게 운영 테이블이다(MO 는 섀도우에 없다).
PREDICTION_TABLE = "TB_CTR_TNK_RST"
RESULT_TABLE_SUFFIX = ""
_TABLE_NAME_RE = re.compile(r"^[A-Za-z0-9_]*$")


def result_table(base: str) -> str:
    """PRE/CUR 저장 테이블 이름(기본 테이블 + --result-table-suffix)."""
    return f"{base}{RESULT_TABLE_SUFFIX}"


def configure_tables(args) -> None:
    """CLI 인자로 조회·저장 테이블을 정한다. SQL 에 그대로 들어가므로 식별자 문자만 허용."""
    global PREDICTION_TABLE, RESULT_TABLE_SUFFIX
    for name, value in (
        ("--prediction-table", args.prediction_table),
        ("--result-table-suffix", args.result_table_suffix),
    ):
        if not _TABLE_NAME_RE.match(value):
            raise ValueError(f"{name} 에는 영문·숫자·_ 만 쓸 수 있습니다: {value!r}")
    if not args.prediction_table:
        raise ValueError("--prediction-table 이 비어 있습니다.")
    PREDICTION_TABLE = args.prediction_table
    RESULT_TABLE_SUFFIX = args.result_table_suffix

DEFAULT_SCHEDULE_OFFSET_MIN = 1  # 01, 06, 11, 16 ... 분에 실행
# PRE 실행 주기(분). 기본 5분은 기존 동작 그대로다. 수요예측이 1분 주기가 되면서
# --interval-min 으로 줄일 수 있게 했다(2026-09-28). 60의 약수만 허용한다 —
# 경계를 "정각 기준 분 % 주기"로 잡으므로 약수가 아니면 시 경계에서 간격이 틀어진다.
DEFAULT_INTERVAL_MIN = 5
ALLOWED_INTERVAL_MIN = (1, 2, 3, 5, 10, 15)
# MO(epanet_mo_gs.py) 루프의 저장 격자. PRE 주기와 별개로 5분 고정이다 —
# PRE 를 1분으로 돌리면 같은 MO 결과가 다섯 번 CUR 로 복사된다(결과시각만 다름).
MO_INTERVAL_MIN = 5
DEFAULT_MO_MAX_AGE_MIN = 10.0  # 최근 정상 MO 결과 최대 허용 경과시간(분)


@dataclass(frozen=True)
class Reading:
    ts: datetime
    value: float


@dataclass
class IdMaps:
    """원본 INP ID와 EPANET 엔진용 ASCII ID 사이의 변환표.

    EPANET toolkit은 현장 INP에 포함된 한글/괄호 ID를 일부 버전에서
    ``Error 252: invalid ID name``으로 거부한다. WNTR 내부 계산에는 원래
    ID를 사용할 수 있지만, 엔진에 넘기는 임시 INP에는 ASCII ID를 사용하고
    결과를 저장할 때 다시 원래 ID로 표시한다.
    """

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
    """EPANET ID로 안전하게 사용할 수 있는 보수적인 ASCII 검사."""
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,31}", value or ""))


def _definition_ids(lines: List[str]) -> List[str]:
    out = []
    for line in lines:
        words = line.split(";", 1)[0].split()
        if words:
            out.append(words[0])
    return out


def _build_id_maps(sections: dict) -> IdMaps:
    """INP의 노드/링크/패턴/곡선 ID를 엔진 호환 ID로 변환한다."""
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
        # INP에는 동일 registry 안의 중복 ID가 없어야 하지만, 순서를 보존하면서 제거한다.
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
    """데이터 부분만 바꿔 주석은 보존한다. section은 대문자(괄호 없음)."""
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
        # 현재 군산 파일에는 비어 있지만, 향후 제어문을 사용할 때를 위한 보수적 치환.
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
    """헤더 없는 시각/값/상태 CSV. 지정한 파일 태그는 DB보다 우선하며 결측도 반영한다."""
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
    """미래값과 유효기간 밖의 값을 제외하고, 같은 시각의 중복값 충돌을 검출한다."""
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
    # 최신 값 자체가 결측이면 더 오래된 값으로 몰래 대체하지 않는다.
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


def validate_inputs(readings: Dict[str, Reading]) -> None:
    required = {fr for _, _, fr in NODE_META if fr}
    required.update(run for _, run, _ in PUMPS)
    missing = sorted(required - readings.keys())
    for nid, _, tag in NODE_META:
        if tag and tag in readings and readings[tag].value < 0:
            raise ValueError(f"{nid}의 유량은 양수 크기(m3/h)로 입력해야 합니다. 공급 부호는 코드에서 적용합니다: {tag}")
    for pid, run, hz in PUMPS:
        if run in readings and readings[run].value < 0:
            raise ValueError(f"{pid} 가동태그가 음수입니다. 결측/오류 코드를 확인하세요: {readings[run].value}")
        if run not in readings or readings[run].value <= 0:
            continue
        if hz not in readings:
            missing.append(f"{hz} ({pid}: 운전 중 주파수 없음)")
        elif not 1.0 <= readings[hz].value <= 60.0:
            raise ValueError(f"{pid} 운전 주파수가 1~60 Hz 범위 밖입니다: {readings[hz].value}")
    if missing:
        raise ValueError("해석에 필요한 계측값이 없습니다: " + ", ".join(missing))





def runtime_tags(valve_mode: str = "opening") -> List[str]:
    """PRE 해석에 필요한 최소 실측 태그만 반환한다."""
    tags = [HAMYEOL_FLOW_TAG]
    tags += [tag for _, run, hz in PUMPS for tag in (run, hz)]

    if valve_mode == "opening":
        # 기본 운영: 개도율만 필요
        tags += [
            VALVE_META["국가산단밸브"]["opening"],
            VALVE_META["지방산단밸브"]["opening"],
        ]
    elif valve_mode == "measured":
        # 국가산단 실측 저항 계산 + 지방산단 개도 확인
        tags += [
            VALVE_META["국가산단밸브"]["opening"],
            VALVE_META["국가산단밸브"]["flow"],
            VALVE_META["국가산단밸브"]["upstream_pressure"],
            VALVE_META["국가산단밸브"]["downstream_pressure"],
            VALVE_META["지방산단밸브"]["opening"],
        ]
    # open / inp 모드는 밸브 실측 태그가 없어도 계산 가능

    return sorted(set(tag for tag in tags if tag))



def fetch_runtime_readings(
        conn,
        target: datetime,
        fallback_sec: int,
        valve_mode: str = "opening",
) -> Dict[str, Reading]:
    """펌프/밸브/함열 공급에 실제 필요한 최소 실측값만 조회."""
    tags = runtime_tags(valve_mode)
    placeholders = ",".join(["%s"] * len(tags))
    sql = f"""
        SELECT r.TAGNAME AS TAGNAME, r.TS AS TS, r.VALUE AS VALUE
        FROM TB_RAWDATA AS r
        JOIN (
            SELECT TAGNAME, MAX(TS) AS TS
            FROM TB_RAWDATA
            WHERE TS >= %s
              AND TS <= %s
              AND TAGNAME IN ({placeholders})
            GROUP BY TAGNAME
        ) AS latest
          ON r.TAGNAME = latest.TAGNAME
         AND r.TS = latest.TS
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
        if not math.isfinite(value):
            continue
        old = latest.get(tag)
        if old is None or stamp > old.ts:
            latest[tag] = Reading(stamp, value)
        elif stamp == old.ts and not math.isclose(value, old.value, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"동일 태그/시각에 서로 다른 값이 있습니다: {tag}, {stamp}")
    return latest


def load_prediction_mapping(conn) -> Dict[str, str]:
    """
    TB_NODE_TAG에서 PRE 대상 NODE_ID -> DSTRB_Q_ID 매핑을 읽는다.
    28/함열은 예측대상이 아니므로 여기서 요구하지 않는다.
    """
    placeholders = ",".join(["%s"] * len(PREDICTION_NODE_IDS))
    sql = f"""
        SELECT NODE_ID, DSTRB_Q_ID
        FROM TB_NODE_TAG
        WHERE NODE_ID IN ({placeholders})
    """
    with conn.cursor() as cur:
        cur.execute(sql, tuple(PREDICTION_NODE_IDS))
        rows = cur.fetchall()

    found: Dict[str, set] = {nid: set() for nid in PREDICTION_NODE_IDS}
    for row in rows:
        nid = str(row["NODE_ID"])
        dstrb = row.get("DSTRB_Q_ID")
        if dstrb is None or not str(dstrb).strip():
            continue
        found.setdefault(nid, set()).add(str(dstrb).strip())

    mapping: Dict[str, str] = {}
    errors = []
    for nid in PREDICTION_NODE_IDS:
        values = sorted(found.get(nid, set()))
        if not values:
            errors.append(f"{nid}: DSTRB_Q_ID 없음")
        elif len(values) > 1:
            errors.append(f"{nid}: DSTRB_Q_ID 중복 {values}")
        else:
            mapping[nid] = values[0]
    if errors:
        raise ValueError("TB_NODE_TAG 예측 매핑 오류: " + "; ".join(errors))

    reverse = {}
    for nid, dstrb in mapping.items():
        if dstrb in reverse:
            raise ValueError(
                f"동일 DSTRB_Q_ID가 여러 NODE_ID에 매핑되어 있습니다: "
                f"{dstrb} -> {reverse[dstrb]}, {nid}"
            )
        reverse[dstrb] = nid
    return mapping


def latest_processed_pre_ts(conn) -> Optional[datetime]:
    """이미 저장된 PRE 결과의 가장 최근 처리시각(--result-table-suffix 반영)."""
    sql = f"""
          SELECT MAX(RGSTR_TIME) AS RGSTR_TIME
          FROM {result_table("TB_TOT_ALG")}
          WHERE FLG = %s \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (RESULT_FLAG,))
        row = cur.fetchone()
    if not row or row.get("RGSTR_TIME") is None:
        return None
    value = row["RGSTR_TIME"]
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))



def _prediction_value_for_horizon(row: dict, horizon_min: int) -> float:
    """TB_CTR_TNK_RST 한 행에서 지정 Horizon의 예측값을 읽는다.

    1분은 PRDCT_VALUE를 기존 호환 컬럼으로 허용하고, 5/15/30분은
    VALUE_5min / VALUE_15min / VALUE_30min 계열을 사용한다.
    """
    if horizon_min not in PREDICTION_COLUMN_CANDIDATES:
        raise ValueError(f"지원하지 않는 예측 Horizon입니다: {horizon_min}분")

    key_map = {str(k).upper(): k for k in row.keys()}
    for candidate in PREDICTION_COLUMN_CANDIDATES[horizon_min]:
        actual = key_map.get(candidate.upper())
        if actual is None:
            continue
        raw = row.get(actual)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"{actual} 숫자 변환 실패: {raw!r}"
            )
        if not math.isfinite(value) or value < 0:
            raise ValueError(
                f"{actual}은 0 이상의 유한값이어야 합니다: {value}"
            )
        return value

    expected = "/".join(PREDICTION_COLUMN_CANDIDATES[horizon_min])
    raise ValueError(f"{horizon_min}분 예측 컬럼({expected}) 또는 값이 없습니다.")


def fetch_prediction_bundle(
        conn,
        mapping: Dict[str, str],
        *,
        last_processed: Optional[datetime] = None,
        snapshot_ts: Optional[datetime] = None,
        max_skew_sec: int = 120,
) -> tuple[Optional[dict], str]:
    """예측 대상별 최신 1/5/15/30분 값을 하나의 동기화된 묶음으로 읽는다."""
    rows_by_node = {}

    for nid, dstrb_id in mapping.items():
        if snapshot_ts is None:
            sql = f"""
                  SELECT *
                  FROM {PREDICTION_TABLE}
                  WHERE DSTRB_ID = %s
                  ORDER BY RGSTR_TIME DESC
                  LIMIT 1 \
                  """
            params = (dstrb_id,)
        else:
            sql = f"""
                  SELECT *
                  FROM {PREDICTION_TABLE}
                  WHERE DSTRB_ID = %s
                    AND RGSTR_TIME <= %s
                  ORDER BY RGSTR_TIME DESC
                  LIMIT 1 \
                  """
            params = (dstrb_id, snapshot_ts)

        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()

        if not row:
            return None, f"{nid}({dstrb_id}) 예측값 없음"

        stamp = row["RGSTR_TIME"]
        if not isinstance(stamp, datetime):
            stamp = datetime.fromisoformat(str(stamp))

        try:
            values = {
                h: _prediction_value_for_horizon(row, h)
                for h in PREDICTION_HORIZONS
            }
        except ValueError as exc:
            return None, f"{nid}({dstrb_id}) {exc}"

        canonical = {
            "NODE_ID": nid,
            "DSTRB_ID": str(row["DSTRB_ID"]),
            "RGSTR_TIME": stamp,
            "PRDCT_VALUE": values[1],  # 구 코드 호환: 1분 예측
            "PREDICTIONS": values,
        }
        for h, value in values.items():
            canonical[f"VALUE_{h}min"] = value
        rows_by_node[nid] = canonical

    stamps = [row["RGSTR_TIME"] for row in rows_by_node.values()]
    batch_min = min(stamps)
    batch_max = max(stamps)
    skew = (batch_max - batch_min).total_seconds()

    if last_processed is not None and snapshot_ts is None:
        not_new = [
            f"{nid}={row['RGSTR_TIME']}"
            for nid, row in rows_by_node.items()
            if row["RGSTR_TIME"] <= last_processed
        ]
        if not_new:
            return None, "아직 새 예측 묶음 미완성: " + ", ".join(not_new)

    if skew > max_skew_sec:
        details = ", ".join(
            f"{nid}={row['RGSTR_TIME']}" for nid, row in rows_by_node.items()
        )
        return None, (
            f"예측 수행시각 차이 {skew:.0f}초 > 허용 {max_skew_sec}초: {details}"
        )

    return {
        "batch_ts": batch_max,
        "batch_min_ts": batch_min,
        "batch_skew_sec": skew,
        "rows": rows_by_node,
        "mapping": mapping,
        "horizons": PREDICTION_HORIZONS,
    }, "ready"




def floor_to_interval(dt: datetime, interval_min: int) -> datetime:
    """dt 를 interval_min 분 경계로 내림한다(interval_min 은 60의 약수)."""
    dt0 = dt.replace(second=0, microsecond=0)
    return dt0 - timedelta(minutes=dt0.minute % interval_min)


def floor_to_5min(dt: datetime) -> datetime:
    """시각을 직전 5분 경계(00/05/10/...)로 내림한다."""
    return floor_to_interval(dt, 5)


def schedule_offset_seconds(args) -> int:
    """실행 오프셋(초). --schedule-offset-sec 가 있으면 그것, 없으면 --schedule-offset-min × 60."""
    if getattr(args, "schedule_offset_sec", None) is not None:
        return int(args.schedule_offset_sec)
    return int(args.schedule_offset_min) * 60


def scheduled_slot_at_or_after(
        dt: datetime,
        offset_min: int = DEFAULT_SCHEDULE_OFFSET_MIN,
        *,
        interval_min: int = DEFAULT_INTERVAL_MIN,
        offset_sec: Optional[int] = None,
) -> datetime:
    """dt 이후(같은 분 포함) 첫 실행 슬롯 = interval_min 경계 + 오프셋.

    "같은 분 포함"은 기존 동작이다 — 슬롯 분 안에 깨어났으면 몇 초 늦었어도
    이번 슬롯을 돈다. 기본값(5분, 오프셋 1분)이면 01/06/11/16/...분이다.
    예를 들어 15:56:20에 프로세스를 시작하면 15:56 회차를 즉시 한 번 처리하고,
    15:57에 시작하면 다음 16:01 회차부터 처리한다.
    """
    offset = offset_min * 60 if offset_sec is None else offset_sec
    period = interval_min * 60
    if not 0 <= offset < period:
        raise ValueError(
            f"실행 오프셋은 0초 이상 주기({period}초) 미만이어야 합니다: {offset}초"
        )
    minute = dt.replace(second=0, microsecond=0)
    slot = floor_to_interval(minute, interval_min) + timedelta(seconds=offset)
    while slot < minute:
        slot += timedelta(minutes=interval_min)
    return slot


def latest_complete_mo_source_ts(
        conn,
        target_ts: datetime,
        max_age_min: float = DEFAULT_MO_MAX_AGE_MIN,
) -> datetime:
    """target_ts 이전의 가장 최근 '정상 완료' MO 시각을 반환한다.

    TB_TOT_ALG 요약 결과뿐 아니라 TB_FP_SI_VAL(노드), TB_FR_SI_VAL(링크) 상세 결과도
    같은 RGSTR_TIME에 존재하는 MO만 선택한다. 최신 MO가 max_age_min보다 오래됐으면
    오래된 결과의 반복 사용을 막기 위해 예외를 발생시킨다.
    """
    if max_age_min <= 0:
        raise ValueError("mo-max-age-min은 0보다 커야 합니다.")

    sql = """
          SELECT t.RGSTR_TIME
          FROM TB_TOT_ALG t
          WHERE t.FLG = %s
            AND t.RGSTR_TIME <= %s
            AND EXISTS (
              SELECT 1
              FROM TB_FP_SI_VAL n
              WHERE n.RGSTR_TIME = t.RGSTR_TIME
                AND n.FLG = %s
          )
            AND EXISTS (
              SELECT 1
              FROM TB_FR_SI_VAL l
              WHERE l.RGSTR_TIME = t.RGSTR_TIME
                AND l.FLG = %s
          )
          ORDER BY t.RGSTR_TIME DESC
          LIMIT 1 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (MO_FLAG, target_ts, MO_FLAG, MO_FLAG))
        row = cur.fetchone()

    if not row or row.get("RGSTR_TIME") is None:
        raise ValueError(
            f"CUR 원본으로 사용할 정상 MO 결과가 없습니다: "
            f"기준시각<={target_ts}, FLG='{MO_FLAG}'"
        )

    mo_ts = row["RGSTR_TIME"]
    if not isinstance(mo_ts, datetime):
        mo_ts = datetime.fromisoformat(str(mo_ts))

    age_min = (target_ts - mo_ts).total_seconds() / 60.0
    if age_min < -1e-9:
        raise ValueError(
            f"CUR 원본 MO 시각이 실행시각보다 미래입니다: MO={mo_ts}, 실행={target_ts}"
        )
    if age_min > max_age_min + 1e-9:
        raise ValueError(
            f"CUR 원본 최신 MO가 너무 오래되었습니다: "
            f"MO={mo_ts}, 실행={target_ts}, 경과={age_min:.1f}분, "
            f"허용<={max_age_min:g}분"
        )

    return mo_ts


def verify_mo_source(conn, mo_ts: datetime) -> dict:
    """CUR 원본으로 사용할 해당 시각의 MO 요약 결과 존재 여부를 확인한다."""
    sql = """
          SELECT RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL
          FROM TB_TOT_ALG
          WHERE RGSTR_TIME = %s AND FLG = %s
          LIMIT 1 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (mo_ts, MO_FLAG))
        row = cur.fetchone()
    if not row:
        raise ValueError(
            f"CUR 원본 MO 결과가 없습니다: TB_TOT_ALG RGSTR_TIME={mo_ts}, FLG='{MO_FLAG}'"
        )
    return row


def copy_mo_to_cur(conn, source_ts: datetime, target_ts: datetime) -> dict:
    """직전 MO 결과를 재해석하지 않고 CUR 결과로 복사한다.

    source: TB_FP_SI_VAL / TB_FR_SI_VAL / TB_TOT_ALG, FLG='mo'
    target: TB_FP_VAL / TB_FR_VAL / TB_TOT_ALG, FLG='CUR'
    target의 RGSTR_TIME은 01/06/11/... 실행 슬롯을 사용한다.
    """
    verify_mo_source(conn, source_ts)

    count_sqls = {
        "node": "SELECT COUNT(*) AS CNT FROM TB_FP_SI_VAL WHERE RGSTR_TIME=%s AND FLG=%s",
        "link": "SELECT COUNT(*) AS CNT FROM TB_FR_SI_VAL WHERE RGSTR_TIME=%s AND FLG=%s",
    }
    source_counts = {}
    with conn.cursor() as cur:
        for key, sql in count_sqls.items():
            cur.execute(sql, (source_ts, MO_FLAG))
            row = cur.fetchone() or {}
            source_counts[key] = int(row.get("CNT") or 0)

    if source_counts["node"] <= 0 or source_counts["link"] <= 0:
        raise ValueError(
            f"CUR 원본 MO 상세 결과가 부족합니다: {source_ts}, "
            f"node={source_counts['node']}, link={source_counts['link']}"
        )

    # 저장 대상(TB_FP_VAL/TB_FR_VAL/TB_TOT_ALG)만 --result-table-suffix 를 따른다.
    # FROM 의 MO 원본(TB_FP_SI_VAL/TB_FR_SI_VAL/TB_TOT_ALG FLG='mo')은 항상 운영 테이블이다.
    node_sql = f"""
               INSERT INTO {result_table("TB_FP_VAL")}
                   (NODE_ID, FP_VAL, FP_ALG_RST_VAL, RGSTR_TIME, FLG)
               SELECT NODE_ID, FP_VAL, FP_ALG_RST_VAL, %s, %s
               FROM TB_FP_SI_VAL
               WHERE RGSTR_TIME = %s AND FLG = %s
               ON DUPLICATE KEY UPDATE
                                    FP_VAL=VALUES(FP_VAL),
                                    FP_ALG_RST_VAL=VALUES(FP_ALG_RST_VAL) \
               """
    link_sql = f"""
               INSERT INTO {result_table("TB_FR_VAL")}
                   (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, LINK_VAL, FLW_ALG_RST_VAL, FLG)
               SELECT LINK_ID, HH_LOSS_VAL, %s, LINK_VAL, FLW_ALG_RST_VAL, %s
               FROM TB_FR_SI_VAL
               WHERE RGSTR_TIME = %s AND FLG = %s
               ON DUPLICATE KEY UPDATE
                                    HH_LOSS_VAL=VALUES(HH_LOSS_VAL),
                                    LINK_VAL=VALUES(LINK_VAL),
                                    FLW_ALG_RST_VAL=VALUES(FLW_ALG_RST_VAL) \
               """
    total_sql = f"""
                INSERT INTO {result_table("TB_TOT_ALG")}
                    (RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL, FLG)
                SELECT %s, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL, %s
                FROM TB_TOT_ALG
                WHERE RGSTR_TIME = %s AND FLG = %s
                ON DUPLICATE KEY UPDATE
                                     HH_LOSS_VAL_TOT=VALUES(HH_LOSS_VAL_TOT),
                                     FLW_VAL=VALUES(FLW_VAL),
                                     FP_VAL=VALUES(FP_VAL),
                                     FP_ALG_RST_VAL=VALUES(FP_ALG_RST_VAL) \
                """

    with conn.cursor() as cur:
        cur.execute(node_sql, (target_ts, CUR_FLAG, source_ts, MO_FLAG))
        node_affected = int(cur.rowcount)
        cur.execute(link_sql, (target_ts, CUR_FLAG, source_ts, MO_FLAG))
        link_affected = int(cur.rowcount)
        cur.execute(total_sql, (target_ts, CUR_FLAG, source_ts, MO_FLAG))
        total_affected = int(cur.rowcount)

    return {
        "source_ts": source_ts,
        "target_ts": target_ts,
        "source_node_count": source_counts["node"],
        "source_link_count": source_counts["link"],
        "node_affected": node_affected,
        "link_affected": link_affected,
        "total_affected": total_affected,
    }

def validate_runtime_inputs(readings: Dict[str, Reading], valve_mode: str) -> None:
    """PRE 계산에 필수인 함열/펌프/밸브 운전조건 검증."""
    missing = []

    if HAMYEOL_FLOW_TAG not in readings:
        missing.append(f"{HAMYEOL_FLOW_TAG} (함열가압장 공급유량)")
    elif readings[HAMYEOL_FLOW_TAG].value < 0:
        raise ValueError("함열가압장 실측 유량은 양수 크기로 저장되어야 합니다.")

    for pid, run_tag, hz_tag in PUMPS:
        if run_tag not in readings:
            missing.append(f"{run_tag} ({pid}: 운전상태)")
            continue
        run_value = readings[run_tag].value
        if run_value < 0:
            raise ValueError(f"{pid} 가동태그가 음수입니다: {run_value}")
        if run_value > 0:
            if hz_tag not in readings:
                missing.append(f"{hz_tag} ({pid}: 운전 중 주파수)")
            elif not 1.0 <= readings[hz_tag].value <= 60.0:
                raise ValueError(
                    f"{pid} 운전 주파수가 1~60 Hz 범위 밖입니다: "
                    f"{readings[hz_tag].value}"
                )

    if valve_mode in ("opening", "measured"):
        for vid in ("국가산단밸브", "지방산단밸브"):
            tag = VALVE_META[vid]["opening"]
            if tag not in readings:
                missing.append(f"{tag} ({vid}: 개도율)")

    if valve_mode == "measured":
        meta = VALVE_META["국가산단밸브"]
        for key in ("flow", "upstream_pressure", "downstream_pressure"):
            tag = meta.get(key)
            if tag and tag not in readings:
                missing.append(f"{tag} (국가산단밸브 measured:{key})")

    if missing:
        raise ValueError("PRE 해석에 필요한 실측 운전조건이 없습니다: " + ", ".join(missing))

def resolve_input_path(value: Path, label: str, *, directory: bool = False) -> Path:
    """명시된 절대 경로는 그대로, 상대 경로는 CWD 다음 코드 폴더에서 찾는다."""
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
    """WNTR의 Error 200에 감춰진 구체적인 INP 오류를 표시하고 기록한다."""
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



def configure_snapshot(
        wn,
        readings: Dict[str, Reading],
        prediction_bundle: dict,
        horizon_min: int,
        reference_hz: float,
        ids: IdMaps,
        keep_inp_demands: bool = False,
) -> tuple:
    """지정 Horizon 예측 Demand + 함열 실측 공급 + 현재 펌프/밸브 상태를 적용."""
    import wntr

    if not math.isfinite(reference_hz) or reference_hz <= 0:
        raise ValueError("성능곡선 기준 주파수는 양수여야 합니다.")

    required_nodes = list(PREDICTION_NODE_IDS) + list(ZERO_DEMAND_NODE_IDS) + [HAMYEOL_NODE_ID]
    for nid in required_nodes:
        if ids.node.get(nid, nid) not in wn.junction_name_list:
            raise ValueError(f"PRE 적용 노드가 INP의 Junction에 없습니다: {nid}")
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

    # 모든 Junction Demand를 먼저 0으로 만든다.
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

    def set_demand(nid: str, q_m3h: float) -> None:
        node = wn.get_node(ids.node.get(nid, nid))
        demands = node.demand_timeseries_list
        if not demands:
            node.add_demand(q_m3h / 3600.0, None)
        else:
            demands[0].base_value = q_m3h / 3600.0
            for demand in list(demands)[1:]:
                demand.base_value = 0.0

    assigned = {}

    # 예측 대상 노드: Horizon별 예측수요 적용
    value_key = f"VALUE_{horizon_min}min"
    for nid in PREDICTION_NODE_IDS:
        row = prediction_bundle["rows"][nid]
        q_m3h = float(row[value_key])
        set_demand(nid, q_m3h)
        assigned[nid] = q_m3h
        print(
            f"[PREDICT {horizon_min:>2}m] {nid}: {q_m3h:,.3f} m3/h [수요] "
            f"(DSTRB_ID={row['DSTRB_ID']}, RGSTR_TIME={row['RGSTR_TIME']})"
        )

    # 28번은 별도 예측값 없이 0 고정
    for nid in ZERO_DEMAND_NODE_IDS:
        set_demand(nid, 0.0)
        assigned[nid] = 0.0
        print(f"[DEMAND] {nid}: 0.000 m3/h [예측 미사용 → 0]")

    # 함열가압장은 실제 공급량
    hamyeol_actual = float(readings[HAMYEOL_FLOW_TAG].value)
    hamyeol_q = -hamyeol_actual
    set_demand(HAMYEOL_NODE_ID, hamyeol_q)
    assigned[HAMYEOL_NODE_ID] = hamyeol_q
    print(
        f"[SUPPLY] {HAMYEOL_NODE_ID}: 실측 {hamyeol_actual:,.3f} m3/h "
        f"→ 적용 {hamyeol_q:,.3f} m3/h [공급]"
    )

    # 펌프는 MO와 동일하게 실제 운전상태/Hz 반영
    pump_rows = []
    for pid, run_tag, hz_tag in PUMPS:
        pump = wn.get_link(ids.link.get(pid, pid))
        running = readings[run_tag].value > 0
        hz = readings[hz_tag].value if running else None
        speed = hz / reference_hz if running else 0.0

        pump.speed_pattern_name = None
        pump.base_speed = speed
        pump.initial_status = (
            wntr.network.LinkStatus.Open if running
            else wntr.network.LinkStatus.Closed
        )

        pump_rows.append({
            "PUMP_ID": pid,
            "RUN_VALUE": readings[run_tag].value,
            "HZ_VALUE": hz,
            "REFERENCE_HZ": reference_hz,
            "APPLIED_STATUS": "OPEN" if running else "CLOSED",
            "APPLIED_SPEED": speed,
        })
        print(
            f"[PUMP] {pid}: {pump_rows[-1]['APPLIED_STATUS']}, "
            f"실측 {hz} Hz, 상대속도 {speed:.6f}"
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
    """log(R) 선형 보간. 관측 범위 밖은 외삽하지 않는다."""
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
    """구경 미확인 상태에서도 측정한 수리저항 R을 보존하는 등가 TCV 모델."""
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
                if opening < 95.0:
                    raise ValueError(f"지방산단 개도율 {opening:.5f}%: 후단 압력과 부분 개방 곡선이 없어 95% 미만을 적용할 수 없습니다.")
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
    """밸브 해석 결과 정리. PRE Demand는 예측값이므로 MO 전용 Demand-태그 경고는 제외."""
    warnings = []
    heads = results.node["head"].loc[0]
    for row in rows:
        lid = ids.link.get(row["VALVE_ID"], row["VALVE_ID"])
        link = wn.get_link(lid)
        sign = row["MEASURED_FLOW_SIGN_TO_INP"]
        q = float(results.link["flowrate"].loc[0, lid]) * 3600.0 * sign
        row["SIM_FLOW_M3H_MEASURED_DIRECTION"] = q
        row["SIM_HEADLOSS_M_MEASURED_DIRECTION"] = (
                float(heads[link.start_node_name] - heads[link.end_node_name]) * sign
        )
        row["SOLVED_STATUS"] = int(results.link["status"].loc[0, lid])

        measured = row["MEASURED_FLOW_M3H"]
        row["FLOW_ERROR_M3H"] = q - measured if measured is not None else None
        row["FLOW_ERROR_PERCENT"] = (
            100 * (q - measured) / measured
            if measured is not None and abs(measured) > 1e-9
            else None
        )

        if (
                measured is not None
                and measured > 100
                and (abs(q) < 1.0 or abs(q - measured) / measured > 0.2)
        ):
            message = (
                f"{row['VALVE_ID']}: 실측={measured:.3f}, "
                f"해석={q:.6f} m3/h. 관로 개폐 상태와 하류 수요를 확인하세요."
            )
            key = ids.link.get("Bks-1874", "Bks-1874")
            if (
                    row["VALVE_ID"] == "국가산단밸브"
                    and key in wn.pipe_name_list
                    and str(wn.get_link(key).initial_status).upper() == "CLOSED"
            ):
                message += (
                    " 현재 INP에서 Bks-1874가 CLOSED입니다. "
                    "국가지선 수요 중복 여부를 확인하세요."
                )
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
    """EPANET에 ASCII 상대 경로만 전달하여 한글 경로 인코딩 오류를 방지한다.

    WNTR의 ENopen은 INP/RPT/BIN 경로를 latin-1로 인코딩한다. Python의
    os.chdir은 한글 경로를 처리하므로, 결과 폴더를 작업 폴더로 삼고 엔진에는
    epanet.inp 같은 영문 파일명만 전달한다. 이 CLI는 단일 스레드로 실행한다.
    """
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



def build_results(
        wn,
        results,
        assigned,
        pump_rows,
        target: datetime,
        ids: IdMaps,
):
    """
    기존 test.py PRE 저장 형식에 맞춰:
      - 전체 노드 해석압력(m)
      - 전체 Pipe 해석유량(m3/h), 관로 수두손실(m)
      - 전체 Pipe 손실 합계
    를 만든다.
    """
    pressure = results.node["pressure"]
    if list(pressure.index) != [0]:
        raise RuntimeError(
            f"0초 한 시점이어야 합니다. 실제 결과 시점: {list(pressure.index)}"
        )

    p = pressure.loc[0]
    h = results.node["head"].loc[0]
    q = results.link["flowrate"].loc[0]
    demand = results.node["demand"].loc[0]

    if not all(math.isfinite(float(x)) for x in list(p) + list(h) + list(q)):
        raise RuntimeError("해석 결과에 유효하지 않은 수치가 있습니다. epanet.rpt를 확인하세요.")

    rn = ids.reverse_node
    rl = ids.reverse_link

    node_rows = []
    for model_nid, node in wn.nodes():
        original_nid = rn.get(model_nid, model_nid)
        node_rows.append({
            "NODE_ID": original_nid,
            "FP_ALG_RST_VAL": float(p[model_nid]),  # 기존 PRE 테이블 의미: m
            "RGSTR_TIME": target,
            "FLG": RESULT_FLAG,
            "NODE_TYPE": node.node_type,
            "PRESSURE_M": float(p[model_nid]),
            "HEAD_M": float(h[model_nid]),
            "DEMAND_M3H": float(demand[model_nid]) * 3600.0,
            "INPUT_DEMAND_M3H": assigned.get(original_nid),
        })

    link_rows = []
    loss_total = 0.0
    for model_lid, pipe in wn.pipes():
        original_lid = rl.get(model_lid, model_lid)
        loss = abs(
            float(h[pipe.start_node_name]) - float(h[pipe.end_node_name])
        )
        loss_total += loss
        link_rows.append({
            "LINK_ID": original_lid,
            "HH_LOSS_VAL": loss,
            "RGSTR_TIME": target,
            "FLG": RESULT_FLAG,
            "FLW_ALG_RST_VAL": float(q[model_lid]) * 3600.0,
            "FLOW_UNIT": "m3/h",
            "FROM_NODE": rn.get(pipe.start_node_name, pipe.start_node_name),
            "TO_NODE": rn.get(pipe.end_node_name, pipe.end_node_name),
        })

    for row in pump_rows:
        model_pid = ids.link.get(row["PUMP_ID"], row["PUMP_ID"])
        row["FLOW_M3H"] = float(q[model_pid]) * 3600.0
        row["SOLVED_STATUS"] = float(results.link["status"].loc[0, model_pid])

    rep_model_nid = ids.node.get(
        REPRESENTATIVE_PRESSURE_NODE, REPRESENTATIVE_PRESSURE_NODE
    )
    if rep_model_nid not in p.index:
        raise ValueError(
            f"대표 압력 노드가 해석 결과에 없습니다: {REPRESENTATIVE_PRESSURE_NODE}"
        )
    representative_pressure_m = float(p[rep_model_nid])

    return node_rows, link_rows, pump_rows, loss_total, representative_pressure_m


def write_network_results(output: Path, wn, results, ids: IdMaps) -> None:
    """전체 관망의 단일 시점 결과를 원본 ID로 내보낸다. 유량은 링크 정방향 기준."""
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




def merge_horizon_results(
        results_by_horizon: Dict[int, dict],
        target: datetime,
) -> tuple[list, list, dict]:
    """1/5/15/30분 독립 해석결과를 NODE/LINK별 한 행(wide)으로 합친다."""
    missing = [h for h in PREDICTION_HORIZONS if h not in results_by_horizon]
    if missing:
        raise ValueError(f"PRE Horizon 해석결과 누락: {missing}")

    node_map: Dict[str, dict] = {}
    link_map: Dict[str, dict] = {}
    total_row = {"RGSTR_TIME": target, "FLG": RESULT_FLAG}

    for horizon in PREDICTION_HORIZONS:
        pack = results_by_horizon[horizon]
        suffix = f"{horizon}MIN"

        for r in pack["node_rows"]:
            row = node_map.setdefault(
                r["NODE_ID"],
                {"NODE_ID": r["NODE_ID"], "RGSTR_TIME": target, "FLG": RESULT_FLAG},
            )
            row[f"FP_ALG_RST_VAL_{suffix}"] = r["FP_ALG_RST_VAL"]

        for r in pack["link_rows"]:
            row = link_map.setdefault(
                r["LINK_ID"],
                {"LINK_ID": r["LINK_ID"], "RGSTR_TIME": target, "FLG": RESULT_FLAG},
            )
            row[f"HH_LOSS_VAL_{suffix}"] = r["HH_LOSS_VAL"]
            row[f"FLW_ALG_RST_VAL_{suffix}"] = r["FLW_ALG_RST_VAL"]

        total_row[f"HH_LOSS_VAL_TOT_{suffix}"] = pack["loss_total"]
        total_row[f"FP_ALG_RST_VAL_{suffix}"] = pack["rep_pressure_m"]

    # 기존 PRE 소비 코드 호환을 위해 legacy 컬럼은 1분 결과를 유지한다.
    for row in node_map.values():
        row["FP_ALG_RST_VAL"] = row["FP_ALG_RST_VAL_1MIN"]
    for row in link_map.values():
        row["HH_LOSS_VAL"] = row["HH_LOSS_VAL_1MIN"]
        row["FLW_ALG_RST_VAL"] = row["FLW_ALG_RST_VAL_1MIN"]
    total_row["HH_LOSS_VAL_TOT"] = total_row["HH_LOSS_VAL_TOT_1MIN"]
    total_row["FP_ALG_RST_VAL"] = total_row["FP_ALG_RST_VAL_1MIN"]

    return list(node_map.values()), list(link_map.values()), total_row


def save_results_db(
        conn,
        node_rows,
        link_rows,
        total_row: dict,
        *,
        cur_source_ts: Optional[datetime] = None,
        cur_target_ts: Optional[datetime] = None,
) -> dict:
    """CUR 복사 후 PRE 1/5/15/30분 wide 결과를 하나의 transaction으로 저장한다.

    저장 테이블은 --result-table-suffix 를 따른다(섀도우 _SH). 2026-10-01 드롭의 wide INSERT 위에
    result_table() 만 씌운 것이며 컬럼 목록은 벤더 원문 그대로다.
    """
    node_sql = f"""
               INSERT INTO {result_table("TB_FP_VAL")} (
                   NODE_ID, FP_ALG_RST_VAL, RGSTR_TIME, FLG,
                   FP_ALG_RST_VAL_1MIN, FP_ALG_RST_VAL_5MIN,
                   FP_ALG_RST_VAL_15MIN, FP_ALG_RST_VAL_30MIN
               ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
                                    FP_ALG_RST_VAL=VALUES(FP_ALG_RST_VAL),
                                    FP_ALG_RST_VAL_1MIN=VALUES(FP_ALG_RST_VAL_1MIN),
                                    FP_ALG_RST_VAL_5MIN=VALUES(FP_ALG_RST_VAL_5MIN),
                                    FP_ALG_RST_VAL_15MIN=VALUES(FP_ALG_RST_VAL_15MIN),
                                    FP_ALG_RST_VAL_30MIN=VALUES(FP_ALG_RST_VAL_30MIN) \
               """
    link_sql = f"""
               INSERT INTO {result_table("TB_FR_VAL")} (
                   LINK_ID, HH_LOSS_VAL, RGSTR_TIME, FLG, FLW_ALG_RST_VAL,
                   HH_LOSS_VAL_1MIN, HH_LOSS_VAL_5MIN, HH_LOSS_VAL_15MIN, HH_LOSS_VAL_30MIN,
                   FLW_ALG_RST_VAL_1MIN, FLW_ALG_RST_VAL_5MIN,
                   FLW_ALG_RST_VAL_15MIN, FLW_ALG_RST_VAL_30MIN
               ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
                                    HH_LOSS_VAL=VALUES(HH_LOSS_VAL),
                                    FLW_ALG_RST_VAL=VALUES(FLW_ALG_RST_VAL),
                                    HH_LOSS_VAL_1MIN=VALUES(HH_LOSS_VAL_1MIN),
                                    HH_LOSS_VAL_5MIN=VALUES(HH_LOSS_VAL_5MIN),
                                    HH_LOSS_VAL_15MIN=VALUES(HH_LOSS_VAL_15MIN),
                                    HH_LOSS_VAL_30MIN=VALUES(HH_LOSS_VAL_30MIN),
                                    FLW_ALG_RST_VAL_1MIN=VALUES(FLW_ALG_RST_VAL_1MIN),
                                    FLW_ALG_RST_VAL_5MIN=VALUES(FLW_ALG_RST_VAL_5MIN),
                                    FLW_ALG_RST_VAL_15MIN=VALUES(FLW_ALG_RST_VAL_15MIN),
                                    FLW_ALG_RST_VAL_30MIN=VALUES(FLW_ALG_RST_VAL_30MIN) \
               """
    total_sql = f"""
                INSERT INTO {result_table("TB_TOT_ALG")} (
                    RGSTR_TIME, HH_LOSS_VAL_TOT, FP_ALG_RST_VAL, FLG,
                    HH_LOSS_VAL_TOT_1MIN, HH_LOSS_VAL_TOT_5MIN,
                    HH_LOSS_VAL_TOT_15MIN, HH_LOSS_VAL_TOT_30MIN,
                    FP_ALG_RST_VAL_1MIN, FP_ALG_RST_VAL_5MIN,
                    FP_ALG_RST_VAL_15MIN, FP_ALG_RST_VAL_30MIN
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                                     HH_LOSS_VAL_TOT=VALUES(HH_LOSS_VAL_TOT),
                                     FP_ALG_RST_VAL=VALUES(FP_ALG_RST_VAL),
                                     HH_LOSS_VAL_TOT_1MIN=VALUES(HH_LOSS_VAL_TOT_1MIN),
                                     HH_LOSS_VAL_TOT_5MIN=VALUES(HH_LOSS_VAL_TOT_5MIN),
                                     HH_LOSS_VAL_TOT_15MIN=VALUES(HH_LOSS_VAL_TOT_15MIN),
                                     HH_LOSS_VAL_TOT_30MIN=VALUES(HH_LOSS_VAL_TOT_30MIN),
                                     FP_ALG_RST_VAL_1MIN=VALUES(FP_ALG_RST_VAL_1MIN),
                                     FP_ALG_RST_VAL_5MIN=VALUES(FP_ALG_RST_VAL_5MIN),
                                     FP_ALG_RST_VAL_15MIN=VALUES(FP_ALG_RST_VAL_15MIN),
                                     FP_ALG_RST_VAL_30MIN=VALUES(FP_ALG_RST_VAL_30MIN) \
                """

    conn.begin()
    try:
        cur_copy = None
        if (cur_source_ts is None) != (cur_target_ts is None):
            raise ValueError("CUR 복사에는 cur_source_ts와 cur_target_ts가 모두 필요합니다.")
        if cur_source_ts is not None:
            cur_copy = copy_mo_to_cur(conn, cur_source_ts, cur_target_ts)

        with conn.cursor() as cur:
            node_count = cur.executemany(node_sql, [(
                r["NODE_ID"], r["FP_ALG_RST_VAL"], r["RGSTR_TIME"], r["FLG"],
                r["FP_ALG_RST_VAL_1MIN"], r["FP_ALG_RST_VAL_5MIN"],
                r["FP_ALG_RST_VAL_15MIN"], r["FP_ALG_RST_VAL_30MIN"],
            ) for r in node_rows])

            link_count = cur.executemany(link_sql, [(
                r["LINK_ID"], r["HH_LOSS_VAL"], r["RGSTR_TIME"], r["FLG"], r["FLW_ALG_RST_VAL"],
                r["HH_LOSS_VAL_1MIN"], r["HH_LOSS_VAL_5MIN"],
                r["HH_LOSS_VAL_15MIN"], r["HH_LOSS_VAL_30MIN"],
                r["FLW_ALG_RST_VAL_1MIN"], r["FLW_ALG_RST_VAL_5MIN"],
                r["FLW_ALG_RST_VAL_15MIN"], r["FLW_ALG_RST_VAL_30MIN"],
            ) for r in link_rows])

            total_count = cur.execute(total_sql, (
                total_row["RGSTR_TIME"], total_row["HH_LOSS_VAL_TOT"],
                total_row["FP_ALG_RST_VAL"], total_row["FLG"],
                total_row["HH_LOSS_VAL_TOT_1MIN"], total_row["HH_LOSS_VAL_TOT_5MIN"],
                total_row["HH_LOSS_VAL_TOT_15MIN"], total_row["HH_LOSS_VAL_TOT_30MIN"],
                total_row["FP_ALG_RST_VAL_1MIN"], total_row["FP_ALG_RST_VAL_5MIN"],
                total_row["FP_ALG_RST_VAL_15MIN"], total_row["FP_ALG_RST_VAL_30MIN"],
            ))
        conn.commit()
        result = {
            "node_insert_count": int(node_count),
            "link_insert_count": int(link_count),
            "total_insert_count": int(total_count),
        }
        if cur_copy is not None:
            result["cur_copy"] = cur_copy
        return result
    except Exception:
        conn.rollback()
        raise




def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="군산 최근 정상 MO 결과의 CUR 복사 + 1/5/15/30분 수요예측(PRE) 관망해석을 5분 주기로 수행합니다.",
        epilog=(
            '기본: python main_epa_gs.py  (01/06/11/16/...분 실행) / '
            '과거 PRE 1회: --snapshot --ts "YYYY-MM-DD HH:MM:SS" --no-save-db'
        ),
    )
    ap.add_argument(
        "--snapshot",
        action="store_true",
        help="--ts 이하 최신 예측 묶음을 사용해 한 번만 해석하고 종료"
    )
    ap.add_argument(
        "--ts",
        default=None,
        help="snapshot에서 예측값을 찾을 상한 시각. 예: 2026-09-11 10:05:00"
    )
    ap.add_argument("--inp", type=Path, default=SCRIPT_DIR / "epa_model.inp")
    ap.add_argument("--conn", type=Path, default=SCRIPT_DIR / "connections.json")
    ap.add_argument("--conn-key", default="maria-ems-db-gu")
    ap.add_argument(
        "--fallback-sec",
        type=int,
        default=600,
        help="펌프/밸브/함열 실측값의 과거 허용범위(초). 기본 600"
    )
    ap.add_argument(
        "--prediction-max-skew-sec",
        type=int,
        default=120,
        help="수요예측 대상 간 수행시각 최대 허용차(초). 기본 120"
    )
    ap.add_argument(
        "--mo-max-age-min",
        type=float,
        default=DEFAULT_MO_MAX_AGE_MIN,
        help="CUR 원본으로 허용할 최근 정상 MO의 최대 경과시간(분). 기본 10"
    )
    ap.add_argument(
        "--interval-min",
        type=int,
        default=DEFAULT_INTERVAL_MIN,
        choices=list(ALLOWED_INTERVAL_MIN),
        help="PRE 실행 주기(분). 기본 5. 수요예측 1분 주기에 맞추려면 1"
    )
    ap.add_argument(
        "--schedule-offset-min",
        type=int,
        default=DEFAULT_SCHEDULE_OFFSET_MIN,
        help="주기 경계 대비 실행 분 오프셋(0 이상 주기 미만). 기본 1 = 01/06/11/16/...분"
    )
    ap.add_argument(
        "--schedule-offset-sec",
        type=int,
        default=None,
        help="주기 경계 대비 실행 초 오프셋. 주면 --schedule-offset-min 대신 쓴다. "
             "1분 주기에서는 필수다(예: 45, 수요예측이 :30초에 적재한 뒤)"
    )
    ap.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="loop 성공 실행 횟수 제한. 0=무제한"
    )
    ap.add_argument(
        "--reference-hz",
        type=float,
        default=60.0,
        help="INP 펌프 성능곡선 기준 Hz"
    )
    ap.add_argument(
        "--inp-value-unit",
        choices=["file", "CMH", "CMD"],
        default=DEFAULT_INP_VALUE_UNIT,
        help="군산 기본 CMH=m3/h"
    )
    ap.add_argument(
        "--pressure-unit",
        choices=["legacy_div10", "kgf_cm2", "bar", "MPa", "kPa", "m"],
        default="legacy_div10",
        help="밸브 압력 실측값 환산용. TB_FP_VAL의 PRE 해석압력은 기존 코드처럼 m로 저장"
    )
    # 이전 실행문 호환용. 운영 버전은 상세 결과폴더를 만들지 않는다.
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=SCRIPT_DIR / "results_gunsan_pre",
        help=argparse.SUPPRESS,
    )
    ap.add_argument(
        "--keep-inp-demands",
        action="store_true",
        help="비교용. 기본은 기존 INP 고정 Demand를 모두 0으로 초기화"
    )
    ap.add_argument(
        "--no-save-db",
        dest="save_db",
        action="store_false",
        help="CUR 복사 및 PRE DB 결과 저장을 생략하고 PRE 계산만 수행"
    )
    ap.set_defaults(save_db=True)
    ap.add_argument(
        "--prediction-table",
        default="TB_CTR_TNK_RST",
        help="수요예측 조회 테이블. 기본 TB_CTR_TNK_RST. 섀도우는 TB_CTR_TNK_RST_SH"
    )
    ap.add_argument(
        "--result-table-suffix",
        default="",
        help="PRE/CUR 저장 테이블 접미사. 기본 없음. 섀도우는 _SH "
             "(TB_FP_VAL_SH / TB_FR_VAL_SH / TB_TOT_ALG_SH 를 DBA 가 미리 만들어야 한다). "
             "MO 원본은 항상 운영 테이블에서 읽는다"
    )
    ap.add_argument(
        "--valve-mode",
        choices=["opening", "measured", "open", "inp"],
        default="opening",
        help="MO와 동일. 운영 기본 opening"
    )
    ap.add_argument("--valve-model", type=Path, default=DEFAULT_VALVE_MODEL)
    ap.add_argument(
        "--valve-csv-dir",
        type=Path,
        help="선택: 밸브 태그 CSV 폴더. 해당 태그는 DB값보다 우선"
    )
    ap.add_argument(
        "--valve-sensor-dz-m",
        type=float,
        help="밸브 전단-후단 압력계 높이차(m)"
    )
    ap.add_argument(
        "--valve-max-skew-sec",
        type=int,
        default=60,
        help="measured 밸브모드 계측 태그간 최대 시각차"
    )
    ap.add_argument(
        "--pipe-status",
        action="append",
        default=[],
        metavar="PIPE=OPEN|CLOSED",
        help="선택 관로 상태 비교용 override"
    )
    return ap




def run_once(
        args,
        prediction_bundle: Optional[dict] = None,
        readings: Optional[Dict[str, Reading]] = None,
        *,
        result_ts: Optional[datetime] = None,
        cur_source_ts: Optional[datetime] = None,
) -> int:
    """PRE 한 회차에서 1/5/15/30분 수요를 각각 독립 Snapshot으로 해석한다."""
    started = time.perf_counter()
    if args.fallback_sec < 0:
        raise ValueError("--fallback-sec는 0 이상이어야 합니다.")
    if args.prediction_max_skew_sec < 0:
        raise ValueError("--prediction-max-skew-sec는 0 이상이어야 합니다.")

    args.inp = resolve_input_path(args.inp, "INP 파일")
    args.conn = resolve_input_path(args.conn, "connections 파일")
    if args.valve_mode == "opening":
        args.valve_model = resolve_input_path(args.valve_model, "밸브 보정 파일")
    if args.valve_csv_dir is not None:
        args.valve_csv_dir = resolve_input_path(
            args.valve_csv_dir, "밸브 CSV 폴더", directory=True
        )

    try:
        import wntr  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "필요 패키지 설치: python -m pip install wntr pandas pymysql"
        ) from exc

    if prediction_bundle is None or readings is None:
        if not args.snapshot or not args.ts:
            raise ValueError("내부 입력이 없으면 --snapshot --ts가 필요합니다.")
        try:
            snapshot_ts = datetime.fromisoformat(str(args.ts))
        except ValueError as exc:
            raise ValueError("시각 형식은 YYYY-MM-DD HH:MM:SS입니다.") from exc

        cfg = load_config(args.conn, args.conn_key)
        conn = connect_db(cfg)
        try:
            mapping = load_prediction_mapping(conn)
            prediction_bundle, reason = fetch_prediction_bundle(
                conn,
                mapping,
                snapshot_ts=snapshot_ts,
                max_skew_sec=args.prediction_max_skew_sec,
            )
            if prediction_bundle is None:
                raise ValueError(f"snapshot 예측 묶음을 찾지 못했습니다: {reason}")
            input_target = prediction_bundle["batch_ts"]
            readings = fetch_runtime_readings(
                conn, input_target, args.fallback_sec, args.valve_mode
            )
        finally:
            conn.close()
    else:
        input_target = prediction_bundle["batch_ts"]

    target = result_ts if result_ts is not None else input_target

    if args.valve_csv_dir:
        csv_readings, provided = read_valve_exports(
            args.valve_csv_dir, input_target, args.fallback_sec
        )
        for tag in provided:
            readings.pop(tag, None)
        readings.update(csv_readings)

    validate_runtime_inputs(readings, args.valve_mode)

    temp_ctx = tempfile.TemporaryDirectory(prefix="epanet_pre_gs_")
    output = Path(temp_ctx.name)

    print(
        f"[INFO] PRE 예측 묶음 시각: {input_target}; "
        f"결과 기준시각: {target}; Horizons={PREDICTION_HORIZONS}"
    )
    print(
        f"[INFO] 예측 수행시각 범위: {prediction_bundle['batch_min_ts']} "
        f"~ {prediction_bundle['batch_ts']} "
        f"(차이 {prediction_bundle['batch_skew_sec']:.0f}초)"
    )
    print(f"[INFO] 사용 INP: {args.inp}")
    print(f"[INFO] 접속 설정 파일: {args.conn}; 접속키: {args.conn_key}")

    for nid in PREDICTION_NODE_IDS:
        row = prediction_bundle["rows"][nid]
        values = ", ".join(
            f"{h}m={row[f'VALUE_{h}min']:,.3f}"
            for h in PREDICTION_HORIZONS
        )
        print(f"[MAPPING] {nid} <- {row['DSTRB_ID']} | {values} m3/h")

    info = prepare_inp(
        args.inp,
        output / "normalized_input.inp",
        args.inp_value_unit,
        )
    ids = IdMaps.from_dict(info.pop("id_maps"))

    results_by_horizon: Dict[int, dict] = {}
    try:
        for horizon in PREDICTION_HORIZONS:
            print(f"\n[HORIZON] +{horizon}분 관망해석 시작")
            wn = None
            results = None
            try:
                wn = load_network_model(output / "normalized_input.inp")

                missing_optional = sorted(set(runtime_tags(args.valve_mode)) - set(readings))
                if missing_optional:
                    print(
                        "[WARN] 미조회 선택/진단용 실측태그: "
                        + ", ".join(missing_optional)
                    )

                assigned, pump_rows, _ = configure_snapshot(
                    wn,
                    readings,
                    prediction_bundle,
                    horizon,
                    args.reference_hz,
                    ids,
                    args.keep_inp_demands,
                )

                apply_pipe_overrides(wn, ids, args.pipe_status)

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

                results = run_epanet_snapshot(wn, output)

                valve_warnings = finish_valve_results(wn, results, ids, valve_rows)
                for message in valve_warnings:
                    if "독립적인 밸브 유량 검증값이 아닙니다" in message:
                        continue
                    print("[WARN] " + message)

                node_rows, link_rows, pump_rows, loss_total, rep_pressure_m = build_results(
                    wn, results, assigned, pump_rows, target, ids
                )

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
                        f"[WARN +{horizon}m] 음압 Junction {len(negative_nodes)}개 "
                        f"(양수 수요가 있는 음압 노드 {len(negative_demand_nodes)}개)."
                    )

                results_by_horizon[horizon] = {
                    "node_rows": node_rows,
                    "link_rows": link_rows,
                    "pump_rows": pump_rows,
                    "loss_total": loss_total,
                    "rep_pressure_m": rep_pressure_m,
                }
                print(
                    f"[RESULT +{horizon}m] 대표압력 {REPRESENTATIVE_PRESSURE_NODE}="
                    f"{rep_pressure_m:.6f}m, HH_LOSS_VAL_TOT={loss_total:.6f}m"
                )
            finally:
                if results is not None:
                    del results
                if wn is not None:
                    del wn
                gc.collect()

        node_rows, link_rows, total_row = merge_horizon_results(
            results_by_horizon, target
        )

        if args.save_db:
            save_conn = connect_db(load_config(args.conn, args.conn_key))
            try:
                counts = save_results_db(
                    save_conn,
                    node_rows,
                    link_rows,
                    total_row,
                    cur_source_ts=cur_source_ts,
                    cur_target_ts=target if cur_source_ts is not None else None,
                )
            finally:
                save_conn.close()

            if counts.get("cur_copy"):
                cc = counts["cur_copy"]
                print(
                    "[OK] CUR 복사 완료: "
                    f"MO {cc['source_ts']} -> CUR {cc['target_ts']} "
                    f"(node={cc['source_node_count']}, link={cc['source_link_count']})"
                )
            print(
                "[OK] PRE 1/5/15/30분 DB 저장 완료: "
                f"{result_table('TB_FP_VAL')}={counts['node_insert_count']}, "
                f"{result_table('TB_FR_VAL')}={counts['link_insert_count']}, "
                f"{result_table('TB_TOT_ALG')}={counts['total_insert_count']}"
            )
        else:
            print("[INFO] --no-save-db: PRE DB 저장 생략")

        elapsed = time.perf_counter() - started
        log_path = append_daily_log("PRE", "SUCCESS", target, elapsed)
        print(f"[OK] 군산 PRE 다중 Horizon 관망해석 완료; 로그={log_path}")
        return 0
    finally:
        gc.collect()
        temp_ctx.cleanup()





def run_loop(args) -> int:
    """01/06/11/...분마다 직전 MO→CUR 복사 후 PRE 관망해석을 수행한다."""
    if args.snapshot or args.ts:
        raise ValueError("loop 실행에서는 --snapshot/--ts를 사용하지 않습니다.")
    if args.max_runs < 0:
        raise ValueError("--max-runs는 0 이상이어야 합니다.")
    if args.mo_max_age_min <= 0:
        raise ValueError("--mo-max-age-min은 0보다 커야 합니다.")
    interval_min = args.interval_min
    offset_sec = schedule_offset_seconds(args)
    if not 0 <= offset_sec < interval_min * 60:
        raise ValueError(
            f"실행 오프셋 {offset_sec}초가 주기 {interval_min}분 범위를 벗어납니다"
            f"(0 이상 {interval_min * 60}초 미만). "
            "1분 주기에서는 --schedule-offset-sec 로 지정하세요(예: 45)."
        )

    args.inp = resolve_input_path(args.inp, "INP 파일")
    args.conn = resolve_input_path(args.conn, "connections 파일")
    if args.valve_mode == "opening":
        args.valve_model = resolve_input_path(args.valve_model, "밸브 보정 파일")
    if args.valve_csv_dir is not None:
        args.valve_csv_dir = resolve_input_path(
            args.valve_csv_dir, "밸브 CSV 폴더", directory=True
        )

    cfg = load_config(args.conn, args.conn_key)

    conn = connect_db(cfg)
    try:
        last_processed = latest_processed_pre_ts(conn) if args.save_db else None
        mapping = load_prediction_mapping(conn)
    finally:
        conn.close()

    print("[LOOP] 군산 CUR(MO 복사) + PRE 관망해석 스케줄 시작")
    print(
        f"[LOOP] 실행시각: 매 {interval_min}분 경계 +{offset_sec}초 "
        f"(기본 5분 +60초 = 01/06/11/16/...분). CUR 원본 MO 격자: {MO_INTERVAL_MIN}분, "
        f"최대 경과 {args.mo_max_age_min:g}분"
    )
    print(
        "[LOOP] 예측 매핑: "
        + ", ".join(f"{nid}={dstrb}" for nid, dstrb in mapping.items())
    )
    print(
        f"[LOOP] 기존 마지막 PRE: "
        f"{last_processed if last_processed else '없음'}"
    )
    print(
        f"[LOOP] DB 저장: "
        f"{'ON (CUR 복사 + PRE 저장)' if args.save_db else 'OFF (--no-save-db; PRE 해석만)'}"
    )
    print(
        f"[LOOP] 테이블: 예측 조회={PREDICTION_TABLE}, "
        f"결과 저장={result_table('TB_FP_VAL')}/{result_table('TB_FR_VAL')}/"
        f"{result_table('TB_TOT_ALG')}, MO 원본=TB_TOT_ALG(운영)"
    )

    runs = 0
    next_slot = scheduled_slot_at_or_after(
        datetime.now(), interval_min=interval_min, offset_sec=offset_sec
    )

    while True:
        now = datetime.now()

        # 한 실행 슬롯을 1분 이상 놓친 경우 과거 슬롯을 몰아서 실행하지 않는다.
        if now >= next_slot + timedelta(minutes=1):
            next_slot = scheduled_slot_at_or_after(
                now, interval_min=interval_min, offset_sec=offset_sec
            )

        if now < next_slot:
            sleep_sec = max(0.2, (next_slot - now).total_seconds())
            print(f"[WAIT] 다음 CUR/PRE 실행: {next_slot}")
            time.sleep(sleep_sec)

        slot_ts = next_slot
        # 실패/결측이어도 같은 슬롯을 반복 실행하지 않고 다음 회차로 이동한다.
        next_slot = slot_ts + timedelta(minutes=interval_min)
        # 결과시각(RGSTR_TIME)은 분 단위로 둔다. 초 오프셋(예: :45)으로 깨어나도
        # 결과는 그 분에 쌓여야 BE 조회·중복 판정이 기존과 같다. 분 오프셋이면
        # slot_ts 와 같다(기본 동작 불변).
        result_ts = slot_ts.replace(second=0, microsecond=0)

        # 같은 실행 슬롯이 이미 PRE로 저장되어 있으면 재기동 직후 중복 실행하지 않는다.
        if args.save_db and last_processed is not None and result_ts <= last_processed:
            print(f"[SKIP] {result_ts}: 이미 PRE 처리 완료 (마지막={last_processed})")
            gc.collect()
            continue

        expected_prediction_from = floor_to_interval(slot_ts, interval_min)
        mo_source_ts = None
        prediction_bundle = None
        readings = None
        reason = ""

        print(
            f"\n[LOOP] 실행 슬롯 {slot_ts} (결과시각 {result_ts}) | "
            f"CUR 원본 MO=최근 정상값 조회 | "
            f"예측 기준>={expected_prediction_from}"
        )

        read_conn = connect_db(cfg)
        try:
            # TB_NODE_TAG 매핑 변경도 다음 주기에 자동 반영한다.
            mapping = load_prediction_mapping(read_conn)
            prediction_bundle, reason = fetch_prediction_bundle(
                read_conn,
                mapping,
                snapshot_ts=slot_ts,
                max_skew_sec=args.prediction_max_skew_sec,
            )

            if prediction_bundle is not None:
                # 직전 5분 회차에 새로 생성된 예측값만 허용한다.
                if prediction_bundle["batch_min_ts"] < expected_prediction_from:
                    reason = (
                        "이번 회차 수요예측 미갱신: "
                        f"예측={prediction_bundle['batch_min_ts']}~{prediction_bundle['batch_ts']}, "
                        f"필요>={expected_prediction_from}"
                    )
                    prediction_bundle = None
                else:
                    readings = fetch_runtime_readings(
                        read_conn,
                        prediction_bundle["batch_ts"],
                        args.fallback_sec,
                        args.valve_mode,
                    )
                    # CUR 저장을 켠 경우 실행시각 이전의 가장 최근 정상 MO를 선택한다.
                    # 최신 MO가 아직 저장 중이면 직전의 완성된 MO를 사용한다.
                    if args.save_db:
                        mo_source_ts = latest_complete_mo_source_ts(
                            read_conn,
                            slot_ts,
                            args.mo_max_age_min,
                        )
                        verify_mo_source(read_conn, mo_source_ts)
        except Exception as exc:
            reason = str(exc)
            prediction_bundle = None
            readings = None
        finally:
            read_conn.close()

        if prediction_bundle is None:
            print(f"[SKIP] {result_ts}: {reason}")
            gc.collect()
            continue

        print(
            f"[LOOP] 예측 묶음 확인: {prediction_bundle['batch_ts']} "
            f"→ 결과시각 {result_ts}"
        )
        if args.save_db and mo_source_ts is not None:
            mo_age_min = (slot_ts - mo_source_ts).total_seconds() / 60.0
            print(
                f"[LOOP] CUR 원본 MO 선택: {mo_source_ts} "
                f"(실행시각 대비 {mo_age_min:.1f}분 전)"
            )

        attempt_started = time.perf_counter()
        try:
            run_once(
                args,
                prediction_bundle=prediction_bundle,
                readings=readings,
                result_ts=result_ts,
                cur_source_ts=mo_source_ts if args.save_db else None,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - attempt_started
            append_daily_log("PRE", "FAIL", result_ts, elapsed, exc)
            print(
                f"[LOOP][ERROR] CUR/PRE {result_ts}: {exc}",
                file=sys.stderr,
            )
            gc.collect()
            continue

        last_processed = result_ts
        runs += 1
        gc.collect()

        if args.max_runs and runs >= args.max_runs:
            print(f"[LOOP] max-runs={args.max_runs} 충족. 종료.")
            return 0



def main(argv=None) -> int:
    ap = parser()
    args = ap.parse_args(argv)
    try:
        configure_tables(args)
    except ValueError as exc:
        ap.error(str(exc))

    if args.snapshot:
        if not args.ts:
            ap.error('--snapshot 사용 시 --ts "YYYY-MM-DD HH:MM:SS"를 지정하세요.')
        return run_once(args)

    if args.ts:
        ap.error('--ts는 --snapshot과 함께 사용하세요.')

    return run_loop(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        append_daily_log(
            "PRE", "FAIL", cli_requested_ts(),
            time.perf_counter() - PROCESS_STARTED, exc
        )
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
