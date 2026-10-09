from wntr.epanet.util import FlowUnits, to_si, HydParam
from wntr.network.model import LinkStatus

from .Tibero import Tibero

class MeasureData:
    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()
        self.junctionDict = {}
        self.nodeTagDict = {}
        self.reservoirPresDict = {}
        self.pumpStatusDict = {}

    def getMeasureData(self, wn, titleData):
        try:
            self.titleData = titleData

            # 01.절점 실시간 유량값 조회
            self.realTimeJunctonsList()

            # 02.관로유량 있는 절점은 기저용수수요량 0으로 입력.
            self.nodeTagList()

            # 03.배수지 수위 값 조회
            self.reservoirLevlList()

            # 배수지 압력 조회 및 수위값 계산(압력*10)
            self.reservoirPresList()

            # 04.펌프 가동 상태 조회
            self.pumpStatusList()

            # 05.실시간 데이터 셋팅
            self.setWnMeasureData(wn)

            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.close()
            raise

    # 01.절점 실시간 유량값 조회
    # 절점과 매핑된 유량 태그의 실시간 값을 절점의 basedemand에 입력
        # demands 데이터를 가져옴
    def realTimeJunctonsList(self):
        query = None

        try:
            if self.titleData.areaSeCd and self.titleData.areaSeCd == 'G':
                query = ("SELECT "
                         "	ID, SUM(BASE_DEMAND) BASE_DEMAND					                            	 "
                         "FROM(																					 "
                         "	SELECT 																				 "
                         "		WJ.INP_NUMBER,																	 "
                         "		WJ.ID,																			 "
                         "		WJ.ELEVATION,																	 "
                         "		ROUND(NVL(VALU,0),5) BASE_DEMAND,												 "
                         "		WJ.PATTERN_ID,																	 "
                         "		WJ.TAG_SN,																		 "
                         "		TO_CHAR(FLUX.COLT_DT,'YYYYMMDDHH24MI') COLT_DT									 "
                         "	FROM 																				 "
                         "	(																					 "
                         "		SELECT WJ.*,WJT.TAG_SN,WJT.TAG_SE_CD											 "
                         "		FROM WH_JUNCTIONS WJ , WH_NODE_TAG WJT											 "
                         "		WHERE  WJ.INP_NUMBER = WJT.INP_NUMBER(+)										 "
                         "		AND WJ.ID = WJT.ID(+)															 "
                         "		AND WJ.INP_NUMBER = ?		                            						 "
                         "		AND WJT.TAG_SE_CD = 'DFRI' --수용가 유량값만 절점에 업데이트					    	 "
                         "	)WJ																					 "
                         "	,(																					 "
                         "		SELECT TAG_SN																	 "
                         "		, COLT_DT																		 "
                         "		, VALU																			 "
                         "		FROM IF_COLT_FLUX																 "
                         "		WHERE COLT_DT = TO_DATE(?,'YYYYMMDDHH24MI')					        			 "
                         "	) FLUX																				 "
                         "	WHERE WJ.TAG_SN = FLUX.TAG_SN														 "
                         ")																						 "
                         "GROUP BY INP_NUMBER,ID,ELEVATION,PATTERN_ID											;")
                self.cursor.execute(query,  self.titleData.inpNumber, self.titleData.coltDt)
            elif self.titleData.areaSeCd and self.titleData.areaSeCd == 'J':
                query = ("SELECT																																 "
                         "	ID,																																	 "
                         "	DECODE(SUM_BASE_DEMAND,0,0,NVL(VALU,0)*(BASE_DEMAND/SUM_BASE_DEMAND)) BASE_DEMAND													 "
                         "FROM 																																	 "
                         "(																																		 "
                         "	SELECT WJ.*,WJF.FCLTY_CD,																											 "
                         "	SUM(WJ.BASE_DEMAND) OVER (PARTITION BY WJF.FCLTY_CD) SUM_BASE_DEMAND																 "
                         "	FROM WH_JUNCTIONS WJ , WH_JUNCTION_FCLTY WJF																						 "
                         "	WHERE  WJ.INP_NUMBER = WJF.INP_NUMBER(+)																							 "
                         "	AND WJ.ID = WJF.ID(+)																												 "
                         "	AND WJ.INP_NUMBER = ?	                            																				 "
                         ")WJ																																	 "
                         ",(																																	 "
                         "	SELECT C.COLT_DT																													 "
                         "	, A.FCLTY_CD																														 "
                         "	, B.TAG_SE_CD																														 "
                         "	, D.MGC_CD																															 "
                         "	, SUM (																																 "
                         "		CASE WHEN D.FCLTY_SE_CD = 'KK' AND A.IN_SE_CD = 'S' THEN (CASE WHEN NVL(A.CALC_TYPE, '+') = '+' THEN C.VALU ELSE -C.VALU END)	 "
                         "		WHEN D.FCLTY_SE_CD = 'BL' AND A.IN_SE_CD = 'I' THEN (CASE WHEN NVL(A.CALC_TYPE, '+') = '+' THEN C.VALU ELSE -C.VALU END)		 "
                         "		END																																 "
                         "	) VALU																																 "
                         "	FROM CM_FCLTY_TAG A, IF_TAG B, IF_COLT_FLUX C, CM_FCLTY D																			 "
                         "	WHERE A.TAG_SN = B.TAG_SN																											 "
                         "	AND B.TAG_SN = C.TAG_SN																												 "
                         "	AND A.FCLTY_CD = D.FCLTY_CD																											 "
                         "	AND B.TAG_SE_CD = 'FRI'																												 "
                         "	AND C.COLT_DT = (SELECT MAX(COLT_DT) FROM IF_COLT_FLUX) 																			 "
                         "	AND D.MGC_CD = ?                        																							 "
                         "	GROUP BY C.COLT_DT, A.FCLTY_CD, B.TAG_SE_CD, D.MGC_CD																				 "
                         ") FLUX																																 "
                         "WHERE WJ.FCLTY_CD = FLUX.FCLTY_CD 																									;")
                self.cursor.execute(query, self.titleData.inpNumber, self.titleData.mgcCd)

            junctionList = self.cursor.fetchall()
            for row in junctionList:
                self.junctionDict[str(row[0])] = str(row[1])

        except Exception as ex:
            print(ex)
            raise

    # 02.관로유량 있는 절점은 기저용수수요량 0으로 입력.
        # inp file의 모든 id에 해당하는 node1 값을 가져온다
    def nodeTagList(self):
        try:
            query = ("SELECT ID																										 "
                     "FROM(																											 "
                     "	SELECT 																										 "
                     "		NT.INP_NUMBER,																							 "
                     "		NT.ID,																									 "
                     "		NT.TAG_SN,																								 "
                     "		NT.TAG_SE_CD,																							 "
                     "		(CASE WHEN NT.TAG_SE_CD='CLI' THEN '잔류염소'															 "
                     "			WHEN NT.TAG_SE_CD='DFRI' THEN '수용가유량'															 "
                     "			WHEN NT.TAG_SE_CD='FLOW' THEN '계량기'																 "
                     "			WHEN NT.TAG_SE_CD='FRI' THEN '관로유량'																 "
                     "			WHEN NT.TAG_SE_CD='LEI' THEN '수위'																	 "
                     "			WHEN NT.TAG_SE_CD='PMB' THEN '펌프'																	 "
                     "			WHEN NT.TAG_SE_CD='PRI' THEN '압력'																	 "
                     "			WHEN NT.TAG_SE_CD='TBI' THEN '탁도' END																 "
                     "		)TAG_SE_NM,																								 "
                     "		(SELECT X FROM WH_COORDINATES WC WHERE NT.INP_NUMBER = WC.INP_NUMBER AND NT.COORD_ID = WC.ID) X ,		 "
                     "		(SELECT Y FROM WH_COORDINATES WC WHERE NT.INP_NUMBER = WC.INP_NUMBER AND NT.COORD_ID = WC.ID) Y			 "
                     "	FROM(																										 "
                     "		SELECT 																									 "
                     "		NT.INP_NUMBER,																							 "
                     "		NT.ID,																									 "
                     "		NT.TAG_SN,																								 "
                     "		NT.TAG_SE_CD,																							 "
                     "		(																										 "
                     "			CASE WHEN TAG_SE_CD = 'PMB' THEN (SELECT NODE1														 "
                     "			FROM WH_PUMPS WP																					 "
                     "			WHERE NT.INP_NUMBER =WP.INP_NUMBER AND NT.ID = WP.ID)												 "
                     "			ELSE NT.ID END																						 "
                     "		)COORD_ID																								 "
                     "		FROM WH_NODE_TAG NT																						 "
                     "	)NT																											 "
                     ")NT																											 "
                     "WHERE NT.INP_NUMBER = ?									            										 "
                     "  AND X IS NOT NULL																							 "
                     "  AND NT.TAG_SE_CD = 'FRI'																					;")

            # self.cursor.execute(query,  'INP20200910104257') # TEST
            self.cursor.execute(query,  self.titleData.inpNumber)

            nodeTagList = self.cursor.fetchall()
            for row in nodeTagList:
                self.nodeTagDict[str(row[0])] = str(row[0])

        except Exception as ex:
            print(ex)
            raise

    # 03.배수지 수위 값 조회
        # elevation (elev) 값을 가져온다 
    def reservoirLevlList(self):
        try:
            query = ("SELECT													 "
                     "	T1.ID,													 "
                     "	MAX(T2.VALU) VALU /* 배수지 MAX수위(계측) */		    	 "
                     "FROM WH_NODE_TAG T1,IF_COLT_LEVL T2						 "
                     "WHERE T1.TAG_SE_CD='LEI'									 "
                     "AND T1.TAG_SN = T2.TAG_SN 								 "
                     "AND INP_NUMBER = ?        								 "
                     "AND T2.COLT_DT = TO_DATE (?, 'YYYYMMDDHH24MI') 	         "
                     "GROUP BY T1.ID,T2.COLT_DT									 ;")

            # self.cursor.execute(query,  'INP20230320144229', '202306010000') # TEST
            self.cursor.execute(query,  self.titleData.inpNumber, self.titleData.coltDt)

            reservoirLevlList = self.cursor.fetchall()
            for row in reservoirLevlList:
                if str(row[1]):
                    self.reservoirPresDict[str(row[0])] = str(row[1])

        except Exception as ex:
            print(ex)
            raise

    # 배수지 수위 값 조회(압력*10)
        # elevation (elev) 값을 가져온다 
    def reservoirPresList(self):
        try:
            query = ("SELECT												 "
                     "	T1.ID,												 "
                     "	MAX(T2.VALU*10) VALU /* 배수지 MAX수위(계측) */		 "
                     "FROM WH_NODE_TAG T1,IF_COLT_PRES T2					 "
                     "WHERE T1.TAG_SE_CD='PRI'								 "
                     "AND T1.TAG_SN = T2.TAG_SN 							 "
                     "AND INP_NUMBER = ?        							 "
                     "AND T2.COLT_DT = TO_DATE (?, 'YYYYMMDDHH24MI')         "
                     "GROUP BY T1.ID,T2.COLT_DT								 ;")

            # self.cursor.execute(query,  'INP20230320144229', '202306010000') # TEST
            self.cursor.execute(query,  self.titleData.inpNumber, self.titleData.coltDt)

            reservoirPresList = self.cursor.fetchall()
            for row in reservoirPresList:
                if not self.reservoirPresDict.get(str(row[0])) and str(row[1]):
                    self.reservoirPresDict[str(row[0])] = str(row[1])

        except Exception as ex:
            print(ex)
            raise

    # 04.펌프 가동 상태 조회
        # pump status 정보를 가져옴 !
    def pumpStatusList(self):
        try:
            query = ("SELECT											"
                     "	T1.ID,											"
                     "	T2.VALU /* 펌프가동상태 */						"
                     "FROM WH_NODE_TAG T1,IF_COLT_POWR T2				"
                     "WHERE T1.TAG_SE_CD='PMB'							"
                     "AND T1.TAG_SN = T2.TAG_SN 						"
                     "AND INP_NUMBER = ?								"
                     "AND T2.COLT_DT = TO_DATE (?, 'YYYYMMDDHH24MI') 	;")

            # self.cursor.execute(query,  'INP20230320144229', '202306010000') # TEST
            self.cursor.execute(query,  self.titleData.inpNumber, self.titleData.coltDt)

            pumpStatusList = self.cursor.fetchall()
            for row in pumpStatusList:
                if str(row[1]):
                    self.pumpStatusDict[str(row[0])] = str(row[1])

        except Exception as ex:
            print(ex)
            raise

    # 05.실시간 데이터 셋팅
        # 가져온 정보들을 wn에 세팅해준다(기존 inp file에서 값을 바꿔줌)
    def setWnMeasureData(self, wn):
        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        junctionList = wn.junction_name_list
        for junctionId in junctionList:
            noObj = wn.get_node(junctionId)

            # Demand Set
            demands = noObj.demand_timeseries_list
            if len(demands) > 0:
                if junctionId in self.junctionDict:
                    dm = self.junctionDict[junctionId]
                    # noObj.base_demand = dm # noObj.base_demand is readonly
                    demands[0].base_value = to_si(flow_unit, float(dm), HydParam.Demand)

            if junctionId in self.nodeTagDict:
                # noObj.base_demand = 0.0 # noObj.base_demand is readonly
                demands[0].base_value = to_si(flow_unit, float(0), HydParam.Demand)

            # Elevation Set
            if junctionId in self.reservoirPresDict:
                level = self.reservoirPresDict[junctionId]
                wn.get_node(junctionId).elevation = to_si(flow_unit, float(level), HydParam.Elevation)

        # Pump status Set
        pumpList = wn.pump_name_list
        for pumpId in pumpList:
            puObj = wn.get_link(pumpId)

            if pumpId in self.pumpStatusDict:
                pumpVal = self.pumpStatusDict[pumpId]

                if pumpVal == LinkStatus.Open:
                    puObj._user_status = LinkStatus.Open
                    puObj.initial_status = LinkStatus.Open
                else:
                    puObj._user_status = LinkStatus.Closed
                    puObj.initial_status = LinkStatus.Closed
