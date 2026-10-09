"""펌프 성능곡선 엔진 선택기.

inp-opt 는 앱 한 벌로 여러 현장을 돌리고, 현장 구분은 APP_CONFIG 가 가리키는
설정 JSON 교체로만 한다(config_path.py, docs/tenant-bundle-guide.md 참조).
이 모듈은 그 설정의 pump_curve.engine 값을 보고 요청을 처리할 엔진 모듈을 고른다.

- 'gosan'(기본) : pump_curve_update        — 기존 고산 구현. 무변경.
- 'gunsan'      : pump_curve_update_gunsan — 군산 태그 + 펌프별 주파수 필터.

두 모듈은 같은 함수 이름·같은 시그니처를 노출하므로 호출부(api_server)는 어느
쪽인지 몰라도 된다. 공통 계약은 다음과 같다.

    apply_table_config(section) / DbManager(cfg) / parse_pump_combination(text)
    run_auto(db, start_date, end_date, pump_nums, pump_hz=None)
    run_manual(db, start_date, end_date, pump_nums, points_text, pump_hz=None)
    ScriptError

epa 쪽 해석 엔진 선택기(epa/app/services/engine.py)와 같은 방식이며, 기본값이
'gosan' 인 것도 같은 이유다 — 기존 현장 설정 파일에는 이 키가 없으므로 고산·기타
현장은 설정을 한 줄도 손대지 않아도 지금까지와 똑같이 동작한다.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_ENGINE = "gosan"

# 설정값 -> 모듈명. 새 현장 엔진이 생기면 여기만 늘린다.
_ENGINE_MODULES = {
    "gosan": "pump_curve_update",
    "gunsan": "pump_curve_update_gunsan",
}


def resolve_engine_name(config: Optional[Dict[str, Any]]) -> str:
    """설정에서 엔진 이름을 읽는다. 키가 없으면 고산으로 본다.

    아는 이름이 아니면 즉시 실패한다. 오타('gusan' 등)를 기본값으로 흘려보내면
    군산 현장에 고산 엔진이 조용히 떠서 엉뚱한 태그를 조회하게 되는데, 그 사고는
    결과 숫자만 보고는 알아채기 어렵다. 설정 파일이 없을 때 조용히 기본값으로
    떨어지지 않는 config_path 의 판단과 같은 이유다.
    """
    section = (config or {}).get("pump_curve") or {}
    name = str(section.get("engine") or DEFAULT_ENGINE).strip().lower()

    if name not in _ENGINE_MODULES:
        known = ", ".join(sorted(_ENGINE_MODULES))
        raise ValueError(
            f"알 수 없는 pump_curve.engine 값입니다: {name!r} (가능한 값: {known})"
        )
    return name


def get_engine(config: Optional[Dict[str, Any]] = None):
    """설정에 맞는 성능곡선 엔진 모듈을 돌려준다.

    import 를 함수 안에서 하는 이유: 고산 배포에서는 군산 모듈이 아예 로드되지
    않게 하려는 것이다. 반대도 마찬가지다. 두 모듈 모두 테이블명을 모듈 전역으로
    들고 있어, 쓰지도 않을 모듈을 함께 올려 둘 이유가 없다.
    """
    name = resolve_engine_name(config)

    if name == "gunsan":
        import pump_curve_update_gunsan as engine
    else:
        import pump_curve_update as engine

    return engine


def describe_engine(config: Optional[Dict[str, Any]]) -> str:
    """적용된 엔진을 기동 로그 한 줄로 요약한다."""
    try:
        name = resolve_engine_name(config)
    except ValueError as exc:
        return f"[pump-curve] 엔진 선택 실패: {exc}"
    return f"[pump-curve] engine={name} module={_ENGINE_MODULES[name]}"
