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
from train_peak_model_gm import get_data

def get_ts(start_date, interval, length):
    start_date = pd.Timestamp(start_date) 
    res = []

    for _ in range(length):
        res.append(start_date)
        start_date += pd.Timedelta(minutes=interval)
        
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')

    parser.add_argument('--target_date')
    parser.add_argument('--target_hour')
    parser.add_argument('--feeder')

    parser.add_argument('--mjson', default='defmodel.json')

    args = parser.parse_args()
    session_name = args.session

    with open("datafeeder.json") as f :
        feeder = json.load(f)[args.feeder]

    with open(args.mjson) as f :
        config = json.load(f)

    session = config[session_name]
    connection_key = session["connection"]

    with open('connections.json') as f:
        connection = json.load(f)[connection_key]
        connection = pymysql.connect(**connection)

    label_col = session['dataset']['label_col']
    scaler_path = session["scaler_output_name"]
    database = feeder["database"]
    pmtable = feeder["pmtable"]

    scaler = joblib.load(scaler_path)
    s, m = scaler.scale_[0], scaler.mean_[0]

    ts = pd.Timestamp(args.target_date)

    #start_ts = ts - pd.Timedelta(hours=25) + pd.Timedelta(hours=int(args.target_hour))
    #end_ts = ts - pd.Timedelta(hours=1) + pd.Timedelta(hours=int(args.target_hour))

    start_ts = ts - pd.Timedelta(hours=24) + pd.Timedelta(hours=int(args.target_hour))
    end_ts = ts + pd.Timedelta(hours=int(args.target_hour))

    from pump_rt_models import FitPumpPerformanceCurve
    from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector
    from pump_rt_algo import get_connection

    pdbc = PumpEQ_DB_connector(connection)
    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=None, pmTable=pmtable)

    print(pumpAttr)
    print(pumpTags)

    tags = pumpAttr.loc["PWI_TAG", :].values.tolist()

    df, scaler = get_data(connection, table=session["input_table"], tags=tags, st_date=start_ts, end_date=end_ts, label_col=label_col)
    s, m = scaler.scale_[0], scaler.mean_[0]

    ts = pd.Timestamp(args.target_date)
    start_ts = ts - pd.Timedelta(hours=24) + pd.Timedelta(hours=int(args.target_hour))
    end_ts = ts + pd.Timedelta(hours=int(args.target_hour))

    v = df.values.reshape((-1, 1440, 7)).astype(np.float32)

    model = tf.keras.models.load_model(session["model_output_name"])
    result = model.predict(v)
    result = result.reshape(-1, 1) * s + m

    df = pd.DataFrame(data=result, columns=['PWR_PRDCT'])
    
    df["PRDCT_TIME"] = get_ts( pd.Timestamp(args.target_date) + pd.Timedelta(hours=int(args.target_hour)), 60, 24)

    ttag = str(pd.Timestamp.now().hour) + str(pd.Timestamp.now().minute)
    df["OPT_IDX"] = df["PRDCT_TIME"].apply(lambda x: "GSPWI:" + x.strftime("%Y%m%d%H") + "-" +  ttag)
    df["ANLY_TIME"] = pd.Timestamp.now()
    df["PRDCT_TIME_DIFF"] = session["window_generator"]["input_time_min_range"]
    df["PRDCT_STD"] = 0
    df["PUMP_GRP"] = 1
    df["TUBE_PRSR_PRDCT"] = 0
    df["PRDCT_MEAN"] = 0

    from pump_rt_algo import get_connection_alchemy_s
    aconn = get_connection_alchemy_s(connection_key)
    df.to_sql("TB_CTR_OPT_RST", if_exists="append", con=aconn, index=False)

    print(df)
