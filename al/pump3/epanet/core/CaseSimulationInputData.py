from .Tibero import Tibero
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
class CaseSimulationInputData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

        self.analsNo = None
        self.inpNumber = None

        self.caseSimulationDict = {}

    # 물리모델 조회
    def getInputData(self, analsNo):
        self.analsNo = analsNo

        try:
            # 사고모의수질영향유량분석 마스터 조회
            self.getInputMasterData()

            # 사고모의수질영향분석조건 상세 조회
            self.getInputDetailData()

            self.conn.close()
        except Exception as ex:
            # print(ex)
            logger.error(ex)
            self.conn.close()
            raise

    # 사고모의수질영향유량분석 마스터 조회
    def getInputMasterData(self):
        try:
            query = ("SELECT "
                     "	ANALS_NO, INP_NO "
                     "FROM TM_LD03001 "
                     "WHERE 1 = 1 "
                     "  AND ANALS_NO = ?;")

            self.cursor.execute(query, self.analsNo)
            row = self.cursor.fetchone()

            if self.cursor.rowcount == 1:
                self.analsNo = row[0]
                self.inpNumber = row[1]
            else:
                raise Exception("[Error] CaseSimulationInputData.getInputMasterData - Data is Not Found!!!")
        except Exception as ex:
            # print(ex)
            logger.error(ex)
            raise

    # 사고모의수질영향분석조건 상세 조회
    def getInputDetailData(self):
        try:
            query = ("SELECT "
                     "	ANALS_NO, LINK_ID, OPEN_YN "
                     "FROM TD_LD03003 "
                     "WHERE 1 = 1 "
                     "  AND ANALS_NO = ? "
                     "ORDER BY LINK_ID;")

            self.cursor.execute(query, self.analsNo)
            inputDetailList = self.cursor.fetchall()

            for inputDetailRow in inputDetailList:
                self.caseSimulationDict[inputDetailRow[1]] = inputDetailRow[2]

        except Exception as ex:
                # print(ex)
                logger.error(ex)
                raise
