from .Tibero import Tibero
from datetime import datetime, timedelta
from flask import current_app
# from wntrLogger import wntrLogger

class TitleData:

    def __init__(self):
        self.inpNumber = None
        self.title = None
        self.areaSeCd = None
        self.mgcCd = None
        self.fileManageId = None

        dt = datetime.now() - timedelta(minutes=11) # 현재일시 - 11분
        self.coltDt = dt.strftime("%Y%m%d%H%M")
        # self.coltDt = '202307121100'

    # 타이틀정보 조회
    def getTitle(self, inpNumber):
        try:
            query = ("SELECT "
                     "    INP_NUMBER, "
                     "    TITLE, "
                     "    MODEL_GBN, "
                     "    ( "
                     "        CASE WHEN MODEL_GBN='MASTER' THEN '온라인관망해석' "
                     "        WHEN MODEL_GBN='STWR' THEN '위기모의' "
                     "        WHEN MODEL_GBN='ETC' THEN '기타' END "
                     "    ) AS MODEL_GBN_NM, "
                     "    (SELECT AREA_SE_CD FROM CM_MGC WHERE MGC_CD = WT.MGC_CD) AS AREA_SE_CD, "
                     "    MGC_CD, "
                     "    REMARK, "
                     "    FILE_MANAGE_ID, "
                     "    (SELECT REAL_FILE_NM FROM CM_FILE_MANAGE T1 WHERE T1.FILE_MANAGE_ID = WT.FILE_MANAGE_ID) AS FILE_NM, "
                     "    ENERGY_GBN, "
                     "    USE_YN, "
                     "    FCLTY_INFO, "
                     "    RGST_ID, "
                     "    (SELECT USER_NM FROM AU_USER WHERE USER_SN = RGST_ID) AS RGST_NM, "
                     "    TO_CHAR (RGST_DT, 'YYYY-MM-DD') AS RGST_DT, "
                     "    UPDT_ID, "
                     "    (SELECT USER_NM FROM AU_USER WHERE USER_SN = UPDT_ID) AS UPDT_NM, "
                     "    TO_CHAR (UPDT_DT, 'YYYY-MM-DD') AS UPDT_DT, "
                     "    (SELECT RPT_NUMBER FROM WH_RPT_MASTER WHERE INP_NUMBER = WT.INP_NUMBER AND ROWNUM = 1) RPT_NUMBER, "
                     "    (SELECT TO_CHAR (RPT_DATE, 'YYYY/MM/DD HH24:MI') FROM WH_RPT_MASTER WHERE INP_NUMBER = WT.INP_NUMBER AND ROWNUM = 1) RPT_DATE "
                     "FROM WH_TITLE WT "
                     "WHERE INP_NUMBER = ?;")

            conn = Tibero().conn
            cursor = conn.cursor()
            cursor.execute(query, inpNumber)
            row = cursor.fetchone()

            if cursor.rowcount == 1:
                self.inpNumber = row[0]
                self.title = row[1]
                self.areaSeCd = row[4]
                self.mgcCd = row[5]
                self.fileManageId = row[7]

                # current_app.logger.info('inpNumber: ' + self.inpNumber)
                current_app.logger.info('---areaSeCd: ' + self.areaSeCd)
                current_app.logger.info('---mgcCd: ' + self.mgcCd)
                current_app.logger.info('---fileManageId: ' + self.fileManageId)
                current_app.logger.info('---coltDt: ' + self.coltDt)
            else:
                raise Exception("Data is Not Found!!!")

            conn.close()
        except Exception as ex:
            current_app.logger.error(ex)
            raise
