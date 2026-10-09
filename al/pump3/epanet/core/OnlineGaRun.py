import wntr

from core.TitleData import TitleData
from core.InpFile import InpFile
from core.MeasureData import MeasureData
from core.GaInputData import GaInputData
from core.GaReportData import GaReportData
from core.GaRun import GaRun


class OnlineGaRun:

    # 온라인 유전자 알고리즘
    def proc(self, rptNumber):
        try:
            # 물리모델 입력데이터 조회
            print('proc[gaInputData]!!')
            gaInputData = GaInputData()
            gaInputData.getInputData(rptNumber)

            # 타이틀정보 조회
            print('proc[titleData]!!')
            titleData = TitleData()
            titleData.getTitle(gaInputData.inpNumber)

            # 파일정보 조회
            print('proc[inpFile]!!')
            inpFile = InpFile()
            inpFile.getFileInfo(titleData.fileManageId)

            # Inp파일 로딩
            print('proc[wn] ' + inpFile.fileName)
            wn = wntr.network.WaterNetworkModel(inpFile.filePath + inpFile.fileName)

            # 측정데이터 적용
            # print('proc[measureData]!!')
            # measureData = MeasureData()
            # measureData.getMeasureData(wn, titleData)

            # GA 알고리즘 적용
            print('proc[gaRun]!!')
            gaRun = GaRun()
            gaRun.gaRun(wn, gaInputData)

            # 결과 저장-expectWtlkg
            gaReportData = GaReportData()
            gaReportData.setReportData(gaInputData, gaRun.resultDataFrame)

        except Exception as ex:
            print("[ERROR] onlineGaRun: ", ex)
            raise
