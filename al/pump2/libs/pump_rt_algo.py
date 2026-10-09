import argparse
import json
import pymysql
from dataset import select_data_from_rdb, select_data_from_rdb_with_tags
from pymysql.cursors import DictCursor
import pandas as pd
from itertools import combinations
from functools import reduce
from pump_rt_models import FitPumpPerformanceCurve
import numpy as np

import re
from sys import exit
import logging

class PumpEQ_DB_connector():
    import numpy as np

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
 #       pass

    def getPumpEq(self, database, PMP_TYP = 1):
        # PMP_TYPE = 1(normal pump),2(inverter pump)

        #데이터베이스에서 펌프 성능 곡선을 검색하고, 
        #이를 전처리하여 펌프의 Q-H(유량-양정) 및 Q-P(유량-동력) 방정식 반환

        # PMP_TYPE에 따라 테이블과 조건 타입 설정 (1: 일반 펌프, 2: 인버터 펌프)
        table = 'TB_PRF_PRFRM_RST' if PMP_TYP == 1 else 'TB_PRF_INVRT_RST'
        CondType = 'WTR_TE' if PMP_TYP == 1 else 'FREQ'

        # 최신 등록 시간을 기준으로 데이터를 검색 쿼리 생성
        query = f"SELECT * FROM {database}.{table} WHERE `RGSTR_TIME` IN (SELECT MAX(`RGSTR_TIME`) FROM {database}.{table} GROUP BY `EQ_TYP`,`{CondType}`,`PUMP_IDX`) "

        cursor = self.conn.cursor(DictCursor)
        self.conn.ping()
        cursor.execute(query)
        
        # eqT = self.getDB(query,target='maria_service')# self.pd.read_csv(TableNM,sep='|')
        eqT = cursor.fetchall()

        if len(eqT) == 0 :
            return None, None

        eqT = pd.DataFrame(eqT) 

        eqs = []
        for EQ_TYP in ['QH','QP']:
            mask = (eqT['EQ_TYP'] == EQ_TYP)
            # 성능계수(PRFRM_COEFF)를 바탕으로 다항식 객체 생성 후 'Eq' 컬럼에 저장
            eqT.loc[mask,'Eq'] = eqT.loc[mask,'PRFRM_COEFF'].apply(lambda x: self.np.poly1d([float(i) for i in x.split(',')]))
            # PUMP_IDX, CondType을 기준으로 피벗하여 각 펌프와 조건에 해당하는 다항식 객체 저장
            d = eqT[mask].pivot_table(columns=['PUMP_IDX'],index=[CondType],values='Eq',aggfunc=max)
            eqs.append(d)

        # Q-H 방정식과 Q-P 방정식을 반환 
        return eqs[0],eqs[1]

    def getPumpAttribute(self, pmTable="ems_db.TB_CTR_PRF_PUMPMST_INF", pumpGroup=None):
        # 펌프 마스터 정보 테이블에서 사용 중인(USE_YN=1) 펌프의 최신 정보를 선택하는 SQL 쿼리 생성
        sql = f"""
        select * FROM {pmTable} 
        WHERE USE_YN=1 and RGSTR_TIME IN (SELECT MAX(RGSTR_TIME) FROM {pmTable} GROUP BY PUMP_IDX)
        """ 

        # 주어진 펌프 그룹(pumpGroup)에 해당하는 정보만 필터링하는 조건 추가
        if pumpGroup is not None:
            sql += f" and PUMP_GRP = {pumpGroup}"

        cursor = self.conn.cursor(DictCursor)
        print(sql)
        cursor.execute(sql)
        data = cursor.fetchall()


        pumpAttr = pd.DataFrame(data)
        # 'LEI_IDX' 컬럼이 존재하고 해당 값이 1인 행만 필터링
        if 'LEI_IDX' in pumpAttr.columns:
            pumpAttr = pumpAttr[ pumpAttr['LEI_IDX'] == 1]

        pumpAttr = pumpAttr.set_index('PUMP_IDX').T


        pumpTags = list(set(pumpAttr.values.reshape(-1))) 
        # 정규 표현식을 사용하여 특정 패턴에 부합하는 태그만 필터링
        rePattern = re.compile('[a-zA-z0-9]{3}-[a-zA-z0-9]{3}-[a-zA-z0-9]{3}-[a-zA-z0-9]{3}')

        for val in reversed(pumpTags):
            if rePattern.match(str(val)):
                continue
            pumpTags.remove(val)

        # 정리된 펌프 속성 정보와 태그 리스트를 반환
        return pumpAttr, pumpTags

