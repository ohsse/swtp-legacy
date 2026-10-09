from datetime import datetime
import json
import logging
import traceback
from flask import Blueprint, request
from app.services import web_service
from app.routes.base_view import BaseView
from app.utils.response import api_success, api_error
from app.utils import messages

from . import bp

logger = logging.getLogger(__name__)

@bp.route('/web/nodes', methods=['GET'])
def get_map_nodes():
    """지도에 표시할 노드 정보를 조회합니다."""
    try:
        nodes = web_service.load_map_nodes()
        return api_success(data=nodes, message=messages.SELECT_SUCCESS)
        
    except Exception as e:
        traceback.print_exc()
        return api_error(message=str(e), code=500) 
    
    
@bp.route('/web/network', methods=['GET'])
def get_network_geojson():
    """지도에 그릴 관망 형상을 현재 INP 에서 만들어 GeoJSON 으로 조회합니다."""
    try:
        data = web_service.load_network_geojson()
        return api_success(data=data, message=messages.SELECT_SUCCESS)

    except Exception as e:
        traceback.print_exc()
        return api_error(message=str(e), code=500)


@bp.route('/web/tanks', methods=['GET'])
def get_tank_nodes():
    """탱크 노드 정보를 조회합니다."""
    try:
        nodes = web_service.load_tank_nodes()
        return api_success(data=nodes, message=messages.SELECT_SUCCESS)
        
    except Exception as e:
        traceback.print_exc()
        return api_error(message=str(e), code=500)
    
@bp.route('/web/monitoring', methods=['GET'])
def get_monitoring_data():
    """모니터링 데이터를 조회합니다."""
    try:
        data = web_service.load_monitoring_data()
        return api_success(data=data, message=messages.SELECT_SUCCESS)
        
    except Exception as e:
        traceback.print_exc()
        return api_error(message=str(e), code=500)
    
    
@bp.route('/web/monitoring/chart', methods=['GET'])
def get_chart_data():
    """특정 Junction ID의 시계열 차트 데이터를 조회합니다."""
    try:
        junction_id = request.args.get('junction_id')
        if not junction_id:
            return api_error(message="'junction_id' 파라미터가 필요합니다.", code=400)

        data = web_service.load_chart_data(junction_id)
        
        if not data or not data.get("ts"):
            return api_error(message=f"'{junction_id}'에 대한 데이터를 찾을 수 없습니다.", code=404)
        
        return api_success(data=data, message=messages.SELECT_SUCCESS)
        
    except Exception as e:
        logger.error(f"차트 데이터 조회 중 오류 발생: {e}", exc_info=True)
        return api_error(message=str(e), code=500)
    
    
@bp.route('/web/updateRate', methods=['POST'])
def update_reservoir_flow_rates():
    """
    관망해석 유량 설정을 업데이트합니다.
    단일 객체 또는 객체의 배열을 Body로 받을 수 있습니다.
    """
    
    try:
        data = request.get_json(force=True)
        if not data:
            return api_error(message="요청 본문에 데이터가 없습니다.", code=400)
        
        dataArray = data['body']
        affected_rows = web_service.update_flow_rates(dataArray)
        
        return api_success(data={"updated_rows": affected_rows}, message=messages.SAVE_SUCCESS)
        
    except ValueError as ve:
        logger.warning(f"유량 설정 업데이트 실패 (잘못된 요청): {ve}")
        return api_error(message=str(ve), code=400)
    except Exception as e:
        logger.error(f"유량 설정 업데이트 중 서버 오류 발생: {e}", exc_info=True)
        return api_error(message=str(e), code=500)
    
@bp.route('/web/simulration', methods=['GET'])
def load_simulation_data():
    """시뮬레이션 데이터를 조회합니다."""
    try:
        data = web_service.load_simulation_data()
        return api_success(data=data, message=messages.SELECT_SUCCESS)
        
    except Exception as e:
        traceback.print_exc()
        return api_error(message=str(e), code=500)
    
@bp.route('/web/simulration/pumpComb', methods=['GET'])
def getSimulrationPumpComb():
    """_summary_
    관망분석 시뮬레이션 펌프 조합 
    """
    
    try:
        pump_grp = request.args.get('pump_grp')
        if not pump_grp:
            return api_error(message="'pump_grp' 파라미터가 필요합니다.", code=400)

        data = web_service.get_pump_comb(pump_grp)
        
        if not data:
            return api_error(message=f"'{pump_grp}'에 대한 데이터를 찾을 수 없습니다.", code=404)
        
        return api_success(data=data, message=messages.SELECT_SUCCESS)
        
    except Exception as e:
        logger.error(f"차트 데이터 조회 중 오류 발생: {e}", exc_info=True)
        return api_error(message=str(e), code=500)