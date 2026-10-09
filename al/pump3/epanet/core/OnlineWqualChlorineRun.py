import wntr

from core.WqualChlorineInputData import WqualChlorineInputData
from core.TitleData import TitleData
from core.InpFile import InpFile
from core.MeasureWqualChlorineData import MeasureWqualChlorineData
from core.ReportWqualChlorineData import ReportWqualChlorineData


class OnlineWqualChlorineRun:

    # 온라인 관망해석(수질해석-잔류염소)
    def proc(self, rptNumber):
        try:
            # 수질분석(잔류염소) 입력데이터 조회
            print('proc[wqualChlorineInputData]!!')
            wqualChlorineInputData = WqualChlorineInputData()
            wqualChlorineInputData.getInputData(rptNumber)

            # 타이틀정보 조회
            print('proc[titleData]!!')
            titleData = TitleData()
            titleData.getTitle(wqualChlorineInputData.inpNumber)

            # 파일정보 조회
            print('proc[inpFile]!!')
            inpFile = InpFile()
            inpFile.getFileInfo(titleData.fileManageId)

            # Inp파일 로딩
            print('proc[wn] ' + inpFile.filePath + inpFile.fileName)
            wn = wntr.network.WaterNetworkModel(inpFile.filePath + inpFile.fileName)

            # 온라인 관망해석(수질해석-잔류염소) 측정데이터 적용
            print('proc[measureWqualChlorineData]!!')
            measureWqualChlorineData = MeasureWqualChlorineData()
            measureWqualChlorineData.getMeasureWqualChlorineData(wn, titleData, wqualChlorineInputData)

            # 해석실행
            print('proc[run_sim]!!')
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()

            # 해석결과 저장
            print('proc[reportData]!!')
            reportWqualChlorineData = ReportWqualChlorineData()
            reportWqualChlorineData.saveReportWqualChlorineData(wn, results, titleData, wqualChlorineInputData)

        except Exception as ex:
            print("[ERROR] onlineWqualChlorineRun: ", ex)
            raise
