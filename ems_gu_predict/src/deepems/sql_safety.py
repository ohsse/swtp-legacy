"""SQL 식별자(테이블명/컬럼명) 검증 — SQL injection 방지용 공용 유틸.

`db_source.py`(원본 조회 쿼리)와 `scripts/upload.py`(결과 적재 쿼리) 둘 다
테이블/컬럼명을 파라미터 바인딩이 아니라 f-string으로 SQL에 직접 끼워
넣는다 — SQL 표준상 식별자(테이블/컬럼명)는 값과 달리 바인드 파라미터로
못 넘기기 때문에(`:table` 같은 자리표시자는 값에만 쓸 수 있다) 근본적으로
불가피하다. 대신 그 문자열이 실제로 "안전한 식별자 모양"인지(영문자/숫자/
밑줄만, 첫 글자는 영문자/밑줄)를 여기서 강제해, config 파일이 손상되거나
악의적으로 조작된 값을 담고 있어도 `테이블명; DROP TABLE ...` 같은 SQL
injection이 성립할 수 없게 한다.

실제 위협 모델은 "외부 공격자가 직접 쿼리를 던지는" 경로가 아니라(값은
전부 파라미터 바인딩됨, 아래 `db_source.fetch_tag_series`/
`scripts/upload.upload_cycle_result` 참고), "설정 파일(db_connections.json,
db_upload_connections.json, YAML config)이 실수로 또는 변조로 이상한 값을
담게 됐을 때, 그게 조용히 SQL 구조를 바꾸는 걸 막는" 방어다(defense in
depth) — 설정 로딩 시점에 바로 명확한 에러로 걸러낸다.
"""
from __future__ import annotations

import re

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_sql_identifier(value: str, field_name: str) -> str:
    """`value`가 안전한 SQL 식별자 모양(영문자/숫자/밑줄, 첫 글자는 영문자/
    밑줄)이면 그대로 돌려주고, 아니면 ValueError를 낸다. 길이도 64자
    (MySQL/MariaDB 식별자 최대 길이)로 제한한다."""
    if not isinstance(value, str) or not _IDENTIFIER_RE.match(value) or len(value) > 64:
        raise ValueError(
            f"{field_name}은(는) 안전한 SQL 식별자(영문자/숫자/밑줄, 첫 글자는 영문자/밑줄, 64자 이하)여야 "
            f"합니다: {value!r} (SQL injection 방지 — sql_safety.py 참고)"
        )
    return value
