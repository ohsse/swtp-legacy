"""일별 실행 로그 설정 — `schedule.py`의 세 모드(dev/dev-server/prod) 모두
여기서 만든 로거로 기록한다.

파일명은 `{log_dir}/{mode}.log`로 고정하고, 자정마다 자동으로
`{mode}.log.YYYY-MM-DD`로 회전(rotate)한다(`TimedRotatingFileHandler`,
`when="midnight"`) — `prod` 모드는 하루 이상 계속 돌아가는 무한 루프라서
"오늘 실행한 것만" 보려면 파일을 직접 나눌 게 아니라 자동 회전이 필요하다.
`backup_count`(기본 90일)보다 오래된 로그는 자동으로 지워진다 — 무기한
누적되어 디스크를 채우는 사고를 막기 위함.

콘솔에도 같은 내용을 동시에 출력한다(운영자가 터미널을 지켜보거나,
systemd/cron이 stdout을 별도로 잡아가는 경우 둘 다 지원하기 위함) — 기존
`print()`를 `logger.info()`로 바꾸되 내용은 그대로 유지했다.
"""
from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def get_logger(mode: str, log_dir: str = "logs", backup_count: int = 90) -> logging.Logger:
    """`deepems_schedule.<mode>` 로거를 만들어(이미 있으면 그대로 재사용 —
    핸들러를 중복으로 붙이지 않음) 돌려준다. `log_dir`이 없으면 만든다.
    """
    logger_name = f"deepems_schedule.{mode}"
    logger = logging.getLogger(logger_name)
    if logger.handlers:  # 같은 프로세스에서 두 번 호출해도 핸들러가 중복 안 붙게
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False  # 루트 로거로 중복 전파돼 콘솔에 두 번 찍히는 것 방지

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        filename=str(log_path / f"{mode}.log"), when="midnight", backupCount=backup_count, encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    logger.addHandler(console_handler)

    return logger
