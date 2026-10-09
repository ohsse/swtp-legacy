"""설정 파일 경로 해석 — GSSource 의 MAIN_2026._resolve_path 와 같은 규약을 쓴다.

  APP_CONFIG            : 설정 JSON 경로 (권장)
  ROUGHNESS_GA_CONFIG   : 구 이름. 하위호환으로만 읽는다.

env 가 가리킨 파일이 없으면 조용히 기본값으로 떨어지지 않고 즉시 실패한다.
compose 에서 마운트를 빠뜨렸을 때 엉뚱한 DB 에 붙는 사고를 막기 위해서다.

api_server 와 run_monitor 가 함께 쓰므로 별도 모듈로 둔다
(run_monitor 는 서브프로세스로 도는 러너라 Flask 를 끌어오면 안 된다).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.prob.json"

ENV_NAME = "APP_CONFIG"
LEGACY_ENV_NAME = "ROUGHNESS_GA_CONFIG"

# 경로 해석 과정에서 알려야 할 내용. 호출 측이 기동 로그로 흘린다.
warnings: list[str] = []


def resolve_config_path() -> Path:
    """APP_CONFIG -> ROUGHNESS_GA_CONFIG(구) -> 모듈 기본값 순으로 설정 경로를 정한다."""
    for name in (ENV_NAME, LEGACY_ENV_NAME):
        raw = os.environ.get(name)
        if not raw:
            continue
        if name == LEGACY_ENV_NAME:
            warnings.append(f"{LEGACY_ENV_NAME} 는 구 이름이다. {ENV_NAME} 로 옮길 것.")
        path = Path(raw)
        if not path.is_absolute():
            path = BASE_DIR / path
        if not path.exists():
            raise FileNotFoundError(f"{name} 가 가리키는 설정 파일이 없습니다: {path}")
        return path

    warnings.append(f"{ENV_NAME} 미설정 - 모듈 기본값 사용: {DEFAULT_CONFIG_PATH.name}")
    return DEFAULT_CONFIG_PATH


def load_config(config_path: Path) -> dict:
    """설정 JSON 을 읽어 dict 로 돌려준다.

    api_server 가 펌프 성능곡선 설정(pump_curve)과 DB 접속 정보(db)를 읽는 데 쓴다.
    러너(run_optimizer / run_monitor)는 지금처럼 각자 경로만 받아 직접 읽으므로
    이 함수를 거치지 않는다.
    """
    with config_path.open(encoding="utf-8") as f:
        return json.load(f)


def describe_config(config_path: Path) -> str:
    """적용된 설정 파일과 DB 대상을 한 줄로 요약한다(비밀번호 제외)."""
    try:
        with config_path.open(encoding="utf-8") as f:
            db = json.load(f).get("db", {})
        target = f"{db.get('host')}:{db.get('port', 3306)}/{db.get('database')}"
    except Exception as exc:  # 설정이 깨져도 기동 로그 자체는 남긴다
        target = f"<확인 실패: {exc}>"
    return f"[config] {ENV_NAME}={config_path} db={target}"
