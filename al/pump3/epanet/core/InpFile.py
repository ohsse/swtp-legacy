from .Tibero import Tibero
from flask import current_app

class InpFile:

    def __init__(self):
        self.filePath = None
        self.fileName = None

    # 파일정보 조회
    def getFileInfo(self, fileManageId):
        try:
            query = ("SELECT "
                     "    FILE_MANAGE_ID AS fileManageId, "
                     "    SEQ_NUM AS seqNum, "
                     "    SAVE_PATH AS savePath, "
                     "    SAVE_FILE_NM AS saveFileNm, "
                     "    REAL_FILE_NM AS realFileNm, "
                     "    FILE_SIZE AS fileSize, "
                     "    USE_YN AS useYn, "
                     "    RGST_ID AS rgstId, "
                     "    RGST_DT AS rgstDt, "
                     "    UPDT_ID AS updtId, "
                     "    UPDT_DT AS updtDt "
                     "FROM CM_FILE_MANAGE "  
                     "WHERE FILE_MANAGE_ID = '" + fileManageId + "';")

            conn = Tibero().conn
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()

            if cursor.rowcount == 1:
                self.filePath = row[2]
                self.fileName = row[3]
            else:
                raise Exception("[Error] InpFile.getFileInfo - Data is Not Found!!!")

            conn.close()
        except Exception as ex:
            current_app.logger.error(ex)
            raise
