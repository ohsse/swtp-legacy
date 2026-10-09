from .Tibero import Tibero
from datetime import datetime, timedelta

class GaReportData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

        self.rptNumber = None
        self.resultDataFrame = None

    # 물리모델 결과 등록
    def setReportData(self, gaInputData, resultDataFrame):
        self.rptNumber = gaInputData.rptNumber
        self.resultDataFrame = resultDataFrame

        try:
            # 물리모델 마스터 결과 갱신
            self.updateReportMasterData()

            # 물리모델 상세 예상누수량 갱신
            self.updateReportDetailData()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise

    # 물리모델 마스터 결과 갱신
    def updateReportMasterData(self):
        try:
            query = ("UPDATE WATERNET.TM_LD010001 SET "
                     "	RPT_DATE = SYSDATE "
                     "WHERE 1 = 1 "
                     "  AND RPT_NUMBER = ?;")
            self.cursor.execute(query, self.rptNumber)
        except Exception as ex:
            print(ex)
            raise

    # 물리모델 상세 예상누수량 갱신
    def updateReportDetailData(self):
        try:
            print(self.resultDataFrame)
            columns = self.resultDataFrame.columns

            query = ("UPDATE WATERNET.TD_LD010002 SET "
                     "	EXPECT_WTLKG = ? "
                     "WHERE 1 = 1 "
                     "  AND RPT_NUMBER = ? "
                     "  AND NODE_ID = ? "
                     "  AND ANALYSIS_TIME = ? ;")
            for nodeId in columns:
                for ii in range(0, len(self.resultDataFrame.axes[0])):
                    self.cursor.execute(query, str(self.resultDataFrame[nodeId][ii]), self.rptNumber, nodeId, self.resultDataFrame.index[ii])
        except Exception as ex:
            print(ex)
            raise
