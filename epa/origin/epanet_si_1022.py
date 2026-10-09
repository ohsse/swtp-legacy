from __future__ import annotations
from typing import Dict, Any, List, Tuple, Iterable, Optional
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

import tempfile as _tmp_si_rule_tempfile
import re as _re_si_rule
from pathlib import Path as _Path_si_rule
from typing import List as _List_si_rule, Dict as _Dict_si_rule, Set as _Set_si_rule, Tuple as _Tuple_si_rule

import pymysql
import pandas as pd
import wntr
from wntr.epanet.util import FlowUnits, to_si, from_si, HydParam


def _parse_flow_unit(name: str, default: FlowUnits = FlowUnits.CMH) -> FlowUnits:
    try:
        return getattr(FlowUnits, str(name).upper())
    except Exception:
        return default


def _si_rule_read_text_guess(path: _Path_si_rule) -> tuple[str, str]:
    for enc in ("utf-8", "utf-8-sig", "cp949", "cp1252", "latin1"):
        try:
            return path.read_text(encoding=enc), enc
        except Exception:
            pass
    raise RuntimeError(f"INP 텍스트 디코딩 실패: {path}")

def _si_rule_write_text_utf8(path: _Path_si_rule, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")

_SECTION_RE_SI_RULE = _re_si_rule.compile(r"^[ \t]*\[(?P<name>[^\]]+)\][ \t]*$", _re_si_rule.MULTILINE)

def _si_rule_split_sections(inp_text: str) -> _Dict_si_rule[str, _Tuple_si_rule[int, int]]:
    positions: _List_si_rule[_Tuple_si_rule[str, int, int]] = []
    for m in _SECTION_RE_SI_RULE.finditer(inp_text):
        positions.append((m.group("name").strip().upper(), m.start(), m.end()))
    sections: _Dict_si_rule[str, _Tuple_si_rule[int, int]] = {}
    for i, (name, s_tag, e_tag) in enumerate(positions):
        body_start = e_tag
        body_end = positions[i + 1][1] if i + 1 < len(positions) else len(inp_text)
        sections[name] = (body_start, body_end)
    return sections

def _si_rule_get_section_text(inp_text: str, sections: _Dict_si_rule[str, _Tuple_si_rule[int, int]], name: str) -> str:
    rng = sections.get(name.upper())
    if not rng:
        return ""
    s, e = rng
    return inp_text[s:e]

def _si_rule_replace_section_text(inp_text: str, sections: _Dict_si_rule[str, _Tuple_si_rule[int, int]], name: str, new_body: str) -> str:
    name_up = name.upper()
    if name_up not in sections:
        end_rng = sections.get("END")
        insert_pos = end_rng[0] if end_rng else len(inp_text)
        block = f"\n[{name_up}]\n{new_body.rstrip()}\n"
        return inp_text[:insert_pos] + block + inp_text[insert_pos:]

    s, e = sections[name_up]
    prefix, suffix = inp_text[:s], inp_text[e:]
    body = new_body
    if not body.startswith("\n"):
        body = "\n" + body
    if not body.endswith("\n"):
        body += "\n"
    return prefix + body + suffix

def _si_rule_parse_table_ids(section_body: str) -> _List_si_rule[str]:
    ids: _List_si_rule[str] = []
    for line in section_body.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        parts = _re_si_rule.split(r"\s+", line)
        if parts:
            ids.append(parts[0])
    return ids

def _si_rule_collect_link_ids(inp_text: str) -> _Dict_si_rule[str, _Set_si_rule[str]]:
    sections = _si_rule_split_sections(inp_text)
    pipes = _si_rule_parse_table_ids(_si_rule_get_section_text(inp_text, sections, "PIPES"))
    pumps = _si_rule_parse_table_ids(_si_rule_get_section_text(inp_text, sections, "PUMPS"))
    valves = _si_rule_parse_table_ids(_si_rule_get_section_text(inp_text, sections, "VALVES"))
    return {
        "PIPES": set(pipes),
        "PUMPS": set(pumps),
        "VALVES": set(valves),
        "LINKS": set(pipes) | set(pumps) | set(valves),
    }

_ID_NORMALIZER_SI_RULE = _re_si_rule.compile(r"^(?:pipe|link|pump|valve)?\s*[_\-#]*\s*(\d+)$", _re_si_rule.IGNORECASE)

def _si_rule_resolve_link_id(raw_id: str, link_ids: _Set_si_rule[str]) -> str:
    pid = raw_id.strip()
    if pid in link_ids:
        return pid
    m = _ID_NORMALIZER_SI_RULE.match(pid)
    if m:
        num = m.group(1)
        if num in link_ids:
            return num
    sample = ", ".join(sorted(list(link_ids))[:15])
    raise ValueError(f"링크 ID '{raw_id}'를 찾을 수 없습니다. (존재 예: {sample} ...)")

def _si_rule_build_pump_rule(
    pipe_id: str,
    flow_min: float,
    flow_max: float,
    pump_comb: list[int],
    priority: int = 24,
    rule_name: str = "1",
) -> list[str]:
    open_set = {int(x) for x in pump_comb}
    lines: list[str] = []
    lines.append(f"RULE {rule_name}")
    lines.append(f"IF LINK {pipe_id} FLOW >= {float(flow_min):g}")
    lines.append(f"AND LINK {pipe_id} FLOW <= {float(flow_max):g}")
    first = True
    for i in range(1, 8): 
        status = "OPEN" if i in open_set else "CLOSED"
        prefix = "THEN" if first else "AND"
        lines.append(f"{prefix} PUMP Old_Pump#{i} STATUS IS {status}")
        first = False
    for i in range(8, 12): 
        status = "OPEN" if i in open_set else "CLOSED"
        prefix = "THEN" if first else "AND"
        lines.append(f"{prefix} PUMP New_Pump#{i-7} STATUS IS {status}")
        first = False
    lines.append(f"PRIORITY {int(priority)}")
    lines.append("; end of rule")
    return lines

def _si_rule_insert_rule_lines(inp_text: str, rule_lines: list[str]) -> str:
    sections = _si_rule_split_sections(inp_text)
    body = _si_rule_get_section_text(inp_text, sections, "RULES")
    if body.strip():
        new_body = body.rstrip() + "\n" + "\n".join(rule_lines) + "\n"
    else:
        new_body = "\n" + "\n".join(rule_lines) + "\n"
    out = _si_rule_replace_section_text(inp_text, sections, "RULES", new_body)
    if not out.endswith("\n"):
        out += "\n"
    return out

def inject_rule_to_inp(
    inp_path: _Path_si_rule,
    pump_comb_str: str,
    flow_min: float,
    flow_max: float,
    rule_pipe_id_raw: str,
    rule_priority: int,
    rule_name: str = "1",
) -> _Path_si_rule:
    text, _enc = _si_rule_read_text_guess(inp_path)
    ids = _si_rule_collect_link_ids(text)
    resolved_pid = _si_rule_resolve_link_id(rule_pipe_id_raw, ids["LINKS"])
    toks = _re_si_rule.split(r"[,\s]+", pump_comb_str.strip())
    pump_comb: list[int] = []
    for t in toks:
        if t:
            pump_comb.append(int(t))
    invalid = [x for x in pump_comb if x < 1 or x > 11]
    if invalid:
        raise ValueError(f"펌프 인덱스 범위는 1..11 입니다. 잘못된 값: {invalid}")
    rule_lines = _si_rule_build_pump_rule(resolved_pid, flow_min, flow_max, pump_comb, rule_priority, rule_name)
    patched = _si_rule_insert_rule_lines(text, rule_lines)
    with _tmp_si_rule_tempfile.NamedTemporaryFile(delete=False, suffix=".inp") as tf:
        tmp_path = _Path_si_rule(tf.name)
    _si_rule_write_text_utf8(tmp_path, patched)
    print(f"[INFO] 패치된 INP 저장: {tmp_path}")
    return tmp_path


def load_db_config(path: str, key: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and key in data and isinstance(data[key], dict):
        cfg = data[key]
    elif all(k in data for k in ("host", "port", "user", "password", "db")):
        cfg = data
    else:
        raise KeyError(f'connections.json에서 "{key}" 키를 찾을 수 없거나 형식이 다릅니다.')
    cfg.setdefault("port", 3306)
    return cfg

class DbManager:
    def __init__(self, cfg: Dict[str, Any], autocommit: bool = False):
        self.conn = pymysql.connect(
            host=cfg["host"],
            port=int(cfg.get("port", 3306)),
            user=cfg["user"],
            password=cfg["password"],
            database=cfg.get("db") or cfg.get("database", "EMS_DB"),
            charset="utf8mb4",
            autocommit=autocommit,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def fetchall(self, sql: str, params: Tuple = ()) -> List[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def executemany(self, sql: str, rows: List[Tuple]) -> None:
        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def load_inp_with_fallback(path: str):
    p = Path(path)
    try:
        return wntr.network.WaterNetworkModel(str(p))
    except Exception:
        pass

    candidates = ("cp949", "euc-kr", "utf-8-sig", "latin-1")
    last_err = None
    for enc in candidates:
        try:
            text = p.read_text(encoding=enc)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
                tmp.write(text)
                tmp_path = tmp.name
            return wntr.network.WaterNetworkModel(tmp_path)
        except Exception as ex:
            last_err = ex
            continue
    raise last_err

def save_inp_with_encoding(wn, out_path: str, encoding: str = "cp949", errors: str = "strict"):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
        tmp_path = tmp.name
    wntr.network.write_inpfile(wn, tmp_path, version=2.2)

    text = Path(tmp_path).read_text(encoding="utf-8")
    text = text.lstrip("\ufeff")
    with open(out_path, "w", encoding=encoding, errors=errors, newline="\r\n") as f:
        f.write(text)


def pick_latest_ts(db: DbManager, now_dt: datetime) -> Optional[datetime]:
    row = db.fetchone("SELECT MAX(ts) AS ts FROM TB_RAWDATA WHERE ts <= %s", (now_dt,))
    return row["ts"] if row and row.get("ts") else None

def load_node_meta(db: DbManager) -> List[dict]:
    sql = """
      SELECT NODE_ID, FP_TAGNAME, FR_TAGNAME
      FROM TB_NODE_TAG
      ORDER BY NODE_ID
    """
    return db.fetchall(sql)

def load_link_meta(db: DbManager) -> List[dict]:
    sql = """
      SELECT LINK_ID, MIN(GRP_NM) AS GRP_NM, MAX(FLW_TAGNAME) AS FLW_TAGNAME
      FROM TB_LINK_GRP
      GROUP BY LINK_ID
      ORDER BY LINK_ID
    """
    return db.fetchall(sql)

def fetch_values_by_tag_nearest(db: DbManager, ts: datetime, tags: list[str]) -> Dict[str, float]:
    tags = [t for t in tags if t]
    if not tags:
        return {}
    ph = ",".join(["%s"] * len(tags))

    sql_le = f"""
      SELECT r.TAGNAME, r.ts AS t, r.VALUE
      FROM TB_RAWDATA r
      JOIN (
        SELECT TAGNAME, MAX(ts) AS ts
        FROM TB_RAWDATA
        WHERE ts <= %s AND TAGNAME IN ({ph})
        GROUP BY TAGNAME
      ) x ON x.TAGNAME = r.TAGNAME AND x.ts = r.ts
    """
    rows_le = db.fetchall(sql_le, (ts, *tags))

    sql_ge = f"""
      SELECT r.TAGNAME, r.ts AS t, r.VALUE
      FROM TB_RAWDATA r
      JOIN (
        SELECT TAGNAME, MIN(ts) AS ts
        FROM TB_RAWDATA
        WHERE ts >= %s AND TAGNAME IN ({ph})
        GROUP BY TAGNAME
      ) x ON x.TAGNAME = r.TAGNAME AND x.ts = r.ts
    """
    rows_ge = db.fetchall(sql_ge, (ts, *tags))

    by_tag = {}
    tmp = {}
    for r in rows_le:
        tmp[(r["TAGNAME"], "le")] = (r["t"], float(r["VALUE"]))
    for r in rows_ge:
        tmp[(r["TAGNAME"], "ge")] = (r["t"], float(r["VALUE"]))

    for t in tags:
        le = tmp.get((t, "le"))
        ge = tmp.get((t, "ge"))
        if le and ge:
            if abs((ts - le[0]).total_seconds()) <= abs((ge[0] - ts).total_seconds()):
                by_tag[t] = le[1]
            else:
                by_tag[t] = ge[1]
        elif le:
            by_tag[t] = le[1]
        elif ge:
            by_tag[t] = ge[1]
    return by_tag


def fetch_reservoir_flow_by_node_nearest(
    db: DbManager, ts: datetime, node_ids: Iterable[str], window_sec: int = 120
) -> Dict[str, float]:
    node_list = [n for n in node_ids if n]
    if not node_list:
        return {}

    ph = ",".join(["%s"] * len(node_list))

    sql_le = f"""
      SELECT t.NODE_ID, t.UPDT_TIME AS t, t.FLOW_RATE
      FROM TB_EPA_SIM_RESV_FLOW t
      JOIN (
        SELECT NODE_ID, MAX(UPDT_TIME) AS UPDT_TIME
        FROM TB_EPA_SIM_RESV_FLOW
        WHERE UPDT_TIME <= %s
          AND UPDT_TIME >= DATE_SUB(%s, INTERVAL %s SECOND)
          AND NODE_ID IN ({ph})
        GROUP BY NODE_ID
      ) x ON x.NODE_ID = t.NODE_ID AND x.UPDT_TIME = t.UPDT_TIME
    """
    rows_le = db.fetchall(sql_le, (ts, ts, window_sec, *node_list))

    sql_ge = f"""
      SELECT t.NODE_ID, t.UPDT_TIME AS t, t.FLOW_RATE
      FROM TB_EPA_SIM_RESV_FLOW t
      JOIN (
        SELECT NODE_ID, MIN(UPDT_TIME) AS UPDT_TIME
        FROM TB_EPA_SIM_RESV_FLOW
        WHERE UPDT_TIME >= %s
          AND UPDT_TIME <= DATE_ADD(%s, INTERVAL %s SECOND)
          AND NODE_ID IN ({ph})
        GROUP BY NODE_ID
      ) x ON x.NODE_ID = t.NODE_ID AND x.UPDT_TIME = t.UPDT_TIME
    """
    rows_ge = db.fetchall(sql_ge, (ts, ts, window_sec, *node_list))

    best: Dict[str, Tuple[datetime, float]] = {}
    for r in rows_le:
        best[r["NODE_ID"]] = (r["t"], float(r["FLOW_RATE"]))
    for r in rows_ge:
        nid = r["NODE_ID"]
        cand = (r["t"], float(r["FLOW_RATE"]))
        if nid not in best:
            best[nid] = cand
        else:
            cur = best[nid]
            if abs((cand[0] - ts).total_seconds()) < abs((ts - cur[0]).total_seconds()):
                best[nid] = cand

    return {k: v for k, (_, v) in best.items()}


def fetch_fc_range_by_comb(
    db: DbManager,
    pump_comb: str,
    pump_grp: Optional[str] = None
) -> Tuple[float, float]:
    pump_comb_norm = ",".join([t.strip() for t in str(pump_comb).split(",") if t.strip()])
    params: List[Any] = []
    where = ["PUMP_COMB = %s"]
    params.append(pump_comb_norm)
    if pump_grp:
        where.append("PUMP_GRP = %s")
        params.append(pump_grp)

    sql = f"""
        SELECT FC_MIN_VAL, FC_MAX_VAL, USE_YN, PUMP_PRIORITY, COUNT_IDX, C_ORD
        FROM TB_PUMP_CAL
        WHERE {" AND ".join(where)}
        ORDER BY (CASE WHEN USE_YN='Y' THEN 1 ELSE 0 END) DESC,
                 PUMP_PRIORITY ASC, COUNT_IDX ASC, C_ORD ASC
        LIMIT 1
    """
    row = db.fetchone(sql, tuple(params))
    if not row:
        raise RuntimeError(f"TB_PUMP_CAL에서 조합 '{pump_comb_norm}'(grp={pump_grp})을 찾지 못했습니다.")

    vmin = float(row["FC_MIN_VAL"]) if row["FC_MIN_VAL"] is not None else 0.0
    vmax = float(row["FC_MAX_VAL"]) if row["FC_MAX_VAL"] is not None else 1e12
    return vmin, vmax  # CMH 기준

def build_demands_from_rawdata(
    node_meta: List[dict],
    fr_by_tag: Dict[str, float],
    raw_flow_unit: FlowUnits,
) -> Dict[str, float]:
    demand_raw_by_node: Dict[str, float] = {}
    for r in node_meta:
        nid = r["NODE_ID"]
        fr_tag = r.get("FR_TAGNAME")
        v = float(fr_by_tag.get(fr_tag, 0.0)) if fr_tag else 0.0
        demand_raw_by_node[nid] = v

    def node_val(nid: str) -> float:
        return demand_raw_by_node.get(nid, 0.0)

    adjusted = dict(demand_raw_by_node)
    if "이서배수지" in adjusted:
        adjusted["이서배수지"] = node_val("이서배수지") / 3.7
    if "왕궁관말" in adjusted:
        adjusted["왕궁관말"] = node_val("왕궁관말") * 1.0
    if "199" in adjusted:
        adjusted["199"] = node_val("천마배수지") * 1.0
    if "201" in adjusted:
        adjusted["201"] = node_val("201") / 1.3
    if "김제(배)" in adjusted:
        adjusted["김제(배)"] = node_val("김제(배)") * 1.0

    si_demands = {nid: to_si(raw_flow_unit, float(v), HydParam.Flow) for nid, v in adjusted.items()}
    return si_demands

def build_demands_merged(
    node_meta: List[dict],
    raw_map_by_node: Dict[str, float],     
    resv_by_node: Dict[str, float],   
    raw_flow_unit: FlowUnits,
    debug_src_map: Optional[Dict[str, str]] = None,
) -> Dict[str, float]:
    merged: Dict[str, float] = {}
    src_map: Dict[str, str] = {}
    for r in node_meta:
        nid = r["NODE_ID"]
        if nid in resv_by_node:
            merged[nid] = float(resv_by_node[nid])
            src_map[nid] = "RESV"
        else:
            merged[nid] = float(raw_map_by_node.get(nid, 0.0))
            src_map[nid] = "RAW"

    def node_val(nid: str) -> float:
        return merged.get(nid, 0.0)

    adjusted = dict(merged)
    if "이서배수지" in adjusted:
        adjusted["이서배수지"] = node_val("이서배수지") / 3.7
    if "왕궁관말" in adjusted:
        adjusted["왕궁관말"] = node_val("왕궁관말") * 1.0
    if "199" in adjusted:
        adjusted["199"] = node_val("천마배수지") * 1.0
    if "201" in adjusted:
        adjusted["201"] = node_val("201") / 1.3
    if "김제(배)" in adjusted:
        adjusted["김제(배)"] = node_val("김제(배)") * 1.0

    if debug_src_map is not None:
        debug_src_map.update(src_map)

    si_demands = {nid: to_si(raw_flow_unit, float(v), HydParam.Flow) for nid, v in adjusted.items()}
    return si_demands


def set_demands_to_model(wn: wntr.network.WaterNetworkModel, si_demands: Dict[str, float]) -> None:
    for name in wn.junction_name_list:
        j = wn.get_node(name)
        v = float(si_demands.get(name, 0.0))
        dlist = getattr(j, "demand_timeseries_list", None)
        if dlist and len(dlist) > 0:
            dlist[0].base_value = v
        else:
            j.add_demand(base=v, pattern=None, category="Base")

def run_snapshot_return_both(wn: wntr.network.WaterNetworkModel):
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    t_index = list(results.node["pressure"].index)
    i0 = 0
    iL = len(t_index) - 1

    p0 = results.node["pressure"].iloc[i0]
    h0 = results.node["head"].iloc[i0]
    f0 = results.link["flowrate"].iloc[i0]
    l0 = results.link["headloss"].iloc[i0]

    pL = results.node["pressure"].iloc[iL]
    hL = results.node["head"].iloc[iL]
    fL = results.link["flowrate"].iloc[iL]
    lL = results.link["headloss"].iloc[iL]

    return (p0, h0, f0, l0), (pL, hL, fL, lL)


def fetch_sum_raw(db: DbManager, ts: datetime, tags: list[str]) -> float:
    tags = [t for t in tags if t]
    if not tags:
        return 0.0
    ph = ",".join(["%s"] * len(tags))
    sql = f"SELECT SUM(value) AS s FROM TB_RAWDATA WHERE ts=%s AND tagname IN ({ph})"
    row = db.fetchone(sql, (ts, *tags))
    return float(row["s"] or 0.0) if row else 0.0

def load_all_link_groups(db: DbManager) -> list[dict]:
    sql = "SELECT LINK_ID, GRP_NM FROM TB_LINK_GRP"
    return db.fetchall(sql)

def pick_avl_group_row(db: DbManager, ts: datetime, flow_sum_for_threshold: float) -> dict | None:
    row = db.fetchone(
        "SELECT * FROM TB_AVL_GRP WHERE STN_FLW_VAL > %s ORDER BY STN_FLW_VAL ASC LIMIT 1",
        (flow_sum_for_threshold/60.0,)
    )
    if row:
        return row
    return db.fetchone("SELECT * FROM TB_AVL_GRP ORDER BY STN_FLW_VAL DESC LIMIT 1")

def compute_group_loss_total(
    wn: wntr.network.WaterNetworkModel,
    link_hloss: pd.Series,
    link_groups: list[dict],
    active_flags_row: dict
) -> float:
    hl_by_link: dict[str, float] = {}
    for link_id in wn.link_name_list:
        ln = wn.get_link(link_id)
        if getattr(ln, "link_type", "") != "Pipe":
            continue
        hl = float(link_hloss.get(link_id, 0.0)) * float(ln.length)
        hl_by_link[link_id] = hl

    grp_sum: dict[str, float] = {}
    for r in link_groups:
        lid = r["LINK_ID"]
        g   = r["GRP_NM"]
        if lid in hl_by_link:
            grp_sum[g] = grp_sum.get(g, 0.0) + hl_by_link[lid]

    total = 0.0
    for g, s in grp_sum.items():
        flag_col = f"GRP_{g}_YN"
        if flag_col in active_flags_row and active_flags_row[flag_col] in (1, True):
            total += s
    return total

def store_node_results(
    db: DbManager,
    ts: datetime,
    node_pressure: pd.Series,
    node_measured_fp: Dict[str, float],
    node_table: str = "TB_FP_SI_VAL"
) -> None:
    rows: List[Tuple] = []
    for node_id, p_alg in node_pressure.items():
        p_meas = node_measured_fp.get(node_id) if node_measured_fp else None
        rows.append((ts, node_id, p_meas, float(p_alg), "si"))
    if rows:
        sql = f"""
          REPLACE INTO {node_table}
            (RGSTR_TIME, NODE_ID, FP_VAL, FP_ALG_RST_VAL, FLG)
          VALUES (%s,%s,%s,%s,%s)
        """
        db.executemany(sql, rows)

def store_link_results(
    db: DbManager,
    ts: datetime,
    wn: wntr.network.WaterNetworkModel,
    link_flow: pd.Series,
    link_hloss: pd.Series,
    link_measured_fr_by_linkid: Dict[str, float],
    link_table: str = "TB_FR_SI_VAL",
    raw_meas_unit: FlowUnits = FlowUnits.CMH,
) -> None:
    # 모델 유닛 감지
    unit_name = getattr(getattr(wn.options, "hydraulic", None), "inpfile_units", None)
    if not unit_name:
        unit_name = wn.to_dict().get("options", {}).get("hydraulic", {}).get("inpfile_units", "CMH")
    model_unit = getattr(FlowUnits, str(unit_name).upper(), FlowUnits.CMH)

    OUT_UNIT = FlowUnits.CMH  # 저장은 m³/h 고정

    rows: List[Tuple] = []
    for link_id in wn.link_name_list:
        ln = wn.get_link(link_id)
        if getattr(ln, "link_type", "") != "Pipe":
            continue

        hh_loss_val = float(link_hloss.get(link_id, 0.0)) * float(ln.length)

        # 모델 결과: 모델유닛 → SI(m³/s) → CMH
        si_alg = float(link_flow.get(link_id, 0.0))            # m³/s
        flw_alg_cmh = from_si(OUT_UNIT, si_alg, HydParam.Flow) # → CMH

        # 실측: 원단위(raw_meas_unit) → SI → CMH
        link_meas_raw = link_measured_fr_by_linkid.get(link_id)
        if link_meas_raw is not None:
            si_meas       = to_si(raw_meas_unit, float(link_meas_raw), HydParam.Flow)
            link_meas_cmh = from_si(OUT_UNIT, si_meas, HydParam.Flow)
        else:
            link_meas_cmh = None

        rows.append((link_id, hh_loss_val, ts, link_meas_cmh, flw_alg_cmh, "si"))

    if rows:
        sql = f"""
          REPLACE INTO {link_table}
            (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, LINK_VAL, FLW_ALG_RST_VAL, FLG)
          VALUES (%s,%s,%s,%s,%s,%s)
        """
        db.executemany(sql, rows)

def store_tot_alg(
    db: DbManager,
    ts: datetime,
    wn: wntr.network.WaterNetworkModel,
    node_pressure: pd.Series,
    link_flow: pd.Series,
    link_hloss: pd.Series,
    tot_table: str,
    tot_node_id: str,
    sum_flow_tags: list[str],
    sum_press_tags: list[str],
):
    flow_sum  = fetch_sum_raw(db, ts, sum_flow_tags)
    press_sum = fetch_sum_raw(db, ts, sum_press_tags)

    avl_row = pick_avl_group_row(db, ts, flow_sum) or {}
    link_groups = load_all_link_groups(db)
    loss_tot = compute_group_loss_total(wn, link_hloss, link_groups, avl_row)

    fp_alg = float(node_pressure.get(tot_node_id, 0.0))

    sql = f"""
      REPLACE INTO {tot_table}
        (RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL, FLG)
      VALUES (%s,%s,%s,%s,%s,%s)
    """
    db.executemany(sql, [(ts, loss_tot, flow_sum, press_sum, fp_alg, "si")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", required=True, help="EPANET INP 파일 경로")
    ap.add_argument("--conn", default="./connections.json", help="connections.json 경로")
    ap.add_argument("--conn-key", default="maria-ems-db-gs", help='connections.json 내 Key')
    ap.add_argument("--ts", default=None, help="강제 실행 시각(예: '2025-08-20 14:55:00'); 없으면 now 기준 직전 ts 자동 선택")

    ap.add_argument("--node-table", default="TB_FP_SI_VAL", help="노드 결과 테이블명")
    ap.add_argument("--link-table", default="TB_FR_SI_VAL", help="링크 결과 테이블명")
    ap.add_argument("--tot-table", default="TB_TOT_ALG", help="총괄 결과 테이블명")
    ap.add_argument("--tot-node-id", default="13", help="FP_ALG_RST_VAL 대표 노드ID")
    ap.add_argument("--sum-flow-tags", default="701-367-FRI-4004,701-367-FRI-4001",
                    help="실측 유량 합계 TAGNAME 목록(쉼표)")
    ap.add_argument("--sum-press-tags", default="701-367-PRI-4019,701-367-PRI-4010",
                    help="실측 압력 합계 TAGNAME 목록(쉼표)")

    ap.add_argument("--save-inp-out", default="", help="수정된 INP 저장 경로(비우면 저장 안함)")
    ap.add_argument("--save-encoding", default="cp949", help="INP 저장 인코딩(cp949/utf-8-sig 등)")

    ap.add_argument("--resv-window-sec", type=int, default=120, help="RESV_FLOW 최근접 허용 윈도(초), 기본 ±120초")
    ap.add_argument("--fallback-sec", type=int, default=600, help="(기타 쿼리용) 폴백 범위(초)")

    ap.add_argument("--pump-comb", default="", help='예: "2,4,5,6,8" (켜둘 펌프 인덱스, 1..7=Old, 8..11=New)')
    ap.add_argument("--flow-min", type=float, default=None, help="RULE 유량 하한 (INP 유닛 기준)")
    ap.add_argument("--flow-max", type=float, default=None, help="RULE 유량 상한 (INP 유닛 기준)")
    ap.add_argument("--rule-pipe-id", default="", help='예: "10" 또는 "Pipe10"(자동 정규화)')
    ap.add_argument("--rule-priority", type=int, default=24, help="RULE 우선순위 (정수)")
    ap.add_argument("--pump-grp", default="", help="TB_PUMP_CAL 조회용 펌프 그룹(선택)")

    ap.add_argument("--raw-flow-unit", default="CMH",
                    help="DB 원자료 유량 단위 (예: CMH, LPS, GPM...)")
    ap.add_argument("--demands-from-rawdata", action="store_true",
                    help="수요를 TB_RAWDATA만으로 구성(RESV 덮어쓰기 비활성)")

    ap.add_argument("--debug-raw", action="store_true", help="수요 매핑(원자료→SI) 일부를 콘솔에 출력")
    ap.add_argument("--dump-demands-csv", default="", help="수요 매핑을 CSV로 저장할 경로")

    args = ap.parse_args()

    cfg = load_db_config(args.conn, args.conn_key)
    db = DbManager(cfg)

    try:
        if args.ts:
            target_ts = datetime.fromisoformat(args.ts)
        else:
            target_ts = pick_latest_ts(db, datetime.now())
            if target_ts is None:
                raise RuntimeError("TB_RAWDATA에서 now 이전의 시각을 찾을 수 없습니다.")
        print(f"[INFO] 실행 시각 ts={target_ts}")

        node_meta = load_node_meta(db)
        link_meta = load_link_meta(db)

        fp_tags = [r["FP_TAGNAME"] for r in node_meta if r.get("FP_TAGNAME")]
        link_fr_tags = [r["FLW_TAGNAME"] for r in link_meta if r.get("FLW_TAGNAME")]

        fp_by_tag      = fetch_values_by_tag_nearest(db, target_ts, fp_tags)
        link_fr_by_tag = fetch_values_by_tag_nearest(db, target_ts, link_fr_tags)

        inp_path_to_use = args.inp

        wn_for_units = load_inp_with_fallback(inp_path_to_use)
        try:
            inp_unit_name = getattr(getattr(wn_for_units.options, "hydraulic", None), "inpfile_units", None)
            if not inp_unit_name:
                toDict = wn_for_units.to_dict()
                inp_unit_name = toDict.get("options", {}).get("hydraulic", {}).get("inpfile_units", "LPS")
            inp_flow_unit = getattr(FlowUnits, str(inp_unit_name).upper())
        except Exception:
            inp_flow_unit = FlowUnits.LPS

        need_rule = bool(args.pump_comb and args.rule_pipe_id)
        if need_rule:
            flow_min = args.flow_min
            flow_max = args.flow_max

            if (flow_min is None or flow_max is None):
                pump_grp = args.pump_grp or None
                cmh_min, cmh_max = fetch_fc_range_by_comb(db, args.pump_comb, pump_grp=pump_grp)
                si_min = to_si(FlowUnits.CMH, cmh_min, HydParam.Flow)
                si_max = to_si(FlowUnits.CMH, cmh_max, HydParam.Flow)
                flow_min = from_si(inp_flow_unit, si_min, HydParam.Flow)
                flow_max = from_si(inp_flow_unit, si_max, HydParam.Flow)

            try:
                tmp_inp = inject_rule_to_inp(
                    inp_path=Path(inp_path_to_use),
                    pump_comb_str=str(args.pump_comb),
                    flow_min=float(flow_min),
                    flow_max=float(flow_max),
                    rule_pipe_id_raw=args.rule_pipe_id,
                    rule_priority=int(args.rule_priority),
                    rule_name="1",
                )
                inp_path_to_use = str(tmp_inp)
                print(f"[INFO] RULE 적용 INP 사용: {inp_path_to_use} (min={flow_min:g}, max={flow_max:g} in INP units)")
            except Exception as e:
                print(f"[WARN] RULE 주입 실패: {e} (원본 INP로 진행)")

        # 최종 INP 로드
        wn = load_inp_with_fallback(inp_path_to_use)

        # 단위 파싱 (원자료 -> SI 변환용)
        raw_unit = _parse_flow_unit(args.raw_flow_unit, default=FlowUnits.CMH)

        # DEMAND 구성 & 적용
        node_ids = [r["NODE_ID"] for r in node_meta]

        # 디버깅 수집용
        raw_map: Dict[str, float] = {}
        tagname_map: Dict[str, Optional[str]] = {}
        src_map: Dict[str, str] = {}

        if args.demands_from_rawdata:
            # RAWDATA만 사용: ‘요청시각과 가장 가까운’ 값
            fr_tags_for_nodes = [r["FR_TAGNAME"] for r in node_meta if r.get("FR_TAGNAME")]
            fr_by_tag = fetch_values_by_tag_nearest(db, target_ts, fr_tags_for_nodes)
            for r in node_meta:
                nid = r["NODE_ID"]
                tg = r.get("FR_TAGNAME")
                tagname_map[nid] = tg
                raw_map[nid] = float(fr_by_tag.get(tg, 0.0)) if tg else 0.0
                src_map[nid] = "RAW"
            si_demands = build_demands_from_rawdata(node_meta, fr_by_tag, raw_flow_unit=raw_unit)

        else:
            # 1) RAWDATA(요청시각과 가장 가까운)로 전체 채움
            fr_tags_for_nodes = [r["FR_TAGNAME"] for r in node_meta if r.get("FR_TAGNAME")]
            fr_by_tag = fetch_values_by_tag_nearest(db, target_ts, fr_tags_for_nodes)
            for r in node_meta:
                nid = r["NODE_ID"]
                tg = r.get("FR_TAGNAME")
                tagname_map[nid] = tg
                raw_map[nid] = float(fr_by_tag.get(tg, 0.0)) if tg else 0.0

            # 2) RESV_FLOW(±window_sec에서 가장 가까운)로 덮어쓰기
            resv_by_node = fetch_reservoir_flow_by_node_nearest(db, target_ts, node_ids, window_sec=args.resv_window_sec)

            # 혼합 수요 생성 + 소스맵 채우기
            si_demands = build_demands_merged(
                node_meta=node_meta,
                raw_map_by_node=raw_map,
                resv_by_node=resv_by_node,
                raw_flow_unit=raw_unit,
                debug_src_map=src_map,
            )

        # 디버그/덤프 출력
        if args.debug_raw or args.dump_demands_csv:
            rows = []
            for r in node_meta:
                nid = r["NODE_ID"]
                tg = tagname_map.get(nid)
                raw_val = raw_map.get(nid, 0.0)
                si_val = float(si_demands.get(nid, 0.0))
                src = src_map.get(nid, "RAW" if args.demands_from_rawdata else ("RESV" if nid not in raw_map else "RAW/RESV"))
                rows.append({
                    "NODE_ID": nid,
                    "FR_TAGNAME": tg,
                    "RAW_VALUE": raw_val,
                    "RAW_UNIT": str(raw_unit.name),
                    "SI_VALUE": si_val,
                    "SRC": src,
                })
            df = pd.DataFrame(rows)
            if args.debug_raw:
                print("[DEBUG] Demand mapping (top 20)")
                print(df.head(20).to_string(index=False))
            if args.dump_demands_csv:
                outp = Path(args.dump_demands_csv)
                df.to_csv(outp, index=False, encoding="utf-8-sig")
                print(f"[DEBUG] Demand mapping CSV saved -> {outp}")

        # 모델에 주입
        set_demands_to_model(wn, si_demands)

        # INP 저장(선택, 한글 보존)
        # (주: wntr이 쓰는 임시 파일은 UTF-8이라 EPANET GUI에서 한글 깨짐 가능.
        #     EPANET에서 열 목적이면 --save-inp-out을 꼭 쓰세요.)
        if args.save_inp_out:
            save_inp_with_encoding(wn, args.save_inp_out, encoding=args.save_encoding)
            print(f"[OK] INP 저장(한글 보존): {args.save_inp_out}")

        # 해석 실행
        (p0, h0, f0, l0), (_pL, _hL, _fL, _lL) = run_snapshot_return_both(wn)

        # 저장용 실측 매핑
        fp_measured_by_node: Dict[str, float] = {}
        for r in node_meta:
            nid = r["NODE_ID"]
            fp_tag = r.get("FP_TAGNAME")
            if fp_tag and fp_tag in fp_by_tag:
                fp_measured_by_node[nid] = float(fp_by_tag[fp_tag])

        link_measured_fr_by_linkid: Dict[str, float] = {}
        for r in link_meta:
            lid = r["LINK_ID"]
            t = r.get("FLW_TAGNAME")
            if t and t in link_fr_by_tag:
                link_measured_fr_by_linkid[lid] = float(link_fr_by_tag[t])

        # 결과 저장 (유량은 CMH 통일)
        store_link_results(
            db=db,
            ts=target_ts,
            wn=wn,
            link_flow=f0,
            link_hloss=l0,
            link_measured_fr_by_linkid=link_measured_fr_by_linkid,
            link_table=args.link_table,
            raw_meas_unit=_parse_flow_unit(args.raw_flow_unit, default=FlowUnits.CMH),
        )

        sum_flow_tags  = [t.strip() for t in args.sum_flow_tags.split(",") if t.strip()]
        sum_press_tags = [t.strip() for t in args.sum_press_tags.split(",") if t.strip()]

        store_tot_alg(
            db=db,
            ts=target_ts,
            wn=wn,
            node_pressure=p0,
            link_flow=f0,
            link_hloss=l0,
            tot_table=args.tot_table,
            tot_node_id=args.tot_node_id,
            sum_flow_tags=sum_flow_tags,
            sum_press_tags=sum_press_tags,
        )

        store_node_results(
            db=db,
            ts=target_ts,
            node_pressure=p0,
            node_measured_fp=fp_measured_by_node,
            node_table=args.node_table,
        )

        db.commit()
        print("[OK] 관망해석 시뮬레이션 저장 완료")

    finally:
        db.close()


if __name__ == "__main__":
    main()