class Calc_pump_properties():
    import numpy as np
    import pandas as pd
    from itertools import combinations
    
    def __init__(self, conn, pumpAttr, pumpTags, database, init=True):
        # get tags used by the pump, all tags used by algorithm
        self.maria = PumpEQ_DB_connector(conn) #TODO
        self.pumpAttr, self.pumpTags = pumpAttr, pumpTags
        
        # group numbers used by the pump
        self.group = self.pumpAttr.loc['PUMP_GRP'].unique()
        self.group.sort()
        self.KelvinT = 273.15
        self.database = database

        if init: 
            self.init()

    def init(self):
        self.QH, self.QP = self.maria.getPumpEq(self.database, 1)
        self.QHinv, self.QPinv = self.maria.getPumpEq(self.database, 2)

    def head_given_QnT(self,idx,q,t):
        # 기온과 유량이 주어졌을때, 양정값 계산
        # q는 시계열 데이터이며, t는 상수값임
        # t(tei) 값은 관측 시점에서 가장 최근값을 가져옴

        t = int(round(t))

        if self.__is_number(q) :
            q = [q]
            
        if isinstance(idx,list) :
            if len(idx) > 1 :
                # 펌프가 여러개 일때 각 펌프별 양정 값 합산 
                # (재귀 호출 함수 임.)
                # q: 유량
                # t: 기온
                # idx: 펌프 리스트 ex: [1,2,]
                return self.__joint_pump_head_at_Q(idx,q,t)
            else :
                return self.QH.loc[t][idx[0]](q)
        else :
            return self.QH.loc[t][idx](q)
    
    def head_given_QnF(self,idx,q,f):
        # calc head for inverter pumps
        if self.__is_number(q) :
            q = [q]

        if isinstance(idx,list) :
            if not isinstance(f,list) :
                return 'Check freq. list!'
            if len(idx) > 1 :
                return self.__joint_pump_head_at_QnF(idx,q,f)
            else :
                idx = idx[0]
                f = f[0]
        else :
            if isinstance(f,list) :
                f=f[0]
                
        ref_freq = self.QHinv[idx].dropna().index[0]
        e = self.QHinv.loc[ref_freq][idx]
        eq = self.__reduced_Eq_inv(e,ref_freq,f)
        
        return eq(q)
    
    def __reduced_Eq_inv(self,e,ref_freq,fval,beta=2.):
        # new func. check please!!
        # r = fval/ref_freq
        r = fval/float(ref_freq) 
        coef = []
        l = len(e.coef)-1
        for i,ecoef in enumerate(e.coef):
            coef.append(ecoef/self.np.power(r,l-i-beta))

        return self.np.poly1d(coef)
    
    def reduced_Eq_inv(self,e,ref_freq,fval,beta=2.) :
        return self.__reduced_Eq_inv(e,ref_freq,fval,beta=beta)

    def power_given_QnT(self,idx,q,t):
        # 기온과 유량이 주어졌을때, 전력값 계산
        # predict_comp_xx.py 파일에서 해당 함수 참조하여 결과 산출
        # q는 시계열 데이터이며, t는 상수값임
        # t(tei) 값은 관측 시점에서 가장 최근값을 가져옴
        # 해당 함수는 노멀펌프에 적용

        qh_eqs = self.QH[idx].loc[t]
        qp_eqs = self.QP[idx].loc[t]
            
        if self.__is_number(q) :
            q = [q]

        if isinstance(idx,list) :
            if len(idx) > 1 :
                return self.__joint_pump_Power_at_Q(qh_eqs,qp_eqs,q)
            else :
                print(qp_eqs[idx[0]], q)
                return qp_eqs[idx[0]](q)
        else :
            return qp_eqs(q)
        
    def power_given_QnF(self,idxs,q,f):
        # 유량과 주파수가 주어졌을때, 전력값 계산
        # predict_comp_xx.py 파일에서 해당 함수 참조하여 결과 산출
        # q는 시계열 데이터이며, f는 상수값임
        # 해당 함수는 인버터 펌프에 적용

        qh_eqs,qp_eqs = self.__get_qh_qp_eqs_inv(idxs,f)
        print('qh_eqs: ', qh_eqs)
        print('qp_eqs: ', qp_eqs)

        if self.__is_number(q) :
            q = [q]
        
        return self.__joint_pump_Power_at_Q(qh_eqs,qp_eqs,q)
        
    def power_given_HnT(self,idxs,h,t):
        # 기온과 양정이 주어졌을때 전력 계산
        # 해당 함수는 사용하고 있지 않고 있음.
        t = int(round(t))

        if self.__is_number(h) :
            h = [h]
            
        if not isinstance(idxs,list) :
            idxs=[idxs]
        
        qh_eqs = self.QH[idxs].loc[t]
        qp_eqs = self.QP[idxs].loc[t]
       
        return self.__joint_pump_Power_at_H(qh_eqs,qp_eqs,h)
    
    def power_given_HnF(self,idxs,h,f):
        # 주파수와 양정이 주어졌을때 전력 계산
        # 해당 함수는 사용하고 있지 않고 있음.
        if self.__is_number(h) :
            h = [h]
            
        qh_eqs,qp_eqs = self.__get_qh_qp_eqs_inv(idxs,f)
                    
        return self.__joint_pump_Power_at_H(qh_eqs,qp_eqs,h)
    
    def __get_qh_qp_eqs_inv(self,idxs,f):
        # idxs(펌프 인덱스)와 f(주파수)를 받아서 적절한 조합을 생성
        if isinstance(idxs,list) :
            if isinstance(f,list) :
                # idxs와 f가 모두 리스트인 경우, 길이가 같다면 쌍으로 묶고 아니라면 경고(주석 처리됨)
                if len(f) == len(idxs): IdxnFreq = zip(idxs,f)
                else : 
                 #   print(len(idxs),len(f),'Check idxs,f size!!')
                    IdxnFreq = zip(idxs,f)
            else : 
                # idxs만 리스트인 경우, f가 단일 값이면 각 idx에 대해 같은 f 적용
                if len(idxs) == 1 : IdxnFreq = zip(idxs,[f])
                else : 
                 #   print(idxs,f,'Check idxs,f size!!')
                # idxs가 단일 값인 경우, f의 타입에 따라 적절히 묶음
                    IdxnFreq = zip(idxs,[f])
        else :
            IdxnFreq = zip([idxs],f) if isinstance(f,list) else zip([idxs],[f])
            
        qh_eqs =[];qp_eqs=[]
        # 생성된 각 펌프 인덱스와 주파수 쌍에 대해 반복
        for idx,fval in IdxnFreq :
            # Q-H 방정식을 위한 참조 주파수와 방정식 추출 및 변환
            ref_freq = self.QHinv[idx].dropna().index[0]
            e = self.QHinv.loc[ref_freq][idx]
            e = self.__reduced_Eq_inv(e,ref_freq,fval)
            qh_eqs.append(e)

            # Q-P 방정식을 위한 참조 주파수와 방정식 추출 및 변환 (beta=3으로 설정)
            ref_freq = self.QPinv[idx].dropna().index[0]
            e = self.QPinv.loc[ref_freq][idx]
            e = self.__reduced_Eq_inv(e,ref_freq,fval,beta=3)
            qp_eqs.append(e)

        # 계산된 Q-H, Q-P 방정식 리스트 반환
        return qh_eqs, qp_eqs
    
    def get_qh_qp_eqs_inv(self,idxs,f):
        return self.__get_qh_qp_eqs_inv(idxs,f)
    
    def flow_given_HnT(self,idxs,h,t):
        t = int(round(t)) # 기온을 반올림한 후 정수로 변환
        if self.__is_number(h) :  # h가 숫자형태이면 리스트로 변환
            h = [h]
            
        if not isinstance(idxs,list) : # idxs가 리스트가 아니면 리스트로 변환
            idxs=[idxs]
        
        qh_eqs = self.QH[idxs].loc[t]  # 주어진 기온(t)에 대한 펌프 리스트(idx)의 Q-H 방정식 가져옴
        
        return self.__joint_pump_flow_at_H(qh_eqs,h) # 가져온 Q-H 방정식과 양정(h)을 이용하여 유량 계산 후 반환
    
    def flow_given_HnF(self,idxs,h,f):
        # 양정과 주파수가 주어졌을때 유량 계산
        # 해당 함수는 사용하지 않음
        
        if self.__is_number(h) :
            h = [h]
            
        if not isinstance(idxs,list) :
            idxs=[idxs]
            
        qh_eqs,qp_eqs = self.__get_qh_qp_eqs_inv(idxs,f)
        
        return self.__joint_pump_flow_at_H(qh_eqs,h)
    
    def __each_pump_flow_at_H(self,eqs,head):
        # 양정이 주어졌을때 각 펌프별로 흐르는 유량 계산
        # __ 가 붙은 함수는 해당 클래스에서 내부 사용 용도의 함수임 
        # main.py에서는 해당 함수들을 참조하지 않음.

        res = []
        #print('__each_pump_flow_at_H: ', eqs)
        #print(eqs)

        for eq in eqs :
            roots = (eq-head).roots # eq 방정식에서 양정값을 뺀후 근을 구함
            condlist = self.np.isreal(roots) # 허근 필터링
            roots= self.np.select(condlist, roots)
            _max = self.np.real(roots).max()
            _max = 0 if _max < 0 else _max
            res.append(_max)
        return res

    def __joint_pump_Power_at_Q(self,qh_eqs,qp_eqs,Qs):
        # __ 가 붙은 함수는 해당 클래스에서 내부 사용 용도의 함수임 
        # main.py에서는 해당 함수들을 참조하지 않음.
                
        res = []
        for q in Qs :
            head = self.__joint_pump_head_at_Q_atomic(qh_eqs,q)
            qs = self.__each_pump_flow_at_H(qh_eqs,head)            
            P = 0
            for pi, eq in enumerate(qp_eqs) :
                P += eq(qs[pi])
            res.append(P)

        return self.np.array(res)
    
    def __joint_pump_Power_at_H(self,qh_eqs,qp_eqs,Hs):        
        
        res = []
        for h in Hs :
            qs = self.__each_pump_flow_at_H(qh_eqs,h)
            P = 0
            for pi, eq in enumerate(qp_eqs) :
                P += eq(qs[pi])
            res.append(P)

        return self.np.array(res)
    
    def __joint_pump_flow_at_H(self,qh_eqs,Hs):        
        
        res = []
        for h in Hs :
            qs = self.__each_pump_flow_at_H(qh_eqs,h)
            res.append(sum(qs))

        return self.np.array(res)
    
    def __joint_pump_head_at_Q(self,idxs,Qs,t):
        # change func. check please!!
        # 펌프가 여러개 일때 각 펌프별 양정 값 합산 
        # (재귀 호출 함수 임.)
        # q: 유량
        # t: 기온
        # idx: 펌프 리스트 ex: [1,2,]
        # QS는 유량 별 구간을 나타냄 
        res = []
        qh_eqs = self.QH[idxs].loc[t]
        for q in Qs :
            head = self.__joint_pump_head_at_Q_atomic(qh_eqs,q)
            print('head: ', head)
            res.append(head)

        return self.np.array(res)
     
    def __joint_pump_head_at_QnF(self,idxs,Qs,f):
        # change func. check please!!
        # 펌프가 여러개 일때 각 펌프별 양정 값 합산  (인버터 펌프 대상)
        # (재귀 호출 함수 임.)
        # f: 주파수
        # idxs: 펌프 리스트 ex: [1,2,]
        # QS는 유량 별 구간을 나타냄 
        res = []
        qh_eqs = []
        for idx,fval in zip(idxs,f):
            ## self.QHinv에 db에 담긴 인버터 펌프 계수가 담겨 있음
            # 이중 첫번째 주파수 참조
            ref_freq = self.QHinv[idx].dropna().index[0]
            e = self.QHinv[idx].loc[ref_freq]
            # 각 계수별 전처리
            e = self.__reduced_Eq_inv(e,ref_freq,fval)
            qh_eqs.append(e)
            
        for q in Qs :
            # 각 유량 구간에 대한 양정값 구함
            head = self.__joint_pump_head_at_Q_atomic(qh_eqs,q)
            res.append(head)

        return self.np.array(res)
        
    
    def __joint_pump_head_at_Q_atomic(self,qh_eqs,Q,h1=90,h2=0,dh=10):
        # change func. check please!!
        # 이함수는 무엇을 하는지 잘 모르겠음
        # qh_eqs: 각 펌프별 계수 테이블 
        # Q: 유량
        Hs = self.np.arange(h1,h2,-dh)
        for h in Hs : 
            qs1 = self.__each_pump_flow_at_H(qh_eqs,h)
            qs2 = self.__each_pump_flow_at_H(qh_eqs,h-dh)

            sum1 = sum(qs1)
            sum2 = sum(qs2)

            if (Q - sum1 > 0) and (Q - sum2 < 0):
                if ((sum2-sum1) < 2) or (dh < 0.001) :
                    h = ((Q - sum1)*h2+(sum2-Q)*h1)/(sum2-sum1)
                    return h
                return self.__joint_pump_head_at_Q_atomic(qh_eqs,Q,h1=h,h2=h-dh,dh=dh*0.5)
            else :
                if (Q - sum1) == 0:
                    return h
                elif (Q - sum2 == 0) :
                    return h-dh
        return h2
    
    def each_pump_flow_at_EqnH(self,qh_eqs,h):
        # 헤드가 주어졌을 때 각 펌프별로 흐르는 유량을 계산 
        # h: 양정
        # qh_eqs: 펌프계수 테이블 
        return self.__each_pump_flow_at_H(qh_eqs,h)
    
    def freq_given_QnH(self,idxs,q,h,mode=1):
        # mode : 1=singlePump, synchronous multi-Pump, 2= single controll pump and max freq. multi-Pump
        # mode: 작동 모드 설정 (1: 단일 펌프 또는 동기 다중 펌프, 2: 단일 제어 펌프와 최대 주파수 다중 펌프)
        if not isinstance(idxs,list) :
            idxs = [idxs]
            
        qh_eqs = [];ref_freq=[];target_freq=[]
        for idx in idxs :
            f = self.QHinv[idx].dropna().index[0] # 첫번째 비어있지 않은 데이터의 인덱스를 참조 주파수로 설정
            e = self.QHinv.loc[f][idx] # 참조 주파수에 해당하는 Q-H 곡선의 방정식 추출
            qh_eqs.append(e) # Q-H 곡선 방정식을 리스트에 추가
            ref_freq.append(f) # 참조 주파수를 리스트에 추가
            target_freq.append('max')  # 기본적으로 'max'를 목표 주파수로 설정

            # qh_attr DataFrame에 Q-H 곡선 방정식, 참조 주파수, 목표 주파수 정보를 저장
        qh_attr = self.pd.DataFrame({'qh_eqs':qh_eqs,'ref_freq':ref_freq,'target_freq':target_freq})
        if mode == 1 :
            qh_attr['target_freq'] = 'ctr' # 모드 1인 경우 모든 목표 주파수를 'ctr'로 설정
            qh_attr = qh_attr.to_numpy()
            # 단일 펌프를 위한 주파수 계산 함수 호출
            return self.__freq_given_QnH_for_single_pump(qh_attr,q,h)
        else :
            qh_attr.loc[qh_attr.index[-1],'target_freq'] = 'ctr'
            # DataFrame을 NumPy 배열로 변환 
            # 단일 펌프를 위한 주파수 계산 함수 호출 (모드 2)
            qh_attr = qh_attr.to_numpy()  
            return self.__freq_given_QnH_for_single_pump(qh_attr,q,h)

    def __freq_given_QnH_for_single_pump(self,qh_attr,Q,h,f1=60,f2=0,df=2):
        # 함수는 단일 펌프에 대해 주어진 유량(Q)과 양정(H)에 기반하여 필요한 주파수를 반복적으로 계산하여 찾아내는 역할을 함.

        # 주파수 범위(f1~f2) 내에서 주어진 df 간격으로 주파수 배열 생성
        fs = self.np.arange(f1,f2,-df)
        for f in fs :
            # 현재 주파수와 주파수-간격인 f-df에 대해 감소된 Q-H 방정식을 계산
            eq1 = self.__reduced_Eqs_inv(qh_attr,f-df)
            eq2 = self.__reduced_Eqs_inv(qh_attr,f)
            # 계산된 방정식을 바탕으로 각각의 주파수에서 펌프 유량 계산
            qs1 = self.each_pump_flow_at_EqnH(eq1,h)
            qs2 = self.each_pump_flow_at_EqnH(eq2,h)

            # 각 주파수에서의 총 유량 합계 계산
            sum1 = sum(qs1)
            sum2 = sum(qs2)
            # 주어진 Q가 계산된 유량 범위 내에 있을 경우, 선형 보간을 통해 주파수 결정
            if (Q - sum1 > 0) and (Q - sum2 < 0):
                # 유량 차이가 매우 작거나 주파수 간격이 충분히 작아진 경우, 결과 반환
                if ((sum2-sum1) < 2) or (df < 0.001) :
                    f = ((Q - sum1)*f2+(sum2-Q)*f1)/(sum2-sum1)
                    return round(f,2)
                # 그렇지 않은 경우, 주파수 간격을 반으로 줄여 재귀적으로 함수 호출
                return self.__freq_given_QnH_for_single_pump(qh_attr,Q,h,f1=f,f2=f-df,df=df*0.5)
            else :
                # 주어진 Q가 계산된 유량 중 하나와 정확히 일치하는 경우, 해당 주파수 반환
                if (Q - sum1) == 0:
                    return round(f,2)
                elif (Q - sum2 == 0) :
                    return round(f-df,2)

        # 주어진 Q에 대한 적절한 주파수를 찾지 못한 경우, 최소 주파수 반환
        return round(f2,2)

    def __reduced_Eqs_inv(self,qh_attr,f):
        res_eq = []
        for eq, ref_f, ftf in qh_attr:
            if ftf == 'ctr':
                e = self.__reduced_Eq_inv(eq,ref_f,f)
            else :
                e = self.__reduced_Eq_inv(eq,ref_f,60.)
            res_eq.append(e)
        return res_eq
    
    def reduced_Eqs_inv(self,qh_attr,f):
        return self.__reduced_Eqs_inv(qh_attr,f)
    
    def NumOfInvPump_given_QnH(self,idxs,q,h):
        # 가동 조합에서 최적 조합의 인버터 펌프 개수를 산출
        # 사용하지 않고 있는 함수. 
        comblist = []
        for i in range(len(idxs)):
            comb = list(self.combinations(idxs,i+1))
            comblist.extend(comb)

        for jdxs in comblist:
            pidxs=[]; f=[]
            for idx in jdxs :
                f.append(60.)
                pidxs.append(idx)
            head = self.head_given_QnF(pidxs,q,f)
            if h < head:
                return pidxs
        return 0
    
    def __is_number(self,s):
        TF = isinstance(s,list) | isinstance(s,type(self.pd.Series(1))) | isinstance(s,type(self.np.arange(1,1,1)))
        if TF:
            return False
        try:
            float(s)
            return True
        except ValueError:
            return False


