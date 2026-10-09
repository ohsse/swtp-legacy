from __future__ import annotations
from typing import Dict, Any, List, Tuple, Iterable, Optional
import argparse
import json
from datetime import datetime
from pathlib import Path
import tempfile

import pymysql
import pandas as pd
import wntr
from wntr.epanet.util import FlowUnits, to_si, from_si, HydParam


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


def fetch_values_by_tag_with_fallback(db, ts, tags, fallback_sec=600):
    tag_list = [t for t in tags if t]
    if not tag_list:
        return {}
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


def fetch_reservoir_flow_by_node(
    db: DbManager, ts: datetime, node_ids: Iterable[str], fallback_sec: int = 600
) -> Dict[str, float]:
    node_list = [n for n in node_ids if n]
    if not node_list:
        return {}
    placeholders = ",".join(["%s"] * len(node_list))
    sql = f"""
      SELECT t.NODE_ID, t.FLOW_RATE
      FROM TB_EPA_SIM_RESV_FLOW t
      JOIN (
        SELECT NODE_ID, MAX(UPDT_TIME) AS UPDT_TIME
        FROM TB_EPA_SIM_RESV_FLOW
        WHERE UPDT_TIME <= %s
          AND UPDT_TIME >= DATE_SUB(%s, INTERVAL %s SECOND)
          AND NODE_ID IN ({placeholders})
        GROUP BY NODE_ID
      ) x ON x.NODE_ID = t.NODE_ID AND x.UPDT_TIME = t.UPDT_TIME
    """
    rows = db.fetchall(sql, (ts, ts, fallback_sec, *node_list))
    return {r["NODE_ID"]: float(r["FLOW_RATE"]) for r in rows}


def build_demands_from_resv_flow(
    node_meta: List[dict],
    resv_by_node: Dict[str, float],
    flow_unit: FlowUnits
) -> Dict[str, float]:
    demand_model_units: Dict[str, float] = {}
    for r in node_meta:
        nid = r["NODE_ID"]
        demand_model_units[nid] = float(resv_by_node.get(nid, 0.0))

    def node_val(nid: str) -> float:
        return demand_model_units.get(nid, 0.0)

    adjusted = dict(demand_model_units)
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

    return {nid: to_si(flow_unit, float(v), HydParam.Demand) for nid, v in adjusted.items()}


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
        rows.append((ts, node_id, p_meas, float(p_alg), "si"))  # FLG='si'
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
    flow_unit: FlowUnits,
    link_flow: pd.Series,
    link_hloss: pd.Series,
    link_measured_fr_by_linkid: Dict[str, float],
    link_table: str = "TB_FR_SI_VAL"
) -> None:
    rows: List[Tuple] = []
    for link_id in wn.link_name_list:
        ln = wn.get_link(link_id)
        if getattr(ln, "link_type", "") != "Pipe":
            continue
        hh_loss_val = float(link_hloss.get(link_id, 0.0)) * float(ln.length)  # 원식 유지
        flw_alg = from_si(flow_unit, float(link_flow.get(link_id, 0.0)), HydParam.Demand)
        link_meas = link_measured_fr_by_linkid.get(link_id) if link_measured_fr_by_linkid else None
        rows.append((link_id, hh_loss_val, ts, link_meas, flw_alg, "si"))  # FLG='si'
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
    flow_unit: FlowUnits,
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
    db.executemany(sql, [(ts, loss_tot, flow_sum, press_sum, fp_alg, "si")])  # FLG='si'


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

    ap.add_argument("--fallback-sec", type=int, default=600, help="폴백 범위(초)")

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
        fp_by_tag      = fetch_values_by_tag_with_fallback(db, target_ts, fp_tags,      fallback_sec=args.fallback_sec)
        link_fr_by_tag = fetch_values_by_tag_with_fallback(db, target_ts, link_fr_tags, fallback_sec=args.fallback_sec)

        wn = load_inp_with_fallback(args.inp)
        unit_name = getattr(getattr(wn.options, "hydraulic", None), "inpfile_units", None)
        if not unit_name:
            toDict = wn.to_dict()
            unit_name = toDict.get("options", {}).get("hydraulic", {}).get("inpfile_units", "LPS")
        flow_unit = FlowUnits[str(unit_name).upper()]

        node_ids = [r["NODE_ID"] for r in node_meta]
        resv_by_node = fetch_reservoir_flow_by_node(db, target_ts, node_ids, fallback_sec=args.fallback_sec)
        si_demands = build_demands_from_resv_flow(node_meta, resv_by_node, flow_unit)
        set_demands_to_model(wn, si_demands)

        if args.save_inp_out:
            save_inp_with_encoding(wn, args.save_inp_out, encoding=args.save_encoding)
            print(f"[OK] INP 저장(한글 보존): {args.save_inp_out}")

        (p0, h0, f0, l0), (_pL, _hL, _fL, _lL) = run_snapshot_return_both(wn)

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

        store_node_results(db, target_ts, p0, fp_measured_by_node, node_table=args.node_table)
        store_link_results(db, target_ts, wn, flow_unit, f0, l0, link_measured_fr_by_linkid, link_table=args.link_table)

        sum_flow_tags  = [t.strip() for t in args.sum_flow_tags.split(",") if t.strip()]
        sum_press_tags = [t.strip() for t in args.sum_press_tags.split(",") if t.strip()]
        store_tot_alg(
            db, target_ts, wn, flow_unit,
            node_pressure=p0, link_flow=f0, link_hloss=l0,
            tot_table=args.tot_table, tot_node_id=args.tot_node_id,
            sum_flow_tags=sum_flow_tags, sum_press_tags=sum_press_tags,
        )

        db.commit()
        print("[OK] 관망해석 시뮬레이션 저장 완료")

    finally:
        db.close()


if __name__ == "__main__":
    main()
