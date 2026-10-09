from .Tibero import Tibero
from wntr.epanet.util import FlowUnits, from_si, HydParam

class ReportLowFlowData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()
        self.riskMapDict = {}

    def saveReportLowFlowData(self, wn, results, titleData, riskMapData):
        self.wn = wn
        self.results = results
        self.titleData = titleData
        self.riskMapDict = riskMapData.riskMapDict

        try:
            # 01.온라인 관망해석(수리모델-저유속) 파이프 저장
            self.insertReportLowFlowPipe()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise


    # 01.온라인 관망해석(수리모델-저유속) 파이프 저장
    # WTL_PIPE_LS_TEMP.OBJECTID, PTBWTR_PLINE_TPJM_MNG_NO  join.
    def insertReportLowFlowPipe(self):
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

            if liObj.link_type == 'Pipe':
                flowList = []
                velocityList = []
                for time in results.link['velocity'].T.dtypes.axes[0]:
                    # flow
                    flow = from_si(flow_unit, result_flowrate.loc[time, linkId], HydParam.Flow)
                    flowList.append(flow)

                    # velocity
                    velocity = round(from_si(flow_unit, result_velocity.loc[time, linkId], HydParam.Velocity), 2)
                    velocityList.append(velocity)

                # flowList 평균
                flowAvg = round(sum(flowList) / len(flowList), 3)

                # velocityList 평균
                velocityAvg = round(sum(velocityList) / len(velocityList), 3)

                # 상세 존재여부 체크
                try:
                    query = ("SELECT A.ANALS_NO || '', A.MNG_DEPT_CD, A.CMPTN_ID, A.UPDUSR_ID "
                             "FROM WATERNET.TD_RM020002 A "
                             "   , WATERNET.WTL_PIPE_LS B "
                             "WHERE 1 = 1 "
                             "  AND A.MNG_DEPT_CD = B.MNG_DEPT_CD "
                             "  AND A.CMPTN_ID = B.OBJECTID "
                             "  AND A.ANALS_NO = ? "
                             "  AND B.PTBWTR_PLINE_TPJM_MNG_NO = ?;")
                    self.cursor.execute(query, self.riskMapDict["analsNo"], linkId)
                    list = self.cursor.fetchall()

                    # 파이프 평균값 Merge Update
                    if len(list) > 0:
                        try:
                            query = ("UPDATE WATERNET.TD_RM020002 A SET "
                                     "      AVG_SPFLD = ? "
                                     "    , AVG_FLUX = ? "
                                     "    , UPDUSR_ID = ? "
                                     "    , UPDT_DT = SYSDATE "
                                     "WHERE 1 = 1 "
                                     "  AND A.ANALS_NO = ? "
                                     "  AND A.MNG_DEPT_CD = ? "
                                     "  AND A.CMPTN_ID = ? ;")
                            self.cursor.execute(query, velocityAvg, flowAvg, list[0][3], list[0][0], list[0][1], list[0][2])
                        except Exception as ex:
                            print(ex)
                            raise
                    else:
                        try:
                            query = ("INSERT INTO WATERNET.TD_RM020002 ( "
                                     "        ANALS_NO, MNG_DEPT_CD, CMPTN_ID "
                                     "      , AVG_SPFLD, AVG_FLUX, RGSTR_ID "
                                     "      , REGIST_DT, UPDUSR_ID, UPDT_DT "
                                     ") "
                                     "SELECT "
                                     "    ? AS ANALS_NO, B.MNG_DEPT_CD, B.OBJECTID AS CMPTN_ID "
                                     "	, ? AS AVG_SPFLD, ? AS AVG_FLUX, ? AS RGSTR_ID "
                                     "	, SYSDATE, ? AS UPDUSR_ID, SYSDATE "
                                     "FROM WATERNET.WTL_PIPE_LS B "
                                     "WHERE 1 = 1 "
                                     "  AND B.MNG_DEPT_CD = ?"
                                     "  AND B.PTBWTR_PLINE_TPJM_MNG_NO = ? "
                                     ";")
                            self.cursor.execute(query, self.riskMapDict['analsNo'], velocityAvg, flowAvg, self.riskMapDict['updusrId'], self.riskMapDict['updusrId'], self.riskMapDict['mngDeptCd'], linkId)
                        except Exception as ex:
                            print(ex)
                            raise
                except Exception as ex:
                    print(ex)
                    raise

