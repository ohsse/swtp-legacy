import pymysql
from pymysql.cursors import DictCursor

class DbManager:
    def __init__(self):
        pass
    def connection(self):
        # 데이터베이스 연결 정보
        self.conn = pymysql.connect(host='localhost', user='ems_user', password='CHANGE_ME', db='EMS_DB', charset='utf8')
        # dictionary로 가져옴
        self.cur = self.conn.cursor(DictCursor)
        return self.cur

    def sqlSelect(self, sql, param=None):
        self.cur.execute(sql, param)
        # datatype : List
        res = self.cur.fetchall()
        return res

    def sqlCommit(self):
        self.conn.commit()
    
    def sqlClose(self):
        self.cur.close()
        self.conn.close()
    