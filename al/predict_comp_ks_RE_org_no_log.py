import tensorflow as tf
from dataset import WindowGenerator, load_dataset_rdb, load_dataset, load_dataset_rdb_1c
from matplotlib import pyplot
import pandas as pd
import json
import argparse
from cutils import _import
import joblib
import numpy as np
from op import psqr 
from dataset import DataSets
from preprocessing import time2vec
from sqlalchemy import create_engine
import pymysql
from pymysql.cursors import DictCursor


def get_ts(start_date, interval, length):
    start_date = pd.Timestamp(start_date) 
    res = []

    for _ in range(length):
        res.append(start_date)
        start_date += pd.Timedelta(minutes=interval)
        
    return res

def get_data(conn, table, tag, st_date, end_date, scaler):
    sql = f"""
        select * from {table} where tagname = '{tag}' and ts >= '{st_date}' and ts < '{end_date}'
    """
    print(sql)

    cursor = conn.cursor(DictCursor)

    cursor.execute(sql)
    data = cursor.fetchall()
    startdts = pd.Timestamp(data[0]["TS"])

    if False and startdts.strftime('%Y-%m-%d %h:%m:%s') != st_date.strftime('%Y-%m-%d %h:%m:%s'):
        frimean = sum(list( float(x["VALUE"]) for x in data)) / len(data)
        data.insert(0, { 'TAGNAME': tag, 'TS': st_date, 'VALUE': frimean, 'QUALITY': 100, 'SERVER': None }) 

    df = pd.DataFrame(data)

    df["VALUE"] = df["VALUE"].astype(np.float64)
    #print('get_data FNC1', df)
    df = df.drop_duplicates(["TS", "TAGNAME"])
    #print('get_data FNC1-1', df)
    df = df.pivot(index='TS', columns='TAGNAME')['VALUE']
    #print('get_data FNC1-2', df)
    #df = df.fillna(df.mean())
    df = df.fillna(method='ffill')
    #print('get_data FNC1-3', df)
    df = df.resample('1min').mean()
    #print('get_data FNC1-4', df)
    df = df.fillna(method='ffill')
    #print('get_data FNC1-5', df)
    df = df.fillna(0)
    #df = df.fillna(df.mean())
    #print('get_data FNC1-6', df)
    df = df[[tag]]
    #print('get_data FNC1-7', df)
    df[[tag]] = scaler.transform(df[[tag]])
    #print('get_data FNC1-8', df)
    df.index = pd.to_datetime(df.index)
    #print('get_data FNC1-9', df)
    #print('get_data FNC1-9 index', df.index)
    df = time2vec(df)
    #print('get_data FNC2', df)
    return df

freqlist = []

def getRangeCase_ks_old(fr):
    if fr >= 16800:
        return 0
    elif fr < 16800:
        return 1
def getRangeCase_ks_new(fr):
    return 0

def func_old(fr):
    if fr >= 16800:
        return [[2,5,6,7,], [0,1,0,0,1,1,1], None]
    elif fr < 16800:
        return [[5,6,7,], [0,0,0,0,1,1,1], None]
    
def func_new(fr):
        return [[10,], [0,1,0,0], None]


f0_0_ks_old = lambda fr: (6.65747311539592) + (0.000024682825959774*fr) + (-0.000000006724816567*fr*fr)
f0_1_ks_old = lambda fr: (4.25420053258273) + (0.000383685292380573*fr) + (-0.000000022809755934*fr*fr)

f0list_ks_old = [f0_0_ks_old, f0_1_ks_old]

f0_0_ks_new  = lambda fr: (8.31343991874646) + (-0.000157455021461971*fr) + (-0.000000117106620951*fr*fr)

