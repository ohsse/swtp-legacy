from .Tibero import Tibero
from datetime import datetime, timedelta

class WqualChlorineInputData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

        self.rptNumber = None
        self.inpNumber = None
        self.rptDate = None
        self.globalBulkCoeff = None
        self.globalWallCoeff = None

        self.reservoirList = [] # 선택된 배수지 목록
        self.initialQualityList = [] # 선택된 배수지의 초기 염소값 목록
        self.tankJunctionList = []  # 선택된 탱크, 절점 목록
        self.sourceQualityList = []  # 선택된 탱크, 절점의 추가 염소값 목록

    # 수질모델(잔류염소) 입력데이터 조회
    def getInputData(self, rptNumber):
        self.rptNumber = rptNumber

        try:
            # 수질모델(잔류염소) 마스터 조회
            self.getInputMasterData()

            # 수질모델(잔류염소) Input정보 조회
            self.getInputDetailData()

            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.close()
            raise

    # 물리모델 마스터 조회
    def getInputMasterData(self):
        try:
            query = ("SELECT "
                     "	  RPT_NUMBER, INP_NUMBER, RPT_DATE "
                     "	, GLOBAL_BULK_COEFF, GLOBAL_WALL_COEFF "
                     "FROM WATERNET.TM_DC01001 "
                     "WHERE 1 = 1 "
                     "  AND RPT_NUMBER = ? ;")

            self.cursor.execute(query, self.rptNumber)
            row = self.cursor.fetchone()

            if self.cursor.rowcount == 1:
                self.rptNumber = row[0]
                self.inpNumber = row[1]
                self.rptDate = str(row[2])
                self.globalBulkCoeff = row[3]
                self.globalWallCoeff = row[4]

                print('rptNumber: ' + self.rptNumber)
                print('inpNumber: ' + self.inpNumber)
                print('rptDate: ' + self.rptDate)
                print('globalBulkCoeff: ' + self.globalBulkCoeff)
                print('globalWallCoeff: ' + self.globalWallCoeff)
            else:
                raise Exception("[Error] GaInputData.getInputMasterData - Data is Not Found!!!")
        except Exception as ex:
            print(ex)
            raise

    # 물리모델 상세: 입력된 절점 별 압력 데이터 조회
    def getInputDetailData(self):
        try:
            query = ("SELECT "
                     "	  RPT_NUMBER, NODE_ID, NODE_TYPE "
                     "	, QUALITY "
                     "FROM WATERNET.TD_DC01001 "
                     "WHERE 1 = 1 "
                     "  AND RPT_NUMBER = ? ;")

            self.cursor.execute(query, self.rptNumber)
            inputDetailList = self.cursor.fetchall()

            for inputDetailRow in inputDetailList:
                rptNumber = inputDetailRow[0]
                nodeId = inputDetailRow[1]
                nodeType = inputDetailRow[2]
                quality = inputDetailRow[3]

                if nodeType == "RESERVOIRS":
                    self.reservoirList.append(nodeId)
                    self.initialQualityList.append(quality)
                else:
                    self.tankJunctionList.append(nodeId)
                    self.sourceQualityList.append(quality)
        except Exception as ex:
            print(ex)
            raise
