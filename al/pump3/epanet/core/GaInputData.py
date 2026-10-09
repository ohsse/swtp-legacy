from .Tibero import Tibero
from datetime import datetime, timedelta

class GaInputData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

        self.rptNumber = None
        self.inpNumber = None
        self.rptDate = None
        self.numGenerations = None
        self.numParentsMating = None
        self.initRangeLow = None
        self.initRangeHigh = None
        self.mutationProbability = []
        self.phyModelPressUnit = None
        self.junctionIdList = []
        self.resultDict = {}

    # 물리모델 조회
    def getInputData(self, rptNumber):
        self.rptNumber = rptNumber

        try:
            # 물리모델 마스터 조회
            self.getInputMasterData()

            # 물리모델 상세: 입력된 절점 별 압력 데이터 조회
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
                     "	, NUM_GENERATIONS, NUM_PARENTS_MATING, INIT_RANGE_LOW "
                     "	, INIT_RANGE_HIGH, MUTATION_PROBABILITY1, MUTATION_PROBABILITY2 "
                     "	, PRESSURE_UNIT "
                     "FROM WATERNET.TM_LD010001 "
                     "WHERE 1 = 1 "
                     "  AND RPT_NUMBER = ?;")

            self.cursor.execute(query, self.rptNumber)
            row = self.cursor.fetchone()

            if self.cursor.rowcount == 1:
                self.rptNumber = row[0]
                self.inpNumber = row[1]
                self.rptDate = str(row[2])
                self.numGenerations = row[3]
                self.numParentsMating = row[4]
                self.initRangeLow = row[5]
                self.initRangeHigh = row[6]
                self.mutationProbability.append(float(row[7]))
                self.mutationProbability.append(float(row[8]))
                self.phyModelPressUnit = row[9]

                print('rptNumber: ' + self.rptNumber)
                print('inpNumber: ' + self.inpNumber)
                print('rptDate: ' + self.rptDate)
                print('numGenerations: ' + self.numGenerations)
                print('numParentsMating: ' + self.numParentsMating)
                print('initRangeLow: ' + self.initRangeLow)
                print('initRangeHigh: ' + self.initRangeHigh)
                print(self.mutationProbability)
                print('phyModelPressUnit: ' + self.phyModelPressUnit)
            else:
                raise Exception("[Error] GaInputData.getInputMasterData - Data is Not Found!!!")
        except Exception as ex:
            print(ex)
            raise

    # 물리모델 상세: 입력된 절점 별 압력 데이터 조회
    def getInputDetailData(self):
        try:
            query = ("SELECT "
                     "	RPT_NUMBER, NODE_ID, NODE_TYPE, "
                     "	ANALYSIS_TIME, PRESSURE, FLOW, "
                     "	EXPECT_WTLKG "
                     "FROM WATERNET.TD_LD010002 "
                     "WHERE 1 = 1 "
                     "  AND RPT_NUMBER = ? "
                     "ORDER BY RPT_NUMBER, NODE_TYPE DESC, NODE_ID, ANALYSIS_TIME;")

            self.cursor.execute(query, self.rptNumber)
            inputDetailList = self.cursor.fetchall()

            timeList = []
            caseList = []
            reserviorId = None
            reserviorFlowList = []
            reserviorPressureList = []
            junctionId = None

            iIndex = 1
            for inputDetailRow in inputDetailList:
                rptNumber = inputDetailRow[0]
                nodeId = inputDetailRow[1]
                nodeType = inputDetailRow[2]
                analysisTime = inputDetailRow[3]
                pressure = inputDetailRow[4]
                flow = inputDetailRow[5]
                expectWtlkg = inputDetailRow[6]

                if nodeType == "RESERVOIR":
                    timeList.append(analysisTime)
                    caseList.append(iIndex)
                    reserviorId = nodeId
                    reserviorFlowList.append(flow)
                    reserviorPressureList.append(pressure)
                    iIndex = iIndex + 1
                elif nodeType == "JUNCTION":
                    if junctionId == "" or junctionId != nodeId:
                        junctionId = nodeId
                        self.junctionIdList.append(junctionId)

            self.resultDict["Time"] = timeList
            self.resultDict["Case"] = caseList
            self.resultDict[reserviorId + "_flow"] = reserviorFlowList
            self.resultDict[reserviorId + "_pressure"] = reserviorPressureList

            for junctionId in self.junctionIdList:
                junctionPressureList = []
                for inputDetailRow in inputDetailList:
                    rptNumber = inputDetailRow[0]
                    nodeId = inputDetailRow[1]
                    nodeType = inputDetailRow[2]
                    analysisTime = inputDetailRow[3]
                    pressure = inputDetailRow[4]
                    flow = inputDetailRow[5]
                    expectWtlkg = inputDetailRow[6]

                    if junctionId == nodeId:
                        junctionPressureList.append(pressure)

                self.resultDict[junctionId] = junctionPressureList

            # print(self.resultDict)
        except Exception as ex:
            print(ex)
            raise
