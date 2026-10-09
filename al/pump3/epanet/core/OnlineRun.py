import wntr

from core.TitleData import TitleData
from core.InpFile import InpFile
from core.MeasureData import MeasureData
from core.ReportData import ReportData
from core.InpFile2Table import Inpfile2Table
# from flask import current_app

class OnlineRun:

    # 온라인 관망해석
    def proc(self, inpNumber):
        try:
            # 타이틀정보 조회
            print('proc[titleData]!!')
            titleData = TitleData()
            titleData.getTitle(inpNumber)

            # 파일정보 조회
            print('proc[inpFile]!!')
            inpFile = InpFile()
            inpFile.getFileInfo(titleData.fileManageId)

            # Inp파일 로딩
            print('proc[wn] ' + inpFile.fileName)
            wn = wntr.network.WaterNetworkModel(inpFile.filePath + inpFile.fileName)

            # 측정데이터 적용
            print('proc[measureData]!!')
            measureData = MeasureData()
            measureData.getMeasureData(wn, titleData)

            # 해석실행
            print('proc[run_sim]!!')
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()

            # 해석결과 저장
            print('proc[reportData]!!')
            reportData = ReportData()
            reportData.saveReportData(wn, results, titleData)

            # 결과파일 저장
            print('proc[write_inpfile]!!')
            wntr.network.write_inpfile(wn, inpFile.filePath + inpFile.fileName, version=2.2)

            # InpFile2Table
            print('proc[saveInpFileData]!!')
            inpFile2Table = Inpfile2Table()
            inpFile2Table.saveInpFileData(wn, titleData)

        except Exception as ex:
            print("[ERROR] onlineRun: ", ex)
            raise