def get_connection(args):
    with open('datafeeder.json') as f:
        feeder = json.load(f)[args.feeder]

    connection = feeder["connection"]
    with open('connections.json') as f:
        db = json.load(f)[connection]
    return pymysql.connect(**db)

def get_connection_alchemy(args):
    with open('datafeeder.json') as f:
        feeder = json.load(f)[args.feeder]

    connection = feeder["connection"]
    with open('connections.json') as f:
        db = json.load(f)[connection]

    from sqlalchemy import create_engine
    q = f'mysql+pymysql://{db["user"]}:{db["password"]}@{db["host"]}/{db["db"]}'
    print(f'connect to {q}')
    e = create_engine(q)
    return e.connect()

def get_connection_alchemy_s(connection_key):
    with open('connections.json') as f:
        db = json.load(f)[connection_key]

    from sqlalchemy import create_engine
    q = f'mysql+pymysql://{db["user"]}:{db["password"]}@{db["host"]}/{db["db"]}'
    print(f'connect to {q}')
    e = create_engine(q)
    return e.connect()

def load_data(args, tot_tags):
    with open('datafeeder.json') as f:
        feeder = json.load(f)[args.feeder]

    connection = feeder["connection"]
    with open('connections.json') as f:
        db = json.load(f)[connection]

    if args.source_type == 'file':
        df = pd.read_csv(args.input_file, index_col=0)
        df.index = pd.to_datetime(df.index)

    elif args.source_type == 'rdb' :
        start_date = pd.Timestamp(args.start_date)
        end_date = (pd.Timestamp(start_date) + pd.Timedelta(days=int(args.ref_days)))
        conn = pymysql.connect(**db)

        data = select_data_from_rdb_with_tags(conn, tot_tags, ts_from=start_date, ts_to=end_date)
        df = pd.DataFrame(data)
        df = df.pivot(index='ts', columns='tagname')['value']
        df = df.resample('1min').mean().fillna(0)

    return df

