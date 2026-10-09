"""태그별 CSV 를 TB_RAWDATA 에 INSERT IGNORE 로 적재한다.

파일명 규칙 : <접두>.<태그번호>.<접미>.csv  예) GSSCADA.891-260-CBB-1312.F_CV.csv → 891-260-CBB-1312
CSV 형식   : 헤더 없음, 1열 TS, 2열 VALUE, 3열(있으면) QUALITY
적재 형식   : (TS, TAGNAME, VALUE, QUALITY, SERVER=마커)  — 테이블에 없는 선택 컬럼은 빼고 넣는다

예)
  python import_csv.py dump --dry-run
  python import_csv.py dump --host localhost --user root --password xxx --db ems_db
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROD_HOSTS = {"localhost"}
PROD_DBS = {"EMS_DB"}
DUP_KEY = 1062          # 중복 키 — INSERT IGNORE 가 무시하는 정상 케이스
SHOW_BAD_ROWS = 5
# 서버/클라이언트가 LOAD DATA LOCAL 을 막았을 때의 오류 코드 → 행 단위로 내려간다
LOCAL_INFILE_DENIED = {1148, 2068, 3948}
# LOAD DATA 실측 속도(군산 개발서버 2026-10-02). PK 가 (TS, TAGNAME) 라 같은 기간에 다른 태그가 이미 있으면
# 페이지 사이에 끼워 넣느라 느려진다: 빈 기간 ~16만 행/s, 태그 10개가 채워진 기간 ~2,600행/s
ROWS_PER_SEC_WORST = 2500


def extract_tag(path: Path) -> str | None:
    parts = path.name.split(".")
    # 접두.태그.접미.csv → 최소 4조각. 태그 자체에 '.' 이 없다는 전제
    return parts[1] if len(parts) >= 4 and parts[1] else None


def collect_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(p.glob("*.csv"))
        elif p.is_file():
            files.append(p)
        else:
            print(f"[경고] 경로 없음: {p}")
    return files


def parse_ts(s: str) -> datetime:
    # fromisoformat 은 'YYYY-MM-DD HH:MM[:SS[.ffffff]]' 를 모두 받는다
    return datetime.fromisoformat(s.strip())


def iter_rows(path: Path, stats: dict):
    """(TS, VALUE, QUALITY) 를 하나씩 낸다. 불량 행은 stats 에 센다."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        for lineno, row in enumerate(csv.reader(f), 1):
            if not row or not any(c.strip() for c in row):
                stats["blank"] = stats.get("blank", 0) + 1
                continue
            stats.setdefault("ncols", set()).add(len(row))
            try:
                ts = parse_ts(row[0])
                value = row[1].strip()
                float(value)             # 숫자 검증만. VALUE 는 문자열 컬럼이라 원문 그대로 넣는다('0' 이 '0.0' 이 되지 않게)
                quality = row[2].strip() if len(row) > 2 and row[2].strip() else None
            except (ValueError, IndexError):
                if lineno == 1:          # 헤더 행
                    stats["header"] = True
                    continue
                stats["bad"] += 1
                if stats["bad"] <= SHOW_BAD_ROWS:
                    print(f"    [불량 {lineno}행] {row}")
                continue
            if stats["min"] is None or ts < stats["min"]:
                stats["min"] = ts
            if stats["max"] is None or ts > stats["max"]:
                stats["max"] = ts
            yield ts, value, quality


def scan(path: Path) -> dict:
    stats = {"rows": 0, "bad": 0, "blank": 0, "ncols": set(), "min": None, "max": None,
             "header": False, "sample": []}
    for r in iter_rows(path, stats):
        stats["rows"] += 1
        if len(stats["sample"]) < 3:
            stats["sample"].append(r)
    with path.open("rb") as f:
        head = f.read(4096)
    stats["eol"] = "\\r\\n" if b"\r\n" in head else "\\n"
    # 히스토리안 내보내기 파일은 UTF-8 BOM 으로 시작한다. utf-8-sig 로 읽는 파이썬은 못 느끼지만
    # LOAD DATA 는 첫 행 TS 앞에 BOM 이 붙어 'Data truncated' 가 난다
    stats["bom"] = head.startswith(b"\xef\xbb\xbf")
    return stats


def bulk_ok(s: dict) -> bool:
    """LOAD DATA 로 넣어도 되는 '깨끗한' 파일인가.

    LOAD DATA … IGNORE 는 형식이 틀린 TS 를 거부하지 않고 0000-00-00 으로 바꿔 넣는다.
    그래서 불량·빈 줄·열 개수 혼재가 하나라도 있으면 행 단위 경로로 보낸다(불량 행만 건너뜀).
    """
    return s["rows"] > 0 and s["bad"] == 0 and s["blank"] == 0 and len(s["ncols"]) == 1 and min(s["ncols"]) >= 2


