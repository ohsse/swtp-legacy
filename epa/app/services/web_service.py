import os
import logging
import json
from datetime import datetime, timedelta # timedelta 추가
from pathlib import Path
from typing import Dict, List, Any
from flask import current_app, g
from app.models import web_models, epa_models
import pandas as pd 
logger = logging.getLogger(__name__)

def load_map_nodes() -> list:
    """표시할 노드 정보를 데이터베이스에서 조회합니다."""

    try:
        db = g.get('db')
        if db is None:
            raise RuntimeError("Database connection is not available in the request context.")
        
        nodes = web_models.load_map_nodes(db)
        current_app.logger.debug(f"Loaded {len(nodes)} map nodes from database.")
        return nodes
    except Exception as e:
        logger.error(f"map node 데이터 조회 중 오류 발생: {e}", exc_info=True)
        raise e
    
def load_tank_nodes() -> list:
    """탱크 노드 정보를 데이터베이스에서 조회합니다."""
    try:
        db = g.get('db')
        if db is None:
            raise RuntimeError("Database connection is not available in the request context.")
        
        nodes = web_models.load_tank_nodes(db)
        current_app.logger.debug(f"Loaded {len(nodes)} tank nodes from database.")
        return nodes
    except Exception as e:
        logger.error(f"tank node 데이터 조회 중 오류 발생: {e}", exc_info=True)
        raise e
    
def load_monitoring_data() -> Dict[str, Any]:
    """
    웹 모니터링 데이터를 조합합니다.
    분석값은 분석 테이블에서, 측정값은 TB_RAWDATA에서 조회합니다.
    """
    db = g.db
    
    target_ts = web_models.get_monitoring_timestamp(db)
    # target_ts = datetime.fromisoformat('2025-08-23 16:05:00')
    if not target_ts:
        logger.warning("모니터링 기준 시각을 찾을 수 없습니다.")
        return {}
    logger.info(f"모니터링 데이터 조회 시작. 기준 시각: {target_ts}")

    # 분석값 조회
    fp_data = web_models.get_fp_data_at_timestamp(db, target_ts, 'mo')
    fr_data = web_models.get_fr_data_at_timestamp(db, target_ts, 'mo')

    # 태그 정보 및 측정값 조회
    tag_info_list = web_models.get_epa_tag_info(db)
    raw_tags_to_fetch = {info[key] for info in tag_info_list for key in ('PRI_TAG', 'FRI_TAG') if info.get(key)}
    raw_data_map = epa_models.fetch_values_by_tag(db, target_ts, list(raw_tags_to_fetch))
    monitoring_data = {}
    # 데이터 조합
    for info in tag_info_list:
        if (j_id := info.get('JUNCTION_ID')) and j_id in fp_data:
            monitoring_data[j_id] = fp_data[j_id]
        if (p_id := info.get('PIPE_ID')) and p_id in fr_data:
            monitoring_data[p_id] = fr_data[p_id]
        if (pri_tag := info.get('PRI_TAG')) and pri_tag in raw_data_map:
            monitoring_data[pri_tag] = raw_data_map[pri_tag]
        if (fri_tag := info.get('FRI_TAG')) and fri_tag in raw_data_map:
            monitoring_data[fri_tag] = raw_data_map[fri_tag]
            
    logger.info(f"모니터링 데이터 {len(monitoring_data)}개 항목 조합 완료.")
    return {
        "ts": target_ts.strftime('%Y-%m-%d %H:%M'),
        "raw": monitoring_data
    }