## pt
def calc_pr_HL(pr_HH:float, pr_LL:float, pr_BSJ:float, pr_buffer:float=.5):
    """ 절대상한(pr_HH), 절대하한(pr_LL), 배수지하한(pr_BSJ)을 고려하여 버퍼가 적용된 운영관압상한, 운영관압하한을 결정한다. """
    # "평택 운영 관압 상한"
    # pt_pr_H = pr_HH - pr_buffer
    # "평택 운영 관압 하한"
    pt_pr_L = round(max(pr_LL + pr_buffer, pr_BSJ + pr_buffer), 2)
    # "평택 운영 관압 상한"
    pr_L_H_sync = .6
    pt_pr_H = round(min(pt_pr_L + pr_L_H_sync, pr_HH - pr_buffer), 2)

    if pt_pr_L > pt_pr_H:
        pt_pr_L = pt_pr_H - .4

    return pt_pr_H, pt_pr_L

def pr_HL_buffering(pr_H, pr_L, elapsed_time:int, buffer_wdw:int=10, buffer_pr:float=0.1):
    pr_buffer = self.calc_pr_buffer(elapsed_time, buffer_wdw, buffer_pr)
    pr_H = round(pr_H + pr_buffer, 2)
    pr_L = round(pr_L - pr_buffer, 2)
    return pr_H, pr_L

