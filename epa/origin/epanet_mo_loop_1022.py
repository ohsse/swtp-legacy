from __future__ import annotations
from typing import Dict, Any, List, Tuple, Iterable, Optional
import argparse
import json
from datetime import datetime
from time import sleep
from pathlib import Path
import tempfile
import warnings

import pymysql
import pandas as pd
import wntr
from wntr.epanet.util import FlowUnits, to_si, from_si, HydParam

# --- 펌프 상태 태그 매핑 (1=ON, 0=OFF) --------------------------------------
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

# --- 공통 유틸 ---------------------------------------------------------------
def _parse_flow_unit(name: str, default: FlowUnits = FlowUnits.CMH) -> FlowUnits:
    try:
        return getattr(FlowUnits, str(name).upper())
    except Exception:
        return default

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
            cur.execute(sql, params); return cur.fetchone()
    def fetchall(self, sql: str, params: Tuple = ()) -> List[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params); return cur.fetchall()
    def executemany(self, sql: str, rows: List[Tuple]) -> None:
        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
    def commit(self) -> None:
        self.conn.commit()
    def close(self) -> None:
        self.conn.close()

def pick_latest_ts(db: DbManager, now_dt: datetime) -> Optional[datetime]:
    row = db.fetchone("SELECT MAX(ts) AS ts FROM TB_RAWDATA WHERE ts <= %s", (now_dt,))
    return row["ts"] if row and row.get("ts") else None

def fetch_values_by_tag_with_fallback(db: DbManager, ts: datetime, tags: List[str], fallback_sec=600) -> Dict[str, float]:
    tag_list = [t for t in tags if t]
    if not tag_list: return {}
    placeholders = ",".join(["%s"] * len(tag_list))
    sql = f"""
      SELECT r.TAGNAME, r.VALUE
      FROM TB_RAWDATA r
      JOIN (
        SELECT TAGNAME, MAX(ts) AS ts
        FROM TB_RAWDATA
        WHERE ts <= %s
          AND ts >= DATE_SUB(%s, INTERVAL %s SECOND)
          AND TAGNAME IN ({placeholders})
        GROUP BY TAGNAME
      ) x ON x.TAGNAME = r.TAGNAME AND x.ts = r.ts
    """
    rows = db.fetchall(sql, (ts, ts, fallback_sec, *tag_list))
    return {r["TAGNAME"]: float(r["VALUE"]) for r in rows}

def load_node_meta(db: DbManager) -> List[dict]:
    return db.fetchall("""
      SELECT NODE_ID, FP_TAGNAME, FR_TAGNAME
      FROM TB_NODE_TAG
      ORDER BY NODE_ID
    """)

def load_link_meta(db: DbManager) -> List[dict]:
    return db.fetchall("""
      SELECT LINK_ID, MIN(GRP_NM) AS GRP_NM, MAX(FLW_TAGNAME) AS FLW_TAGNAME
      FROM TB_LINK_GRP
      GROUP BY LINK_ID
      ORDER BY LINK_ID
    """)

def fetch_fc_range_by_comb(db: DbManager, pump_comb: str, pump_grp: Optional[str] = None) -> Tuple[float, float]:
    pump_comb_norm = ",".join([t.strip() for t in str(pump_comb).split(",") if t.strip()])
    params: List[Any] = []
    where = ["PUMP_COMB = %s"]; params.append(pump_comb_norm)
    if pump_grp: where.append("PUMP_GRP = %s"); params.append(pump_grp)
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
    return vmin, vmax  # CMH

# --- INP/결과 단위 처리 (si_patched 동일 원칙) -------------------------------
def get_inp_flow_unit(wn) -> FlowUnits:
    try:
        name = getattr(getattr(wn.options, "hydraulic", None), "inpfile_units", None)
        if not name:
            name = wn.to_dict().get("options", {}).get("hydraulic", {}).get("inpfile_units", "CMH")
        return getattr(FlowUnits, str(name).upper(), FlowUnits.CMH)
    except Exception:
        return FlowUnits.CMH