def load_chart_data(junction_id: str) -> Dict[str, List]:
    """
    [수정] 특정 Junction ID의 12시간 시계열 데이터를 '5분 간격'으로 가공하여 반환합니다.
    """
    db = g.db
    
    # 1. 기준 시간 결정 (개발용 고정값 제거)
    end_ts = web_models.get_monitoring_timestamp(db)
    # end_ts = datetime.fromisoformat('2025-08-23 16:05:00')
    if not end_ts:
        logger.warning(f"차트 데이터 조회를 위한 기준 시각을 찾지 못했습니다: {junction_id}")
        return {}
    
    start_ts = end_ts - timedelta(hours=12)
    logger.info(f"차트 데이터 조회 시작: {junction_id}, 기간: {start_ts} ~ {end_ts}")

    # 2. Junction ID로 관련 정보 조회
    tag_info = web_models.get_tag_info_by_junction_id(db, junction_id)
    if not tag_info:
        logger.warning(f"Junction ID '{junction_id}'에 해당하는 태그 정보를 찾을 수 없습니다.")
        return {}
    
    pipe_id = tag_info.get('PIPE_ID')
    pri_tag = tag_info.get('PRI_TAG')
    fri_tag = tag_info.get('FRI_TAG')
    
    # 3. 각 테이블에서 시계열 데이터 조회
    node_analysis_data = web_models.get_node_timeseries(db, junction_id, start_ts, end_ts)
    link_analysis_data = web_models.get_link_timeseries(db, pipe_id, start_ts, end_ts) if pipe_id else []
    pressure_raw_data = web_models.get_rawdata_timeseries(db, pri_tag, start_ts, end_ts) if pri_tag else []
    flow_raw_data = web_models.get_rawdata_timeseries(db, fri_tag, start_ts, end_ts) if fri_tag else []

    # 4. Pandas DataFrame으로 데이터 통합 및 가공
    df_epa_pressure = pd.DataFrame(node_analysis_data).rename(columns={'RGSTR_TIME': 'ts', 'FP_ALG_RST_VAL': 'epa_pressure'})
    df_epa_flow = pd.DataFrame(link_analysis_data).rename(columns={'RGSTR_TIME': 'ts', 'FLW_ALG_RST_VAL': 'epa_flow'})
    df_pressure = pd.DataFrame(pressure_raw_data).rename(columns={'TS': 'ts', 'VALUE': 'pressure'})
    df_flow = pd.DataFrame(flow_raw_data).rename(columns={'TS': 'ts', 'VALUE': 'flow'})
    
    data_frames = []
    for df in [df_epa_pressure, df_epa_flow, df_pressure, df_flow]:
        if not df.empty:
            df['ts'] = pd.to_datetime(df['ts'])
            for col in ['epa_pressure', 'epa_flow', 'pressure', 'flow']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            data_frames.append(df.set_index('ts'))
            
    if not data_frames:
        return {}

    # 모든 DataFrame을 'ts' 기준으로 병합
    merged_df = pd.concat(data_frames, axis=1)

    # --- [핵심 수정] 5분 간격으로 리샘플링 ---
    # '5T'는 5분 간격을 의미합니다.
    # interpolate(method='time')는 시간 기준으로 선형 보간하여 빈 값을 채웁니다.
    # fillna(0.0)은 보간 후에도 남은 빈 값을 0으로 채웁니다.
    resampled_df = merged_df.resample('5T').interpolate(method='time').fillna(0.0)
    # ------------------------------------
    
    # 최종 결과 형식으로 변환
    chart_data = {
        "ts": [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in resampled_df.index],
        "pressure": resampled_df['pressure'].tolist() if 'pressure' in resampled_df else [],
        "epa_pressure": resampled_df['epa_pressure'].tolist() if 'epa_pressure' in resampled_df else [],
        "flow": resampled_df['flow'].tolist() if 'flow' in resampled_df else [],
        "epa_flow": resampled_df['epa_flow'].tolist() if 'epa_flow' in resampled_df else []
    }
        
    return chart_data

def update_flow_rates(update_list: List[Dict]) -> int:
    """
    유량 설정 데이터를 검증하고 데이터베이스에 업데이트를 요청합니다.
    """
    # 만약 update_list가 str이면 json.loads로 파싱
    if isinstance(update_list, str):
        update_list = json.loads(update_list)
    db = g.db
    logger.info(f"{update_list} 업데이트 목록")
    # 1. 데이터 유효성 검사
    for item in update_list:
        print(type(item), item)  # 타입 확인용
        if 'node_id' not in item or 'flow_rate' not in item:
            raise ValueError("입력 데이터에 'node_id'와 'flow_rate'가 모두 포함되어야 합니다.")
        flow_rate = item['flow_rate']
        if not isinstance(flow_rate, (int, float)):
            raise ValueError(f"'{item['node_id']}'의 flow_rate가 숫자가 아닙니다: {flow_rate}")
        if flow_rate < 0:
            raise ValueError(f"'{item['node_id']}'의 flow_rate는 음수일 수 없습니다: {flow_rate}")

    # 2. 모델 함수를 호출하여 DB 업데이트
    logger.info(f"{update_list} 업데이트 목록")
    affected_rows = web_models.update_reservoir_flow_rates(db, update_list)
    db.commit() # 변경사항 최종 저장
    
    logger.info(f"{affected_rows}개의 유량 설정이 업데이트되었습니다.")
    return affected_rows