f0list_ks_new = [f0_0_ks_new]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')
    parser.add_argument('--target_date')
    parser.add_argument('--target_hour')
    parser.add_argument('--pumpGroup')
    parser.add_argument('--database')
    parser.add_argument('--mjson', default='defmodel.json')

    args = parser.parse_args()
    session_name = args.session
    
    nowPumpGroup = args.pumpGroup

    with open(args.mjson) as f :
        config = json.load(f)
    #print('config',config)
    #print('####session_name:',session_name)
    session = config[session_name]
    connection_key = session["connection"]

    with open('connections.json') as f:
        connection = json.load(f)[connection_key]
        connection = pymysql.connect(**connection)

    def _get(session, subGroup):
        label_col = session['dataset']['label_col']
        scaler_path = session["scaler_output_name"]
        database = args.database
        #print('####scaler_path:',scaler_path)
        #scaler = jobload(scaler_path)
        scaler = joblib.load(scaler_path)
        s, m = scaler.scale_[0], scaler.mean_[0]
        print('GET s',s)
        print('GET m',m)
        ts = pd.Timestamp(args.target_date)

        start_ts = ts - pd.Timedelta(hours=24) + pd.Timedelta(hours=int(args.target_hour))
        end_ts = ts + pd.Timedelta(hours=int(args.target_hour))
        
        #print('session["input_table"]',session["input_table"])
        #print('session["dataset"]["label_col"]',session["dataset"]["label_col"])

        df = get_data(connection, table=session["input_table"], tag=session["dataset"]["label_col"], st_date=start_ts, end_date=end_ts, scaler=scaler)
        
        #print('####getData',df)
        
        v = df.values.reshape((-1, 1440, 7)).astype(np.float32)
        #v1 = df.values.reshape((-2, 1440, 7)).astype(np.float32)
        
        #print('####vvvvvvv',v)
        #print('##############session["model_output_name"]',session["model_output_name"])
        model = tf.keras.models.load_model(session["model_output_name"])
        result = model.predict(v)

        #print('####getData11111 result',result)

        result = result.reshape(-1, 1) * s + m
        
        #print('####getData11111 result s + m',s + m)
        
        #print('####getData22222222 result',result)
        
        df = pd.DataFrame(data=result, columns=['PRDCT_MEAN'])
        
        #print('####getData22222222',df)


        df["PRDCT_TIME"] = get_ts( pd.Timestamp(args.target_date) + pd.Timedelta(hours=int(args.target_hour)+1), 60, 24)
        df["ANLY_TIME"] = pd.Timestamp.now()

        #df["INF_REF_END"] = get_ts( pd.Timestamp(args.start_date) + pd.Timedelta(minutes=session["window_generator"]["input_time_min_range"]), session["window_generator"]["input_time_min_range"], predict.shape[0])
        df["PRDCT_TIME_DIFF"] = session["window_generator"]["input_time_min_range"]

        #df["RST_DURATION"] = session["window_generator"]["output_min_time"]
        #df["PRDT_TYPE"] = 'AVG'
        d = args.target_date.replace('-', '') 

        df['DC_NMB'] = 'a '
        df['FLAG'] = 1

        from pump_rt_models import FitPumpPerformanceCurve
        from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector
        from pump_rt_algo import get_connection

        pdbc = PumpEQ_DB_connector(connection)
        pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=int(args.pumpGroup), pmTable=f'{database}.TB_CTR_PRF_PUMPMST_INF')

        #print('#subGroup', subGroup)

        if subGroup ==1:
            getRangeCase = getRangeCase_ks_old
            func = func_old
            pumpidxs = [1, 2, 3, 4, 5, 6, 7]
            f0list = f0list_ks_old
        
        else :
            getRangeCase = getRangeCase_ks_new
            func = func_new
            pumpidxs = [8, 9 , 10, 11]
            f0list = f0list_ks_new
        '''
        def predict_pwr(fr, freqs):
            rangeCase = getRangeCase(fr)
            f0 = f0list[rangeCase]

            if subGroup ==1: 
               f1_0 = lambda tmp, fr: (-36.6407*tmp) + (0.0049*fr) + (10.4872*60) + (13.5402*60) + (16.9349*60) + (11.7216*60) + (264.7133)
               f1_1 = lambda tmp, fr: (-36.6407*tmp) + (0.0049*fr) + (13.5402*60) + (16.9349*60) + (11.7216*60) + (264.7133)
               tmp = f0(fr)
               if rangeCase ==0:
                  pwr = f1_0(tmp, fr)
               else:
                  pwr = f1_1(tmp, fr)
            else :
                f1_2 = lambda tmp, fr: (tmp) + (fr) + ()
                tmp = f0_2_ks(fr)
                pwr = f1_2
            return pwr, tmp  # Return both pwr and tmp
        '''
        def predict_pwr(fr, freqs):
            #print('#predict_pwr fr',fr)
            rangeCase = getRangeCase(fr)
            #print('#predict_pwr rangeCase',rangeCase)
            #print('#predict_pwr f0list',f0list)
            f0 = f0list[rangeCase]
            #print('#predict_pwr f0',f0)
            #print('#predict_pwr subGroup',subGroup)
            if subGroup ==1: 
               f1_0 = lambda tmp, fr: (-36.6407*tmp) + (0.0049*fr) + (10.4872*60) + (13.5402*60) + (16.9349*60) + (11.7216*60) + (264.7133)
               f1_1 = lambda tmp, fr: (-36.6407*tmp) + (0.0049*fr) + (13.5402*60) + (16.9349*60) + (11.7216*60) + (264.7133)
               tmp = f0(fr)
               if rangeCase ==0:
                  pwr = f1_0(tmp, fr)
               else:
                  pwr = f1_1(tmp, fr)
            else :
                f2_0 = lambda tmp, fr: (-0.9869*tmp) + (0.0392*fr) + (578.5376)
                tmp = f0(fr)
                pwr = f2_0(tmp, fr)
            return pwr, tmp  # Return both pwr and tmp        
            
        idxs = df["PRDCT_MEAN"].apply(lambda x : func(x)).values.tolist()
        F = 0

        df["FREQ"] = F
        freq = df["FREQ"].values.tolist()
 
        #df['PWR_PRDCT'] = [ predict_pwr(Q, freqs) for (idxs, _, freqs), Q in zip(idxs, df['PRDCT_MEAN'].values)]
        
        print('########## dfdfdfdf #############',df)

        results = [predict_pwr(Q, freqs) for (idxs, _, freqs), Q in zip(idxs, df['PRDCT_MEAN'].values)]
        df['PWR_PRDCT'] = [result[0] for result in results]  # First element is the predicted power
        df['TUBE_PRSR_PRDCT'] = [result[1] for result in results]  # Second element is the tmp value
        #df['FREQ'] = [result[3] for result in results]  # Second element is the tmp value

        ttag = str(pd.Timestamp.now().hour) + str(pd.Timestamp.now().minute)
        df["OPT_IDX"] = df["PRDCT_TIME"].apply(lambda x: "701-367-FRI:" + x.strftime("%Y%m%d%H%s") + "-" +  ttag)
        df["PUMP_GRP"] = args.pumpGroup

        
        
        #print('###############  df##############')
        #print(df)
        
        #print('###############  idxs ##############')
        #print(idxs)
        
        
        pmp_idxs = list(x[1] for x in idxs)
        
        #print('####pmp_idxs',pmp_idxs)
        
        #pump_yn_df = pd.DataFrame(pmp_idxs, columns=pumpidxs) #TODO
        #pump_yn_df["OPT_IDX"] = df["OPT_IDX"]
        #pump_yn_df = pump_yn_df.merge(df[['OPT_IDX','FREQ']], on='OPT_IDX', how='left')

        df = df.drop('FREQ', axis=1)
        
        #print('###############  pump_yn_df ##############')
        #print(pump_yn_df)
        
        #ctr_optfk_rst = pump_yn_df.melt('OPT_IDX', var_name="PUMP_IDX", value_name="PUMP_YN")
        #freq_df = pump_yn_df[['OPT_IDX', 'FREQ']].drop_duplicates()
        # 'pump_idx' 열에서 'freq' 값을 제외하고 melt 작업을 위한 열을 선택
        #columns_to_melt = [col for col in pump_yn_df.columns if col not in ['OPT_IDX', 'FREQ']]

        # 1단계: 'OPT_IDX'와 'FREQ' 열만 선택하고 중복 제거
        #freq_df = pump_yn_df[['OPT_IDX', 'FREQ']].drop_duplicates()

        # 2단계: 수정된 pump_yn_df를 melt 함수를 사용하여 재구조화
        #ctr_optfk_rst = pump_yn_df.melt(id_vars='OPT_IDX', value_vars=columns_to_melt, var_name="PUMP_IDX", value_name="PUMP_YN")

        # 3단계: ctr_optfk_rst에 freq_df를 'OPT_IDX'를 기준으로 병합하여 'FREQ' 열 추가
        #ctr_optfk_rst = ctr_optfk_rst.merge(freq_df, on='OPT_IDX', how='left')
        
        #ctr_optfk_rst["PUMP_TYP"] = 1
        #ctr_optfk_rst["DC_NMB"] = 'test'
        #ctr_optfk_rst["FLAG"] = 0
        #ctr_optfk_rst["PUMP_GRP"] = args.pumpGroup
        #ctr_optfk_rst["FREQ"] = freq_df["FREQ"]

        #ctr_optfk_rst['PUMP_YN'] = ctr_optfk_rst['PUMP_YN'].astype(int)
        #ctr_optfk_rst = ctr_optfk_rst.merge(pump_yn_df, on='OPT_IDX', how='left')
        #ctr_optfk_rst = ctr_optfk_rst.drop_duplicates(['OPT_IDX', 'PUMP_GRP', 'PUMP_IDX'])
        
        
        
        #print('###############  ctr_optfk_rst##############')
        #print(ctr_optfk_rst)
       
        #print('###############  freq_df##############')
        #print(freq_df)

        
        return df
    print('####nowPumpGroup',nowPumpGroup)
    if nowPumpGroup == '1':
        print('####nowPumpGroup IF',nowPumpGroup)
        df_2 = _get(config['701-367-FRI-4001_24_cnn'], 1)
    else:
        print('####nowPumpGroup ELSE',nowPumpGroup)
        df_2 = _get(config['701-367-FRI-4004_24_cnn'], 2)
        
    #df_1 = _get(config['701-367-FRI-4001_24_cnn'], 1)
    

    #print('###############  opt_1 ##############')
    #print(opt_1) 

    #tdf = pd.concat([df_1, df_2]).sort_values('OPT_IDX')
    '''
    tdf = tdf.groupby('OPT_IDX').agg({
        'PRDCT_MEAN': 'sum',
        'PRDCT_TIME': 'max',
        'ANLY_TIME': 'max',
        'PRDCT_TIME_DIFF': 'max',
        'PWR_PRDCT': 'sum',
    })
    '''

    #tdf['PUMP_GRP'] = 3
    #tdf = tdf.sort_index()
    df_2['PRDCT_TIME_DIFF'] = range(1, df_2.index.size + 1)
    #df_2['OPT_IDX'] = df_2.index.values

    #optdf = pd.concat([opt_1, opt_2]).sort_values('OPT_IDX')
    #optdf['PUMP_GRP'] = 3
    
    print('###############  tdf ##############')
    print(df_2)

    cursor = connection.cursor()
    query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"
    query = query_form.format(TB_NM='TB_CTR_OPT_RST',
                                COLUMNS='`, `'.join(df_2.columns.tolist()),
                                VALS=(",".join(["%s"] * df_2.shape[1])))

    cursor.executemany(query, df_2.values.tolist())

    from pump_rt_algo import get_connection_alchemy_s
    aconn = get_connection_alchemy_s(connection_key)
    #optdf.to_sql('TB_CTR_PUMPYN_RST', if_exists="append", con=aconn, index=False)
    
    connection.commit()

    connection.close()
    exit(0)