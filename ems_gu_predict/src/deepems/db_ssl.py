"""DB 연결에 TLS(SSL)를 켜는 공용 로직 — `db_source.py`(원본 읽기)와
`scripts/upload.py`(결과 쓰기) 둘 다 여기서 만든 `connect_args`를 그대로
`sqlalchemy.create_engine(..., connect_args=...)`에 넘긴다.

지금까지는 DB 연결에 암호화가 전혀 없었다 — 비밀번호는 코드에 안
박아두지만(`config._expand_env`, `db_connections.json` gitignore 등),
정작 그 비밀번호와 조회 결과 자체가 네트워크 위에서는 평문으로 오갔다는
뜻이다. 운영 DB가 같은 로컬 네트워크가 아니라 원격이라면(특히 인터넷을
거친다면) 이 경로가 도청/중간자 공격에 노출된다 — 그래서 접속정보에
`ssl_ca`(CA 인증서 경로)를 지정하면 TLS를 켜도록 지원한다.

접속정보(json)에 `ssl_ca`/`ssl_cert`/`ssl_key`/`ssl_verify_identity` 중
하나라도 있으면 TLS를 켠다 — 아무것도 없으면 지금까지와 동일하게 평문
연결이다(기존 배포를 깨지 않기 위한 하위호환, 로컬/개발 환경에서는 TLS
없는 DB가 흔하므로 강제하지 않는다). 운영(prod)에서는 최소
`ssl_ca`(서버 인증서를 검증할 CA 인증서 경로)를 지정하는 걸 강하게
권장한다.
"""
from __future__ import annotations

_SSL_KEYS = ("ssl_ca", "ssl_cert", "ssl_key")


def ssl_connect_args(conn_params: dict) -> dict:
    """`conn_params`(host/user/password/db 등이 든 dict, 원본을 바꾸지 않음)에서
    `ssl_*` 키를 읽어 PyMySQL이 이해하는 `connect_args`(`{"ssl": {...}}`)를
    만든다. `ssl_*` 키가 하나도 없으면 빈 dict를 돌려준다(TLS 없이 지금까지와
    동일하게 연결 — 하위호환).

    - `ssl_ca`/`ssl_cert`/`ssl_key`: 파일 경로. PyMySQL의 `ssl={"ca":...,
      "cert":...,"key":...}` 형식 그대로 전달한다.
    - `ssl_verify_identity`(기본 True): 서버 인증서의 호스트명을 실제 접속
      호스트와 대조하는지. `ssl_ca`를 지정하고도 이걸 꺼두면(`False`) 중간자
      공격에 다시 노출되므로, 명시적으로 `False`를 줬을 때만 끈다.
    """
    ssl_opts = {}
    for src_key, dst_key in (("ssl_ca", "ca"), ("ssl_cert", "cert"), ("ssl_key", "key")):
        if conn_params.get(src_key):
            ssl_opts[dst_key] = conn_params[src_key]

    if not ssl_opts:
        return {}

    ssl_opts["check_hostname"] = bool(conn_params.get("ssl_verify_identity", True))
    return {"ssl": ssl_opts}
