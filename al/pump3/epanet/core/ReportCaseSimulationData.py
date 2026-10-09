from .Tibero import Tibero
from wntr.epanet.util import FlowUnits, from_si, HydParam

class ReportCaseSimulationData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

    def saveReportData(self, wn, results, caseSimulationInputData, order):
        self.wn = wn
        self.results = results
        self.caseSimulationInputData = caseSimulationInputData
        self.order = order # first, second

        try:
            # 01. 관망해석결과_Links 등록
            self.insertReportLinks()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise

    # 01. 관망해석결과_Links 등록
    def insertReportLinks(self):
        wn = self.wn
        results = self.results
        # result_quality = results.link['quality']
        result_flowrate = results.link['flowrate']
        # result_velocity = results.link['velocity']
        # result_headloss = results.link['headloss']
        # result_status = results.link['status']
        # result_setting = results.link['setting']
        # result_friction_factor = results.link['friction_factor']
        # result_reaction_rate = results.link['reaction_rate']

        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        linkList = wn.link_name_list
        for linkId in linkList:
            # flow
            flow = round(from_si(flow_unit, result_flowrate.loc[:, linkId], HydParam.Flow), 2)[0]
            val = '0'
            if (flow > 0):
                val = '+'
            elif (flow < 0):
                val = '-'

            try:
                if (self.order == 'first'):
                    query = ("UPDATE TD_LD03002 SET "
                             "      BF_FLUX = ? "
                             "    , UPDUSR_ID = RGSTR_ID "
                             "    , UPDT_DT = SYSDATE "
                             "WHERE 1 = 1 "
                             "  AND ANALS_NO = ? "
                             "  AND LINK_ID = ? "
                             ";")
                else:
                    query = ("UPDATE TD_LD03002 SET "
                             "      AF_FLUX = ? "
                             "    , UPDUSR_ID = RGSTR_ID "
                             "    , UPDT_DT = SYSDATE "
                             "WHERE 1 = 1 "
                             "  AND ANALS_NO = ? "
                             "  AND LINK_ID = ? "
                             ";")

                self.cursor.execute(query, val, str(self.caseSimulationInputData.analsNo), linkId)
            except Exception as ex:
                print(ex)
                # raise
