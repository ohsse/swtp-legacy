import tensorflow as tf
from dataset import WindowGenerator, load_dataset_rdb, load_dataset, load_dataset_rdb_1c
#from matplotlib import pyplot
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

from datetime import datetime
from slogger import get_logger
logger = get_logger('predict_comp_ks_RE', 'ems_al.log', 'GS')
loggerView = get_logger('predict_comp_ks_RE_view', 'view_ems_al.log', 'GS')

# TensorFlow에 사용할 최대 스레드 수를 설정
#tf.config.threading.set_inter_op_parallelism_threads(2)
#tf.config.threading.set_intra_op_parallelism_threads(2)


def get_ts(start_date, interval, length):
    start_date = pd.Timestamp(start_date) 
    res = []

    for _ in range(length):
        res.append(start_date)
        start_date += pd.Timedelta(minutes=interval)
        
    return res

def get_data(conn, table, tag, st_date, end_date, scaler,subGroup):
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

     # IN TAG 전송 부분 시작
    viewInDf = pd.DataFrame()
    rawDatadf = pd.DataFrame()
    # TS 컬럼에서 시간 추출
    rawDatadf = df[df['TS'].dt.minute == 0]
    rawDatadf['Hour'] = rawDatadf['TS'].dt.hour

    # VALUE 값을 tag_val에 직접 할당
    viewInDf['tag_val'] = rawDatadf['VALUE']
    viewInDf['time'] = rawDatadf['TS'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    #viewInDf['time'] = df['TS'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    viewInDf['site'] = 'GS'
    viewInDf['step'] = 'EMS_AL'
    
    def assign_fri_tag_desc(hour, subGroup):
        if subGroup == '1':
            text = "고산(구) 정수장 전체유량 ["+ str(hour)+"시]"
            #701-367-FRI-4001
        else:
            text = "고산(신) 정수장 전체유량 ["+ str(hour)+"시]"
            #701-367-FRI-4004
        return text

    # Hour 컬럼을 기반으로 tag_sn 컬럼 추가
    if subGroup =='1':
        viewInDf['tag_sn'] = '701-367-FRI-4001'
        viewInDf['desc'] =  rawDatadf['Hour'].apply(lambda hour: assign_fri_tag_desc(hour, subGroup))
    else:
        viewInDf['tag_sn'] = '701-367-FRI-4004'
        viewInDf['desc'] = rawDatadf['Hour'].apply(lambda hour: assign_fri_tag_desc(hour, subGroup))
    
    viewInDf['itm'] = 'FRI'
    viewInDf['kind'] = 'IN'
    print(viewInDf)
    for index, row in viewInDf.iterrows():
        print(row.to_dict())
        json_message = json.dumps(row.to_dict(), ensure_ascii=False)
        loggerView.info(json_message)
    # IN TAG 전송 부분 종료

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

    logger.info(f'{{"STR_DT":"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"}}')

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
        #print('GET s',s)
        #print('GET m',m)
        ts = pd.Timestamp(args.target_date)

        start_ts = ts - pd.Timedelta(hours=24) + pd.Timedelta(hours=int(args.target_hour))
        end_ts = ts + pd.Timedelta(hours=int(args.target_hour))
        
        #print('session["input_table"]',session["input_table"])
        #print('session["dataset"]["label_col"]',session["dataset"]["label_col"])
        try:
            df = get_data(connection, table=session["input_table"], tag=session["dataset"]["label_col"], st_date=start_ts, end_date=end_ts, scaler=scaler, subGroup=subGroup)
        except Exception as e:
            logger.error(f'{{"ERR_MSG":"Data loading failed: {e}"}}')
            exit()
        #print('####getData',df)
        try:
            v = df.values.reshape((-1, 1440, 7)).astype(np.float32)
            #v1 = df.values.reshape((-2, 1440, 7)).astype(np.float32)
            print('#LoadModel Start:',session["model_output_name"])
            model = tf.keras.models.load_model(session["model_output_name"])
            print('#LoadModel End:',session["model_output_name"])
            result = model.predict(v)

            result = result.reshape(-1, 1) * s + m
            
            df = pd.DataFrame(data=result, columns=['PRDCT_MEAN'])

            df["PRDCT_TIME"] = get_ts( pd.Timestamp(args.target_date) + pd.Timedelta(hours=int(args.target_hour)+1), 60, 24)
            df["ANLY_TIME"] = pd.Timestamp.now()

            #df["INF_REF_END"] = get_ts( pd.Timestamp(args.start_date) + pd.Timedelta(minutes=session["window_generator"]["input_time_min_range"]), session["window_generator"]["input_time_min_range"], predict.shape[0])
            df["PRDCT_TIME_DIFF"] = session["window_generator"]["input_time_min_range"]

            #df["RST_DURATION"] = session["window_generator"]["output_min_time"]
            #df["PRDT_TYPE"] = 'AVG'
            d = args.target_date.replace('-', '') 

            df['DC_NMB'] = 'a '
            df['FLAG'] = 1
        except Exception as e:
            logger.error(f'{{"ERR_MSG":"Model loading or prediction failed: {e}"}}')
            exit()

        #from pump_rt_models import FitPumpPerformanceCurve
        #from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector
        #from pump_rt_algo import get_connection

        #pdbc = PumpEQ_DB_connector(connection)
        #pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=int(args.pumpGroup), pmTable=f'{database}.TB_CTR_PRF_PUMPMST_INF')

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
        
        #print('########## dfdfdfdf #############',df)

        results = [predict_pwr(Q, freqs) for (idxs, _, freqs), Q in zip(idxs, df['PRDCT_MEAN'].values)]
        df['PWR_PRDCT'] = [result[0] for result in results]  # First element is the predicted power
        df['TUBE_PRSR_PRDCT'] = [result[1] for result in results]  # Second element is the tmp value
        #df['FREQ'] = [result[3] for result in results]  # Second element is the tmp value

        ttag = str(pd.Timestamp.now().hour) + str(pd.Timestamp.now().minute)
        df["OPT_IDX"] = df["PRDCT_TIME"].apply(lambda x: "701-367-FRI:" + x.strftime("%Y%m%d%H%s") + "-" +  ttag)
        df["PUMP_GRP"] = args.pumpGroup
        
        pmp_idxs = list(x[1] for x in idxs)

        df = df.drop('FREQ', axis=1)

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

    #예측 결과 전송 시작
    viewDf = pd.DataFrame()
    # PRDCT_TIME 컬럼에서 시간 추출
    df_2['Hour'] = df_2['PRDCT_TIME'].dt.hour

    # PWR_PRDCT 값을 tag_val에 직접 할당
    viewDf['tag_val'] = df_2['PWR_PRDCT']
    viewDf['time'] = df_2['PRDCT_TIME'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    viewDf['site'] = 'GS'
    viewDf['step'] = 'EMS_AL'

    # tag_sn 생성 및 tag_val 설정을 위한 함수 정의
    #전력
    def assign_pwr_tag_sn(hour , nowPumpGroup):
        if nowPumpGroup == '1':
            base_tag = 1212  # 시작 태그 번호
        else:
            base_tag = 1140  # 시작 태그 번호
        
        return f'701-367-EMS-{base_tag + hour}'
    
    def assign_pwr_tag_desc(hour , nowPumpGroup):
        if nowPumpGroup == '1':
            text = "고산(구) 정수장용수수요 전력예측 시간대 ["+ str(hour)+"시]"
        else:
            text = "고산(신) 정수장용수수요 전력예측 시간대 ["+ str(hour)+"시]"
        return text

    # Hour 컬럼을 기반으로 tag_sn 컬럼 추가
    viewDf['tag_sn'] = df_2['Hour'].apply(lambda hour: assign_pwr_tag_sn(hour, nowPumpGroup))
    viewDf['itm'] = 'PWR'
    viewDf['desc'] = df_2['Hour'].apply(lambda hour: assign_pwr_tag_desc(hour, nowPumpGroup))
    viewDf['kind'] = 'OUT'

    for index, row in viewDf.iterrows():
        json_message = json.dumps(row.to_dict(), ensure_ascii=False)
        loggerView.info(json_message)
    df_2 = df_2.drop('Hour', axis=1)
    #예측 결과 기록 종료

    try:
        cursor = connection.cursor()
        query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"
        query = query_form.format(TB_NM='TB_CTR_OPT_RST',
                                    COLUMNS='`, `'.join(df_2.columns.tolist()),
                                    VALS=(",".join(["%s"] * df_2.shape[1])))

        cursor.executemany(query, df_2.values.tolist())

        #from pump_rt_algo import get_connection_alchemy_s
        #aconn = get_connection_alchemy_s(connection_key)
        #optdf.to_sql('TB_CTR_PUMPYN_RST', if_exists="append", con=aconn, index=False)
        
        connection.commit()
    except pymysql.MySQLError as e:  # Use pymysql.MySQLError for catching PyMySQL errors
        logger.error(f'{{"ERR_MSG":"DataFrame manipulation or SQL database storage failed: {e}"}}')
        exit()
    logger.info(f'{{"END_DT":"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"}}')
    connection.close()
    exit(0)
