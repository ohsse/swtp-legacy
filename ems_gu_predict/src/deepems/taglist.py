"""태그리스트(GunS_taglist.xlsx) 로딩.

기존 코드(initialization() in main_guns_v1.py, load_varlist() in the
training notebooks)와 동일한 필터링 규칙(비고 != 'NU', 변수명 첫 글자로
FLUX/PRES 구분)을 쓰되, 한 곳에만 정의해서 학습/추론이 다른 규칙을
쓰는 일이 없도록 한다.
"""
from __future__ import annotations

import dataclasses
import re

import pandas as pd


@dataclasses.dataclass
class TagInfo:
    tag_name: str  # 태그명, 예: 891-365-FRI-8950
    tag_desc: str  # 태그 설명
    var_name: str  # 변수명, 예: Q_GunSnS
    role: str  # 비고: target / variable / NU


def list_sheets(taglist_path: str) -> list[str]:
    """태그리스트 엑셀의 시트 이름 목록. 시트 하나 = 하나의 "단계"(정수장/배수지 등)를
    의미한다 (예: gunsan/gj/nw/osd). main_guns_v1.py의 predict_and_upload_flux_test()가
    `taglist.sheetnames`를 순회하는 것과 같은 방식."""
    import openpyxl

    wb = openpyxl.load_workbook(taglist_path, read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def load_taglist(taglist_path: str, sheet: str, mode: str = "BOTH") -> list[TagInfo]:
    ws = pd.read_excel(taglist_path, sheet_name=sheet)
    ws = ws.dropna(subset=["태그명", "변수명"])

    if mode == "PRES":
        ws = ws.loc[(ws["비고"] != "NU") & (ws["변수명"].str[0] != "P")]
    elif mode == "FLUX":
        ws = ws.loc[(ws["비고"] != "NU") & (ws["변수명"].str[0] == "P")]
    elif mode == "BOTH":
        ws = ws.loc[ws["비고"] != "NU"]
    else:
        raise ValueError(f"unknown mode: {mode}")

    tags = [
        TagInfo(
            tag_name=str(row["태그명"]),
            tag_desc=str(row.get("태그 설명", "")),
            var_name=str(row["변수명"]),
            role=str(row["비고"]),
        )
        for _, row in ws.iterrows()
    ]
    if not any(t.role == "target" for t in tags):
        raise ValueError(f"sheet '{sheet}' has no target (비고=='target') variable")
    return tags


def filter_excluded(tags: list[TagInfo], exclude_vars: list[str]) -> list[TagInfo]:
    """var_name이 exclude_vars에 있는 태그를 제외한다.

    태그 하나(Q8)만 최근 데이터밖에 없을 때, "그 태그 포함 버전"과 "그 태그를
    빼서 나머지가 전체 기간을 다 쓸 수 있는 버전"을 config 하나로(태그리스트는
    안 건드리고) 나누기 위한 것 — config.py의 DataConfig.exclude_vars 참고."""
    if not exclude_vars:
        return tags
    exclude = set(exclude_vars)
    kept = [t for t in tags if t.var_name not in exclude]
    if not any(t.role == "target" for t in kept):
        raise ValueError(f"exclude_vars {exclude_vars}를 적용하면 target 변수가 하나도 안 남습니다.")
    return kept


def combine_max(tags: list[TagInfo], groups: dict[str, list[str]]) -> list[TagInfo]:
    """groups={새 변수명: [원본 변수명들]}에 지정된 태그들을 새 태그 하나로 합친다.

    실제 값 병합(결측 아닌 값들의 최댓값)은 data.combine_max_columns가 raw
    DataFrame에서 한다 — 이 함수는 그 결과에 맞춰 tags 메타데이터(따라서
    feature_vars/target_vars가 만드는 컬럼 목록)만 갱신한다. 새 태그는 그룹의
    첫 원소가 있던 자리에 들어가고, 나머지 원소는 목록에서 빠진다. tag_name은
    원본들의 tag_name을 "|"로 이어붙인 참고용 값이다(실제 DB/CSV 태그명이
    아니다 — raw 로딩은 이 함수를 적용하기 전의 원본 tags로 이미 끝나 있어야
    한다. pipeline.prepare_data 참고).
    """
    if not groups:
        return tags
    by_var = {t.var_name: t for t in tags}
    member_to_group: dict[str, str] = {}
    for new_name, members in groups.items():
        missing = [m for m in members if m not in by_var]
        if missing:
            raise ValueError(f"combine_max_columns['{new_name}']에 있는 변수 {missing}가 태그리스트에 없습니다.")
        roles = {by_var[m].role for m in members}
        if len(roles) > 1:
            raise ValueError(f"combine_max_columns['{new_name}']의 변수들이 role이 서로 다릅니다: {roles}")
        for m in members:
            member_to_group[m] = new_name

    result: list[TagInfo] = []
    inserted: set[str] = set()
    for t in tags:
        group = member_to_group.get(t.var_name)
        if group is None:
            result.append(t)
            continue
        if group in inserted:
            continue  # 이 그룹의 병합 태그는 첫 멤버 자리에서 이미 넣었음
        members = groups[group]
        combined_tag_name = "|".join(by_var[m].tag_name for m in members)
        combined_desc = " / ".join(by_var[m].tag_desc for m in members if by_var[m].tag_desc)
        result.append(TagInfo(tag_name=combined_tag_name, tag_desc=combined_desc, var_name=group, role=by_var[members[0]].role))
        inserted.add(group)
    return result


# 변수명 접두문자 -> 물리량 종류. 이 저장소의 태그 명명 규칙(GU_taglist.xlsx)이다:
# Q/O = 유량(flow), P = 압력(pressure), H = 수위(level). H3_1/H3_2, H7_1/H7_2처럼
# 병합(combine_max) 전 원본 태그명도 규칙이 같아서 그대로 적용된다.
QUANTITY_PREFIXES = {"Q": "유량", "O": "유량", "P": "압력", "H": "수위"}


def classify_quantity(var_name: str) -> str:
    """변수명 첫 글자로 물리량 종류를 구분한다. analyze.py의 network_graph에서
    태그를 유량/압력/수위별로 색을 다르게 그리는 데 쓴다 — 예를 들어 압력 노드가
    유량 노드를 선행하는 관계는 "상류 압력 변화가 하류 유량에 반영된다"는 식으로
    물리적으로 해석하기 쉬워진다. 규칙에 없는 접두문자는 "기타"로 분류된다."""
    if not var_name:
        return "기타"
    return QUANTITY_PREFIXES.get(var_name[0].upper(), "기타")


# 사용자가 제공한 실측 관망도(2026-09) 기준 태그 간 연결 관계 — "상류 지점의
# (유량/압력) 태그 -> 하류 지점의 (유량/압력) 태그" 쌍으로 지점(site) 단위
# 연결을 태그 단위로 펼쳐뒀다. 아래 각 tag_name(FRI/PRI/LEI 코드)이 실제
# 관망도에 적힌 것과 정확히 일치하는지 직접 대조해서 확인했다(load_taglist
# 실측). combine_max로 합쳐진 이름(H3, H7)을 쓴다 — analyze.py의
# network_graph가 그리는 노드 집합과 그대로 맞아떨어지게 하기 위해서다.
#
# 원본 기록은 docs/GU_network_topology.md(Mermaid 다이어그램 + 지점별
# 태그 표 + 연결 표)다 — 이 문서가 사람이 읽고 고치는 원본이고, 아래
# 목록은 그걸 코드에서 쓰는 형태로 옮긴 것이다. 태그가 추가/변경되면
# 그 문서를 먼저 고치고 여기를 그에 맞춰 갱신할 것.
#
# 관망도 요약(2026-09-15, Mermaid 다이어그램 기준으로 정정 — 자세한
# 정정 이력은 REFERENCE_NETWORK_EDGES 정의 앞 주석 참고):
#   군산정수장(Q_GunS,P_GunS) -> 개정분기(P1) <- 함열가압장(Q_Ham,P_Ham)
#   개정분기(P1) -> 지방산단(Q2,P2) -> 나운배수지(H3, 공업)
#              -> 국가산단(Q4,P4) -> 군장에너지(Q8)
#                                  -> 군산관말(Q6,P6) -> 오식도배수지 유입(Q7)
#                                                      -> 오식도배수지 수위(H7)
#                                                      -> 오식도배수지 유출(O7)
#                                  -> 내초도분기(Q5,P5)  (별도 종단, 오식도배수지 유입에는 안 합류)
#
# analyze.cross_correlation_pairs()가 데이터에서 찾아낸 관계와 이 실측
# 토폴로지가 얼마나 겹치는지 비교하는 참고용이다(analyze.plot_network_graph의
# reference_edges 인자) — 이 목록 자체가 학습에 쓰이는 값은 아니다.
#
# 밸브(V2=지방산단밸브, V4=국가산단밸브)는 여기(관망도 노드)엔 없다 — 이
# 목록은 "지점 A -> 지점 B로 물이 흐른다"는 지점 간 관계만 담고, 밸브는
# 지점이 아니라 지점 안의 제어 요소이기 때문이다(REFERENCE_SAME_SITE_GROUPS
# 참고, V2/P2/Q2처럼 같은 지점 그룹에 속함). analyze.py의 밸브 분석
# (valve_control_summary 등)이 밸브가 속한 지점을 통해 이 목록에서 하류를
# 찾을 때 그 지점 대표 노드(예: V2 -> Q2)를 거친다.
# 2026-09-15: 실측 관망도(docs/GU_network_topology.md) 원본 Mermaid
# 다이어그램을 기준으로 재확인 - 이 목록이 그 표(연결 관계 지점 단위)와
# 어긋나 있었던 걸 발견해 다이어그램에 맞춰 고쳤다. 바뀐 부분:
# (1) 함열가압장(Q_Ham/P_Ham) -> 개정분기(P1) 연결 추가(빠져 있었음),
# (2) 군산정수장/함열가압장 -> 내초도분기(Q5/P5) 직결 삭제(존재하지 않음),
# (3) 내초도분기(Q5/P5) -> 오식도배수지 유입(Q7) 삭제(존재하지 않음),
# (4) 군산관말(Q6/P6) -> 내초도분기(Q5/P5) 연결 추가. 즉 내초도분기는
# 군산관말에서만 받고 그 자체로 끝나는 별도 저수지/배수지다(오식도배수지
# 유입에 합류하지 않음) - 실측으로 확인. 같은 정리 중 `H3_2`(나운배수지-
# 생활, 지자체/고산쪽 관리)는 이 관망도 소속이 아님이 확인돼 문서에서
# 빠졌다 - `H3`는 이제 이 목록상 나운배수지(공업, H3_1)만 가리키지만,
# combine_max_columns로 H3_1/H3_2를 합치는 학습 설정 자체는 안 바꿨다
# (이 목록은 참고용 오버레이일 뿐 학습에 쓰이지 않음).
REFERENCE_NETWORK_EDGES: list[tuple[str, str]] = [
    # 군산정수장 -> 개정분기
    ("Q_GunS", "P1"), ("P_GunS", "P1"),
    # 함열가압장 -> 개정분기
    ("Q_Ham", "P1"), ("P_Ham", "P1"),
    # 개정분기 -> 지방산단
    ("P1", "Q2"), ("P1", "P2"),
    # 개정분기 -> 국가산단
    ("P1", "Q4"), ("P1", "P4"),
    # 지방산단 -> 나운배수지(공업)
    ("Q2", "H3"), ("P2", "H3"),
    # 국가산단 -> 군장에너지
    ("Q4", "Q8"), ("P4", "Q8"),
    # 국가산단 -> 군산관말
    ("Q4", "Q6"), ("Q4", "P6"), ("P4", "Q6"), ("P4", "P6"),
    # 군산관말 -> 오식도배수지 유입
    ("Q6", "Q7"), ("P6", "Q7"),
    # 군산관말 -> 내초도분기 (별도 종단 - 오식도배수지 유입에는 합류하지 않음)
    ("Q6", "Q5"), ("Q6", "P5"), ("P6", "Q5"), ("P6", "P5"),
    # 오식도배수지: 유입 -> 수위(H7_1/H7_2 병합) -> 유출
    ("Q7", "H7"), ("H7", "O7"),
]

# 같은 지점(site) 안에서 서로 묶이는 태그 그룹 — REFERENCE_NETWORK_EDGES가
# "지점 A -> 지점 B"(물이 실제로 흐르는 방향)만 담는 것과 달리, 이건 "같은
# 지점에서 같이 재는 값들"이다(예: 정수장의 유량/압력, 오식도배수지의
# 유입유량-수위-유출유량). 방향(상류->하류) 개념이 아니라 "물리적으로
# 같은 위치라 강하게 연관될 수밖에 없다"는 뜻이라 REFERENCE_NETWORK_EDGES와
# 분리했다 — analyze.plot_network_graph()가 이 목록을 받으면 그룹 안의
# 태그끼리 더 굵은 선으로 이어서 시각적으로 "묶어" 보여준다. 리스트 순서가
# 그대로 연결 순서다(3개 이상인 그룹은 사슬로 이음 — 예: 오식도배수지는
# 유입->수위->유출 순).
#
# V2(지방산단밸브 개도, 891-365-POI-8601)/V4(국가산단밸브 개도, 891-365-
# POI-8600)는 role="variable"(target 아님)로 각 지점 그룹 맨 앞에 추가했다
# — 밸브가 그 지점의 유량/압력보다 상류(원인 쪽)라 순서상 앞에 둔다(밸브
# 개도 -> 유량 -> 압력). analyze.valve_control_summary()/
# analyze.ccf_for_pairs()가 "밸브가 상시개방인지 제어를 하는지", "밸브와
# 같은 지점 유량/압력의 관계"를 분석할 때 이 그룹을 그대로 쓴다.
REFERENCE_SAME_SITE_GROUPS: list[list[str]] = [
    ["Q_GunS", "P_GunS"],       # 군산정수장
    ["Q_Ham", "P_Ham"],     # 함열가압장
    ["V2", "Q2", "P2"],     # 지방산단: 밸브 개도 -> 유량 -> 압력
    ["V4", "Q4", "P4"],     # 국가산단: 밸브 개도 -> 유량 -> 압력
    ["Q6", "P6"],           # 군산관말
    ["Q5", "P5"],           # 내초도분기
    ["Q7", "H7", "O7"],     # 오식도배수지: 유입유량 -> 수위 -> 유출유량
]

# recommend.py(Stage 3)가 "레버"(운영자가 실제로 조작할 수 있는 변수)로 다뤄도
# 되는 var_name 목록 — 2026-09-11, 사용자 확인: P_GunS(정수장 압력)는 펌프/밸브
# 조작의 "결과"로 나오는 측정값이지 직접 설정하는 값이 아니다(Q_Ham/P_Ham,
# Q2/P2, Q4/P4, Q5/P5, Q6/P6 등 다른 유량/압력 쌍도 마찬가지로 압력 쪽은
# 전부 측정값으로 취급 — 이 목록에 압력(P_*) 태그를 넣지 않은 이유).
#
# 밸브(V2/V4)를 2026-09-14에 한 번 뺐다가(운영 판단) 다시 넣었다 - Q_GunS
# 하나만 레버로 두니 게인이 너무 작아서(19.15 vs 0.42, ~45배 차이) 이분탐색이
# search_max까지 가도 목표를 못 채우는 경우가 잦았고, 심지어 achievable=True로
# 나온 경우도 delta_lever가 원시 예측을 음수로 만드는(정수장 송수유량이
# 마이너스가 되는) 물리적으로 말이 안 되는 해를 내놓는 사례가 실측으로
# 확인됐다(Q_GunS만으로는 필요 조정폭이 너무 커서 생기는 문제). V2/V4를
# 다시 넣어 게인 기반 레버 선택(estimate_gain 순위)이 정상 작동하게
# 복구했다 - 대신 "V2/V4를 실제로 추천에 반영하지는 않는다"는 요구사항은
# 별도 clip 로직 없이 이미 자동으로 만족된다: V2/V4는 taglist role이
# target이 아니라 variable이라 Stage1 NN의 target_cols(따라서 `analysis.
# CycleResult.forecast`의 컬럼)에 아예 없다 - `upload.
# build_target_forecast_rows`가 `used_lever`와 일치하는 forecast 컬럼을
# 찾아 delta_lever를 더하는데, V2/V4는 그 컬럼 자체가 없어서 그 로직이
# 그냥 아무 데도 적용이 안 된다(Q_GunS도 used_lever가 아니게 되므로 원시
# 예측 그대로 올라감). 즉 레버 "선택/계산"은 V2/V4를 포함해 정상적으로
# 하되, DB 업로드에는 어떤 조정도 반영되지 않는다.
#
# recommend.compare_lever_gains()/recommend_across_levers()/
# recommend_joint_intervention() 등을 부를 때 lever_cols/lever_gains는
# 이 목록에서만 고를 것 — 함수 자체는 어떤 컬럼이든 받아주므로(강제하지
# 않음) 호출부가 이 제약을 지켜야 한다.
CONTROLLABLE_LEVERS: list[str] = ["Q_GunS", "V2", "V4"]

# 레버의 "실질 가동 범위" 최소/최대값 (None이면 그 방향 제한 없음) -
# 2026-09-14, "V2를 증가/감소로 쓸 수 있는지부터 판단" 요청에 대응.
#
# 처음엔 밸브 개도의 이론상 물리 한계인 (0, 100)을 그대로 썼는데, 실측
# DB 이력(2024-01~2025-09, 175,350포인트)을 확인해보니 V2는 그 기간
# 전체를 통틀어 0/100 근처에 간 적이 거의 없었다(최댓값 85.7, 99%ile도
# 64.4) - 즉 (0,100) 기준으로는 room-check가 사실상 절대 발동하지 않아
# 기능이 있으나 마나였다("극단값이 문제가 아니라 많이 사용하는 범위가
# 있지 않나?" 라는 사용자 지적으로 발견). 그래서 이론적 물리 한계
# 대신, 실측 분포의 1~99%ile을 "실질 가동 범위"로 등록해 그 바깥으로
# 나가려는 방향은 "여유 없음"으로 판단하게 했다. `recommend.
# lever_has_room()`이 이 경계와 `analysis.run_cycle`이 넘기는 현재값
# (origin 시점 실측)을 비교해서 판단한다. Q_GunS(정수장 송수유량)는
# 등록된 상한이 없어(플랜트 최대 처리용량 같은 값을 아직 모름) 여기
# 없음 - `lever_has_room()`은 min/max가 None이면 항상 "여유 있음"으로
# 취급한다.
#
# 값 산출 근거(같은 이력 데이터, 태그별 quantile) — **2026-09-17 정정**:
# 원래 이 숫자를 계산할 때 태그리스트에 V2(891-365-POI-8600)/V4
# (891-365-POI-8601)가 서로 뒤바뀌어 등록돼 있었다(사용자 확인). 물리
# 태그(POI-8600/8601) 자체의 실측 분포는 그대로지만, 그때 "V2"라는
# 이름으로 계산됐던 숫자는 사실 지금 기준 V4(POI-8601, 국가산단)의
# 것이었고 그 반대도 마찬가지였다 — 그래서 아래는 태그리스트 수정에 맞춰
# 두 항목을 그대로 맞바꾼 값이다(데이터 자체를 다시 뽑은 게 아니라 라벨만
# 교정 - 두 태그의 실측 분포 자체는 바뀌지 않았으므로 이 교정으로 충분함):
#   V2(891-365-POI-8600, 지방산단): 1%ile=98.526, 99%ile=98.906 (사실상
#       항상 98.5~99 부근 고정 - 거의 조작되지 않는 밸브라 게인도
#       음수/사용불가로 필터링됨, train.py 참고). 단, 2026-08-03 이후
#       저수위 사태로 이 밸브의 실제 운영 방식 자체가 "고정 개방"에서
#       "수위 연동 조절"로 바뀌었다(docs/model_results.md 참고) - 이
#       1~99%ile은 그 전환 이전 이력 위주라 지금은 다시 낮게 잡혀 있을
#       가능성이 있다. 재학습 시 최근 구간만으로 재계산 검토할 것.
#   V4(891-365-POI-8601, 국가산단): 1%ile=13.115, 99%ile=64.408
#       (중앙값 24.08, 최댓값 85.75) - 상대적으로 활발히 조작되는 밸브.
# 범위가 극단적으로 좁은 쪽(V2)은 room-check가 자주 걸리겠지만, 애초에
# CONTROLLABLE_LEVERS 우선순위에서 게인 필터로 거의 선택되지 않는
# 레버라 실질 영향은 작다.
LEVER_PHYSICAL_BOUNDS: dict[str, tuple[float | None, float | None]] = {
    "V2": (98.526, 98.906),
    "V4": (13.115, 64.408),
}


_TAG_CODE_RE = re.compile(r"[A-Z]{2,4}-\d+")


def short_tag_name(tag_name: str) -> str:
    """tag_name(실제 DB/태그리스트 코드, 예: "891-365-FRI-8950",
    "740-914-PRI-1009")에서 앞의 지역/설비 번호(예: "891-365-",
    "740-914-")와 (있다면) 뒤의 접미사를 떼고, 의미가 실리는
    코드부(예: "FRI-8950", "PRI-1009")만 남긴다 — network_graph.png처럼
    표시 공간이 좁은 곳에서 쓴다. 정규식으로 "영문 2~4자-숫자" 패턴만
    골라내는 방식이라 접두/접미사가 어떤 형태든(SS. 접두사 유무 등)
    같은 규칙으로 처리된다. combine_max로 합쳐진 "코드1|코드2" 형태는
    각각 줄여서 "|"로 다시 잇는다. 패턴에 안 맞는 문자열은 원본 그대로
    돌려준다(방어적 fallback). 원본 전체 코드가 필요하면(DB 조회 등)
    tag_name을 그대로 써야 한다 — 이 함수는 표시 전용이다.
    """
    parts = tag_name.split("|")
    shortened = [(_TAG_CODE_RE.search(p).group(0) if _TAG_CODE_RE.search(p) else p) for p in parts]
    return "|".join(shortened)


def is_valve_tag(tag_name: str) -> bool:
    """tag_name의 코드부(short_tag_name()과 같은 규칙으로 뽑음)가 "POI"로
    시작하면 밸브(개도) 태그로 본다 — 이 태그리스트의 계측 코드 접두어
    규칙상 FRI=유량, PRI=압력, LEI=수위처럼 POI는 밸브 개도(Position
    Open/Opening Indicator로 추정)를 가리킨다(예: V2=891-365-POI-8601,
    V4=891-365-POI-8600).

    role(taglist 엑셀의 "비고" 컬럼, target/variable)이 아니라 tag_name
    자체로 판별하는 이유: role은 "이 변수를 모델 target으로 쓰는지"를
    나타내는 모델링 상의 구분이지 "이게 물리적으로 밸브인지"와는 별개다 —
    role을 깜빡 잘못 표기해도(또는 나중에 role 체계가 바뀌어도) 밸브 분석
    (analyze.py의 밸브 상시개방/제어 판별 등)이 태그 자체의 정체성으로
    믿을 수 있게 켜지도록, POI 코드 여부로 직접 판별한다.

    combine_max로 합쳐진 "코드1|코드2" 형태는 그중 하나라도 POI면 True.
    """
    return any(seg.startswith("POI") for seg in short_tag_name(tag_name).split("|"))


def feature_vars(tags: list[TagInfo]) -> list[str]:
    """모델 입력으로 쓰이는 모든 변수명 (target 포함, NU 제외)."""
    return [t.var_name for t in tags]


def target_vars(tags: list[TagInfo]) -> list[str]:
    return [t.var_name for t in tags if t.role == "target"]
