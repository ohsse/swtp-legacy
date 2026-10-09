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

    if startdts.strftime('%Y-%m-%d %h:%m:%s') != st_date.strftime('%Y-%m-%d %h:%m:%s'):
        frimean = sum(list( float(x["VALUE"]) for x in data)) / len(data)
        data.insert(0, { 'TAGNAME': tag, 'TS': st_date, 'VALUE': frimean, 'QUALITY': 100, 'SERVER': None }) 

    df = pd.DataFrame(data)
    print(df)

    df["VALUE"] = df["VALUE"].astype(np.float32)

    df = df.pivot(index='TS', columns='TAGNAME')['VALUE']
    df = df.fillna(method='ffill')

    df = df.resample('1min').mean()
    df = df.fillna(method='ffill')
    df = df.fillna(0)

    print(df)
    df = df[[tag]]
    df[tag] 
    df[[tag]] = scaler.transform(df[[tag]])

    df.index = pd.to_datetime(df.index)
    df = time2vec(df)
    
    return df

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

    with open(args.mjson) as f :
        config = json.load(f)

    session = config[session_name]
    connection_key = session["connection"]

    with open('connections.json') as f:
        connection = json.load(f)[connection_key]
        connection = pymysql.connect(**connection)

    label_col = session['dataset']['label_col']
    scaler_path = session["scaler_output_name"]
    database = args.database

    scaler = joblib.load(scaler_path)
    s, m = scaler.scale_[0], scaler.mean_[0]

    ts = pd.Timestamp(args.target_date)

    #start_ts = ts - pd.Timedelta(hours=25) + pd.Timedelta(hours=int(args.target_hour))
    #end_ts = ts - pd.Timedelta(hours=1) + pd.Timedelta(hours=int(args.target_hour))

    start_ts = ts - pd.Timedelta(hours=24) + pd.Timedelta(hours=int(args.target_hour))
    end_ts = ts + pd.Timedelta(hours=int(args.target_hour))
    
    df = get_data(connection, table=session["input_table"], tag=session["dataset"]["label_col"], st_date=start_ts, end_date=end_ts, scaler=scaler)
    v = df.values.reshape((-1, 1440, 7)).astype(np.float32)

    model = tf.keras.models.load_model(session["model_output_name"])
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

    df['DC_NMB'] = 'a'
    df['FLAG'] = 1

    from pump_rt_models import FitPumpPerformanceCurve
    from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector
    from pump_rt_algo import get_connection

    pdbc = PumpEQ_DB_connector(connection)
    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=int(args.pumpGroup))
    print(pumpAttr)
    print(pumpTags)

    FPPC = FitPumpPerformanceCurve(pumpAttr, pumpTags)
    CPP = Calc_pump_properties(connection, pumpAttr, pumpTags, database=database)


    def getpumpcomb_gs_1(fr):
        if fr < 15662:
            return [[3], [0,0,1,0]]
        elif fr < 16995:
            return [[4], [0,0,0,1]]
        else:
            return [[4], [0,0,0,1]]

    def getpumpcomb_gs_2(fr):
        if fr < 3924:
            return [[10], [0,0,0,0,1,1,1]]
        elif fr < 3966:
            return [[9,10,11],[0,0,0,0,1,1,1]]
        else:
            return [[9,10,11],[0,0,0,0,1,1,1]]

    func = getpumpcomb_gs_1  if int(args.pumpGroup) == 1 else getpumpcomb_gs_2
    
    idxs = df["PRDCT_MEAN"].apply(lambda x : func(x)).values.tolist()

    if int(args.pumpGroup) == 1:
        pumpidxs = [1,2,3,4]
    else :
        #df["PRDCT_MEAN"] *= 3
        pumpidxs = [5,6,7,8,9,10,11]

    print(df)
    df['TUBE_PRSR_PRDCT'] = [CPP.head_given_QnT(idxs[0], Q, 20)[0]*FPPC.rho_water(20)/1e4 for idxs, Q in zip(idxs, df['PRDCT_MEAN'].values)] # 2개 이상이면 예측 관압이 0이 나오는 이유 확인 해야 함 
    df['PWR_PRDCT'] = [CPP.power_given_QnT(idxs[0], Q, 20)[0] for idxs, Q in zip(idxs, df['PRDCT_MEAN'].values)]
    df['PWR_PRDCT'] = df['PWR_PRDCT'].clip(lower=200.0)

    ttag = str(pd.Timestamp.now().hour) + str(pd.Timestamp.now().minute)  + str(pd.Timestamp.now().second)
    df["OPT_IDX"] = df["PRDCT_TIME"].apply(lambda x: "701-367-FRI:" + x.strftime("%Y%m%d%H") + "-" +  ttag)

    df["PUMP_GRP"] = args.pumpGroup
    query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"

    print(df)
    query = query_form.format(TB_NM='TB_CTR_OPT_RST',
                              COLUMNS='`, `'.join(df.columns.tolist()),
                              VALS=(",".join(["%s"] * df.shape[1])))

    cursor = connection.cursor()
    cursor.executemany(query, df.values.tolist())
    connection.commit()
    connection.close()

    pmp_idxs = list(x[1] for x in idxs)
    print(pmp_idxs)
    pump_yn_df = pd.DataFrame(pmp_idxs, columns=pumpidxs) #TODO
    pump_yn_df["OPT_IDX"] = df["OPT_IDX"]

    ctr_optfk_rst = pump_yn_df.melt('OPT_IDX', var_name="PUMP_IDX", value_name="PUMP_YN")
    
    ctr_optfk_rst["PUMP_TYP"] = 1
    ctr_optfk_rst["DC_NMB"] = 'test'
    ctr_optfk_rst["FLAG"] = 0
    ctr_optfk_rst["PUMP_GRP"] = args.pumpGroup

    ctr_optfk_rst['PUMP_YN'] = ctr_optfk_rst['PUMP_YN'].astype(int)
    ctr_optfk_rst['FREQ'] = 0
    from pump_rt_algo import get_connection_alchemy_s
    aconn = get_connection_alchemy_s(connection_key)
    print(ctr_optfk_rst)
    ctr_optfk_rst = ctr_optfk_rst.drop_duplicates(['OPT_IDX', 'PUMP_GRP', 'PUMP_IDX'])
    ctr_optfk_rst.to_sql('TB_CTR_PUMPYN_RST', if_exists="append", con=aconn, index=False)

