# /app/routes/epa_routes.py
import logging
from datetime import datetime
import traceback
from flask import request
from app.services.engine import get_engine, EngineBusyError, EngineRequestError
from app.scheduler import scheduler
from app.routes.base_view import BaseView
from app.utils.response import api_success, api_error
from app.utils import messages
import json
from . import bp

logger = logging.getLogger(__name__)


def _parse_selected_pumps(settings_data):
    """
    settings.pumps -> (pump_comb CSV, {펌프번호: Hz}) 를 만든다.

    군산 화면이 보내는 신규 형식이다:
        "pumps": [{"pumpNo": 1, "hz": 55}, {"pumpNo": 3, "hz": 52}]

    키가 아예 없으면 (None, None) 을 돌려준다 — 호출부가 기존 형식
    (settings.selectedCombo.rawMinConfig.PUMP_COMB)으로 떨어지게 하기 위해서다.
    고산 프런트는 이 키를 보내지 않으므로 지금까지와 똑같이 처리된다.

    형식이 틀리면 ValueError 를 올린다. 호출부가 400 으로 바꾼다 — 서버 잘못이 아니다.

    값의 '범위'(펌프 1~4호기, Hz 1~60)는 여기서 보지 않는다. 그 숫자는 관망 모델에
    딸린 것이라 엔진이 SSOT 다(epanet_si_gs.py 의 parse_pump_combination /
    parse_pump_hz). 여기에 한 벌 더 두면 엔진이 바뀔 때 조용히 어긋난다.
    """
    pumps = settings_data.get('pumps')
    # 키 자체가 없어야 "기존 형식"이다. 빈 배열은 "군산 화면이 보냈는데 0대"라는
    # 다른 상황이므로 기존 경로로 흘려보내지 않는다 — 흘려보내면 "selectedCombo 가
    # 없습니다" 라는 엉뚱한 안내가 나간다.
    if pumps is None:
        return None, None
    if not isinstance(pumps, list):
        raise ValueError("settings.pumps 는 배열이어야 합니다.")
    if not pumps:
        raise ValueError("가동할 펌프를 최소 1대 선택하세요.")

    pump_hz = {}
    for item in pumps:
        if not isinstance(item, dict):
            raise ValueError(f"settings.pumps 의 항목이 객체가 아닙니다: {item!r}")

        no_raw = item.get('pumpNo')
        try:
            pump_no = int(no_raw)
        except (TypeError, ValueError):
            raise ValueError(f"펌프 번호가 정수가 아닙니다: {no_raw!r}")

        hz_raw = item.get('hz')
        if hz_raw is None or hz_raw == '':
            raise ValueError(f"{pump_no}호기의 주파수(Hz)가 비어 있습니다.")
        try:
            hz = float(hz_raw)
        except (TypeError, ValueError):
            raise ValueError(f"{pump_no}호기의 주파수(Hz)가 숫자가 아닙니다: {hz_raw!r}")

        if pump_no in pump_hz:
            raise ValueError(f"{pump_no}호기가 중복 지정됐습니다.")
        pump_hz[pump_no] = hz

    if not pump_hz:
        raise ValueError("가동할 펌프를 최소 1대 선택하세요.")

    pump_comb = ",".join(str(n) for n in sorted(pump_hz))
    return pump_comb, pump_hz