# ---------------------------------------------------------------- DB

def connect(args):
    import pymysql
    return pymysql.connect(host=args.host, port=args.port, user=args.user, password=args.password,
                           database=args.db, charset="utf8mb4", autocommit=False, local_infile=True,
                           connect_timeout=10, read_timeout=600, write_timeout=600)


def table_columns(conn, db: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT UPPER(COLUMN_NAME) FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='TB_RAWDATA'", (db,))
        return {r[0] for r in cur.fetchall()}


def partition_upper(conn, db: str, ts: datetime) -> tuple[bool, str]:
    """ts 가 기존 파티션 범위 안이면 (True, 설명). 판단할 수 없으면 통과시키고 설명만 남긴다.

    MariaDB 의 INSERT IGNORE 는 '파티션 없음(1526)' 도 경고로 바꾸고 행을 버린다.
    그래서 중복 무시와 구분되지 않으니 쓰기 전에 확인한다.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT PARTITION_METHOD, PARTITION_EXPRESSION, PARTITION_DESCRIPTION "
                    "FROM information_schema.PARTITIONS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='TB_RAWDATA' "
                    "AND PARTITION_NAME IS NOT NULL", (db,))
        parts = cur.fetchall()
        if not parts:
            return True, "파티션 없음(단일 테이블)"
        method, expr = parts[0][0], (parts[0][1] or "").lower()
        if method != "RANGE":
            return True, f"{method} 파티션 — 범위 점검 생략"
        descs = [p[2] for p in parts]
        if any(d and d.upper() == "MAXVALUE" for d in descs):
            return True, "MAXVALUE 파티션 있음"
        upper = max(int(d) for d in descs)
        if "unix_timestamp" in expr:
            cur.execute("SELECT UNIX_TIMESTAMP(%s), FROM_UNIXTIME(%s)", (ts, upper))
        elif "to_days" in expr:
            cur.execute("SELECT TO_DAYS(%s), FROM_DAYS(%s)", (ts, upper))
        else:
            return True, f"파티션식 {expr} — 범위 점검 생략(적재 중 경고로 확인)"
        val, bound = cur.fetchone()
        return val < upper, f"마지막 파티션 경계 {bound} 미만까지 적재 가능"


def load_file_bulk(conn, path: Path, tag: str, s: dict, cols: list[str], marker: str) -> int:
    """LOAD DATA LOCAL INFILE … IGNORE 로 파일 하나를 한 트랜잭션에 넣고 신규 행 수를 돌려준다.

    executemany 보다 수백 배 빠르다(개발서버 5만 행: 75초 → 0.3초).
    서버 응답의 Skipped(중복) 와 Warnings 를 비교해, 중복이 아닌 경고가 있으면 롤백한다.
    """
    ncol = min(s["ncols"])
    targets = ["@ts" if s["bom"] else "TS", "VALUE", "@q"][:min(ncol, 3)] + [f"@x{i}" for i in range(3, ncol)]
    sets = ["TAGNAME = %s"]
    if s["bom"]:
        sets.append("TS = REPLACE(@ts, _utf8mb4 X'EFBBBF', '')")
    params = [str(path.resolve()), tag]
    if "QUALITY" in cols and ncol >= 3:
        sets.append("QUALITY = NULLIF(TRIM(@q), '')")
    if "SERVER" in cols:
        sets.append("SERVER = %s")
        params.append(marker)
    sql = (f"LOAD DATA LOCAL INFILE %s IGNORE INTO TABLE TB_RAWDATA CHARACTER SET utf8mb4 "
           f"FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '{s['eol']}' "
           f"{'IGNORE 1 LINES ' if s['header'] else ''}"
           f"({', '.join(targets)}) SET {', '.join(sets)}")
    with conn.cursor() as cur:
        n = cur.execute(sql, params)
        msg = (conn._result.message or b"").decode() if conn._result else ""
        info = dict(re.findall(r"(\w+):\s*(\d+)", msg))
        skipped, warnings = int(info.get("Skipped", 0)), int(info.get("Warnings", 0))
        if warnings > skipped or int(info.get("Records", s["rows"])) != s["rows"]:
            cur.execute("SHOW WARNINGS LIMIT 5")
            sample = [w for w in cur.fetchall() if w[1] != DUP_KEY]
            conn.rollback()
            raise SystemExit(f"[오류] {path.name}: 중복이 아닌 경고가 있어 롤백했습니다 ({msg}). 예: {sample}")
    conn.commit()
    return n


def load_file(conn, path: Path, tag: str, cols: list[str], marker: str, batch: int) -> dict:
    sql = (f"INSERT IGNORE INTO TB_RAWDATA ({', '.join(cols)}) "
           f"VALUES ({', '.join(['%s'] * len(cols))})")
    stats = {"rows": 0, "bad": 0, "min": None, "max": None, "header": False}
    inserted = 0
    buf: list[tuple] = []

    def flush():
        nonlocal inserted
        with conn.cursor() as cur:
            n = cur.executemany(sql, buf) or 0
            if n < len(buf):
                # 중복(1062) 외의 경고가 있으면 행이 조용히 버려진 것 → 중단
                cur.execute("SHOW WARNINGS")
                other = [w for w in cur.fetchall() if w[1] != DUP_KEY]
                if other:
                    conn.rollback()
                    raise SystemExit(f"[오류] 중복이 아닌 이유로 행이 버려졌습니다 ({buf[0][0]} 부근): {other[:3]}\n"
                                     "파티션 누락이면 DBA 와 확인 후 파티션을 추가하고 다시 실행하세요.")
        conn.commit()
        inserted += n
        buf.clear()

    for ts, value, quality in iter_rows(path, stats):
        stats["rows"] += 1
        row = {"TS": ts, "TAGNAME": tag, "VALUE": value, "QUALITY": quality, "SERVER": marker}
        buf.append(tuple(row[c] for c in cols))
        if len(buf) >= batch:
            flush()
            if stats["rows"] % (batch * 40) == 0:
                print(f"    … {stats['rows']:,}행")
    if buf:
        flush()
    stats["inserted"] = inserted
    return stats


# ---------------------------------------------------------------- main

def fmt(ts) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "-"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        # 백그라운드 실행 시 출력이 파일로 가면 블록 버퍼링돼 끝날 때까지 로그가 비어 보인다 → 줄 단위로 내보낸다
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(description="태그별 CSV → TB_RAWDATA (INSERT IGNORE)")
    ap.add_argument("paths", nargs="+", help="CSV 파일 또는 폴더(폴더면 *.csv 전부)")
    ap.add_argument("--host")
    ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user")
    ap.add_argument("--password", default="")
    ap.add_argument("--db", help="database 명")
    ap.add_argument("--marker", default="CSV_IMPORT", help="SERVER 컬럼 값. 기본 CSV_IMPORT")
    ap.add_argument("--batch", type=int, default=5000)
    ap.add_argument("--dry-run", action="store_true", help="DB 에 쓰지 않고 파싱 결과만(접속 정보가 있으면 파티션 점검까지)")
    ap.add_argument("--no-bulk", action="store_true", help="LOAD DATA LOCAL 을 쓰지 않고 행 단위 INSERT IGNORE 로만(느림)")
    ap.add_argument("--allow-prod", action="store_true", help="운영 DB 적재를 명시적으로 허용")
    args = ap.parse_args()

    files = collect_files(args.paths)
    targets = []
    for f in files:
        tag = extract_tag(f)
        if tag is None:
            print(f"[경고] 태그를 뽑을 수 없는 파일명이라 건너뜀: {f.name}  (형식: 접두.태그.접미.csv)")
            continue
        targets.append((f, tag))
    if not targets:
        raise SystemExit("[오류] 적재할 CSV 가 없습니다.")

    has_conn = all([args.host, args.user, args.db])
    if not args.dry_run and not has_conn:
        raise SystemExit("[오류] --host --user --db (필요하면 --port --password) 를 지정하세요. 미리보기만이면 --dry-run.")
    if has_conn and (args.host in PROD_HOSTS or args.db.upper() in PROD_DBS) and not args.allow_prod:
        raise SystemExit(f"[거부] 운영 DB({args.host}/{args.db}) 입니다. 정말 넣으려면 --allow-prod 를 붙이세요.")

    conn = connect(args) if has_conn else None
    cols = ["TS", "TAGNAME", "VALUE"]
    if conn:
        existing = table_columns(conn, args.db)
        if not existing:
            raise SystemExit(f"[오류] {args.db} 에 TB_RAWDATA 테이블이 없습니다.")
        missing = [c for c in cols if c not in existing]
        if missing:
            raise SystemExit(f"[오류] TB_RAWDATA 에 필수 컬럼이 없습니다: {missing}")
        cols += [c for c in ("QUALITY", "SERVER") if c in existing]
        print(f"대상 DB: {args.host}:{args.port}/{args.db}  |  컬럼 {cols}  |  SERVER={args.marker}")

    mode = "미리보기" if args.dry_run else "적재"
    print(f"{mode}: 파일 {len(targets)}개\n")

    # 1) 스캔 — 행 수·TS 범위 확인 (적재 시에도 파티션 점검을 위해 먼저 훑는다)
    scans = {}
    for f, tag in targets:
        t0 = time.time()
        s = scan(f)
        scans[f] = s
        print(f"  {tag:<22} {s['rows']:>10,}행  {fmt(s['min'])} ~ {fmt(s['max'])}"
              f"  불량 {s['bad']}{'  (헤더 건너뜀)' if s['header'] else ''}  [{time.time() - t0:.1f}s]")
        if args.dry_run:
            for r in s["sample"]:
                print(f"      샘플 {fmt(r[0])}  VALUE={r[1]}  QUALITY={r[2]}")

    if conn:
        overall_max = max(s["max"] for s in scans.values() if s["max"])
        ok, note = partition_upper(conn, args.db, overall_max)
        print(f"\n파티션 점검: {note} → {'통과' if ok else '초과'}")
        if not ok:
            raise SystemExit(f"[오류] 최대 TS {fmt(overall_max)} 가 TB_RAWDATA 파티션 범위를 넘습니다. "
                             "INSERT IGNORE 는 이 행들을 조용히 버리므로 적재를 중단합니다. DBA 에 파티션 추가를 요청하세요.")

    total = sum(s["rows"] for s in scans.values())
    worst_min = total / ROWS_PER_SEC_WORST / 60
    print(f"\n예상 소요: 최대 약 {worst_min:,.0f}분 (총 {total:,}행, 같은 기간에 다른 태그가 이미 있을 때 기준 "
          f"{ROWS_PER_SEC_WORST:,}행/s)")
    if worst_min > 100:
        print("  [주의] 에이전트 백그라운드 실행 한도(2시간)를 넘을 수 있습니다. 파일을 나눠 여러 번 실행하세요.")

    if args.dry_run:
        print("\n--dry-run 이라 DB 에 쓰지 않았습니다.")
        return

    # 2) 적재
    print()
    total_rows = total_ins = 0
    rollback = []
    use_bulk = not args.no_bulk
    for f, tag in targets:
        t0 = time.time()
        sc = scans[f]
        s = None
        if use_bulk and bulk_ok(sc):
            print(f"  ▶ {tag} ({f.name})  [LOAD DATA]  시작 {datetime.now():%H:%M:%S}")
            try:
                s = dict(sc, inserted=load_file_bulk(conn, f, tag, sc, cols, args.marker))
            except Exception as e:  # noqa: BLE001 — local_infile 거부만 골라 행 단위로 내려간다
                code = e.args[0] if e.args and isinstance(e.args[0], int) else None
                if code not in LOCAL_INFILE_DENIED:
                    raise
                conn.rollback()
                use_bulk = False
                print(f"    LOAD DATA LOCAL 이 거부됨({code}) → 이후 파일은 행 단위 INSERT IGNORE 로 진행 (느림)")
        if s is None:
            if use_bulk:
                print(f"  ▶ {tag} ({f.name})  [행 단위 — 불량·빈 줄·열 개수 혼재가 있어 해당 행만 건너뜀]")
            else:
                print(f"  ▶ {tag} ({f.name})  [행 단위]")
            s = load_file(conn, f, tag, cols, args.marker, args.batch)
        ignored = s["rows"] - s["inserted"]
        total_rows += s["rows"]
        total_ins += s["inserted"]
        dt = time.time() - t0
        print(f"    완료: {s['rows']:,}행 중 신규 {s['inserted']:,} · 중복 무시 {ignored:,} · 불량 {s['bad']}"
              f"  [{dt:.1f}s, {s['rows'] / max(dt, 0.001):,.0f}행/s]")
        if s["min"]:
            rollback.append((tag, fmt(s["min"]), fmt(s["max"])))
    conn.close()

    print(f"\n합계: {total_rows:,}행 중 신규 {total_ins:,} · 중복 무시 {total_rows - total_ins:,}")
    if "SERVER" in cols:
        print("\n되돌리기(이번 마커 행만 삭제, PK 를 타도록 TS 범위 포함):")
        for tag, lo, hi in rollback:
            print(f"  DELETE FROM TB_RAWDATA WHERE TS BETWEEN '{lo}' AND '{hi}' "
                  f"AND TAGNAME = '{tag}' AND SERVER = '{args.marker}';")
    else:
        print("\n[참고] SERVER 컬럼이 없어 마커로 되돌릴 수 없습니다. 기존 실측과 구분하려면 적재 전 상태를 기록해 두세요.")


if __name__ == "__main__":
    main()