def _set_pump_idx(pump_grp, pump_grp_idx):
    return int(pump_grp) * 100 + int(pump_grp_idx)

def _get_pump_idx(val):
    return (int(val / 100), val % 100)

def get_tags(connection, pumpGroup, pmTable="ems_dev.CTR_PRF_PUMPMST_INF"):
    sql = f""" select * from {pmTable} where `PUMP_GRP` = {pumpGroup}"""
    cursor = connection.cursor(DictCursor)
    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    print(df)
    #df["PUMP_GRP_ITG_IDX"] = df["PUMP_GRP_IDX"]

    return df

def getLogger(appName):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: [%(name)s] (%(levelname)s): %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


class PumpControl:
    logger = getLogger('PumpControl')

    def __init__(self, conn, config, CTR_PRF_PUMP_INF, pumpAttr, pumpTags, database, init=True):
        self.CTR_PRF_PUMP_INF = CTR_PRF_PUMP_INF
        self.CPP = Calc_pump_properties(conn, pumpAttr, pumpTags, database=database, init=init)
        self.FPPC = FitPumpPerformanceCurve(pumpAttr, pumpTags)

        self.database = database

        self.le = 8
        self.te = 20
        self.total_time_threshold = 5 # sequence control total term delay time threshold
        self.time_threshold = 3 # sequence control each term delay time threshold

        self.pmp_idxs = self.CTR_PRF_PUMP_INF["PUMP_IDX"] #펌프 인덱스 리스트 취합
        self.pmp_use_yns = self.CTR_PRF_PUMP_INF["USE_YN"] #펌프 사용 유므 리스트 취합
        self.tot_pmp_num = len(self.pmp_idxs)        
        self.pmp_sz = dict(zip(self.pmp_idxs, self.CTR_PRF_PUMP_INF['PRRT_TYP'].values))
        df = self.CTR_PRF_PUMP_INF    

        self.fr_tags = df["FRI_TAG"].values.tolist() #유량 태그 취합
        self.pr_tags = df["PRI_T_TAG"].values.tolist() #관압태그 취합
        self.te_tags = df["TEI_TAG"].values.tolist() # 기온 태그 치합
        # lei_tags = df["LEI_TAG"].values.tolist()
        self.lei_tags = ["701-367-LEI-4008", "701-367-LEI-4009"] #TODO
        self.pmb_tags = df["PMB_TAG"].values.tolist()

        self.rnk = self.CTR_PRF_PUMP_INF["PRRT_RNK"]

        self.fr1 = 9999
        self.pr1 = 9.9

        self.elapsed_time = None
    
    def hz_rounding(self, hz, decimals=1):
        return [round(h, decimals) for h in list(hz)]

    def pressure2head(self, p, le=None, te=None, offset=1e4):
        # 수위와 기온이 주어졌을때, 관압 값을 양정값으로 변환

        """ h: 양정(CPP.head_given...), le:흡수정수위, te:정수수온, """
        if le is None:
            le = self.le
        
        if te is None:
            te = self.te
        
        return p * offset / self.FPPC.rho_water(te) - le + 3

    def head2pressure(self, h, le=None, te=None, offset=1e4):
        # 수위와 기온이 주어졌을때, 양정값을 관압값으로 변환
        """ h: 양정(CPP.head_given...), le:흡수정수위, te:정수수온, """

        if le is None:
            le = self.le
        
        if te is None:
            te = self.te
        
        self.logger.info(f'head2pressure h:{h}, le:{le} te:{te}')
        return (h + (le - 3)) * self.FPPC.rho_water(te) / offset
    
    def pump_algo(self, raw_data, pmb_idxs):
        pr_HH, pr_LL = 10.5, 2.5
        current_data = raw_data.iloc[-1, :]

        return self.pump_select(current_data, pmb_idxs=pmb_idxs , pr_H=pr_HH, pr_L=pr_LL, fr_L=500, upward=True)

    def pump_select(self, current_data, pmb_idxs, pr_H, pr_L, fr_L, upward: bool, Q_width:float=2000., Q_wdw:float=50.):
        # current_data: 입력 데이터
        # pmb_idxs: 전체 펌프 리스트
        # pr_H: 관압 하한
        # pr_L: 관압 하한

        # 디버깅 플래그 설정
        debug_flag = False 
        self.pmb_idxs = pmb_idxs
        for t in self.te_tags:
            d = current_data[t]
            if current_data[t] == 0:
                # 기온 데이터가 0인 경우 기본값(20)으로 설정
                current_data[t] = 20
        
        C = self.set_pump_combinations()
        print('C: ',C)
        self.fr0 = current_data[self.fr_tags[0]]
        self.pr0 = current_data[self.pr_tags[0]]
        self.te0 = current_data[self.te_tags[0]]

        # 현재 압력이 압력 하한(pr_L) 미만인 경우 상승 상태로 설정, 압력 상한(pr_H) 이상인 경우 하강 상태로 설정
        if round(self.pr0, 2) < pr_L:
            upward = True
        elif round(self.pr0, 2) >= pr_H:
            upward = False

        Q = self.get_Q(upward)  # 상승 또는 하강 상태에 따라 필요한 유량 계산
        A = []
        for c in C:
            print('c: ', c)
            h0 = self.CPP.head_given_QnT(c, self.fr0, self.te0)
            pr0 = self.head2pressure(h0)
            v = np.sign(int(upward) - .5) * np.sign(pr0 - self.pr0)

            # 상승/하강 상태와 압력 변화 방향이 일치하는 경우에만 계속 진행
            if np.sign(int(upward) - .5) * np.sign(pr0 - self.pr0) > 0:
                hs = self.CPP.head_given_QnT(c, Q, self.te0) #  필요한 유량과 기온에 대한 양정 계산
                prs = self.head2pressure(hs) # ex. [6.865, 6.854, ..., 6.683]  # 계산된 양정을 압력으로 변환 
                A.append([",".join([str(x) for x in c])] + list(prs))
            else:
                continue # 상승/하강 상태와 압력 변화 방향이 일치하지 않는 경우 이후 작업을 생략

        A = pd.DataFrame(A, columns=['C']+list(range(len(Q)))) # A : pressure (펌프 조합에 따른 펌프 압력 변화 배열)
        print(A)

        B = pd.DataFrame(columns=range(len(Q)))
        slope_classes = ['FAST','MIDDLE']#,'SLOW']
        slopes = [1/450., 1/1000.] #[1/500., 1/1000.] #[1/300., 1/300.] #[1/800., 1/1000., 1/1200.] #[1/500., 1/1000., 1/1500.] ########## 2022-06-22
        b = []  # 경사도에 따른 압력 변화를 저장할 리스트 초기화

        for s in slopes: # ex. s=1/500 # 각 경사도에 대해 반복
            dQ = Q - self.fr0  # 기준 유량(self.fr0)과의 차이 계산
            dP = dQ * s # 유량 차이에 따른 압력 차이 계산
            # 계산된 압력 차이를 현재 압력에 더해 최종 압력 계산
            prs = self.pr0 + dP # ex. [6.6, 6.7, ... , 7.7]
            # 결과 리스트에 추가
            b.append(list(prs))

        # 계산된 압력 값을 DataFrame으로 변환하고 성능 곡선 클래스를 컬럼으로 추가
        B = pd.concat((B, pd.DataFrame(b)), axis=0)
        B = pd.concat((pd.DataFrame(slope_classes, index=B.index, columns=['S']), B), axis=1)

        D = [] # 최소 거리 인덱스를 저장할 리스트 초기화

         # A DataFrame의 각 행에 대해 반복
        for _, c in A.iterrows(): # ex. c[0]=c=[5], c[1]=h=[55], c[2]=6.864766, ...
            d = []

            for _, s in B.iterrows(): # ex. s[0]=s=['FAST'], s[1]=6.6, ...
                a = c.values[1:]
                b = s.values[1:]
                di = np.argmin(np.abs(a-b))  # a와 b 사이의 절대값 차이가 최소인 인덱스 찾기
                d.append(di)
            D.append(d)
            
        D = pd.DataFrame(D, columns=slope_classes)

        P = [] # 선택된 펌프 조합에 대한 압력 값을 저장할 리스트 초기화

        for i, a in A.drop(columns=['C']).iterrows():
            P.append(a.values[D.values[i]]) #각 펌프 조합에 대해 최소 거리에 해당하는 압력 값 선택

        P = pd.DataFrame(P, columns=slope_classes)
        P = pd.concat((A[['C']], P), axis=1)  # 펌프 조합 정보를 포함하여 최종 DataFrame 생성

        P_copy = P.copy()
        #TEMP!
        #P_copy = P_copy.loc[~(np.any(np.round(P_copy[slope_classes].values,2) > pr_H, axis=1))] # 상한을 넘어가는 조합은 선택하지 않음. # any -> all (11-01)
        #P_copy = P_copy.loc[~(np.any(np.round(P_copy[slope_classes].values,2) < pr_L, axis=1))] # 하한을 하회하는 조합은 선택하지 않음. # any -> all (jrp)

        #TEMP!
        # 필터링 조건은 상한(pr_H)과 하한(pr_L)을 넘어가는 조합을 제외
        if (len(P_copy)<1) and (upward) and (self.pr0 < pr_L - 0.5):
            P_copy = P.copy()
            P_copy = P_copy.loc[~(np.any(np.round(P_copy[['MIDDLE']].values,2) > pr_H, axis=1))] # 상한을 넘어가는 조합은 선택하지 않음. # any -> all (11-01)
            P_copy = P_copy.loc[~(np.any(np.round(P_copy[['MIDDLE']].values,2) < pr_L - 0.1, axis=1))] # 하한을 하회하는 조합은 선택하지 않음. # any -> all (jrp)
        
        P = P_copy

        W = P.apply(lambda r: self.CPP.power_given_HnT([int(x) for x in r['C'].split(",")],r['MIDDLE'], self.te0)[0], axis=1)
        #print("9. P의 c들 중 s[1](중간 시스템 곡선)의 예상유량값(R[c])을 계산한다.")
        R = P.apply(lambda r: self.CPP.flow_given_HnT([int(x) for x in r['C'].split(",")],self.pressure2head(r['MIDDLE']), self.te0)[0], axis=1)

        #시스템곡선 MIDDLE에 해당하는 효율 지표 계산 
        F = 0.163 * R * self.pressure2head(P['MIDDLE']) / W / 60.

        PWRFUM = P[['C','MIDDLE']].copy()
        PWRFUM.loc[:,'W'] = W.values
        PWRFUM.loc[:,'R'] = R.values
        PWRFUM.loc[:,'F'] = F.values
        PWRFUM = PWRFUM.loc[PWRFUM['R'] >= fr_L]

        if len(PWRFUM)<1:
            ##print("유량 운영 조건 부합하는 펌프조합(주파수) 식별 불가능. 현재 운전상태를 그대로 유지함.")
            pt_pump1 = pump0
            pt_fr1 = self.fr0
            pt_pr1 = float(self.pr0)
            #print(f"{pt_pump0}, ({pt_fr0}, {pt_pr0})  ---> {pt_pump1}, ({pt_fr1}, {pt_pr1})")
            pt_debug_flag = "pt3__fr1_never"
            #print(pt_debug_flag)
            return pt_pump1, pt_fr1, pt_pr1, pt_debug_flag

        common_idx_nums = np.array([sum([t[0]==t[1] for t in zip([int(i) for i in pmb_idxs], [int(i) for i in c.split(",")])]) for c in PWRFUM['C']])

        if common_idx_nums.max() < 1: #TODO 이부분 문의 필요
            PWRFUM.loc[:,'U'] = np.clip(common_idx_nums, 0., 1.)
        else:
            #print(pt_pump0, common_idx_nums)
            PWRFUM.loc[:,'U'] = np.clip(common_idx_nums / common_idx_nums.max(), 0., 1.)

        W_normed = (1/PWRFUM['W']) / self.get_norm((1/PWRFUM['W']))
        F_normed = PWRFUM['F'].clip(.1,None) / self.get_norm(PWRFUM['F'].clip(.1,None))
        PWRFUM.loc[:,'M'] = (PWRFUM['U'] * 2 + W_normed + F_normed * 2) / 5
        PWRFUM.loc[:,'M2'] = (W_normed + F_normed * 2) / 5

        pump1, pr1 = PWRFUM.iloc[np.argmax(PWRFUM['M']),:][['C','MIDDLE']]
        pump1 = [int(x) for x in pump1.split(",")]

        #pump1 = self.idx2pmb(pump1,'pt')

        fr1 = PWRFUM['R'].iloc[np.argmax(PWRFUM['M'])].round()
        pr1 = round(pr1,4)
        print(PWRFUM)
        return PWRFUM
    

    def get_norm(self, vec):
        norm = np.sqrt(np.sum(np.power(vec,2)))
        return norm

    def set_pump_combinations(self):
        # 해당 함수는 가능한 모든 펌프 조합을 산출합니다.
        # 만약 펌프 그룹이 아래와 같은 펌프들을 가지고 있다면,
        # [1,2]
        # 아래와 같은 결과를 산출합니다.
        # [[1], [2], [1,2]]
        _pmps = list( x for i, x in enumerate(self.pmp_idxs) if int(self.pmp_use_yns[i]) == 1)
        C = []

        for n in range(len(_pmps)):
            for c in list(combinations(_pmps,n+1)):
                C.append(list(c))

        return C
    
    def get_Q(self, upward, Q_width=2000., Q_wdw=50.):
        print(self.fr0, Q_width, Q_wdw)
        if upward:
            Q = np.arange(self.fr0, self.fr0 + Q_width + 1, Q_wdw)
        else:
            Q = np.arange(max(self.fr0 - Q_width,0), self.fr0 + 1, Q_wdw)

        self.Q = Q
        return Q