class SimulationSIView(BaseView):
    def post(self):
        """새로운 SI 시뮬레이션을 생성합니다."""
        try:
            # 1. 프론트의 이중 인코딩된 데이터를 받음
            data = request.get_json(force=True)
            if not data:
                return api_error(message="요청 본문에 데이터가 없습니다.", code=400)
            
            # 2. 'body' 키의 '문자열' 값을 가져옴
            json_string = data.get('body')
            if not json_string:
                 return api_error(message="요청 본문에 'body' 데이터가 없습니다.", code=400)

            # 3. '문자열'을 Python 딕셔너리로 다시 파싱
            try:
                parsed_data = json.loads(json_string)
            except json.JSONDecodeError:
                return api_error(message="body 데이터가 유효한 JSON 문자열이 아닙니다.", code=400)

            # 4. 'settings' 객체를 가져옴
            settings_data = parsed_data.get('settings')
            if not settings_data:
                return api_error(message="body JSON 내부에 'settings' 객체가 없습니다.", code=400)

            # 5. 'ts' 값 추출 (선택 사항)
            ts_str = settings_data.get('ts') 
            
            # 6. 펌프 조합과 펌프별 주파수(Hz) 추출
            #    신규(군산): settings.pumps = [{"pumpNo": 1, "hz": 55}, ...]
            #    기존(고산): settings.selectedCombo.rawMinConfig.PUMP_COMB (Hz 없음)
            #    신규 키가 있으면 그걸 쓰고, 없으면 기존 경로로 떨어진다.
            try:
                pump_comb, pump_hz = _parse_selected_pumps(settings_data)
            except ValueError as e:
                return api_error(message=str(e), code=400)

            if pump_comb is None:
                try:
                    pump_comb = settings_data.get('selectedCombo').get('rawMinConfig').get('PUMP_COMB')
                except AttributeError:
                    # .get('selectedCombo')가 None이거나 .get('rawMinConfig')가 None일 경우
                    return api_error(message="데이터 구조 오류: selectedCombo 또는 rawMinConfig가 없습니다.", code=400)

            # 7. 데이터 검증 (pump_comb는 필수)
            if not pump_comb:
                # 키는 있지만 값이 비어있거나 None일 경우
                return api_error(message="settings.selectedCombo.rawMinConfig.PUMP_COMB 값이 없습니다.", code=400)

            # 8. (이하 동일)
            target_ts = None
            if ts_str:
                try:
                    target_ts = datetime.fromisoformat(ts_str)
                except ValueError:
                    return api_error(message="잘못된 시간 형식입니다.", code=400)
                    
            logger.info(
                f"SI 시뮬레이션 요청 - ts: {target_ts or '최신 시각'}, "
                f"pump_comb: {pump_comb}, pump_hz: {pump_hz or '(미지정 - 실측 Hz 사용)'}"
            )

            # 9. 서비스 함수로 'PUMP_COMB 문자열' ("2,4,6,7,11")을 전달
            #    pump_hz 는 군산 엔진만 쓴다. 고산 서비스는 인자만 받고 무시한다.
            result = get_engine().run_si_simulation(
                ts=target_ts,
                pump_comb=pump_comb, # 👈 이제 딕셔너리 객체가 아닌 문자열이 전달됨
                rule_pipe_id=10,
                pump_hz=pump_hz
            )
            
            return api_success(data=result, message=messages.INSERT_SUCCESS)
                
        except EngineBusyError as e:
            # 군산 엔진은 동시 실행이 안 된다(os.chdir 가 프로세스 전역).
            # 오래 기다리게 두는 대신 바로 돌려주고 재시도를 유도한다.
            logger.warning(f"SI 시뮬레이션 거절 (엔진 사용 중): {e}")
            return api_error(message=str(e), code=503)
        except Exception as e:
            logger.error(f"SI 시뮬레이션 실행 중 오류: {e}", exc_info=True)
            return api_error(message=str(e), code=500)

class BatchSimulationView(BaseView):
    def post(self):
        """
        주어진 시간 범위(start_ts, end_ts)에 대해
        5분 간격으로 'mo' 시뮬레이션을 배치 실행합니다.
        """
        try:
            # 1. 표준 JSON 데이터를 받음 ({"start_ts": "...", "end_ts": "..."})
            data = request.get_json()
            if not data:
                return api_error(message="요청 본문에 데이터가 없습니다.", code=400)

            # 2. 'start_ts'와 'end_ts' 값 추출
            start_ts_str = data.get('start_ts')
            end_ts_str = data.get('end_ts')

            if not start_ts_str or not end_ts_str:
                return api_error(message="'start_ts'와 'end_ts'는 필수입니다.", code=400)

            # 3. 'ts' 값들을 datetime 객체로 변환
            try:
                start_dt = datetime.fromisoformat(start_ts_str)
                end_dt = datetime.fromisoformat(end_ts_str)
            except ValueError:
                return api_error(message="잘못된 시간 형식입니다. ISO 8601 형식(YYYY-MM-DDTHH:MM:SS)을 사용하세요.", code=400)
            
            if start_dt > end_dt:
                return api_error(message="시작 시간이 종료 시간보다 늦을 수 없습니다.", code=400)

            logger.info(f"MO 배치 시뮬레이션 요청 - 기간: {start_dt} ~ {end_dt}")

            # 4. 서비스 함수 호출 (epa_service.py의 해당 함수)
            result = get_engine().run_mo_simulation_for_range(
                start_ts=start_dt,
                end_ts=end_dt
            )
            
            return api_success(data=result, message="배치 시뮬레이션 작업이 완료되었습니다.")
                
        except EngineRequestError as e:
            # 요청 구간이 엔진이 감당할 수 없는 길이다. 서버 잘못이 아니다.
            logger.warning(f"MO 배치 요청 거절: {e}")
            return api_error(message=str(e), code=400)
        except EngineBusyError as e:
            logger.warning(f"MO 배치 거절 (엔진 사용 중): {e}")
            return api_error(message=str(e), code=503)
        except Exception as e:
            logger.error(f"MO 배치 시뮬레이션 실행 중 오류: {e}", exc_info=True)
            return api_error(message=str(e), code=500)

# --- URL 규칙 추가 ---
bp.add_url_rule('/simulations/si', view_func=SimulationSIView.as_view('run_si_simulation_api'))

# --- [신규 추가] MO 배치 시뮬레이션 API 엔드포인트 ---
bp.add_url_rule('/simulations/mo/batch', view_func=BatchSimulationView.as_view('run_mo_simulation_batch_api'))

@bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    if not scheduler.running:
        return api_success(data={"status": "stopped", "jobs": []})
    
    jobs = [{"id": job.id, "name": job.name, "trigger": str(job.trigger), "next_run_time": str(job.next_run_time)} for job in scheduler.get_jobs()]
    return api_success(data={"status": "running", "jobs": jobs})

@bp.route('/monitoringTest', methods=['GET'])
def monitoringTest():
    ts = "2025-10-21 17:56:00"
    get_engine().run_mo_simulation(datetime.fromisoformat(ts))
    
    return api_success(data={"status": "running"})
