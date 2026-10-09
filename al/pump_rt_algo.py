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
        table = 'TB_PRF_PRFRM_RST' if PMP_TYP == 1 else 'TB_PRF_INVRT_RST'
        CondType = 'WTR_TE' if PMP_TYP == 1 else 'FREQ'
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
            eqT.loc[mask,'Eq'] = eqT.loc[mask,'PRFRM_COEFF'].apply(lambda x: self.np.poly1d([float(i) for i in x.split(',')]))
            d = eqT[mask].pivot_table(columns=['PUMP_IDX'],index=[CondType],values='Eq',aggfunc=max)
            eqs.append(d)
                
        return eqs[0],eqs[1]

    def getPumpAttribute(self, pmTable="EMS_DB.TB_CTR_PRF_PUMPMST_INF", pumpGroup=None):
        sql = f"""
        select * FROM {pmTable} 
        WHERE USE_YN=1 and RGSTR_TIME IN (SELECT MAX(RGSTR_TIME) FROM {pmTable} GROUP BY PUMP_IDX)
        """ # TODO
        if pumpGroup is not None:
            sql += f" and PUMP_GRP = {pumpGroup}"

        cursor = self.conn.cursor(DictCursor)
        print(sql)
        cursor.execute(sql)
        data = cursor.fetchall()


        pumpAttr = pd.DataFrame(data)

        if 'LEI_IDX' in pumpAttr.columns:
            pumpAttr = pumpAttr[ pumpAttr['LEI_IDX'] == 1]

        pumpAttr = pumpAttr.set_index('PUMP_IDX').T


        pumpTags = list(set(pumpAttr.values.reshape(-1))) 

        rePattern = re.compile('[a-zA-z0-9]{3}-[a-zA-z0-9]{3}-[a-zA-z0-9]{3}-[a-zA-z0-9]{3}')

        for val in reversed(pumpTags):
            if rePattern.match(str(val)):
                continue
            pumpTags.remove(val)

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
        t = int(round(t))

        if self.__is_number(q) :
            q = [q]
            
        if isinstance(idx,list) :
            if len(idx) > 1 :
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
        qh_eqs,qp_eqs = self.__get_qh_qp_eqs_inv(idxs,f)
        if self.__is_number(q) :
            q = [q]
        
        return self.__joint_pump_Power_at_Q(qh_eqs,qp_eqs,q)
        
    def power_given_HnT(self,idxs,h,t):
        t = int(round(t))

        if self.__is_number(h) :
            h = [h]
            
        if not isinstance(idxs,list) :
            idxs=[idxs]
        
        qh_eqs = self.QH[idxs].loc[t]
        qp_eqs = self.QP[idxs].loc[t]
       
        return self.__joint_pump_Power_at_H(qh_eqs,qp_eqs,h)
    
    def power_given_HnF(self,idxs,h,f):
        if self.__is_number(h) :
            h = [h]
            
        qh_eqs,qp_eqs = self.__get_qh_qp_eqs_inv(idxs,f)
                    
        return self.__joint_pump_Power_at_H(qh_eqs,qp_eqs,h)
    
    def __get_qh_qp_eqs_inv(self,idxs,f):
        if isinstance(idxs,list) :
            if isinstance(f,list) :
                if len(f) == len(idxs): IdxnFreq = zip(idxs,f)
                else : 
                 #   print(len(idxs),len(f),'Check idxs,f size!!')
                    IdxnFreq = zip(idxs,f)
            else : 
                if len(idxs) == 1 : IdxnFreq = zip(idxs,[f])
                else : 
                 #   print(idxs,f,'Check idxs,f size!!')
                    IdxnFreq = zip(idxs,[f])
        else :
            IdxnFreq = zip([idxs],f) if isinstance(f,list) else zip([idxs],[f])
            
        qh_eqs =[];qp_eqs=[]
        for idx,fval in IdxnFreq :
            ref_freq = self.QHinv[idx].dropna().index[0]
            e = self.QHinv.loc[ref_freq][idx]
            e = self.__reduced_Eq_inv(e,ref_freq,fval)
            qh_eqs.append(e)
            ref_freq = self.QPinv[idx].dropna().index[0]
            e = self.QPinv.loc[ref_freq][idx]
            e = self.__reduced_Eq_inv(e,ref_freq,fval,beta=3)
            qp_eqs.append(e)
        return qh_eqs, qp_eqs
    
    def get_qh_qp_eqs_inv(self,idxs,f):
        return self.__get_qh_qp_eqs_inv(idxs,f)
    
    def flow_given_HnT(self,idxs,h,t):
        t = int(round(t))
        if self.__is_number(h) :
            h = [h]
            
        if not isinstance(idxs,list) :
            idxs=[idxs]
        
        qh_eqs = self.QH[idxs].loc[t]
        
        return self.__joint_pump_flow_at_H(qh_eqs,h)
    
    def flow_given_HnF(self,idxs,h,f):
        if self.__is_number(h) :
            h = [h]
            
        if not isinstance(idxs,list) :
            idxs=[idxs]
            
        qh_eqs,qp_eqs = self.__get_qh_qp_eqs_inv(idxs,f)
        
        return self.__joint_pump_flow_at_H(qh_eqs,h)
    
    def __each_pump_flow_at_H(self,eqs,head):
        res = []
        #print('__each_pump_flow_at_H: ', eqs)
        #print(eqs)

        for eq in eqs :
            roots = (eq-head).roots
            condlist = self.np.isreal(roots)
            roots= self.np.select(condlist, roots)
            _max = self.np.real(roots).max()
            _max = 0 if _max < 0 else _max
            res.append(_max)
        return res

    def __joint_pump_Power_at_Q(self,qh_eqs,qp_eqs,Qs):
                
        res = []
        print('Qs!', Qs)
        for q in Qs :
            head = self.__joint_pump_head_at_Q_atomic(qh_eqs,q)
            qs = self.__each_pump_flow_at_H(qh_eqs,head)            
            print('head: ', head)
            print('result qs: ', qs);
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
        res = []
        qh_eqs = self.QH[idxs].loc[t]
        for q in Qs :
            head = self.__joint_pump_head_at_Q_atomic(qh_eqs,q)
            print('head: ', head)
            res.append(head)

        return self.np.array(res)
     
    def __joint_pump_head_at_QnF(self,idxs,Qs,f):
        # new func.
        res = []
        qh_eqs = []
        for idx,fval in zip(idxs,f):
            ref_freq = self.QHinv[idx].dropna().index[0]
            e = self.QHinv[idx].loc[ref_freq]
            e = self.__reduced_Eq_inv(e,ref_freq,fval)
            qh_eqs.append(e)
            
        for q in Qs :
            head = self.__joint_pump_head_at_Q_atomic(qh_eqs,q)
            res.append(head)

        return self.np.array(res)
        
    
    def __joint_pump_head_at_Q_atomic(self,qh_eqs,Q,h1=90,h2=0,dh=10):
        # change func. check please!!
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
        return self.__each_pump_flow_at_H(qh_eqs,h)
    
    def freq_given_QnH(self,idxs,q,h,mode=1):
    # mode : 1=singlePump, synchronous multi-Pump, 2= single controll pump and max freq. multi-Pump
        if not isinstance(idxs,list) :
            idxs = [idxs]
            
        qh_eqs = [];ref_freq=[];target_freq=[]
        for idx in idxs :
            f = self.QHinv[idx].dropna().index[0]
            e = self.QHinv.loc[f][idx]
            qh_eqs.append(e)
            ref_freq.append(f)
            target_freq.append('max')

        qh_attr = self.pd.DataFrame({'qh_eqs':qh_eqs,'ref_freq':ref_freq,'target_freq':target_freq})
        if mode == 1 :
            qh_attr['target_freq'] = 'ctr'
            qh_attr = qh_attr.to_numpy()
            return self.__freq_given_QnH_for_single_pump(qh_attr,q,h)
        else :
            qh_attr.loc[qh_attr.index[-1],'target_freq'] = 'ctr'
            qh_attr = qh_attr.to_numpy()
            return self.__freq_given_QnH_for_single_pump(qh_attr,q,h)

    def __freq_given_QnH_for_single_pump(self,qh_attr,Q,h,f1=60,f2=0,df=2):
        # change func. check please!!
        fs = self.np.arange(f1,f2,-df)
        for f in fs :
            eq1 = self.__reduced_Eqs_inv(qh_attr,f-df)
            eq2 = self.__reduced_Eqs_inv(qh_attr,f)
            qs1 = self.each_pump_flow_at_EqnH(eq1,h)
            qs2 = self.each_pump_flow_at_EqnH(eq2,h)
            sum1 = sum(qs1)
            sum2 = sum(qs2)
            if (Q - sum1 > 0) and (Q - sum2 < 0):
                if ((sum2-sum1) < 2) or (df < 0.001) :
                    f = ((Q - sum1)*f2+(sum2-Q)*f1)/(sum2-sum1)
                    return round(f,2)
                return self.__freq_given_QnH_for_single_pump(qh_attr,Q,h,f1=f,f2=f-df,df=df*0.5)
            else :
                if (Q - sum1) == 0:
                    return round(f,2)
                elif (Q - sum2 == 0) :
                    return round(f-df,2)

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

        self.pmp_idxs = self.CTR_PRF_PUMP_INF["PUMP_IDX"]
        self.pmp_use_yns = self.CTR_PRF_PUMP_INF["USE_YN"]
        self.tot_pmp_num = len(self.pmp_idxs)        
        self.pmp_sz = dict(zip(self.pmp_idxs, self.CTR_PRF_PUMP_INF['PRRT_TYP'].values))
        df = self.CTR_PRF_PUMP_INF    

        self.fr_tags = df["FRI_TAG"].values.tolist()
        self.pr_tags = df["PRI_T_TAG"].values.tolist()
        self.te_tags = df["TEI_TAG"].values.tolist()
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
        """ h: 양정(CPP.head_given...), le:흡수정수위, te:정수수온, """
        if le is None:
            le = self.le
        
        if te is None:
            te = self.te
        
        return p * offset / self.FPPC.rho_water(te) - le + 3

    def head2pressure(self, h, le=None, te=None, offset=1e4):
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
        debug_flag = False 
        self.pmb_idxs = pmb_idxs
        for t in self.te_tags:
            d = current_data[t]
            if current_data[t] == 0:
                current_data[t] = 20
        
        C = self.set_pump_combinations()
        print('C: ',C)
        self.fr0 = current_data[self.fr_tags[0]]
        self.pr0 = current_data[self.pr_tags[0]]
        self.te0 = current_data[self.te_tags[0]]

        if round(self.pr0, 2) < pr_L:
            upward = True
        elif round(self.pr0, 2) >= pr_H:
            upward = False

        Q = self.get_Q(upward)
        A = []
        for c in C:
            print('c: ', c)
            h0 = self.CPP.head_given_QnT(c, self.fr0, self.te0)
            pr0 = self.head2pressure(h0)
            v = np.sign(int(upward) - .5) * np.sign(pr0 - self.pr0)

            if np.sign(int(upward) - .5) * np.sign(pr0 - self.pr0) > 0:
                hs = self.CPP.head_given_QnT(c, Q, self.te0)
                prs = self.head2pressure(hs) # ex. [6.865, 6.854, ..., 6.683]
                A.append([",".join([str(x) for x in c])] + list(prs))
            else:
                continue

        A = pd.DataFrame(A, columns=['C']+list(range(len(Q)))) # A : pressure (펌프 조합에 따른 펌프 압력 변화 배열)
        print(A)

        B = pd.DataFrame(columns=range(len(Q)))
        slope_classes = ['FAST','MIDDLE']#,'SLOW']
        slopes = [1/450., 1/1000.] #[1/500., 1/1000.] #[1/300., 1/300.] #[1/800., 1/1000., 1/1200.] #[1/500., 1/1000., 1/1500.] ########## 2022-06-22
        b = []

        for s in slopes: # ex. s=1/500
            dQ = Q - self.fr0 
            dP = dQ * s
            prs = self.pr0 + dP # ex. [6.6, 6.7, ... , 7.7]
            b.append(list(prs))

        B = pd.concat((B, pd.DataFrame(b)), axis=0)
        B = pd.concat((pd.DataFrame(slope_classes, index=B.index, columns=['S']), B), axis=1)

        D = []
        for _, c in A.iterrows(): # ex. c[0]=c=[5], c[1]=h=[55], c[2]=6.864766, ...
            d = []
            for _, s in B.iterrows(): # ex. s[0]=s=['FAST'], s[1]=6.6, ...
                a = c.values[1:]
                b = s.values[1:]
                di = np.argmin(np.abs(a-b))
                d.append(di)
            D.append(d)
            
        D = pd.DataFrame(D, columns=slope_classes)

        P = []

        for i, a in A.drop(columns=['C']).iterrows():
            P.append(a.values[D.values[i]])
        P = pd.DataFrame(P, columns=slope_classes)
        P = pd.concat((A[['C']], P), axis=1)

        P_copy = P.copy()
        #TEMP!
        #P_copy = P_copy.loc[~(np.any(np.round(P_copy[slope_classes].values,2) > pr_H, axis=1))] # 상한을 넘어가는 조합은 선택하지 않음. # any -> all (11-01)
        #P_copy = P_copy.loc[~(np.any(np.round(P_copy[slope_classes].values,2) < pr_L, axis=1))] # 하한을 하회하는 조합은 선택하지 않음. # any -> all (jrp)

        #TEMP!
        if (len(P_copy)<1) and (upward) and (self.pr0 < pr_L - 0.5):
            P_copy = P.copy()
            P_copy = P_copy.loc[~(np.any(np.round(P_copy[['MIDDLE']].values,2) > pr_H, axis=1))] # 상한을 넘어가는 조합은 선택하지 않음. # any -> all (11-01)
            P_copy = P_copy.loc[~(np.any(np.round(P_copy[['MIDDLE']].values,2) < pr_L - 0.1, axis=1))] # 하한을 하회하는 조합은 선택하지 않음. # any -> all (jrp)
        
        P = P_copy

        W = P.apply(lambda r: self.CPP.power_given_HnT([int(x) for x in r['C'].split(",")],r['MIDDLE'], self.te0)[0], axis=1)
        #print("9. P의 c들 중 s[1](중간 시스템 곡선)의 예상유량값(R[c])을 계산한다.")
        R = P.apply(lambda r: self.CPP.flow_given_HnT([int(x) for x in r['C'].split(",")],self.pressure2head(r['MIDDLE']), self.te0)[0], axis=1)

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

    with open('datafeeder.json') as w:
        feeder = json.load(w)[feeder]
        print(feeder)

    ctr_df = get_tags(conn, pumpGroup=args.pumpGroup, pmTable=feeder['pmtable'])
    database = feeder['database']

    pdbc = PumpEQ_DB_connector(conn);
    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=args.pumpGroup, pmTable=feeder['pmtable'])

    st_date = pd.Timestamp(args.start_date) 
    end_date = pd.Timestamp(args.end_date)

    raw_data = select_data_from_rdb_with_tags(conn, pumpTags, st_date, end_date, table=feeder["rawtable"])
    raw_df = pd.DataFrame(raw_data)
    raw_df = raw_df.pivot(index='ts', columns='tagname')['value']

    for c in raw_df.columns:
        raw_df[c] = raw_df[c].astype(float)

    df = raw_df.resample('1min').mean().fillna(0)
    #df[ df["865-334-FRI-4001"] == 0 ] = df[ df["865-334-FRI-4001"] != 0 ].mean() #TEMP!

    df.index = pd.to_datetime(df.index)

    pc = PumpControl(conn, None, ctr_df, pumpAttr, pumpTags, database=database)
    _df = pc.FPPC.calc_diff_head(df) # proc
    #print(_df)

    #QH = pc.FPPC.calc_equationTable_NonInv(_df, 'h',[1,2,3], st_date=st_date)
    #QP = pc.FPPC.calc_equationTable_NonInv(_df, 'p',[1,2,3], st_date=st_date)

    df = pc.pump_algo(_df, pumpAttr.columns)
    print(df)
    df.to_csv("result.csv")
    df["START_DATE"] = st_date
    return

    #print('tags: ', pumpTags)
    print('tot_tags: ', tot_tags)

    if args.source_type == 'file':
        raw_df = pd.read_csv(args.input_file, index_col=0)
        raw_df.index = pd.to_datetime(raw_df.index)
        raw_df = raw_df[tot_tags]
    else:
        raw_data = select_data_from_rdb_with_tags(conn, tot_tags, pd.Timestamp(args.start_date), pd.Timestamp('2022-11-02'))
        raw_df = pd.DataFrame(raw_data).pivot(index='ts', columns='tagname')['value']

    raw_df = raw_df.resample('1min').mean().fillna(0)
    print(fr_tags, pr_tags, te_tags, lei_tags, pmb_tags)
    print(raw_df)

    pc.pump_algo(raw_df)

    return 1

    fr0 = fr_tags[0]
    pr0 = pr_tags[0]
    te0 = te_tags[0]
    pmb0 = pmb_tags[0] 

    pr_HH, pr_LL = 8.5, 6.4

    pr_H, pr_L = calc_pr_HL(pr_HH, pr_LL, 0) 
    pr_H, pr_L = pr_HL_buffering(pr_H, pr_L, )

    print(pr_H, pr_L)


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
  