def detect_results_flow_unit_or_inp(wn, results) -> Tuple[Optional[FlowUnits], str]:
    """
    1) results.metadata['units']['link']['flowrate'] 우선
    2) 없으면 INP 유닛을 결과의 '표기 단위'로 가정
    3) metadata가 SI(m^3/s)이면 None 리턴 → 그대로 SI 처리
    """
    try:
        u = results.metadata['units']['link']['flowrate']
        tok = (str(u) or "").replace("^3", "3").replace(" ", "").lower()
    except Exception:
        tok = ""
    m = {
        "lps": FlowUnits.LPS, "gpm": FlowUnits.GPM, "cfs": FlowUnits.CFS,
        "mgd": FlowUnits.MGD, "cmh": FlowUnits.CMH, "m3/h": FlowUnits.CMH, "m^3/h": FlowUnits.CMH,
        "m3/s": None, "m^3/s": None, "m3persec": None
    }
    if tok in m:
        fu = m[tok]
        return fu, ("metadata(SI)" if fu is None else "metadata")
    return get_inp_flow_unit(wn), "fallback_inp"

def to_cmh_from_results_value(wn, results, raw_flow: float) -> Tuple[float, Optional[FlowUnits], str, float]:
    fu, source = detect_results_flow_unit_or_inp(wn, results)
    if fu is None:  # already SI
        si_val = float(raw_flow)
    else:
        si_val = to_si(fu, float(raw_flow), HydParam.Flow)
    cmh = from_si(FlowUnits.CMH, si_val, HydParam.Flow)
    return cmh, fu, source, si_val

# --- 수요(노드 demand) : TB_RAWDATA 만 사용 -------------------------------
def build_demands_from_rawdata(node_meta: List[dict], fr_by_tag: Dict[str, float], raw_flow_unit: FlowUnits) -> Dict[str, float]:
    demand_raw_by_node: Dict[str, float] = {}
    for r in node_meta:
        nid = r["NODE_ID"]; fr_tag = r.get("FR_TAGNAME")
        v = float(fr_by_tag.get(fr_tag, 0.0)) if fr_tag else 0.0
        demand_raw_by_node[nid] = v
    # (사이트 보정 로직 유지 시 필요 부분만 남김)
    def node_val(nid: str) -> float: return demand_raw_by_node.get(nid, 0.0)
    adjusted = dict(demand_raw_by_node)
    if "이서배수지" in adjusted: adjusted["이서배수지"] = node_val("이서배수지") / 3.7
    if "왕궁관말" in adjusted:   adjusted["왕궁관말"]   = node_val("왕궁관말") * 1.0
    if "199" in adjusted:        adjusted["199"]        = node_val("천마배수지") * 1.0
    if "201" in adjusted:        adjusted["201"]        = node_val("201") / 1.3
    if "김제(배)" in adjusted:    adjusted["김제(배)"]     = node_val("김제(배)") * 1.0
    # 태그 단위 → SI(m^3/s)
    return {nid: to_si(raw_flow_unit, float(v), HydParam.Flow) for nid, v in adjusted.items()}

def set_demands_to_model(wn: wntr.network.WaterNetworkModel, si_demands: Dict[str, float]) -> None:
    for name in wn.junction_name_list:
        j = wn.get_node(name)
        v = float(si_demands.get(name, 0.0))
        dlist = getattr(j, "demand_timeseries_list", None)
        if dlist and len(dlist) > 0: dlist[0].base_value = v
        else: j.add_demand(base=v, pattern=None, category="Base")

def load_inp_with_fallback(path: str):
    p = Path(path)
    try:
        return wntr.network.WaterNetworkModel(str(p))
    except Exception:
        pass
    for enc in ("cp949", "euc-kr", "utf-8-sig", "latin-1"):
        try:
            text = p.read_text(encoding=enc)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
                tmp.write(text); tmp_path = tmp.name
            return wntr.network.WaterNetworkModel(tmp_path)
        except Exception:
            continue
    raise RuntimeError("INP 로드 실패")