def PreProcessing(FPPC,totDF,inv_pump_idx=[5,6]):
    # 시계열 데이터 전처리 
    # 해당함수는 사용하나 화성에 특화된 부분이 있어 추후 확인 필요.
    mask = totDF.index > pd.to_datetime("2019-01-01")
    tmp = totDF[mask][FPPC.pumpTags].copy()
    for pi in inv_pump_idx:
        tmp[FPPC.pumpAttr[pi]['PRI_D_TAG']] = tmp[FPPC.pumpAttr[pi]['PRI_D_TAG']].apply(lambda x: np.nan if (x < 4) or (x>14) else x)
        tmp[FPPC.pumpAttr[pi]['PRI_S_TAG']] = tmp[FPPC.pumpAttr[pi]['PRI_S_TAG']].apply(lambda x: np.nan if (x < 0.4) or (x>0.8) else x)
        m1 = tmp[FPPC.pumpAttr[pi]['FRI_TAG']].rolling(3,center=True).std() < 0.001
        tmp[FPPC.pumpAttr[pi]['FRI_TAG']][m1]= np.nan
        tmp[FPPC.pumpAttr[pi]['SPI_TAG']] = tmp[FPPC.pumpAttr[pi]['SPI_TAG']].apply(lambda x: np.nan if (x > 60)|(x < 30) else x)
    tmp = FPPC.calc_diff_head(tmp)
    return tmp


