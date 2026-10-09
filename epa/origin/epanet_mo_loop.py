from __future__ import annotations
import argparse, json, time, tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Iterable, Optional

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
    for enc in ("cp949", "euc-kr", "utf-8-sig", "latin-1"):
        try:
            text = p.read_text(encoding=enc)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
                tmp.write(text)
                tmp_path = tmp.name
            return wntr.network.WaterNetworkModel(tmp_path)
        except Exception:
            continue
    raise RuntimeError(f"INP 파일을 읽을 수 없습니다: {path}")

def save_inp_with_encoding(wn, out_path: str, encoding: str = "utf-8-sig"):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".inp", delete=False) as tmp:
        tmp_path = tmp.name
    wntr.network.write_inpfile(wn, tmp_path, version=2.2)
    text = Path(tmp_path).read_text(encoding="utf-8")
    Path(out_path).write_text(text, encoding=encoding)

def pick_latest_ts_rawdata(db: DbManager, now_dt: datetime) -> Optional[datetime]:
    row = db.fetchone("SELECT MAX(ts) AS ts FROM TB_RAWDATA WHERE ts <= %s", (now_dt,))
    return row["ts"] if row and row.get("ts") else None


def floor_to_5min(dt: datetime) -> datetime:
    dt0 = dt.replace(second=0, microsecond=0)
    return dt0 - timedelta(minutes=dt0.minute % 5)


def sleep_to_next_5min():
    now = datetime.now()
    sec_from_hour = now.minute * 60 + now.second
    remain = (300 - (sec_from_hour % 300)) % 300
    if remain == 0:
        remain = 300
    time.sleep(remain)

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


def load_all_link_groups(db: DbManager) -> list[dict]:
    return db.fetchall("SELECT LINK_ID, GRP_NM FROM TB_LINK_GRP")


def fetch_values_by_tag_with_fallback(
    db: DbManager, ts: datetime, tags: Iterable[str], fallback_sec: int = 600
) -> Dict[str, float]:
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

def build_demands_from_rawdata(
    node_meta: List[dict],
    tag_values: Dict[str, float],
    flow_unit: FlowUnits
) -> Dict[str, float]:
    demand_model_units: Dict[str, float] = {}
    for r in node_meta:
        nid = r["NODE_ID"]
        fr_tag = r.get("FR_TAGNAME")
        val = float(tag_values.get(fr_tag, 0.0)) if fr_tag else 0.0
        demand_model_units[nid] = val

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

    nP = results.node["pressure"]
    nH = results.node["head"]
    lQ = results.link["flowrate"]
    lL = results.link["headloss"]

    first_idx = nP.index[0]
    last_idx = nP.index[-1]

    p0, h0, q0, l0 = nP.loc[first_idx], nH.loc[first_idx], lQ.loc[first_idx], lL.loc[first_idx]
    pL, hL, qL, lL_ = nP.loc[last_idx], nH.loc[last_idx], lQ.loc[last_idx], lL.loc[last_idx]

    return (p0, h0, q0, l0), (pL, hL, qL, lL_), (first_idx, last_idx)


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
        rows.append((ts, node_id, p_meas, float(p_alg), "mo"))
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
        hh_loss_val = float(link_hloss.get(link_id, 0.0)) * float(ln.length)
        flw_alg = from_si(flow_unit, float(link_flow.get(link_id, 0.0)), HydParam.Demand)
        link_meas = link_measured_fr_by_linkid.get(link_id) if link_measured_fr_by_linkid else None
        rows.append((link_id, hh_loss_val, ts, link_meas, flw_alg, "mo"))

    if rows:
        sql = f"""
          REPLACE INTO {link_table}
            (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, LINK_VAL, FLW_ALG_RST_VAL, FLG)
          VALUES (%s,%s,%s,%s,%s,%s)
        """
        db.executemany(sql, rows)


def fetch_sum_raw(db: DbManager, ts: datetime, tags: list[str]) -> float:
    tags = [t for t in tags if t]
    if not tags:
        return 0.0
    ph = ",".join(["%s"] * len(tags))
    sql = f"SELECT SUM(value) AS s FROM TB_RAWDATA WHERE ts=%s AND tagname IN ({ph})"
    row = db.fetchone(sql, (ts, *tags))
    return float(row["s"] or 0.0) if row else 0.0