# --- 결과 저장 ---------------------------------------------------------------
def fetch_sum_raw(db: DbManager, ts: datetime, tags: list[str]) -> float:
    tags = [t for t in tags if t]
    if not tags: return 0.0
    ph = ",".join(["%s"]*len(tags))
    row = db.fetchone(f"SELECT SUM(value) AS s FROM TB_RAWDATA WHERE ts=%s AND tagname IN ({ph})", (ts, *tags))
    return float(row["s"] or 0.0) if row else 0.0

def store_node_results(db: DbManager, ts: datetime, node_pressure: pd.Series, node_measured_fp: Dict[str, float],
                       node_table: str = "TB_FP_SI_VAL", flag: str="mo") -> None:
    rows: List[Tuple] = []
    for node_id, p_alg in node_pressure.items():
        p_meas = node_measured_fp.get(node_id) if node_measured_fp else None
        rows.append((ts, node_id, p_meas, float(p_alg), flag))
    if rows:
        sql = f"""
          REPLACE INTO {node_table}
            (RGSTR_TIME, NODE_ID, FP_VAL, FP_ALG_RST_VAL, FLG)
          VALUES (%s,%s,%s,%s,%s)
        """
        db.executemany(sql, rows)

def store_link_results(db: DbManager, ts: datetime, wn: wntr.network.WaterNetworkModel, results,
                       link_measured_fr_by_linkid: Dict[str, float] | None,
                       link_table: str = "TB_FR_SI_VAL",
                       raw_meas_unit: FlowUnits = FlowUnits.CMH,
                       use_abs_flow: bool=False, debug_flow: bool=False, flag: str="mo") -> None:
    f0 = results.link["flowrate"].iloc[0]
    l0 = results.link["headloss"].iloc[0]

    fu_res, src_res = detect_results_flow_unit_or_inp(wn, results)
    if debug_flow:
        print(f"[DEBUG] results flow unit source = {src_res}, mapped = {fu_res or 'SI(m^3/s)'}")

    rows: List[Tuple] = []
    for link_id in wn.link_name_list:
        ln = wn.get_link(link_id)
        if getattr(ln, "link_type", "") != "Pipe":
            continue

        # 알고리즘 유량: 결과값 → CMH
        raw_val = float(f0.get(link_id, 0.0))
        si_val = float(raw_val)
        if use_abs_flow:
            si_val = abs(si_val)
        flw_alg_cmh = si_val * 3600.0

        # 실측 유량: 태그 단위(raw_meas_unit) → CMH
        link_meas_cmh = None
        if link_measured_fr_by_linkid and (link_id in link_measured_fr_by_linkid):
            meas_raw = float(link_measured_fr_by_linkid[link_id])
            si_meas  = to_si(raw_meas_unit, meas_raw, HydParam.Flow)
            link_meas_cmh = from_si(FlowUnits.CMH, si_meas, HydParam.Flow)

        hh_loss_val = float(l0.get(link_id, 0.0)) * float(ln.length)
        rows.append((link_id, hh_loss_val, ts, link_meas_cmh, flw_alg_cmh, flag))

    if rows:
        sql = f"""
          REPLACE INTO {link_table}
            (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, LINK_VAL, FLW_ALG_RST_VAL, FLG)
          VALUES (%s,%s,%s,%s,%s,%s)
        """
        db.executemany(sql, rows)

def store_tot_alg(db: DbManager, ts: datetime, wn: wntr.network.WaterNetworkModel,
                  node_pressure: pd.Series, link_flow: pd.Series, link_hloss: pd.Series,
                  tot_table: str, tot_node_id: str, sum_flow_tags: list[str], sum_press_tags: list[str], flag: str="mo"):
    # 합계는 TB_RAWDATA 태그 합으로 산정
    flow_sum  = fetch_sum_raw(db, ts, sum_flow_tags)
    press_sum = fetch_sum_raw(db, ts, sum_press_tags)
    fp_alg = float(node_pressure.get(tot_node_id, 0.0))
    sql = f"""
      REPLACE INTO {tot_table}
        (RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL, FLG)
      VALUES (%s,%s,%s,%s,%s,%s)
    """
    db.executemany(sql, [(ts, 0.0, flow_sum, press_sum, fp_alg, flag)])

