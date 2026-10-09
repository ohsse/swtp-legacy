from .Tibero import Tibero
from wntr.epanet.util import FlowUnits, from_si, HydParam

class ReportData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

    def saveReportData(self, wn, results, titleData):
        self.wn = wn
        self.results = results
        self.titleData = titleData

        try:
            # 01. 리포트 번호 조회
            self.selectReportMaster()

            # 02.관망해석결과_마스터 등록
            self.insertReportMaster()

            # 03. 관망해석결과_Nodes 등록
            self.insertReportNodes()

            # 04. 관망해석결과_Links 등록
            self.insertReportLinks()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise

    # 01. 리포트 번호 조회
    def selectReportMaster(self):
        try:
            query = "SELECT 'RPT'||TO_CHAR(SYSTIMESTAMP,'YYYYMMDDHH24MISSFF4') FROM DUAL;"
            self.cursor.execute(query)
            reportNumber = self.cursor.fetchone()
            self.titleData.reportNumber = reportNumber[0]
        except Exception as ex:
            print(ex)
            raise

    # 02.관망해석결과_마스터 등록
    def insertReportMaster(self):
        try:
            query = ("INSERT INTO WH_RPT_MASTER										 "
                     "	(															 "
                     "		RPT_NUMBER,												 "
                     "		MGC_CD,													 "
                     "		INP_NUMBER,												 "
                     "		RPT_DATE,												 "
                     "		TITLE,													 "
                     "		AUTO_MANUAL,											 "
                     "		TARGET_DATE												 "
                     "	) 															 "
                     "VALUES														 "
                     "	(															 "
                     "		?,      "
                     "		?, 										            	 "
                     "		?, 					            						 "
                     "		NVL(TO_DATE(?,'YYYYMMDDHH24MI'),SYSDATE),	        	 "
                     "		?,                                                       "
                     "		'N', 				            						 "
                     "		?								            			 "
                     "	)															 ;")

            self.cursor.execute(query, self.titleData.reportNumber, self.titleData.mgcCd, self.titleData.inpNumber, self.titleData.coltDt,
                                self.titleData.title, self.titleData.coltDt)
        except Exception as ex:
            print(ex)
            raise

    # 03. 관망해석결과_Nodes 등록
    def insertReportNodes(self):
        wn = self.wn
        results = self.results
        result_demand = results.node['demand']
        result_head = results.node['head']
        result_pressure = results.node['pressure']
        result_quality = results.node['quality']
        analysis_time = '00:00:00'

        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        nodeList = wn.node_name_list
        for nodeId in nodeList:
            noObj = wn.get_node(nodeId)

            # basedemand
            basedemand = 0.0

            if noObj.node_type == 'Reservoir':
                # elevation(base_haed)
                elevation = round(noObj.base_head, 2)
            elif noObj.node_type == 'Tank':
                # elevation
                elevation = round(noObj.elevation, 2)
            else: # Junction
                # elevation
                elevation = round(noObj.elevation, 2)

                # basedemand
                demands = noObj.demand_timeseries_list
                if len(demands) > 0:
                    basedemand = round(from_si(flow_unit, demands[len(demands) - 1].base_value, HydParam.Demand), 2)

            # for time in results.node['pressure'].T.dtypes.axes[0]:
            # demand
            demand_to_si = result_demand.loc[:, nodeId]
            demand = round(from_si(flow_unit, demand_to_si, HydParam.Demand), 2)[0]

            # head
            head = round(result_head.loc[:, nodeId], 2)[0]

            # pressure
            pressure = round(result_pressure.loc[:, nodeId], 2)[0]

            # quality
            quality = round(result_quality.loc[:, nodeId], 2)[0]

            try:
                query = ("INSERT INTO WH_RPT_NODES ( "
                         "      RPT_NUMBER, INP_NUMBER, NODE_ID "
                         "    , ANALYSIS_TIME, ELEVATION, BASEDEMAND "
                         "    , DEMAND, HEAD, PRESSURE"
                         "    , QUALITY "
                         ") VALUES ( "
                         "    ?, ?, ?, ?, ?, ?, ?, ?, ?, ? "
                         ");")
                self.cursor.execute(query, self.titleData.reportNumber, self.titleData.inpNumber, nodeId,
                                    analysis_time, str(elevation), str(basedemand),
                                    str(demand), str(head), str(pressure),
                                    str(quality))
            except Exception as ex:
                print(ex)
                raise

    # 04. 관망해석결과_Links 등록
    def insertReportLinks(self):
        wn = self.wn
        results = self.results
        # result_quality = results.link['quality']
        result_flowrate = results.link['flowrate']
        result_velocity = results.link['velocity']
        result_headloss = results.link['headloss']
        # result_status = results.link['status']
        # result_setting = results.link['setting']
        # result_friction_factor = results.link['friction_factor']
        # result_reaction_rate = results.link['reaction_rate']
        analysis_time = '00:00:00'

        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        linkList = wn.link_name_list
        for linkId in linkList:
            liObj = wn.get_link(linkId)

            diameter = 0.0
            length = 0.0
            roughness = 0.0

            if liObj.link_type == 'Pipe':
                diameter = round(from_si(flow_unit, liObj.diameter, HydParam.PipeDiameter), 2)
                length = round(from_si(flow_unit, liObj.length, HydParam.Length), 2)
                roughness = round(from_si(flow_unit, liObj.roughness, HydParam.RoughnessCoeff), 2)

                # headloss
                headloss = round(from_si(flow_unit, result_headloss.loc[:, linkId], HydParam.HeadLoss), 2)[0]
            elif liObj.link_type == 'Pump':
                roughness = liObj.base_speed

                # headloss
                headloss = round(result_headloss.loc[:, linkId], 2)[0]
            else: #Valve
                diameter = round(from_si(flow_unit, liObj.diameter, HydParam.PipeDiameter), 2)

                # headloss
                headloss = round(from_si(flow_unit, result_headloss.loc[:, linkId], HydParam.HeadLoss), 2)[0]

            # flow
            flow = round(from_si(flow_unit, result_flowrate.loc[:, linkId], HydParam.Flow), 2)[0]

            # velocity
            velocity = round(from_si(flow_unit, result_velocity.loc[:, linkId], HydParam.Velocity), 2)[0]

            try:
                query = ("INSERT INTO WH_RPT_LINKS ( "
                         "      RPT_NUMBER, INP_NUMBER, LINK_ID "
                         "    , ANALYSIS_TIME, DIAMETER, LENGTH "
                         "    , ROUGHNESS, FLOW, VELOCITY "
                         "    , HEADLOSS "
                         ") VALUES ( "
                         "    ?, ?, ?, ?, ?, ?, ?, ?, ?, ? "
                         ");")
                self.cursor.execute(query, self.titleData.reportNumber, self.titleData.inpNumber, linkId,
                                    analysis_time, str(diameter), str(length),
                                    str(roughness), str(flow), str(velocity),
                                    str(headloss))
            except Exception as ex:
                print(ex)
                raise
