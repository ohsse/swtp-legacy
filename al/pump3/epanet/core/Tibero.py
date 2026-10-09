import os

import pyodbc

class Tibero:
    def __init__(self):
        self._connection()

    def _connection(self):
        try:
            pyodbc.pooling = True
            # 접속정보는 환경변수로 주입한다
            conn = pyodbc.connect('DSN={};UID={};PWD={}'.format(
                os.environ.get('TIBERO_DSN', 'tibero'), os.environ['TIBERO_UID'], os.environ['TIBERO_PWD']))
            conn.setdecoding(pyodbc.SQL_CHAR, encoding='euc-kr')
            conn.setdecoding(pyodbc.SQL_WCHAR, encoding='euc-kr')
            conn.setdecoding(pyodbc.SQL_WMETADATA, encoding='euc-kr')
            conn.setencoding(encoding='euc-kr')
        except Exception as ex:
            print(ex)
            raise

        self.conn = conn
