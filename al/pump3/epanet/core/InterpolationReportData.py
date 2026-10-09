from .Tibero import Tibero
from wntr.epanet.util import FlowUnits, from_si, HydParam

class InterpolationReportData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()
        self.reportDict = {}

    def saveReportData(self, interpolationRun):
        self.reportDict = interpolationRun.reportDict

        try:
            # 01. 안심확인제 보간법 결과 삭제
            self.deleteSafetyConfirmInterpolation()

            # 02. 안심확인제 보간법 결과 등록
            self.insertSafetyConfirmInterpolation()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise


    def deleteSafetyConfirmInterpolation(self):
        try:
            query = ("DELETE FROM WATERNET.TD_RM020004 WHERE ANALS_NO = ?;")
            self.cursor.execute(query, self.reportDict["analsNo"])
        except Exception as ex:
            print(ex)
            raise

    # 01. 안심확인제 보간법 결과 등록
    def insertSafetyConfirmInterpolation(self):
        try:
            analsNo = self.reportDict["analsNo"]
            x = self.reportDict["x"]
            y = self.reportDict["y"]
            t = self.reportDict["t"]
            c = self.reportDict["c"]
            g = self.reportDict["g"]
            p = self.reportDict["p"]
            j = self.reportDict["j"]
            a = self.reportDict["a"]

            query = ("INSERT INTO WATERNET.TD_RM020004 ( "
                     "   ANALS_NO, X, Y "
                     " , NTU, FE, CU "
                     " , PH, CL, ZN "
                     ") VALUES ( "
                     "   ?, ?, ? "
                     " , ?, ?, ? "
                     " , ?, ?, ? "
                     "	);")

            for ii in range(0, len(x)):
                for jj in range(0, len(x)):
                    self.cursor.execute(query, analsNo, str(x[ii][jj]), str(y[ii][jj]),
                                        str(t[ii][jj]), str(c[ii][jj]), str(g[ii][jj]),
                                        str(p[ii][jj]), str(j[ii][jj]), str(a[ii][jj]))
        except Exception as ex:
            print(ex)
            raise