def load_simulation_data() -> Dict[str, Any]:
    """
    웹 모니터링 데이터를 조합합니다.
    분석값은 분석 테이블에서, 측정값은 TB_RAWDATA에서 조회합니다.
    """
    db = g.db
    
    target_ts = web_models.get_monitoring_timestamp(db, 'si')
    # target_ts = datetime.fromisoformat('2025-08-23 16:05:00')
    if not target_ts:
        logger.warning("모니터링 기준 시각을 찾을 수 없습니다.")
        return {}
    logger.info(f"모니터링 데이터 조회 시작. 기준 시각: {target_ts}")

    # 분석값 조회
    fp_data = web_models.get_fp_data_at_timestamp(db, target_ts, 'si')
    fr_data = web_models.get_fr_data_at_timestamp(db, target_ts, 'si')

    # 태그 정보 및 측정값 조회
    tag_info_list = web_models.get_epa_tag_info(db)


    # 데이터 조합
    monitoring_data = {}
    for info in tag_info_list:
        if (j_id := info.get('JUNCTION_ID')) and j_id in fp_data:
            monitoring_data[j_id] = fp_data[j_id]
        if (p_id := info.get('PIPE_ID')) and p_id in fr_data:
            monitoring_data[p_id] = fr_data[p_id]

            
    logger.info(f"시뮬레이션 데이터 {len(monitoring_data)}개 항목 조합 완료.")
    return {
        "ts": target_ts.strftime('%Y-%m-%d %H:%M'),
        "raw": monitoring_data
    }

def get_pump_comb(pump_grp: int) -> List[Dict]:
    """펌프 그룹의 전체 펌프 조합을 조회합니다.

    Args:
        pump_grp (int): 조회할 펌프 그룹 번호

    Returns:
        List[Dict]: 펌프 그룹의 전체 펌프 조합 목록
        
    Raises:
        RuntimeError: DB 연결이 없는 경우
    """
    db = g.db
    if db is None:
        raise RuntimeError("Database connection is not available")
        
    pump_combs = web_models.get_grp_comb(db, pump_grp)
    pump_pwr_unit = web_models.ger_comb_unit(db)
    pwr_unit_map: Dict[str, Dict] = {item['PUMP_COMB']: item for item in pump_pwr_unit}
    merged_list: List[Dict] = []
    
    for comb_item in pump_combs:
        pump_comb_key = comb_item['PUMP_COMB']

        # pwr_unit_map에 해당 PUMP_COMB 키가 있는지 확인
        if pump_comb_key in pwr_unit_map:
            # 키가 존재하면, pwr_unit_map에서 해당 데이터를 가져옴
            pwr_unit_data = pwr_unit_map[pump_comb_key]
                        
            merged_item = {**comb_item, **pwr_unit_data}

            # 병합된 결과를 새 리스트에 추가
            merged_list.append(merged_item)
        else:

            merged_list.append(comb_item)
 
    return merged_list


# ---------------------------------------------------------------------------
# 관망 형상(GeoJSON)
#
# 지도 좌표의 원천은 프런트 번들의 정적 asset 이 아니라 "지금 이 스택이 실제로 해석하는
# INP" 여야 한다. 그래야 현장별 관망이 맞고, inpEditor 의 '적용'(InpFileService.
# applyCurrentRevision)이 INP 를 런타임에 덮어써도 지도가 따라간다.
#
# 응답 스키마는 예전 정적 파일(fe/src/assets/combined_network.json)과 같게 유지한다 —
# 평면 FeatureCollection, properties.type 은 'junction'/'pipe', 단위는 wntr 의 SI
# (길이·관경 m, 수요량 m^3/s). 프런트 styleFunction 이 이 형태를 그대로 읽는다.
# ---------------------------------------------------------------------------

# {INP 경로: (시그니처, payload)}.  INP 는 4MB 라 매 요청 파싱하면 비싸고,
# load_inp_with_fallback 이 임시파일을 delete=False 로 남기므로 누수로도 이어진다.
_NETWORK_CACHE: Dict[str, tuple] = {}