# --- 기타 유틸 ---------------------------------------------------------------
def fetch_pump_comb_from_rawdata(db: DbManager, ts: datetime, pump_tag_map: Dict[int, str],
                                 fallback_sec: int=600, debug: bool=False) -> List[int]:
    tags = [t for t in pump_tag_map.values() if t]
    tag2val = fetch_values_by_tag_with_fallback(db, ts, tags, fallback_sec=fallback_sec)
    on_indices: List[int] = []
    for idx, tag in pump_tag_map.items():
        val = float(tag2val.get(tag, 0.0))
        if debug:
            print(f"[DEBUG] pump tag {tag} idx={idx} val={val}")
        if int(round(val)) == 1:
            on_indices.append(idx)
    on_indices.sort()
    return on_indices

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

# --- 메인 실행 ---------------------------------------------------------------
def run_once(args, db: DbManager, now_ts: datetime, flag: str="mo") -> None:
    print(f"[INFO] 실행 시각 ts={now_ts}")

    # 메타/태그 로드
    node_meta = load_node_meta(db)
    link_meta = load_link_meta(db)

    fp_tags = [r["FP_TAGNAME"] for r in node_meta if r.get("FP_TAGNAME")]
    link_fr_tags = [r["FLW_TAGNAME"] for r in link_meta if r.get("FLW_TAGNAME")]
    fp_by_tag      = fetch_values_by_tag_with_fallback(db, now_ts, fp_tags, fallback_sec=args.fallback_sec)
    link_fr_by_tag = fetch_values_by_tag_with_fallback(db, now_ts, link_fr_tags, fallback_sec=args.fallback_sec)

    # INP 로드 및 단위
    wn = load_inp_with_fallback(args.inp)
    inp_flow_unit = get_inp_flow_unit(wn)

    # 펌프조합(1/0 → ON 인덱스)
    pump_tag_map = PUMP_STATUS_TAG_MAP_DEFAULT.copy()
    if args.pump_map_json:
        pump_tag_map.update(json.loads(Path(args.pump_map_json).read_text(encoding="utf-8")))
    on_indices = fetch_pump_comb_from_rawdata(db, now_ts, pump_tag_map, fallback_sec=args.fallback_sec, debug=args.debug_pump)
    pump_comb_str = ",".join(str(i) for i in on_indices) if on_indices else ""
    print(f"[INFO] 감지된 펌프조합: {pump_comb_str or '(none)'}")

    # TB_PUMP_CAL 밴드(CMH)
    cmh_min = cmh_max = None
    if pump_comb_str:
        cmh_min, cmh_max = fetch_fc_range_by_comb(db, pump_comb_str, pump_grp=(args.pump_grp or None))
        si_min = to_si(FlowUnits.CMH, cmh_min, HydParam.Flow)
        si_max = to_si(FlowUnits.CMH, cmh_max, HydParam.Flow)
        band_min_inp = from_si(inp_flow_unit, si_min, HydParam.Flow)
        band_max_inp = from_si(inp_flow_unit, si_max, HydParam.Flow)
        print(f"[INFO] 밴드(CMH) min={cmh_min:g}, max={cmh_max:g} / INP유닛 min={band_min_inp:g}, max={band_max_inp:g}")
    else:
        print("[WARN] 가동 펌프 없음: 밴드 조회 생략")

    # 수요 구성 = TB_RAWDATA 기반
    raw_unit = _parse_flow_unit(args.raw_flow_unit, default=FlowUnits.CMH)
    fr_tags_for_nodes = [r["FR_TAGNAME"] for r in node_meta if r.get("FR_TAGNAME")]
    fr_by_tag_for_demands = fetch_values_by_tag_with_fallback(db, now_ts, fr_tags_for_nodes, fallback_sec=args.fallback_sec)
    si_demands = build_demands_from_rawdata(node_meta, fr_by_tag_for_demands, raw_flow_unit=raw_unit)
    set_demands_to_model(wn, si_demands)

    # 해석
    results = run_and_get_results(wn)
    p0 = results.node["pressure"].iloc[0]
    f0 = results.link["flowrate"].iloc[0]

    # 밴드 체크
    try:
        tgt_link = resolve_target_link(wn, args.rule_pipe_id)
        if tgt_link is None:
            print(f"[WARN] 기준 링크를 찾을 수 없습니다(rule-pipe-id={args.rule_pipe_id}). 밴드 체크 생략")
        else:
            raw = float(f0.get(tgt_link, 0.0))
            si_val = float(raw)
            cmh = si_val * 3600.0
            fu_res, src_res = None, "forced_SI"

            if args.debug_flow:
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
    store_link_results(db, now_ts, wn, results, link_measured_fr_by_linkid,
                       link_table=args.link_table, raw_meas_unit=raw_unit,
                       use_abs_flow=args.abs_flow, debug_flow=args.debug_flow, flag=flag)
    store_tot_alg(db, now_ts, wn, p0, results.link["flowrate"].iloc[0], results.link["headloss"].iloc[0],
                  tot_table=args.tot_table, tot_node_id=args.tot_node_id,
                  sum_flow_tags=[t.strip() for t in args.sum_flow_tags.split(",") if t.strip()],
                  sum_press_tags=[t.strip() for t in args.sum_press_tags.split(",") if t.strip()],
                  flag=flag)
    db.commit()
    print("[OK] 관망해석 시뮬레이션 저장 완료")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", required=True, help="EPANET INP 파일 경로")
    ap.add_argument("--conn", default="./connections.json", help="connections.json 경로")
    ap.add_argument("--conn-key", default="maria-ems-db-gs", help='connections.json 내 Key')
    ap.add_argument("--rule-pipe-id", required=True, help="밴드 체크용 기준 링크ID (예: 10 또는 Pipe10)")
    ap.add_argument("--rule-priority", type=int, default=24)  # 미사용(호환 유지만)

    ap.add_argument("--node-table", default="TB_FP_SI_VAL")
    ap.add_argument("--link-table", default="TB_FR_SI_VAL")
    ap.add_argument("--tot-table", default="TB_TOT_ALG")
    ap.add_argument("--tot-node-id", default="13")
    ap.add_argument("--sum-flow-tags", default="701-367-FRI-4004,701-367-FRI-4001")
    ap.add_argument("--sum-press-tags", default="701-367-PRI-4019,701-367-PRI-4010")

    ap.add_argument("--fallback-sec", type=int, default=600)
    ap.add_argument("--raw-flow-unit", default="CMH", help="태그 유량 단위(CMH/LPS/GPM 등)")
    ap.add_argument("--pump-grp", default="")
    ap.add_argument("--pump-map-json", default="", help="인덱스→태그명 매핑 JSON 파일(선택)")

    ap.add_argument("--abs-flow", action="store_true")
    ap.add_argument("--debug-flow", action="store_true")
    ap.add_argument("--debug-pump", action="store_true")
    ap.add_argument("--flag", default="mo", help="저장 플래그 값(기본 mo)")

    ap.add_argument("--ts", default=None, help="테스트 단발 실행 시각(YYYY-MM-DD HH:MM:SS). 지정 시 루프 미사용.")
    ap.add_argument("--loop", action="store_true", help="루프 모드(5분 간격)")

    args = ap.parse_args()

    cfg = load_db_config(args.conn, args.conn_key)
    db = DbManager(cfg)

    try:
        if args.ts:
            run_once(args, db, datetime.fromisoformat(args.ts), flag=args.flag)
            return
        if not args.loop:
            now_ts = pick_latest_ts(db, datetime.now()) or datetime.now()
            run_once(args, db, now_ts, flag=args.flag)
            return
        print("[INFO] 루프 모드 시작 (5분 간격, 분%5==0에서만 실행)")
        last_run_min = None
        while True:
            now = datetime.now()
            minute = now.minute
            if minute % 5 == 0 and minute != last_run_min:
                ts_to_run = pick_latest_ts(db, now) or now
                run_once(args, db, ts_to_run, flag=args.flag)
                last_run_min = minute
            sleep(5)
    finally:
        db.close()

if __name__ == "__main__":
    main()
