import wntr

from core.RiskMapData import RiskMapData
from core.TitleData import TitleData
from core.InpFile import InpFile
from core.MeasureLowFlowData import MeasureLowFlowData
from core.ReportLowFlowData import ReportLowFlowData
from flask import current_app

class OnlineLowFlowRun:

    # 온라인 관망해석(수리모델-저유속)
    def proc(self, analsNo):
        try:
            # RISKMAP분석결과 조회
            current_app.logger.info('proc[riskMapData]!!')
            riskMapData = RiskMapData()
            riskMapData.getRiskMapData(analsNo)

            # 타이틀정보 조회
            current_app.logger.info('proc[titleData]!!')
            titleData = TitleData()
            titleData.getTitle(riskMapData.riskMapDict["inpNumber"])

            # 파일정보 조회
            print('proc[inpFile]!!')
            inpFile = InpFile()
            inpFile.getFileInfo(titleData.fileManageId)

            # Inp파일 로딩
            print('proc[wn] ' + inpFile.fileName)
            wn = wntr.network.WaterNetworkModel(inpFile.filePath + inpFile.fileName)

            # 저유속 측정데이터 적용
            print('proc[measureLowFlowData]!!')
            measureLowFlowData = MeasureLowFlowData()
            measureLowFlowData.getMeasureLowFlowData(wn, titleData, riskMapData)

            # 해석실행
            print('proc[run_sim]!!')
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()

            # 해석결과 저장
            print('proc[reportLowFlowData]!!')
            reportLowFlowData = ReportLowFlowData()
            reportLowFlowData.saveReportLowFlowData(wn, results, titleData, riskMapData)

        except Exception as ex:
            print("[ERROR] onlineRun: ", ex)
            raise
