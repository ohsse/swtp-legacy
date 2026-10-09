# /app/services/simulation_service.py

import tempfile
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path as _Path_si_rule
from typing import List as _List_si_rule, Dict as _Dict_si_rule, Set as _Set_si_rule, Tuple as _Tuple_si_rule
import re as _re_si_rule
import uuid
import os
import logging
import json
import warnings
import time
import tempfile as _tmp_si_rule_tempfile
import pandas as pd
import wntr
from flask import current_app, g
from wntr.epanet.util import FlowUnits, HydParam, from_si, to_si
from app.models.db import DbManager, load_db_config
from app.models import epa_models
from wntr.network.elements import LinkStatus

logger = logging.getLogger(__name__)

_SECTION_RE_SI_RULE = _re_si_rule.compile(r"^[ \t]*\[(?P<name>[^\]]+)\][ \t]*$", _re_si_rule.MULTILINE)

PUMP_STATUS_TAG_MAP_DEFAULT: Dict[int, str] = {
    1: "701-367-PMB-4002",
    2: "701-367-PMB-4005",
    3: "701-367-PMB-4009",
    4: "701-367-PMB-4014",
    5: "701-367-PMB-4023",
    6: "701-367-PMB-4032",
    7: "701-367-PMB-4041",
    8: "701-367-PMB-4303",
    9: "701-367-PMB-4082",
    10:"701-367-PMB-4086",
    11:"701-367-PMB-4090",
}

PUMP_TAG_TO_LINKNAME: Dict[str, str] = {
    "701-367-PMB-4002": "Old_Pump#1",
    "701-367-PMB-4005": "Old_Pump#2",
    "701-367-PMB-4009": "Old_Pump#3",
    "701-367-PMB-4014": "Old_Pump#4",
    "701-367-PMB-4023": "Old_Pump#5",
    "701-367-PMB-4032": "Old_Pump#6",
    "701-367-PMB-4041": "Old_Pump#7",
    "701-367-PMB-4303": "New_Pump#1",
    "701-367-PMB-4082": "New_Pump#2",
    "701-367-PMB-4086": "New_Pump#3",
    "701-367-PMB-4090": "New_Pump#4",
}


def load_inp_with_fallback(path: str) -> wntr.network.WaterNetworkModel:
    p = Path(path)
    if not p.exists(): raise FileNotFoundError(f"INP 파일을 찾을 수 없습니다: {path}")
    for enc in ("cp949", "euc-kr", "utf-8-sig", "latin-1", "utf-8"):
        try:
            text = p.read_text(encoding=enc)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
                tmp.write(text)
                return wntr.network.WaterNetworkModel(tmp.name)
        except Exception: continue
    raise RuntimeError(f"INP 파일을 읽을 수 없습니다: {path}")

def set_pumps_from_rawdata(
    wn,
    db,
    ts,
    tag_map=PUMP_STATUS_TAG_MAP_DEFAULT,
    tag_to_link=PUMP_TAG_TO_LINKNAME,
    fallback_sec=600,
    debug=False,
):
    tags = [t for t in tag_map.values() if t]
    tag2val = epa_models.fetch_values_by_tag_with_fallback(db, ts, tags, fallback_sec=fallback_sec)

    for idx, tag in tag_map.items():
        raw = float(tag2val.get(tag, 0.0))
        on = int(round(raw)) == 1
        link_name = (tag_to_link or {}).get(tag, tag)
        if link_name not in wn.pump_name_list:
            if debug:
                print(f"[WARN] 펌프 링크를 찾지 못함: '{link_name}' (tag='{tag}', idx={idx})")
            continue
        pump = wn.get_link(link_name)
        new_status = LinkStatus.Open if on else LinkStatus.Closed  # 변경: Enum 사용
        pump.initial_status = new_status  # 변경: initial_status만 설정

        if debug:
            print(f"[DEBUG] PUMP STATUS 주입: {link_name} <- {new_status} (tag={tag}, idx={idx}, raw={raw})")


def _si_rule_read_text_guess(path: _Path_si_rule) -> tuple[str, str]:
    for enc in ("utf-8", "utf-8-sig", "cp949", "cp1252", "latin1"):
        try:
            return path.read_text(encoding=enc), enc
        except Exception:
            pass
    raise RuntimeError(f"INP 텍스트 디코딩 실패: {path}")

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

