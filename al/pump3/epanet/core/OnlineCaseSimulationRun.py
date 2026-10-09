import wntr

from core.TitleData import TitleData
from core.InpFile import InpFile
from core.MeasureCaseSimulationData import MeasureCaseSimulationData
from core.ReportCaseSimulationData import ReportCaseSimulationData
from core.CaseSimulationInputData import CaseSimulationInputData


class OnlineCaseSimulationRun:

    # 사고모의수질영향유량분석
    def proc(self, analsNo):
        try:
            # 사고모의수질영향유량분석 입력데이터 조회
            print('proc[caseSimulationInputData]!!')
            caseSimulationInputData = CaseSimulationInputData()
            caseSimulationInputData.getInputData(analsNo)

            # 타이틀정보 조회
            print('proc[titleData]!!')
            titleData = TitleData()
            titleData.getTitle(caseSimulationInputData.inpNumber)

            # 파일정보 조회
            print('proc[inpFile]!!')
            inpFile = InpFile()
            inpFile.getFileInfo(titleData.fileManageId)

            # Inp파일 로딩
            print('proc[wn] ' + inpFile.fileName)
            wn = wntr.network.WaterNetworkModel(inpFile.filePath + inpFile.fileName)

            # 해석실행
            print('proc[run_sim]!!')
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()

            # 해석결과 저장
            print('proc[reportCaseSimulationData]!!')
            reportCaseSimulationData = ReportCaseSimulationData()
            reportCaseSimulationData.saveReportData(wn, results, caseSimulationInputData, 'first')

            # Status 변경 측정데이터 적용
            print('proc[measureCaseSimulationData]!!')
            measureCaseSimulationData = MeasureCaseSimulationData()
            measureCaseSimulationData.getMeasureData(wn, caseSimulationInputData)

            # 해석실행
            print('proc[run_sim]!!')
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()

            # 해석결과 저장
            print('proc[reportCaseSimulationData]!!')
            reportCaseSimulationData = ReportCaseSimulationData()
            reportCaseSimulationData.saveReportData(wn, results, caseSimulationInputData, 'second')

        except Exception as ex:
            print("[ERROR] onlineCaseSimulationRun: ", ex)
            raise
