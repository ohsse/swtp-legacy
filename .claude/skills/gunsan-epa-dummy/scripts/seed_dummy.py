#!/usr/bin/env python3
"""
군산 관망해석(MO·PRE) 시뮬레이션용 더미데이터 생성기.

해석 엔진이 DB 에서 읽는 것만 채운다.
  - TB_RAWDATA      : MO/PRE 가 읽는 계측 태그 (1분 간격)
  - TB_CTR_TNK_RST  : PRE 가 읽는 수요예측 (5분 경계마다 Q2/Q7_Predict)
  - TB_NODE_TAG     : PRE 의 예측 매핑(DSTRB_Q_ID) — 비어 있을 때만 채운다

태그 목록은 엔진 모듈(epa/epanet_gunsan)에서 직접 가져온다. 엔진에 태그가 추가되면
여기를 고치지 않아도 따라간다. 단, 새 태그의 값 모양은 PROFILES 에 없으면 경고 후 건너뛴다.

실행 예 (리포 루트에서):
  python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --dry-run
  python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --hours 3 --verify
  python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --follow
  python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --purge --from "2026-09-01 00:00"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py → 리포 루트는 4단계 위
REPO_ROOT = Path(__file__).resolve().parents[4]
ENGINE_DIR = REPO_ROOT / "epa" / "epanet_gunsan"

DEFAULT_CONN = REPO_ROOT / "epa" / "connections.gunsan.json"
DEFAULT_CONN_KEY = "maria-ems-db-gu-test"  # 군산 개발서버 DB (localhost / ems_db)
DEFAULT_MARKER = "DUMMY_SIM"

# 운영 DB 로 알려진 접속. --allow-prod 없이는 거부한다.
PROD_HOSTS = {"localhost"}
PROD_DB_NAMES = {"ems_db"}

# ---------------------------------------------------------------------------
# 값 모양 — 태그별 (기준값, 일변동 진폭 비율, 노이즈 비율, 하한, 상한, 소수 자릿수)
# 기준값은 개발서버 DB 실측(2026-08-23 03·10·19시 각 1시간 평균)에 맞췄다.
# "(추정)" 은 dev DB 에 그 태그가 아예 없어 인근 계측·유량 수지로 잡은 값이다.
# 유량 m3/h, 압력 kgf/cm2(legacy), 개도율 %.
# ---------------------------------------------------------------------------
PROFILES = {
    # 수요/공급 (MO 필수)
    "891-365-FRI-8851": (300.0, 0.10, 0.02, 0, None, 3),     # 절점 28 (장항) (추정: 함열+송수 − 나머지 수요)
    "891-365-FRI-8802": (650.0, 0.08, 0.08, 0, None, 3),     # 군장에너지 — 실측 470~880, 요동이 크다
    "891-365-FRI-8600": (1600.0, 0.10, 0.03, 0, None, 3),    # 나운(배) — MO 가 읽는 태그. 저녁이 높다
    "891-365-FRI-8601": (1600.0, 0.10, 0.03, 0, None, 3),    # 나운(배) — PRE·SI 가 읽는 태그 (추정: 8600 과 같은 물량)
    "891-365-FRI-8652": (2880.0, 0.08, 0.03, 0, None, 3),    # 오식도(배)공업 — 실측 2,580~3,280
    "740-914-FRI-1001": (2850.0, 0.03, 0.005, 0, None, 3),   # 함열가압장 공급 (양수로 넣는다. 부호는 엔진이 바꾼다)
    # 밸브 개도율 (필수)
    # POI-8601: 실측은 29~70% 로 움직이지만 보정곡선 유효범위가 11.07~51.43 이라 그 안에 가둔다
    "891-365-POI-8601": (35.0, 0.10, 0.01, 12.0, 50.0, 5),
    # POI-8600: 실측은 74~90% 지만 엔진은 0 이 아니면 전개방으로 근사하고, 그 근사가 맞는 구간이
    # 95~100% 다(epanet_mo_gs.py 머리 주석). 근사가 성립하는 값으로 둔다.
    "891-365-POI-8600": (99.0, 0.00, 0.003, 96.0, 100.0, 5),
    # 비교용 유량 (선택)
    "891-365-FRI-8950": (2600.0, 0.05, 0.02, 0, None, 3),    # 군산(정) 송수
    "891-365-FRI-8850": (0.0, 0.00, 0.00, 0, None, 3),       # 장항산단 유출 — 실측 0
    "891-365-FRI-8602": (2040.0, 0.08, 0.04, 0, None, 3),
    "891-365-FRI-8800": (1370.0, 0.12, 0.04, 0, None, 3),
    "891-365-FRI-8303": (1650.0, 0.02, 0.01, 0, None, 3),
    "891-365-FRI-9010": (300.0, 0.10, 0.02, 0, None, 3),     # (추정)
    # 비교용 압력 (선택) — 수요가 클수록 약간 낮아지게 진폭을 음수로 둔다
    "891-365-PRI-9010": (2.60, -0.02, 0.005, 0, None, 5),    # (추정)
    "891-365-PRI-8301": (4.30, -0.01, 0.003, 0, None, 5),
    "891-365-PRI-4000": (1.82, -0.04, 0.01, 0, None, 5),
    "891-365-PRI-8700": (5.45, -0.01, 0.003, 0, None, 5),
    "891-365-PRI-8601": (2.92, -0.01, 0.003, 0, None, 5),
    "891-365-PRI-8800": (4.27, -0.01, 0.002, 0, None, 5),
    "891-365-PRI-8603": (2.29, -0.02, 0.005, 0, None, 5),    # (추정: 2025-05-08 스냅샷)
    "891-365-PRI-8600": (3.07, -0.01, 0.002, 0, None, 5),
    "701-367-PRI-9322": (2.20, -0.02, 0.005, 0, None, 5),    # (추정)
    "701-367-PRI-9160": (2.30, -0.02, 0.005, 0, None, 5),    # (추정)
    "701-367-PRI-9300": (2.10, -0.02, 0.005, 0, None, 5),    # (추정)
}

# 예측 ID → 그 예측의 근거가 되는 실측 태그 (docs/sql/gunsan_ems_tag_seed.sql:121-125)
PRED_SOURCE = {
    "Q2_Predict": "891-365-FRI-8600",
    "Q7_Predict": "891-365-FRI-8652",
}
DEFAULT_PRED_MAPPING = {"나운(배)": "Q2_Predict", "오식도(배)공업": "Q7_Predict"}
# TB_CTR_TNK_RST 의 예측 지평 컬럼 (ems_gu_predict/readme.txt:34-48)
HORIZONS = [("VALUE_5min", 5), ("VALUE_10min", 10), ("VALUE_30min", 30), ("VALUE_1h", 60),
            ("VALUE_2h", 120), ("VALUE_3h", 180), ("VALUE_4h", 240), ("VALUE_5h", 300), ("VALUE_6h", 360)]

# 실측: 1·3번 운전, 36.7~42.8Hz
DEFAULT_PUMPS_ON = "1,3"
PUMP_HZ_BASE, PUMP_HZ_AMP = 41.0, 1.5
PUMP_HZ_RANGE = (36.0, 50.0)


# ---------------------------------------------------------------------------
# 엔진에서 태그 목록 가져오기
# ---------------------------------------------------------------------------
def load_engine_meta():
    sys.path.insert(0, str(ENGINE_DIR))
    try:
        import epanet_mo_gs as mo
        import main_epa_gs as pre
    finally:
        sys.path.pop(0)
    tags = set(mo.all_tags()) | set(pre.runtime_tags("opening"))
    return {
        "tags": sorted(tags),
        "pumps": [(pid, run, hz) for pid, run, hz in mo.PUMPS],
        "pred_nodes": tuple(pre.PREDICTION_NODE_IDS),
    }


# ---------------------------------------------------------------------------
# 값 생성 — (seed, 태그, 시각) 에만 의존하므로 구간을 나눠 넣어도 같은 값이 나온다
# ---------------------------------------------------------------------------
def daily_shape(ts: datetime) -> float:
    """-1~1 사이 하루 주기. 오전 8시·저녁 7시 전후가 높고 새벽 3~4시가 낮다."""
    h = ts.hour + ts.minute / 60.0
    v = 0.65 * math.sin(2 * math.pi * (h - 8.0) / 24.0) + 0.35 * math.sin(4 * math.pi * (h - 5.0) / 24.0)
    return max(-1.0, min(1.0, v))


def noise(seed: int, key: str, ts: datetime) -> float:
    digest = hashlib.md5(f"{seed}|{key}|{ts:%Y%m%d%H%M}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16)).gauss(0.0, 1.0)


def profile_value(tag: str, ts: datetime, seed: int, *, with_noise: bool = True) -> float:
    base, amp, nz, lo, hi, nd = PROFILES[tag]
    v = base * (1.0 + amp * daily_shape(ts))
    if with_noise:
        v += base * nz * noise(seed, tag, ts)
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return round(v, nd)


def pump_values(pumps, pumps_on, ts: datetime, seed: int) -> dict:
    """가동 태그(PMB)는 1/0, 운전 펌프 주파수(SPI)는 수요 모양을 따라 41±1.5Hz."""
    out = {}
    lo, hi = PUMP_HZ_RANGE
    for idx, (_, run_tag, hz_tag) in enumerate(pumps, start=1):
        running = idx in pumps_on
        out[run_tag] = 1 if running else 0
        if running:
            hz = PUMP_HZ_BASE + PUMP_HZ_AMP * daily_shape(ts) + 0.3 * noise(seed, hz_tag, ts)
            out[hz_tag] = round(min(hi, max(lo, hz)), 2)
        else:
            out[hz_tag] = 0
    return out


def raw_rows(tags, pumps, pumps_on, start: datetime, end: datetime, seed: int):
    """(TS, TAGNAME, VALUE, QUALITY). SERVER 마커는 write_raw 가 붙인다."""
    pump_tags = {t for _, r, h in pumps for t in (r, h)}
    value_tags = [t for t in tags if t not in pump_tags and t in PROFILES]
    ts = start
    while ts <= end:
        for tag in value_tags:
            yield (ts, tag, f"{profile_value(tag, ts, seed)}", "100")
        for tag, val in pump_values(pumps, pumps_on, ts, seed).items():
            yield (ts, tag, f"{val}", "100")
        ts += timedelta(minutes=1)


def pred_rows(pred_ids, start: datetime, end: datetime, seed: int):
    """5분 경계마다 한 묶음. 두 예측의 RGSTR_TIME 이 같아 PRE 의 skew 검사(≤120초)를 통과한다."""
    ts = floor5(start)
    if ts < start:
        ts += timedelta(minutes=5)
    while ts <= end:
        for pid in pred_ids:
            src = PRED_SOURCE[pid]
            vals = []
            for _, mins in HORIZONS:
                future = ts + timedelta(minutes=mins)
                # 예측 오차: 지평이 멀수록 커진다(1%→4%)
                err = 0.01 + 0.03 * mins / 360.0
                v = profile_value(src, future, seed, with_noise=False)
                v *= 1.0 + err * noise(seed, f"{pid}|{mins}", ts)
                vals.append(round(max(0.0, v), 3))
            yield (pid, ts, vals[0], *vals)
        ts += timedelta(minutes=5)


def floor5(ts: datetime) -> datetime:
    return ts.replace(minute=ts.minute - ts.minute % 5, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
def load_conn(path: Path, key: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cfg = data.get(key) if isinstance(data, dict) else None
    if not isinstance(cfg, dict):
        raise SystemExit(f"[오류] {path} 에 접속키 {key!r} 가 없습니다. 있는 키: {list(data)}")
    missing = [k for k in ("host", "user", "password") if k not in cfg]
    if missing or not (cfg.get("db") or cfg.get("database")):
        raise SystemExit("[오류] 접속 설정에는 host, user, password, db 가 필요합니다.")
    return cfg


def guard_prod(cfg: dict, allow_prod: bool) -> None:
    db = str(cfg.get("db") or cfg.get("database"))
    if (cfg["host"] in PROD_HOSTS or db.lower() in PROD_DB_NAMES) and not allow_prod:
        raise SystemExit(
            f"[거부] 운영 DB 로 보이는 대상입니다: {cfg['host']} / {db}\n"
            "더미를 운영 DB 에 넣으면 실측과 섞여 해석·예측·제어 판단이 오염됩니다.\n"
            "정말 의도한 것이면 --allow-prod 를 붙이세요.")


def connect(cfg: dict):
    import pymysql
    return pymysql.connect(
        host=cfg["host"], port=int(cfg.get("port", 3306)), user=cfg["user"],
        password=cfg["password"], database=cfg.get("db") or cfg["database"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=False, connect_timeout=10, read_timeout=120, write_timeout=120)


def db_now(conn) -> datetime:
    with conn.cursor() as cur:
        cur.execute("SELECT NOW() AS n")
        return cur.fetchone()["n"].replace(second=0, microsecond=0)


def write_raw(conn, rows, marker: str, chunk: int = 5000) -> tuple[int, int]:
    """
    실측 행은 절대 덮어쓰지 않는다. 같은 (TS,TAGNAME) 이 이미 있으면
    그 행의 SERVER 가 우리 마커일 때만 값을 갱신한다(재실행으로 값 모양을 바꿀 수 있게).
    """
    # pymysql executemany 는 VALUES(...) 밖의 %s 를 채우지 못하므로 IF 비교값은 이스케이프한 리터럴로 넣는다
    sql = ("INSERT INTO TB_RAWDATA (TS, TAGNAME, VALUE, QUALITY, SERVER) VALUES (%s,%s,%s,%s,%s) "
           f"ON DUPLICATE KEY UPDATE VALUE = IF(SERVER = {conn.escape(marker)}, VALUES(VALUE), VALUE)")
    total, affected = 0, 0
    buf = []
    for r in rows:
        buf.append((*r, marker))
        if len(buf) >= chunk:
            affected += _exec_many(conn, sql, buf)
            total += len(buf)
            buf.clear()
    if buf:
        affected += _exec_many(conn, sql, buf)
        total += len(buf)
    return total, affected


def _exec_many(conn, sql, buf) -> int:
    import pymysql
    try:
        with conn.cursor() as cur:
            n = cur.executemany(sql, buf)
        conn.commit()
        return n or 0
    except pymysql.err.OperationalError as e:
        conn.rollback()
        if e.args and e.args[0] == 1526:
            raise SystemExit(
                f"[오류] TB_RAWDATA 에 이 시각의 파티션이 없습니다: {buf[0][0]}\n"
                "월 단위 RANGE 파티션이라 해당 월(또는 p_future) 파티션이 있어야 삽입됩니다.\n"
                "DBA 와 확인 후 ALTER TABLE TB_RAWDATA REORGANIZE PARTITION ... 로 추가하세요.") from e
        raise


def write_pred(conn, rows, replace: bool) -> int:
    """
    테이블에 실제로 있는 컬럼만 쓴다. 개발서버 덤프는 VALUE_5min~6h 가 없는 옛 스키마
    (DSTRB_ID, PRDCT_VALUE, RGSTR_TIME) 이고, PRE 가 읽는 것은 PRDCT_VALUE 뿐이다.
    """
    all_cols = ["DSTRB_ID", "RGSTR_TIME", "PRDCT_VALUE"] + [c for c, _ in HORIZONS]
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM TB_CTR_TNK_RST")
        present = {r["Field"].upper() for r in cur.fetchall()}
    keep = [i for i, c in enumerate(all_cols) if c.upper() in present]
    cols = [all_cols[i] for i in keep]
    verb = "REPLACE" if replace else "INSERT IGNORE"
    sql = f"{verb} INTO TB_CTR_TNK_RST ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})"
    rows = [tuple(r[i] for i in keep) for r in rows]
    if not rows:
        return 0
    with conn.cursor() as cur:
        n = cur.executemany(sql, rows)
    conn.commit()
    return n or 0


def ensure_mapping(conn, pred_nodes, dry_run: bool) -> dict:
    """TB_NODE_TAG.DSTRB_Q_ID 가 비어 있는 노드만 채운다. 다른 값이 있으면 건드리지 않는다."""
    ph = ",".join(["%s"] * len(pred_nodes))
    with conn.cursor() as cur:
        cur.execute(f"SELECT NODE_ID, DSTRB_Q_ID FROM TB_NODE_TAG WHERE NODE_ID IN ({ph})", tuple(pred_nodes))
        rows = cur.fetchall()
    current = {}
    for r in rows:
        if r["DSTRB_Q_ID"] and str(r["DSTRB_Q_ID"]).strip():
            current.setdefault(r["NODE_ID"], set()).add(str(r["DSTRB_Q_ID"]).strip())
    mapping = {}
    for node in pred_nodes:
        have = current.get(node)
        want = DEFAULT_PRED_MAPPING.get(node)
        if have:
            if len(have) > 1:
                print(f"  [경고] TB_NODE_TAG {node}: DSTRB_Q_ID 가 여러 개 {sorted(have)} — PRE 가 거부합니다. 손으로 정리하세요.")
            mapping[node] = sorted(have)[0]
            if want and mapping[node] != want:
                print(f"  [경고] TB_NODE_TAG {node} = {mapping[node]} (기본 {want} 와 다름) — 그대로 둡니다.")
            continue
        if not want:
            print(f"  [경고] {node} 의 기본 예측 매핑을 모릅니다. DEFAULT_PRED_MAPPING 에 추가하세요.")
            continue
        mapping[node] = want
        print(f"  TB_NODE_TAG {node} → {want} {'(dry-run, 쓰지 않음)' if dry_run else '채움'}")
        if not dry_run:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO TB_NODE_TAG (NODE_ID, DSTRB_Q_ID) VALUES (%s,%s) "
                            "ON DUPLICATE KEY UPDATE DSTRB_Q_ID = VALUES(DSTRB_Q_ID)", (node, want))
            conn.commit()
    return mapping


def purge(conn, tags, pred_ids, start, end, marker) -> None:
    ph = ",".join(["%s"] * len(tags))
    with conn.cursor() as cur:
        # (TAGNAME, TS) 인덱스를 타도록 태그·시각 조건을 반드시 같이 건다
        n1 = cur.execute(f"DELETE FROM TB_RAWDATA WHERE TAGNAME IN ({ph}) AND TS BETWEEN %s AND %s AND SERVER = %s",
                         (*tags, start, end, marker))
        ph2 = ",".join(["%s"] * len(pred_ids))
        n2 = cur.execute(f"DELETE FROM TB_CTR_TNK_RST WHERE DSTRB_ID IN ({ph2}) AND RGSTR_TIME BETWEEN %s AND %s",
                         (*pred_ids, start, end))
    conn.commit()
    print(f"  삭제: TB_RAWDATA {n1}행(SERVER={marker}), TB_CTR_TNK_RST {n2}행")


def coverage_report(conn, tags, pred_ids, at: datetime, fallback_sec: int) -> list:
    """엔진과 같은 조건(at-fallback ~ at 최신 1행)으로 태그가 잡히는지 확인한다."""
    since = at - timedelta(seconds=fallback_sec)
    ph = ",".join(["%s"] * len(tags))
    with conn.cursor() as cur:
        cur.execute(f"SELECT TAGNAME, MAX(TS) AS TS FROM TB_RAWDATA WHERE TS >= %s AND TS <= %s "
                    f"AND TAGNAME IN ({ph}) GROUP BY TAGNAME", (since, at, *tags))
        seen = {r["TAGNAME"]: r["TS"] for r in cur.fetchall()}
        ph2 = ",".join(["%s"] * len(pred_ids))
        cur.execute(f"SELECT DSTRB_ID, MAX(RGSTR_TIME) AS T FROM TB_CTR_TNK_RST WHERE DSTRB_ID IN ({ph2}) "
                    f"AND RGSTR_TIME <= %s GROUP BY DSTRB_ID", (*pred_ids, at))
        preds = {r["DSTRB_ID"]: r["T"] for r in cur.fetchall()}
    missing = [t for t in tags if t not in seen]
    print(f"  기준시각 {at} (창 {fallback_sec}초): 태그 {len(seen)}/{len(tags)} 확인"
          + (f", 없음 {missing}" if missing else ""))
    for pid in pred_ids:
        print(f"  예측 {pid}: 최신 RGSTR_TIME {preds.get(pid)}")
    return missing


# ---------------------------------------------------------------------------
# 검증 — 엔진 CLI 를 DB 저장 없이 한 번씩 돌린다
# ---------------------------------------------------------------------------
def run_verify(conn_path: Path, conn_key: str, at: datetime) -> bool:
    ts = f"{floor5(at):%Y-%m-%d %H:%M:%S}"
    inp = REPO_ROOT / "epa" / "inp" / "epa_model.inp"
    common = ["--ts", ts, "--inp", str(inp), "--conn", str(conn_path), "--conn-key", conn_key,
              "--snapshot", "--no-save-db"]
    ok = True
    for label, script in (("MO", "epanet_mo_gs.py"), ("PRE", "main_epa_gs.py")):
        cmd = [sys.executable, str(ENGINE_DIR / script), *common]
        print(f"\n== 검증 {label}: {script} --snapshot --ts '{ts}' --no-save-db")
        p = subprocess.run(cmd, cwd=ENGINE_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = (p.stdout + p.stderr).strip().splitlines()[-8:]
        for line in tail:
            print("   " + line)
        print(f"   → exit {p.returncode} {'성공' if p.returncode == 0 else '실패'}")
        ok &= p.returncode == 0
    return ok


# ---------------------------------------------------------------------------
def parse_ts(s: str) -> datetime:
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"시각 형식이 아닙니다: {s!r} (예: 2026-09-28 10:00)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="군산 관망해석(MO·PRE) 더미데이터 생성기")
    ap.add_argument("--conn", type=Path, default=DEFAULT_CONN, help="접속 JSON (엔진과 같은 {키:{host,port,user,password,db}} 형식)")
    ap.add_argument("--conn-key", default=DEFAULT_CONN_KEY, help=f"접속 키. 기본 {DEFAULT_CONN_KEY}(군산 개발서버)")
    ap.add_argument("--from", dest="start", type=parse_ts, help="시작 시각. 생략하면 DB 현재시각 - --hours")
    ap.add_argument("--to", dest="end", type=parse_ts, help="끝 시각. 생략하면 DB 현재시각")
    ap.add_argument("--hours", type=float, default=3.0, help="--from 생략 시 채울 과거 시간. 기본 3")
    ap.add_argument("--pumps-on", default=DEFAULT_PUMPS_ON, help=f"운전 펌프 번호. 기본 {DEFAULT_PUMPS_ON}(실측 운전 조합)")
    ap.add_argument("--seed", type=int, default=20260928, help="난수 시드. 같으면 같은 값")
    ap.add_argument("--marker", default=DEFAULT_MARKER, help=f"TB_RAWDATA.SERVER 표시. 기본 {DEFAULT_MARKER}")
    ap.add_argument("--only", choices=["raw", "pred", "mapping"], action="append",
                    help="일부만 적재 (여러 번 지정 가능). 기본 전부")
    ap.add_argument("--replace-pred", action="store_true", help="TB_CTR_TNK_RST 기존 행을 덮어쓴다(기본은 있으면 건너뜀)")
    ap.add_argument("--follow", action="store_true", help="백필 후 매분 계속 적재 (Ctrl+C 로 종료)")
    ap.add_argument("--verify", action="store_true", help="적재 후 MO·PRE 엔진을 --no-save-db 로 1회 실행")
    ap.add_argument("--fallback-sec", type=int, default=600, help="적재 확인에 쓸 창(초). 엔진 기본 600")
    ap.add_argument("--purge", action="store_true", help="적재 대신 구간의 더미를 삭제")
    ap.add_argument("--dry-run", action="store_true", help="DB 에 쓰지 않고 요약과 샘플만 출력")
    ap.add_argument("--allow-prod", action="store_true", help="운영 DB 보호를 해제 (쓰지 말 것)")
    args = ap.parse_args(argv)

    meta = load_engine_meta()
    tags, pumps = meta["tags"], meta["pumps"]
    unknown = [t for t in tags if t not in PROFILES and not any(t in (r, h) for _, r, h in pumps)]
    if unknown:
        print(f"[경고] 값 모양이 정의되지 않은 엔진 태그 {unknown} — 건너뜁니다. PROFILES 에 추가하세요.")
    pumps_on = {int(x) for x in args.pumps_on.split(",") if x.strip()}
    if not pumps_on or not pumps_on <= set(range(1, len(pumps) + 1)):
        raise SystemExit(f"[오류] --pumps-on 은 1~{len(pumps)} 중에서 고르세요: {args.pumps_on}")
    parts = set(args.only or ["raw", "pred", "mapping"])

    cfg = load_conn(args.conn, args.conn_key)
    guard_prod(cfg, args.allow_prod)
    conn = connect(cfg)
    try:
        now = db_now(conn)
        end = args.end or now
        start = args.start or (end - timedelta(hours=args.hours))
        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)
        if start > end:
            raise SystemExit("[오류] --from 이 --to 보다 늦습니다.")
        db_name = cfg.get("db") or cfg.get("database")
        print(f"== 대상 {cfg['host']} / {db_name}  (키 {args.conn_key})")
        print(f"   DB 현재시각 {now}  |  구간 {start} ~ {end}  |  마커 SERVER={args.marker}")
        print(f"   태그 {len(tags)}개, 운전 펌프 {sorted(pumps_on)}, 적재 {sorted(parts)}"
              + ("  [dry-run]" if args.dry_run else ""))

        mapping = ensure_mapping(conn, meta["pred_nodes"], args.dry_run or "mapping" not in parts)
        pred_ids = sorted({pid for pid in mapping.values() if pid in PRED_SOURCE})
        for pid in set(mapping.values()) - set(PRED_SOURCE):
            print(f"  [경고] 예측 ID {pid} 의 근거 태그를 모릅니다. PRED_SOURCE 에 추가하세요.")

        if args.purge:
            if args.dry_run:
                print("  [dry-run] 삭제하지 않습니다.")
            else:
                purge(conn, tags, pred_ids or list(PRED_SOURCE), start, end, args.marker)
            return 0

        def load_range(a: datetime, b: datetime, quiet: bool = False):
            if "raw" in parts:
                rows = raw_rows(tags, pumps, pumps_on, a, b, args.seed)
                if args.dry_run:
                    rows = list(rows)
                    print(f"  TB_RAWDATA {len(rows)}행 예정. 샘플:")
                    for r in rows[:len(tags)]:
                        print(f"    {r[0]}  {r[1]:20s} {r[2]}")
                else:
                    total, aff = write_raw(conn, rows, args.marker)
                    if not quiet:
                        print(f"  TB_RAWDATA {total}행 시도 (영향 {aff}: 신규 1·갱신 2 로 셈. 실측과 겹친 행은 보존)")
            if "pred" in parts and pred_ids:
                prow = list(pred_rows(pred_ids, a, b, args.seed))
                if args.dry_run:
                    print(f"  TB_CTR_TNK_RST {len(prow)}행 예정. 샘플: {prow[:2]}")
                else:
                    n = write_pred(conn, prow, args.replace_pred)
                    if not quiet:
                        print(f"  TB_CTR_TNK_RST {len(prow)}행 시도 (적재 {n})")

        load_range(start, end)
        if args.dry_run:
            return 0

        print("\n== 적재 확인")
        missing = coverage_report(conn, tags, pred_ids, end, args.fallback_sec)

        ok = True
        if args.verify:
            ok = run_verify(args.conn, args.conn_key, end)

        if args.follow:
            print("\n== 실시간 적재 시작 (매분). Ctrl+C 로 종료")
            last = end
            try:
                while True:
                    time.sleep(max(1.0, 62 - datetime.now().second))
                    cur_now = db_now(conn)
                    if cur_now <= last:
                        continue
                    load_range(last + timedelta(minutes=1), cur_now, quiet=True)
                    print(f"  {cur_now:%H:%M} 적재" + ("  (+예측)" if cur_now.minute % 5 == 0 else ""))
                    last = cur_now
            except KeyboardInterrupt:
                print("\n  종료")
        return 0 if ok and not missing else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