def pick_avl_group_row(db: DbManager, flow_sum_for_threshold: float) -> dict | None:
    row = db.fetchone(
        "SELECT * FROM TB_AVL_GRP WHERE STN_FLW_VAL > %s ORDER BY STN_FLW_VAL ASC LIMIT 1",
        (flow_sum_for_threshold / 60.0,)
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
        g = r["GRP_NM"]
        if lid in hl_by_link:
            grp_sum[g] = grp_sum.get(g, 0.0) + hl_by_link[lid]

    total = 0.0
    for g, s in grp_sum.items():
        flag_col = f"GRP_{g}_YN"
        if flag_col in active_flags_row and active_flags_row[flag_col] in (1, True):
            total += s
    return total


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
    flow_sum = fetch_sum_raw(db, ts, sum_flow_tags)
    press_sum = fetch_sum_raw(db, ts, sum_press_tags)
    avl_row = pick_avl_group_row(db, flow_sum) or {}
    link_groups = load_all_link_groups(db)
    loss_tot = compute_group_loss_total(wn, link_hloss, link_groups, avl_row)
    fp_alg = float(node_pressure.get(tot_node_id, 0.0))

    sql = f"""
      REPLACE INTO {tot_table}
        (RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL, FLG)
      VALUES (%s,%s,%s,%s,%s,%s)
    """
    db.executemany(sql, [(ts, loss_tot, flow_sum, press_sum, fp_alg, "mo")])


def run_once(args):
    cfg = load_db_config(args.conn, args.conn_key)
    db = DbManager(cfg)

    try:
        if args.ts:
            target_ts = datetime.fromisoformat(args.ts)
        else:
            target_ts = pick_latest_ts_rawdata(db, datetime.now())
            if target_ts is None:
                raise RuntimeError("TB_RAWDATA에서 now 이전의 시각을 찾지 못했습니다.")
        print(f"[INFO] 실행 시각 ts={target_ts}")

        node_meta = load_node_meta(db)
        link_meta = load_link_meta(db)

        fp_tags = [r["FP_TAGNAME"] for r in node_meta if r.get("FP_TAGNAME")]
        fr_tags = [r["FR_TAGNAME"] for r in node_meta if r.get("FR_TAGNAME")]
        link_fr_tags = [r["FLW_TAGNAME"] for r in link_meta if r.get("FLW_TAGNAME")]

        fp_by_tag = fetch_values_by_tag_with_fallback(db, target_ts, fp_tags, args.fallback_sec)
        fr_by_tag = fetch_values_by_tag_with_fallback(db, target_ts, fr_tags, args.fallback_sec)
        link_fr_by_tag = fetch_values_by_tag_with_fallback(db, target_ts, link_fr_tags, args.fallback_sec)

        wn = load_inp_with_fallback(args.inp)
        unit_name = getattr(getattr(wn.options, "hydraulic", None), "inpfile_units", None)
        if not unit_name:
            toDict = wn.to_dict()
            unit_name = toDict.get("options", {}).get("hydraulic", {}).get("inpfile_units", "LPS")
        flow_unit = FlowUnits[str(unit_name).upper()]

        si_demands = build_demands_from_rawdata(node_meta, fr_by_tag, flow_unit)
        set_demands_to_model(wn, si_demands)

        (p0, h0, q0, l0), (_pL, _hL, _qL, _lL), (t_first, t_last) = run_snapshot_return_both(wn)
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
        store_link_results(db, target_ts, wn, flow_unit, q0, l0, link_measured_fr_by_linkid, link_table=args.link_table)

        sum_flow_tags = [s.strip() for s in args.sum_flow_tags.split(",") if s.strip()]
        sum_press_tags = [s.strip() for s in args.sum_press_tags.split(",") if s.strip()]
        store_tot_alg(
            db, target_ts, wn, flow_unit,
            node_pressure=p0, link_flow=q0, link_hloss=l0,
            tot_table=args.tot_table, tot_node_id=args.tot_node_id,
            sum_flow_tags=sum_flow_tags, sum_press_tags=sum_press_tags
        )

        db.commit()
        print("[OK] 저장 완료 (last_step=", int(t_last), ")")

    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", required=True, help="EPANET INP 파일 경로")
    ap.add_argument("--conn", default="./connections.json", help="connections.json 경로")
    ap.add_argument("--conn-key", default="maria-ems-db-gs", help='connections.json Key')
    ap.add_argument("--ts", default=None, help="단발 실행 시 강제 시각(예: '2025-08-20 15:00:00')")
    ap.add_argument("--node-table", default="TB_FP_SI_VAL")
    ap.add_argument("--link-table", default="TB_FR_SI_VAL")
    ap.add_argument("--tot-table", default="TB_TOT_ALG")
    ap.add_argument("--tot-node-id", default="13")
    ap.add_argument("--sum-flow-tags", default="701-367-FRI-4004,701-367-FRI-4001")
    ap.add_argument("--sum-press-tags", default="701-367-PRI-4019,701-367-PRI-4010")
    ap.add_argument("--fallback-sec", type=int, default=600, help="RAWDATA 폴백 범위(초), 기본 600=10분")

    ap.add_argument("--loop", action="store_true", help="5분 경계(:00/:05/… )마다 자동 실행")
    ap.add_argument("--max-runs", type=int, default=0, help="반복 횟수 제한(0=무제한)")
    args = ap.parse_args()

    if not args.loop:
        run_once(args)
        return

    print("[LOOP] 5분 경계마다 자동 실행 시작")
    last_ts: datetime | None = None
    runs = 0
    try:
        while True:
            sleep_to_next_5min()
            target = floor_to_5min(datetime.now())
            if last_ts is not None and target <= last_ts:
                continue
            
            run_args = argparse.Namespace(**vars(args))
            run_args.ts = target.strftime("%Y-%m-%d %H:%M:%S")

            print(f"[LOOP] 실행 ts={run_args.ts}")
            try:
                run_once(run_args)
                last_ts = target
                runs += 1
                if args.max_runs and runs >= args.max_runs:
                    print(f"[LOOP] max-runs={args.max_runs} 충족. 종료.")
                    break
            except Exception as e:
                print(f"[LOOP][ERROR] {e}")

    except KeyboardInterrupt:
        print("\n[LOOP] 사용자 종료")


if __name__ == "__main__":
    main()