# 속성 키 순서. junction 과 pipe 가 같은 12개 키를 공유하고 해당 없는 값은 None 이다
# (예전 내보내기와 동일). 뒤에 node_type / link_type 만 덧붙인다.
_FEATURE_KEYS = ('id', 'type', 'elevation', 'base_demand', 'pattern',
                 'start_node', 'end_node', 'length', 'status',
                 'diameter', 'roughness', 'minor_loss')


# epa 루트. 이 파일이 <epa>/app/services/ 에 있으므로 두 단계 위가 <epa> 다.
# (epa_service_gunsan.py:42 와 같은 계산)
_EPA_ROOT = Path(__file__).resolve().parents[2]


def _resolve_network_inp_path() -> str:
    """현재 엔진이 해석에 쓰는 INP 경로를 config 에서 골라 절대경로로 돌려준다.

    엔진 선택은 engine.py 의 get_engine() 과 같은 방어다 — EPA_ENGINE 키가 없는 기존
    현장 설정(deploy/*/conf/epa/config.py)은 고산으로 떨어져 지금까지와 똑같이 동작한다.
    엔진 모듈을 import 하지 않고 config 만 읽는다(읽기 전용 지도 API 가 해석엔진을
    깨울 이유가 없고, 군산 어댑터 import 는 sys.path 를 건드린다).

    **절대경로로 바꾸는 것이 핵심이다.** config 값은 './inp/epa_model.inp' 같은
    상대경로이고, 군산 엔진은 EPANET 에 한글 경로를 숨기려 run_sim 동안 os.chdir 를
    한다(epanet_si_gs.py:1041). CWD 는 프로세스 전역인데 이 앱은 스레드 4개로 돌고
    (Dockerfile), _ENGINE_LOCK 은 엔진끼리만 막는다. 상대경로로 두면 해석이 도는 중에
    지도를 열었을 때만 간헐적으로 파일을 못 찾는다.
    """
    cfg = current_app.config
    if cfg.get('EPA_ENGINE', 'gosan') == 'gunsan':
        value, label = cfg['GUNSAN_INP_PATH'], 'GUNSAN_INP_PATH'
    else:
        # 고산은 모니터링이 실제로 푸는 모델을 쓴다(epa_service.py:442). inpEditor 의
        # '적용' 대상도 이 파일이라 지도가 적용된 모델을 따라간다. MO 키가 없는 구버전
        # 마운트 config 를 위해 INP_FILE_PATH 로 물러선다.
        value = cfg.get('INP_MO_FILE_PATH') or cfg['INP_FILE_PATH']
        label = 'INP_MO_FILE_PATH'

    path = Path(value)
    if not path.is_absolute():
        path = (_EPA_ROOT / path).resolve()
    if not path.exists():
        raise FileNotFoundError(
            "관망 INP 를 찾을 수 없습니다: %s (config %s = %s)" % (path, label, value)
        )
    return str(path)


def _num(value, digits=None):
    """wntr 이 돌려주는 값(numpy 스칼라 포함)을 JSON 이 아는 float 으로 바꾼다.

    digits 를 주면 그 자리에서 반올림한다. wntr 이 INP 의 mm/m 를 SI 로 고칠 때 나오는
    부동소수 잡음(관경 2300mm -> 2.3000000000000003 m)을 지우는 용도다. 길이 계열은
    6자리면 마이크로미터라 잃는 정보가 없다.

    반대로 base_demand 는 반올림하지 않는다 — m^3/s 라 값 자체가 0.0573888… 처럼 작아서
    6자리로 자르면 하루 0.86 m^3 만큼이 날아간다.
    """
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if digits is None else round(number, digits)


def _xy(coord) -> list:
    """좌표를 소수 2자리로 줄인다. INP 의 COORDINATES 자체가 소수 2~3자리다."""
    return [round(float(coord[0]), 2), round(float(coord[1]), 2)]


def _status_value(link):
    """LinkStatus(IntEnum) 를 예전 내보내기와 같은 숫자(0/1)로 바꾼다."""
    status = getattr(link, 'initial_status', None)
    if status is None:
        return None
    try:
        return int(status)
    except (TypeError, ValueError):
        return None


