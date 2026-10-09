from wntr.epanet.util import FlowUnits, to_si, HydParam
import pandas as pd
from flask import current_app
from .Tibero import Tibero


class MeasureLowFlowData:
    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()
        self.riskMapDict = {}
        self.pipeList = []

    def getMeasureLowFlowData(self, wn, titleData, riskMapData):
        try:
            self.titleData = titleData
            self.riskMapDict = riskMapData.riskMapDict

            # 01.관로별 평균 사용량 조회
            self.pipeAvgUsageList()

            # 02.데이터 셋팅
            self.setWnMeasureData(wn)

            self.conn.close()
        except Exception as ex:
            current_app.logger.error(ex)
            self.conn.close()
            raise

    # 01.관로별 평균 사용량 조회
    # 관로에 연결된 수용가의 기간별 총 사용량에 대한 관로별 평균값 조회
    def pipeAvgUsageList(self):
        query = None

        try:
            query = ("SELECT "
                     "    PTBWTR_PLINE_TPJM_MNG_NO "
                     "  , AVG(SUM_WSUSEVOL) AS AVG_WSUSEVOL "
                     "FROM ( "
                     "	SELECT "
                     "		PP.PTBWTR_PLINE_TPJM_MNG_NO /* 시설물관리ID = 파이프ID */ "
                     "	  , ST.STYM /* 검침년월 */ "
                     "	  , SUM(ST.WSUSEVOL) AS SUM_WSUSEVOL /* 검침량 */ "
                     "	FROM TM_RM020001 RM "
                     "	   , WTL_PIPE_LS PP "
                     "	   , WTL_SPLY_LS SP 		/* 하위 배수관들을 상위로 가지는 급수관 */ "
                     "	   , WTL_META_PS MT 		/* 급수관들을 상위로 가지는 수도미터 */ "
                     "	   , WI_STWCHRG ST "
                     "	WHERE 1 = 1 "
                     "	  AND RM.MNG_DEPT_CD = PP.MNG_DEPT_CD "
                     "	  AND PP.OBJECTID = SP.PIPE_OBJECTID "
                     "	  AND SP.OBJECTID = MT.SPLY_OBJECTID "
                     "	  AND MT.CSTMR_NO = ST.DMNO "
                     "	  AND RM.ANALS_NO = ? "
                     "	  AND ST.STYM BETWEEN ? AND ? "
                     "	GROUP BY PP.PTBWTR_PLINE_TPJM_MNG_NO, ST.STYM "
                     ") "
                     "GROUP BY PTBWTR_PLINE_TPJM_MNG_NO;")
            self.cursor.execute(query, self.riskMapDict["analsNo"], self.riskMapDict["lowSpfldStrtDe"][0:6], self.riskMapDict["lowSpfldEndDe"][0:6])
            self.pipeList = self.cursor.fetchall()
        except Exception as ex:
            current_app.logger.error(ex)
            raise


    # 02.데이터 셋팅
    def setWnMeasureData(self, wn):
        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        for pipeDict in self.pipeList:
            try:
                pipeObj = wn.get_link(pipeDict[0])
                noObj = pipeObj.end_node # 하위관로
                demands = noObj.demand_timeseries_list
                if len(demands) > 0:
                    demands[0].base_value = to_si(flow_unit, float(pipeDict[1]), HydParam.Demand)

            except Exception as ex:
                current_app.logger.error('[MeasureLowFlowData-setWnMeasureData] Not Found Pipe Id: ' + str(ex))
                #raise