def _si_rule_get_section_text(inp_text: str, sections: _Dict_si_rule[str, _Tuple_si_rule[int, int]], name: str) -> str:
    rng = sections.get(name.upper())
    if not rng:
        return ""
    s, e = rng
    return inp_text[s:e]

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
def _si_rule_write_text_utf8(path: _Path_si_rule, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")

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

def _parse_flow_unit(name: str, default: FlowUnits = FlowUnits.CMH) -> FlowUnits:
    try:
        return getattr(FlowUnits, str(name).upper())
    except Exception:
        return default
    
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

def save_inp_with_encoding(wn, out_path: str, encoding: str = "cp949", errors: str = "strict"):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
        tmp_path = tmp.name
    wntr.network.write_inpfile(wn, tmp_path, version=2.2)

    text = Path(tmp_path).read_text(encoding="utf-8")
    text = text.lstrip("\ufeff")
    with open(out_path, "w", encoding=encoding, errors=errors, newline="\r\n") as f:
        f.write(text)

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

def run_snapshot_initial_only(wn: wntr.network.WaterNetworkModel):
    wn.options.time.duration = 0
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    p0 = results.node["pressure"].iloc[0]
    h0 = results.node["head"].iloc[0]
    f0 = results.link["flowrate"].iloc[0]
    l0 = results.link["headloss"].iloc[0]

    return p0, h0, f0, l0

def get_inp_flow_unit(wn) -> FlowUnits:
    try:
        name = getattr(getattr(wn.options, "hydraulic", None), "inpfile_units", None)
        if not name:
            name = wn.to_dict().get("options", {}).get("hydraulic", {}).get("inpfile_units", "CMH")
        return getattr(FlowUnits, str(name).upper(), FlowUnits.CMH)
    except Exception:
        return FlowUnits.CMH

def get_inp_flow_unit_from_file(path: str, default: FlowUnits = FlowUnits.CMH) -> FlowUnits:
    text, _enc = _si_rule_read_text_guess(Path(path))
    sections = _si_rule_split_sections(text)
    options = _si_rule_get_section_text(text, sections, "OPTIONS")
    for line in options.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        parts = _re_si_rule.split(r"\s+", line, maxsplit=1)
        if len(parts) == 2 and parts[0].upper() == "UNITS":
            return getattr(FlowUnits, parts[1].strip().upper(), default)
    return default
    
def resolve_target_link(wn: wntr.network.WaterNetworkModel, rule_pipe_id: str) -> Optional[str]:
    cand = str(rule_pipe_id).strip()
    names = {n: n for n in wn.link_name_list}
    lower = {n.lower(): n for n in wn.link_name_list}
    if cand in names: return cand
    if cand.lower() in lower: return lower[cand.lower()]
    pipe_form = f"Pipe{cand}"
    if pipe_form in names: return pipe_form
    if pipe_form.lower() in lower: return lower[pipe_form.lower()]
    for n in wn.link_name_list:
        if n.lower().endswith(cand.lower()):
            return n
    return None

def run_and_get_results(wn: wntr.network.WaterNetworkModel):
    warnings.filterwarnings("ignore", category=UserWarning)  # curves 경고 무시
    sim = wntr.sim.EpanetSimulator(wn)
    return sim.run_sim()

def run_mo_simulation(ts: Optional[datetime] = None, db_session: Optional[DbManager] = None) -> dict:
    """_summary_
        'mo' 모드 EPANET 시뮬레이션을 실행하고 결과를 DB에 저장합니다.
        이 함수는 서버 구동시 스케쥴링을 통해 5분간격으로 호출되어 해당시간대의 데이터를 기반으로 관망 해석을 수행하며,
        결과는 TB_FP_SI_VAL, TB_FR_SI_VAL 테이블에 'mo' 플래그로 기록됩니다.
    Args:
        ts (Optional[datetime], optional): _description_. Defaults to None.
        conn_key (Optional[str], optional): _description_. Defaults to None.

    Raises:
        ValueError: _description_

    Returns:
        dict: _description_
    """
    rule_pipe_id = 10
    config = current_app.config
    sum_flow_tags = config['TOT_SUM_FLOW_TAGS']
    sum_press_tags = config['TOT_SUM_PRESS_TAGS']
    raw_flow_unit = config['RAW_FLOW_UNIT']
    demands_from_rawdata = config['SI_DEMANDS_FROM_RAWDATA_ONLY'] # boolean 값으로 가져옴
    resv_window_sec = config['SI_RESV_WINDOW_SEC']
    tot_node_id = config['TOT_NODE_ID']
    inp_path_to_use = config['INP_MO_FILE_PATH']
    node_table = config['NODE_TABLE']
    link_table = config['LINK_TABLE']
    tot_table = config['TOT_TABLE']
    pump_grp = 0
    fallback_sec = config['FALLBACK_SEC']
    pump_map_json = ""
    debug_pump = False
    debug_flow = False
    abs_flow = False
    flag = "mo"
    db = db_session or g.db
    
    now_ts = ts or epa_models.get_latest_5min_ts_from_rawdata(db)
    logger.info(f"MO 시뮬레이션 대상 시각: {now_ts} (입력 ts: {ts})")
    
    # 메타/태그 로드
    node_meta = epa_models.load_node_meta(db)
    link_meta = epa_models.load_link_meta(db)

    fp_tags = [r["FP_TAGNAME"] for r in node_meta if r.get("FP_TAGNAME")]
    link_fr_tags = [r["FLW_TAGNAME"] for r in link_meta if r.get("FLW_TAGNAME")]
    fp_by_tag      = epa_models.fetch_values_by_tag_with_fallback(db, now_ts, fp_tags, fallback_sec=fallback_sec)
    link_fr_by_tag = epa_models.fetch_values_by_tag_with_fallback(db, now_ts, link_fr_tags, fallback_sec=fallback_sec)

    # INP 로드 및 단위
    wn = load_inp_with_fallback(inp_path_to_use)
    inp_flow_unit = get_inp_flow_unit(wn)

    # 펌프조합(1/0 → ON 인덱스)
    pump_tag_map = PUMP_STATUS_TAG_MAP_DEFAULT.copy()
    if pump_map_json:
        pump_tag_map.update(json.loads(Path(pump_map_json).read_text(encoding="utf-8")))
    set_pumps_from_rawdata(
        wn,
        db,
        now_ts,
        tag_map=pump_tag_map,
        tag_to_link=PUMP_TAG_TO_LINKNAME,
        fallback_sec=fallback_sec,
        debug=debug_pump,
    )
    on_indices = fetch_pump_comb_from_rawdata(db, now_ts, pump_tag_map, fallback_sec=fallback_sec, debug=debug_pump)
    pump_comb_str = ",".join(str(i) for i in on_indices) if on_indices else ""
    print(f"[INFO] 감지된 펌프조합: {pump_comb_str or '(none)'}")

    # TB_PUMP_CAL 밴드(CMH)
    cmh_min = cmh_max = None
    if pump_comb_str:
        cmh_min, cmh_max = epa_models.fetch_fc_range_by_comb(db, pump_comb_str, pump_grp=(pump_grp or None))
        si_min = to_si(FlowUnits.CMH, cmh_min, HydParam.Flow)
        si_max = to_si(FlowUnits.CMH, cmh_max, HydParam.Flow)
        band_min_inp = from_si(inp_flow_unit, si_min, HydParam.Flow)
        band_max_inp = from_si(inp_flow_unit, si_max, HydParam.Flow)
        print(f"[INFO] 밴드(CMH) min={cmh_min:g}, max={cmh_max:g} / INP유닛 min={band_min_inp:g}, max={band_max_inp:g}")
    else:
        print("[WARN] 가동 펌프 없음: 밴드 조회 생략")

    # 수요 구성 = TB_RAWDATA 기반
    raw_unit = _parse_flow_unit(raw_flow_unit, default=FlowUnits.CMH)
    fr_tags_for_nodes = [r["FR_TAGNAME"] for r in node_meta if r.get("FR_TAGNAME")]
    fr_by_tag_for_demands = epa_models.fetch_values_by_tag_with_fallback(db, now_ts, fr_tags_for_nodes, fallback_sec=fallback_sec)
    si_demands = build_demands_from_rawdata(node_meta, fr_by_tag_for_demands, raw_flow_unit=raw_unit)
    set_demands_to_model(wn, si_demands)

    # 해석
    results = run_and_get_results(wn)
    p0 = results.node["pressure"].iloc[0]
    f0 = results.link["flowrate"].iloc[0]
    l0 = results.link["headloss"].iloc[0]
    # 밴드 체크
    try:
        tgt_link = resolve_target_link(wn, rule_pipe_id)
        if tgt_link is None:
            print(f"[WARN] 기준 링크를 찾을 수 없습니다(rule-pipe-id={rule_pipe_id}). 밴드 체크 생략")
        else:
            raw = float(f0.get(tgt_link, 0.0))
            si_val = float(raw)
            cmh = si_val * 3600.0
            fu_res, src_res = None, "forced_SI"

            if debug_flow:
                asum = "SI(m^3/s)" if fu_res is None else str(fu_res)
                print(f"[DEBUG] band-check link={tgt_link} raw={raw:g} unit_src={src_res} assumed={asum}  SI={si_val:g}  CMH={cmh:g}")
            if cmh_min is not None and cmh_max is not None:
                ok = (cmh_min <= cmh <= cmh_max)
                state = "OK" if ok else "WARN"
                print(f"[{state}] 기준링크={tgt_link} 유량={cmh:.3f} CMH, 밴드=[{cmh_min:g}, {cmh_max:g}]")
            else:
                print(f"[INFO] 기준링크={tgt_link} 유량={cmh:.3f} CMH (밴드 미조회)")
    except Exception as e:
        print(f"[WARN] 밴드 체크 중 예외 발생: {e}")

    # 실측 매핑(태그 → 링크ID/노드)
    fp_measured_by_node: Dict[str, float] = {}
    for r in node_meta:
        nid = r["NODE_ID"]; tag = r.get("FP_TAGNAME")
        if tag and tag in fp_by_tag: fp_measured_by_node[nid] = float(fp_by_tag[tag])
    link_measured_fr_by_linkid: Dict[str, float] = {}
    for r in link_meta:
        lid = r["LINK_ID"]; t = r.get("FLW_TAGNAME")
        if t and t in link_fr_by_tag: link_measured_fr_by_linkid[lid] = float(link_fr_by_tag[t])

    # 저장
    epa_models.store_link_results(
        db,
        now_ts,
        wn,
        results,
        link_measured_fr_by_linkid,
        link_table=link_table,
        raw_meas_unit=raw_unit,
        use_abs_flow=abs_flow,
        debug_flow=debug_flow,
        flag=flag,
    )
    epa_models.store_node_results( 
        db=db,
        ts=now_ts,
        node_pressure=p0,
        node_measured_fp=fp_measured_by_node,
        node_table=node_table,
        flag = flag
    )
    epa_models.store_tot_alg(
        db, 
        now_ts, 
        wn, 
        p0, 
        results.link["flowrate"].iloc[0], 
        results.link["headloss"].iloc[0],          
        tot_table=tot_table, tot_node_id=tot_node_id,
        sum_flow_tags=[t.strip() for t in sum_flow_tags.split(",") if t.strip()],
        sum_press_tags=[t.strip() for t in sum_press_tags.split(",") if t.strip()],
        flag=flag
    )
    db.commit()


def run_si_simulation(
    ts: Optional[datetime] = None,
    db_session: Optional[DbManager] = None,
    pump_comb: Optional[str] = None,
    flow_min: Optional[float] = None,
    flow_max: Optional[float] = None,
    rule_pipe_id: int = 10,
    rule_priority: int = 24,
    pump_hz: Optional[dict] = None,
) -> dict:
    """'si' 모드 시뮬레이션을 실행합니다. (pump_comb / flow_min/flow_max 옵션 지원)

    pump_hz 는 군산 전용이라 여기서는 받기만 하고 쓰지 않는다.
    고산은 펌프를 [RULES] 의 STATUS OPEN/CLOSED 로만 표현해 가변속(주파수) 개념이 없다.
    그래도 인자를 받아 두는 이유: app/services/engine.py 가 두 모듈을 같은 시그니처로
    바꿔 끼우므로(engine.py:12), 라우트가 어느 엔진인지 모르고 pump_hz 를 넘겨도
    TypeError 가 나지 않아야 한다.
    """
    db = db_session or g.db
    config = current_app.config
    sum_flow_tags = config['TOT_SUM_FLOW_TAGS']
    sum_press_tags = config['TOT_SUM_PRESS_TAGS']
    raw_flow_unit = config['RAW_FLOW_UNIT']
    demands_from_rawdata = config['SI_DEMANDS_FROM_RAWDATA_ONLY'] # boolean 값으로 가져옴
    resv_window_sec = config['SI_RESV_WINDOW_SEC']
    tot_node_id = config['TOT_NODE_ID']
    inp_path_to_use = config['INP_SI_FILE_PATH']
    node_table = config['NODE_TABLE']
    link_table = config['LINK_TABLE']
    tot_table = config['TOT_TABLE']
    pump_grp = 0
    flag = "si"
    started_at = time.perf_counter()
    try:
        # print(pump_comb.PUMP_COMB)
        target_ts = ts or epa_models.get_latest_ts_from_rawdata(db)
        if not target_ts:
            raise ValueError("실행할 데이터 시각을 찾을 수 없습니다.")
        print(target_ts)
        node_meta = epa_models.load_node_meta(db)
        link_meta = epa_models.load_link_meta(db)
        
        fp_tags = [r["FP_TAGNAME"] for r in node_meta if r.get("FP_TAGNAME")]
        link_fr_tags = [r["FLW_TAGNAME"] for r in link_meta if r.get("FLW_TAGNAME")]
        
        fp_by_tag      = epa_models.fetch_values_by_tag_nearest(db, target_ts, fp_tags)
        link_fr_by_tag = epa_models.fetch_values_by_tag_nearest(db, target_ts, link_fr_tags)
        
        if not inp_path_to_use:
            raise ValueError("INP_SI_FILE_PATH 설정이 없습니다.")
        
        if not Path(inp_path_to_use).exists():
            raise FileNotFoundError(f"INP 파일을 찾을 수 없습니다: {inp_path_to_use}")
        
        inp_flow_unit = get_inp_flow_unit_from_file(inp_path_to_use, default=FlowUnits.LPS)
            
        need_rule = bool(pump_comb and rule_pipe_id)
        if need_rule:
            flow_min = flow_min
            flow_max = flow_max

            if (flow_min is None or flow_max is None):
                pump_grp = pump_grp or None
                cmh_min, cmh_max = epa_models.fetch_fc_range_by_comb(db, pump_comb, pump_grp=pump_grp)
                si_min = to_si(FlowUnits.CMH, cmh_min, HydParam.Flow)
                si_max = to_si(FlowUnits.CMH, cmh_max, HydParam.Flow)
                flow_min = from_si(inp_flow_unit, si_min, HydParam.Flow)
                flow_max = from_si(inp_flow_unit, si_max, HydParam.Flow)

            try:
                tmp_inp = inject_rule_to_inp(
                    inp_path=Path(inp_path_to_use),
                    pump_comb_str=str(pump_comb),
                    flow_min=float(flow_min),
                    flow_max=float(flow_max),
                    rule_pipe_id_raw=str(rule_pipe_id),  # 여기를 수정: int를 str로 변환
                    rule_priority=int(rule_priority),
                    rule_name="1",
                )
                inp_path_to_use = str(tmp_inp)
                print(f"[INFO] RULE 적용 INP 사용: {inp_path_to_use} (min={flow_min:g}, max={flow_max:g} in INP units)")
            except Exception as e:
                print(f"[WARN] RULE 주입 실패: {e} (원본 INP로 진행)")
                
                
        # 최종 INP 로드
        wn = load_inp_with_fallback(inp_path_to_use)

        # 단위 파싱 (원자료 -> SI 변환용)
        raw_unit = _parse_flow_unit(raw_flow_unit, default=FlowUnits.CMH)

        # DEMAND 구성 & 적용
        node_ids = [r["NODE_ID"] for r in node_meta]

        # 디버깅 수집용
        raw_map: Dict[str, float] = {}
        tagname_map: Dict[str, Optional[str]] = {}
        src_map: Dict[str, str] = {}

        if demands_from_rawdata:
            # RAWDATA만 사용: ‘요청시각과 가장 가까운’ 값
            fr_tags_for_nodes = [r["FR_TAGNAME"] for r in node_meta if r.get("FR_TAGNAME")]
            fr_by_tag = epa_models.fetch_values_by_tag_nearest(db, target_ts, fr_tags_for_nodes)
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
            fr_by_tag = epa_models.fetch_values_by_tag_nearest(db, target_ts, fr_tags_for_nodes)
            for r in node_meta:
                nid = r["NODE_ID"]
                tg = r.get("FR_TAGNAME")
                tagname_map[nid] = tg
                raw_map[nid] = float(fr_by_tag.get(tg, 0.0)) if tg else 0.0

            # 2) RESV_FLOW(±window_sec에서 가장 가까운)로 덮어쓰기
            resv_by_node = epa_models.fetch_reservoir_flow_by_node_nearest(db, target_ts, node_ids, window_sec=resv_window_sec)

            # 혼합 수요 생성 + 소스맵 채우기
            si_demands = build_demands_merged(
                node_meta=node_meta,
                raw_map_by_node=raw_map,
                resv_by_node=resv_by_node,
                raw_flow_unit=raw_unit,
                debug_src_map=src_map,
            )

        debug_raw  = "False"
        dump_demands_csv = ""
        # 디버그/덤프 출력
        if debug_raw or dump_demands_csv:
            rows = []
            for r in node_meta:
                nid = r["NODE_ID"]
                tg = tagname_map.get(nid)
                raw_val = raw_map.get(nid, 0.0)
                si_val = float(si_demands.get(nid, 0.0))
                src = src_map.get(nid, "RAW" if demands_from_rawdata else ("RESV" if nid not in raw_map else "RAW/RESV"))
                rows.append({
                    "NODE_ID": nid,
                    "FR_TAGNAME": tg,
                    "RAW_VALUE": raw_val,
                    "RAW_UNIT": str(raw_unit.name),
                    "SI_VALUE": si_val,
                    "SRC": src,
                })
            df = pd.DataFrame(rows)
            if debug_raw:
                print("[DEBUG] Demand mapping (top 20)")
                print(df.head(20).to_string(index=False))
            if dump_demands_csv:
                outp = Path(dump_demands_csv)
                df.to_csv(outp, index=False, encoding="utf-8-sig")
                print(f"[DEBUG] Demand mapping CSV saved -> {outp}")

        # 모델에 주입
        set_demands_to_model(wn, si_demands)

        # INP 저장(선택, 한글 보존)
        # (주: wntr이 쓰는 임시 파일은 UTF-8이라 EPANET GUI에서 한글 깨짐 가능.
        #     EPANET에서 열 목적이면 --save-inp-out을 꼭 쓰세요.)
        save_inp_out = ""
        save_encoding = "cp949"
        if save_inp_out:
            save_inp_with_encoding(wn, save_inp_out, encoding=save_encoding)
            print(f"[OK] INP 저장(한글 보존): {save_inp_out}")

        # 해석 실행: SI API는 첫 번째 timestep 결과만 저장하므로 duration=0 스냅샷만 계산합니다.
        p0, h0, f0, l0 = run_snapshot_initial_only(wn)

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
        epa_models.store_si_link_results(
            db=db,
            ts=target_ts,
            wn=wn,
            link_flow=f0,
            link_hloss=l0,
            link_measured_fr_by_linkid=link_measured_fr_by_linkid,
            link_table=link_table,
            raw_meas_unit=_parse_flow_unit(raw_flow_unit, default=FlowUnits.CMH),
            flag=flag
        )

        sum_flow_tags  = [t.strip() for t in sum_flow_tags.split(",") if t.strip()]
        sum_press_tags = [t.strip() for t in sum_press_tags.split(",") if t.strip()]

        epa_models.store_tot_alg(
            db=db,
            ts=target_ts,
            wn=wn,
            node_pressure=p0,
            link_flow=f0,
            link_hloss=l0,
            tot_table=tot_table,
            tot_node_id=tot_node_id,
            sum_flow_tags=sum_flow_tags,
            sum_press_tags=sum_press_tags,
            flag=flag
        )
        
        logger.debug("store_tot_alg 호출 직전 샘플 출력")
        try:
            logger.debug(f"node_pressure (top10): {p0.iloc[:10].to_dict() if hasattr(p0, 'iloc') else dict(list(p0.items())[:10])}")
        except Exception:
            logger.debug("node_pressure 출력 불가")
        try:
            logger.debug(f"link_flow (top10): {f0.iloc[:10].to_dict() if hasattr(f0, 'iloc') else dict(list(f0.items())[:10])}")
        except Exception:
            logger.debug("link_flow 출력 불가")
        try:
            logger.debug(f"link_hloss (top10): {l0.iloc[:10].to_dict() if hasattr(l0, 'iloc') else dict(list(l0.items())[:10])}")
        except Exception:
            logger.debug("link_hloss 출력 불가")

        epa_models.store_node_results(
            db=db,
            ts=target_ts,
            node_pressure=p0,
            node_measured_fp=fp_measured_by_node,
            node_table=node_table,
            flag=flag
        )
        logger.debug(f"store_node_results 호출 직후: fp_measured_by_node count={len(fp_measured_by_node)}; sample={list(fp_measured_by_node.items())[:10]}")

        # 커밋 및 커밋 직후 DB 샘플 조회 (디버깅)
    
        db.commit()
        elapsed = time.perf_counter() - started_at
        logger.info("SI 시뮬레이션 결과 DB 저장 완료 (commit), elapsed=%.2fs", elapsed)
        return {
            "status": "completed",
            "target_ts": target_ts.isoformat(),
            "pump_comb": pump_comb,
            "elapsed_sec": round(elapsed, 3),
        }
        

    except Exception as e:
        logger.error(f"SI 시뮬레이션 중 오류 발생: {e}", exc_info=True)
        # [수정] 오류 발생 시 롤백을 명시적으로 추가하면 더 안전합니다.
        if db and db.conn:
            db.conn.rollback()
        raise e
    
def fetch_pump_comb_from_rawdata(db: DbManager, ts: datetime, pump_tag_map: Dict[int, str],
                                 fallback_sec: int=600, debug: bool=False) -> List[int]:
    tags = [t for t in pump_tag_map.values() if t]
    tag2val = epa_models.fetch_values_by_tag_with_fallback(db, ts, tags, fallback_sec=fallback_sec)
    on_indices: List[int] = []
    for idx, tag in pump_tag_map.items():
        val = float(tag2val.get(tag, 0.0))
        if debug:
            print(f"[DEBUG] pump tag {tag} idx={idx} val={val}")
        if int(round(val)) == 1:
            on_indices.append(idx)
    on_indices.sort()
    return on_indices

def run_mo_simulation_for_range(start_ts: datetime, 
                              end_ts: datetime, 
                              db_session: Optional[DbManager] = None) -> dict:
    """
    주어진 시간 범위(start_ts ~ end_ts) 내에서 5분 간격으로
    run_mo_simulation을 반복 실행합니다.
    
    Args:
        start_ts (datetime): 시뮬레이션 시작 시각
        end_ts (datetime): 시뮬레이션 종료 시각 (이 시각 포함)
        db_session (Optional[DbManager]): 사용할 DB 세션. 
                                        None이면 g.db에서 가져옵니다.

    Returns:
        dict: 실행 결과 요약 (성공/실패 건수)
    """
    
    # 1. DB 세션 가져오기 (기존 함수와 동일한 로직)
    db = db_session or g.db
    
    # 2. 타임스탬프 루프 생성
    current_ts = start_ts
    success_count = 0
    fail_count = 0
    total_count = 0
    
    logger.info(f"시뮬레이션 배치 작업 시작: {start_ts} ~ {end_ts}")

    while current_ts <= end_ts:
        total_count += 1
        logger.info(f"--- [{current_ts}] 시뮬레이션 처리 시작 ---")
        try:
            # 3. 'ts'를 지정하여 개별 시뮬레이션 실행
            # (run_mo_simulation이 내부적으로 db.commit()을 호출합니다)
            run_mo_simulation(ts=current_ts, db_session=db)
            
            logger.info(f"[SUCCESS] [{current_ts}] 시뮬레이션 성공.")
            success_count += 1
            
        except Exception as e:
            logger.error(f"[FAILURE] [{current_ts}] 시뮬레이션 중 오류 발생: {e}")
            logger.error(traceback.format_exc()) # 로그에 상세 스택 트레이스 남기기
            fail_count += 1
            
            # 4. 개별 실행 실패 시 롤백
            # (run_mo_simulation이 commit 전에 실패했을 경우를 대비)
            try:
                db.conn.rollback()
                logger.warning(f"[{current_ts}] 실패로 인한 롤백 수행.")
            except Exception as rb_e:
                logger.error(f"[ERROR] 롤백 중 오류 발생: {rb_e}")

        # 5. 다음 5분으로 이동
        current_ts += timedelta(minutes=5)

    logger.info(f"시뮬레이션 배치 작업 완료. (총 {total_count}건 중 성공: {success_count}, 실패: {fail_count})")
    
    return {
        "status": "completed",
        "total": total_count,
        "success": success_count,
        "failed": fail_count
    }
