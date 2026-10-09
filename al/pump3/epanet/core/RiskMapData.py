from .Tibero import Tibero
from flask import current_app


class RiskMapData:

    def __init__(self):
        self.riskMapDict = {}

    # RISKMAP분석결과 조회
    def getRiskMapData(self, analsNo):
        try:
            # WATERNET.TM_RM020001 WT, WATERNET.TD_RM020002
            query = ("SELECT "
                     "      (ANALS_NO || '') AS ANALS_NO, INP_NO, LOW_SPFLD_STRT_DE "
                     "    , LOW_SPFLD_END_DE, UPDUSR_ID, MNG_DEPT_CD "
                     "FROM WATERNET.TM_RM020001 WT "
                     "WHERE ANALS_NO = ?;")

            conn = Tibero().conn
            cursor = conn.cursor()
            cursor.execute(query, analsNo)
            row = cursor.fetchone()

            if cursor.rowcount == 1:
                self.riskMapDict["analsNo"] = row[0]
                self.riskMapDict["inpNumber"] = row[1]
                self.riskMapDict["lowSpfldStrtDe"] = row[2]
                self.riskMapDict["lowSpfldEndDe"] = row[3]
                self.riskMapDict["updusrId"] = row[4]
                self.riskMapDict["mngDeptCd"] = row[5]

                current_app.logger.info('analsNo: ' + self.riskMapDict["analsNo"])
                current_app.logger.info('inpNumber: ' + self.riskMapDict["inpNumber"])
                current_app.logger.info('lowSpfldStrtDe: ' + self.riskMapDict["lowSpfldStrtDe"])
                current_app.logger.info('lowSpfldEndDe: ' + self.riskMapDict["lowSpfldEndDe"])
                current_app.logger.info('updusrId: ' + self.riskMapDict["updusrId"])
                current_app.logger.info('mngDeptCd: ' + self.riskMapDict["mngDeptCd"])
            else:
                raise Exception("[Error] RiskMapData.getRiskMapData - Data is Not Found!!!")

            conn.close()
        except Exception as ex:
            current_app.logger.error(ex)
            raise
