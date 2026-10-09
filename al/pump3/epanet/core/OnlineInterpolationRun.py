from core.SafetyConfirmData import SafetyConfirmData
from core.InterpolationRun import InterpolationRun
from core.InterpolationReportData import InterpolationReportData


class OnlineInterpolationRun:

    # 안심확인제 보간법
    def proc(self, analsNo):
        try:
            # 수용가 안심확인제 정보조회
            print('proc[safetyConfirmData]!!')
            safetyConfirmData = SafetyConfirmData()
            safetyConfirmData.getSafetyConfirmData(analsNo)

            # 안심확인제 보간법 실행
            print('proc[interpolationRun]!!')
            interpolationRun = InterpolationRun()
            interpolationRun.interpolationRun(safetyConfirmData)

            # 보간법 결과 저장
            print('proc[interpolationReportData]!!')
            interpolationReportData = InterpolationReportData()
            interpolationReportData.saveReportData(interpolationRun)

        except Exception as ex:
            print("[ERROR] OnlineInterpolationRun: ", ex)
            raise