def _blank_props(feature_id, feature_type: str) -> Dict[str, Any]:
    """12개 키를 순서대로 None 으로 깔아 둔다(값은 호출측에서 덮어쓴다)."""
    props: Dict[str, Any] = {key: None for key in _FEATURE_KEYS}
    props['id'] = str(feature_id)
    props['type'] = feature_type
    return props


def _find_stale_tag_refs(inp_path: str) -> List[str]:
    """[TAGS] 가 [PIPES]/[PUMPS]/[VALVES] · [JUNCTIONS]/[RESERVOIRS]/[TANKS] 에 없는
    객체를 가리키는 줄을 찾는다. INP 로드 실패 시 원인을 지목하는 용도라 실패해도 조용히
    빈 목록을 돌려준다 — 진단이 진단을 가려서는 안 된다.

    2026-09-11 군산 epa_model.inp 에서 2줄(`LINK 13 SANDAN`, `LINK 지방산단 SANDAN`),
    2026-09-14 군산_수정_r0.inp 에서 같은 2줄이 나왔다. 내보내기 도구가 [TAGS] 를
    원본째 실어 나르므로 INP 를 다시 뽑을 때마다 재발한다.
    """
    LINK_SECTIONS = ('[PIPES]', '[PUMPS]', '[VALVES]')
    NODE_SECTIONS = ('[JUNCTIONS]', '[RESERVOIRS]', '[TANKS]')
    try:
        raw = open(inp_path, 'rb').read()
    except OSError:
        return []

    # epanet_si_gs.py:650 의 prepare_inp 와 같은 순서. latin-1 은 넣지 않는다 —
    # 어떤 바이트열에도 성공해서 뒤 후보를 잡아먹고 한글을 조용히 깨뜨린다.
    text = None
    for enc in ('utf-8-sig', 'cp949', 'euc-kr'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return []

    section = None
    links, nodes, tag_rows = set(), set(), []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(';'):
            continue
        if stripped.startswith('['):
            section = stripped.split(']')[0].upper() + ']'
            continue
        tokens = stripped.split()
        if section in LINK_SECTIONS:
            links.add(tokens[0])
        elif section in NODE_SECTIONS:
            nodes.add(tokens[0])
        elif section == '[TAGS]' and len(tokens) >= 2:
            tag_rows.append((tokens[0].upper(), tokens[1]))

    stale = []
    for kind, target in tag_rows:
        if kind == 'LINK' and target not in links:
            stale.append('LINK ' + target)
        elif kind == 'NODE' and target not in nodes:
            stale.append('NODE ' + target)
    return stale


def _build_network_geojson(inp_path: str, crs_name: str) -> Dict[str, Any]:
    """INP 를 읽어 지도용 GeoJSON FeatureCollection 을 만든다."""
    # 함수 안에서 import 하는 이유는 engine.py 와 같다 — 모듈 적재 시점에 wntr 과
    # 고산 엔진 모듈을 끌어오지 않는다.
    from app.services.epa_service import load_inp_with_fallback

    try:
        wn = load_inp_with_fallback(inp_path)
    except Exception as e:
        # load_inp_with_fallback 은 인코딩 후보를 돌며 모든 예외를 삼키고 마지막에
        # "INP 파일을 읽을 수 없습니다" 하나로 뭉갠다. 그런데 실제로 가장 잦은 원인은
        # 인코딩이 아니라 [TAGS] 의 유령 참조다 — wntr 의 _read_tags 가 미선언 객체에
        # get_link() 를 무방비로 부르면 KeyError 가 AttributeError 로 둔갑해
        # "str object has no attribute name" 으로 나온다. 그대로 두면 인코딩 문제로
        # 헛짚게 되므로, 실패했을 때만 [TAGS] 를 훑어 원인을 지목한다.
        stale = _find_stale_tag_refs(inp_path)
        if stale:
            raise RuntimeError(
                "INP 의 [TAGS] 가 선언되지 않은 객체를 참조합니다(%d건: %s). 해당 줄을 "
                "지우면 읽힙니다. [TAGS] 는 표시용이라 해석에 영향이 없습니다: %s"
                % (len(stale), ', '.join(stale[:5]), inp_path)
            ) from e
        raise

    features: List[Dict[str, Any]] = []
    coord_by_node: Dict[str, list] = {}

    # --- 노드: 절점 / 저수지 / 탱크 ---------------------------------------
    # 저수지·탱크도 type 은 'junction' 으로 둔다. 프런트 styleFunction 이 type 만 보고
    # 분기하므로 그 함수를 건드리지 않고 관망이 이어진다. 세부 구분은 node_type 이 한다.
    for node_type, group in (('junction', wn.junctions()),
                             ('reservoir', wn.reservoirs()),
                             ('tank', wn.tanks())):
        for name, node in group:
            coord = getattr(node, 'coordinates', None)
            if not coord:
                logger.warning("좌표가 없는 노드를 건너뜁니다: %s (%s)", name, node_type)
                continue
            xy = _xy(coord)
            coord_by_node[name] = xy

            props = _blank_props(name, 'junction')
            props['elevation'] = _num(getattr(node, 'elevation', None), 6)
            props['base_demand'] = _num(getattr(node, 'base_demand', None))
            props['node_type'] = node_type
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': xy},
                'properties': props,
            })

    # --- 링크: 관로 / 펌프 / 밸브 -----------------------------------------
    # 펌프·밸브도 type 은 'pipe' 다(노드와 같은 이유). 관경이 없거나 작아 styleFunction
    # 에서 가는 선으로 떨어진다 — 관망이 끊겨 보이지 않게만 하면 된다.
    for link_type, group in (('pipe', wn.pipes()),
                             ('pump', wn.pumps()),
                             ('valve', wn.valves())):
        for name, link in group:
            start = coord_by_node.get(link.start_node_name)
            end = coord_by_node.get(link.end_node_name)
            if start is None or end is None:
                logger.warning("양 끝 좌표가 없는 링크를 건너뜁니다: %s (%s)", name, link_type)
                continue

            # 시작노드 -> 중간 정점(VERTICES) -> 끝노드.
            line = [start]
            for vertex in (getattr(link, 'vertices', None) or []):
                line.append(_xy(vertex))
            line.append(end)

            props = _blank_props(name, 'pipe')
            props['start_node'] = link.start_node_name
            props['end_node'] = link.end_node_name
            props['length'] = _num(getattr(link, 'length', None), 6)
            props['status'] = _num(_status_value(link))
            props['diameter'] = _num(getattr(link, 'diameter', None), 6)
            props['roughness'] = _num(getattr(link, 'roughness', None), 6)
            props['minor_loss'] = _num(getattr(link, 'minor_loss', None), 6)
            props['link_type'] = link_type
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'LineString', 'coordinates': line},
                'properties': props,
            })

    return {
        'type': 'FeatureCollection',
        'name': 'network',
        # 좌표는 재투영하지 않은 INP 원본 투영좌표다. 프런트가 이 값을 OpenLayers 의
        # dataProjection 으로 그대로 쓴다.
        'crs': {'type': 'name', 'properties': {'name': crs_name}},
        'features': features,
    }


