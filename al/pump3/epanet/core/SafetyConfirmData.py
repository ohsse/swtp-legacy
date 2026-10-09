from .Tibero import Tibero
from datetime import datetime, timedelta

class SafetyConfirmData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()
        self.analsNo = None
        self.masterDict = {}
        self.safetyConfirmMinMaxXyDict = {}
        self.safetyConfirmList = []
        self.xList = []
        self.yList = []
        self.tList = []
        self.cList = []
        self.gList = []
        self.pList = []
        self.jList = []
        self.aList = []


    # 물리모델 조회
    def getSafetyConfirmData(self, analsNo):
        self.analsNo = analsNo

        try:
            # 분석 마스터 조회
            self.getMasterData()

            # 수용가 최대 최소 좌표값(X, Y) 조회
            self.getSafetyConfirmMinMaxXyData()

            # 수용가 안심확인제 수질데이터 목록조회
            self.getSafetyConfirmList()

            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.close()
            raise

    # 분석 마스터 조회
    def getMasterData(self):
        try:
            query = ("SELECT MNG_DEPT_CD				/* 지역코드 */ "
                     "	, TRGET_BLCK				/* 대상 블럭 */ "
                     "	, WTQLT_STDR_OVER_STRT_DE 	/* 수질기준초과적용기간시작일 */ "
                     "	, WTQLT_STDR_OVER_END_DE 	/* 수질기준초과적용기간종료일 */ "
                     "FROM TM_RM020001	/* 분석 마스터 */ "
                     "WHERE 1 = 1 "
                     "  AND ANALS_NO = ?	/* 분석순번 */ ;")

            self.cursor.execute(query, self.analsNo)
            row = self.cursor.fetchone()

            if self.cursor.rowcount == 1:
                self.masterDict["mngDeptCd"] = row[0]
                self.masterDict["trgetBlck"] = row[1]
                self.masterDict["wtqltStdrOverStrtDe"] = row[2]
                self.masterDict["wtqltStdrOverEndDe"] = row[3]
            else:
                raise Exception("[Error] SafetyConfirmData.getMasterData - Data is Not Found!!!")
        except Exception as ex:
            print(ex)
            raise

    # 수용가 최대 최소 좌표값(X, Y) 조회
    def getSafetyConfirmMinMaxXyData(self):
        try:
            query = ("SELECT ST_MINX(BA.GEOMETRY) AS minX "
                     "	, ST_MINY(BA.GEOMETRY) AS minY "
                     "	, ST_MAXX(BA.GEOMETRY) AS maxX "
                     "	, ST_MAXY(BA.GEOMETRY) AS maxY "
                     "FROM WTL_BLSM_AS BA		/* 소블럭GIS */ "
                     "WHERE BA.MNG_DEPT_CD = ? "
                     "  AND BA.OBJECTID = ? ;")

            self.cursor.execute(query, self.masterDict["mngDeptCd"], self.masterDict["trgetBlck"])
            row = self.cursor.fetchone()

            if self.cursor.rowcount == 1:
                self.safetyConfirmMinMaxXyDict["minX"] = row[0]
                self.safetyConfirmMinMaxXyDict["minY"] = row[1]
                self.safetyConfirmMinMaxXyDict["maxX"] = row[2]
                self.safetyConfirmMinMaxXyDict["maxY"] = row[3]
            else:
                raise Exception("[Error] SafetyConfirmData.getSafetyConfirmMinMaxXyData - Data is Not Found!!!")
        except Exception as ex:
            print(ex)
            raise

    # 수용가 안심확인제 수질데이터 목록조회
    def getSafetyConfirmList(self):
        try:
            # TODO 안심확인제 실제 연계 이후, WTL_WQ_PS_TEMP_TEMP 를 실제 테이블로 바꿔줘야 함
            query = ("SELECT TO_NUMBER(WP.탁도) AS t "
                     "	, TO_NUMBER(WP.철) AS c "
                     "	, TO_NUMBER(WP.구리) AS g "
                     "	, TO_NUMBER(WP.pH) AS p "
                     "	, TO_NUMBER(WP.잔류염) AS j "
                     "	, 0 AS a /* 아연 데이터 없음 */ "
                     "	, ST_X(MP.GEOMETRY) AS X "
                     "	, ST_Y(MP.GEOMETRY) AS Y "
                     "	FROM WTL_META_PS MP		/* 소블럭GIS */ "
                     "	  INNER JOIN WTL_WQ_PS_TEMP_TEMP WP ON MP.CSTMR_NO = WP.CSTMR_NO "
                     "	    AND TO_DATE(WP.채수일,'YYYY-MM-DD') BETWEEN TO_DATE(? || '000000','YYYYMMDDHH24MISS') AND TO_DATE(? || '235959','YYYYMMDDHH24MISS') "
                     "	WHERE MP.MNG_DEPT_CD = ? "
                     "	AND ST_INTERSECTS(MP.GEOMETRY,(SELECT BA.GEOMETRY "
                     "	                                 FROM WTL_BLSM_AS BA		/* 소블럭GIS */ "
                     "	                                WHERE BA.MNG_DEPT_CD = ? "
                     "	                                  AND BA.OBJECTID = ?)) = 1  ;")

            self.cursor.execute(query, self.masterDict["wtqltStdrOverStrtDe"], self.masterDict["wtqltStdrOverEndDe"], self.masterDict["mngDeptCd"], self.masterDict["mngDeptCd"], self.masterDict["trgetBlck"])
            self.safetyConfirmList = self.cursor.fetchall()

            for row in self.safetyConfirmList:
                t = row[0]
                c = row[1]
                g = row[2]
                p = row[3]
                j = row[4]
                a = row[5]
                x = row[6]
                y = row[7]

                self.xList.append(x)
                self.yList.append(y)
                self.tList.append(t)
                self.cList.append(c)
                self.gList.append(g)
                self.pList.append(p)
                self.jList.append(j)
                self.aList.append(a)

        except Exception as ex:
            print(ex)
            raise