def main(args, wpp_code, conn, feeder):
        # 설정 파일(datafeeder.json)에서 테이블 매핑 정보 불러오기
    with open('datafeeder.json') as w:
        feeder = json.load(w)[feeder]
        print(feeder)
    # 데이터베이스에서 펌프 태그 정보 가져오기
    ctr_df = get_tags(conn, pumpGroup=args.pumpGroup, pmTable=feeder['pmtable'])
    database = feeder['database']

    # 데이터베이스 커넥터 초기화 및 펌프 속성 정보 가져오기
    pdbc = PumpEQ_DB_connector(conn);
    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=args.pumpGroup, pmTable=feeder['pmtable'])

    # 입력으로 주어진 시작 및 종료 날짜를 pandas Timestamp 객체로 변환
    st_date = pd.Timestamp(args.start_date) 
    end_date = pd.Timestamp(args.end_date)

    # TB_RAWDATA 테이블에서 원시 데이터 가져오기
    raw_data = select_data_from_rdb_with_tags(conn, pumpTags, st_date, end_date, table=feeder["rawtable"])
    raw_df = pd.DataFrame(raw_data)
    # 원시 데이터를 pivot하여 타임스탬프(ts)를 인덱스로, 태그 이름(tagname)을 컬럼으로 하는 데이터프레임 생성
    raw_df = raw_df.pivot(index='ts', columns='tagname')['value']

    for c in raw_df.columns:
        raw_df[c] = raw_df[c].astype(float)

    # 데이터를 1분 간격으로 리샘플링하고, 누락된 값은 0으로 채움
    df = raw_df.resample('1min').mean().fillna(0)
    #df[ df["865-334-FRI-4001"] == 0 ] = df[ df["865-334-FRI-4001"] != 0 ].mean() #TEMP!

    df.index = pd.to_datetime(df.index)

    pc = PumpControl(conn, None, ctr_df, pumpAttr, pumpTags, database=database)

    # 차압 계산 처리
    _df = pc.FPPC.calc_diff_head(df) # proc


    # 펌프 제어 알고리즘 적용
    df = pc.pump_algo(_df, pumpAttr.columns)
    print(df)
    df.to_csv("result.csv")
    df["START_DATE"] = st_date
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='pump_rt_algo')

    parser.add_argument('--session')
    parser.add_argument('--start_date')
    parser.add_argument('--wppcode')
    parser.add_argument('--pumpGroup')
    parser.add_argument('--tablename', default='ems_data.rawdata_5year')
    parser.add_argument('--end_date', default=None)
    parser.add_argument('--source_type', default='rdb')
    parser.add_argument('--input_file', default=None)
    parser.add_argument('--feeder', default=None)

    args = parser.parse_args()
    conn = get_connection(args)

    try :
        main(args, args.wppcode, conn=conn, feeder=args.feeder)
    finally:
        conn.close()
  