def load_network_geojson() -> Dict[str, Any]:
    """지도에 그릴 관망 형상을 현재 INP 에서 만들어 GeoJSON 으로 돌려준다."""
    inp_path = _resolve_network_inp_path()
    crs_name = current_app.config.get('NETWORK_CRS', 'EPSG:5186')

    stat = os.stat(inp_path)
    # mtime+size 로 무효화한다. inpEditor 의 '적용'이 같은 경로를 덮어쓰므로 경로만으로는
    # 바뀐 줄 모른다. '적용'은 .tmp 로 복사한 뒤 리네임하므로 mtime 이 반드시 갱신된다
    # (deploy/gunsan/README.md).
    signature = (stat.st_mtime_ns, stat.st_size, crs_name)
    cached = _NETWORK_CACHE.get(inp_path)
    if cached and cached[0] == signature:
        return cached[1]

    payload = _build_network_geojson(inp_path, crs_name)

    # 파싱 중에 '적용'이 파일을 갈아치웠으면(stat 과 read 사이의 경합) 새 내용을 옛 키로
    # 캐싱해 영구히 안 갱신되는 상태가 된다. 시그니처가 달라졌으면 이번 응답만 쓰고
    # 캐싱하지 않는다 — 다음 요청이 다시 읽는다.
    if os.stat(inp_path).st_mtime_ns == stat.st_mtime_ns:
        _NETWORK_CACHE[inp_path] = (signature, payload)
    current_app.logger.info(
        "관망 GeoJSON 생성: %s (feature %d개, crs=%s)",
        inp_path, len(payload['features']), crs_name,
    )
    return payload
