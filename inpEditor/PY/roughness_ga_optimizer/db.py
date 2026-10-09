from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

import pymysql


@dataclass
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


class DbManager:
    """EMS_EPA의 DbManager와 같은 사용감을 가진 간단한 MariaDB wrapper입니다."""

    def __init__(self, config: DbConfig):
        self.conn = pymysql.connect(
            host=config.host,
            port=int(config.port),
            user=config.user,
            password=config.password,
            database=config.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def executemany(self, sql: str, rows: list[tuple]) -> int:
        with self.conn.cursor() as cur:
            return cur.executemany(sql, rows)

    def execute(self, sql: str, params: tuple = ()) -> int:
        with self.conn.cursor() as cur:
            return cur.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def make_placeholders(values: Iterable[Any]) -> str:
    return ",".join(["%s"] * len(list(values)))
