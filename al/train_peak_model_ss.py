import tensorflow as tf
from dataset import WindowGenerator, load_dataset_rdb, load_dataset, load_dataset_rdb_1c
from matplotlib import pyplot
import pandas as pd
import json
import argparse
from cutils import _import, load_model_from_config
import joblib
import numpy as np
from op import psqr 
from dataset import DataSets
from preprocessing import time2vec
from sqlalchemy import create_engine
import pymysql
from pymysql.cursors import DictCursor
from sklearn.preprocessing import StandardScaler, MinMaxScaler

def get_ts(start_date, interval, length):
    start_date = pd.Timestamp(start_date) 
    res = []

    for _ in range(length):
        res.append(start_date)
        start_date += pd.Timedelta(minutes=interval)
        
    return res

def get_data(conn, table, tags, st_date, end_date, label_col):
    from functools import reduce
    tagss = reduce(lambda x, y : x + ',' + "'" + y + "'", tags, "")[2:-1]

    sql = f"""
        select * from {table} where tagname in ( '{tagss}' ) and ts >= '{st_date}' and ts < '{end_date}'
    """
    print(sql)
    cursor = conn.cursor(DictCursor)

    cursor.execute(sql)
    data = cursor.fetchall()

    df = pd.DataFrame(data)

    df["value"] = df["value"].astype(np.float32)

    df = df.pivot(index='ts', columns='tagname')['value']
    df = df.fillna(method='ffill')

    df = df.resample('1min').mean()
    df = df.fillna(method='ffill')
    df = df.fillna(0)

    df[label_col] = df.sum(axis=1)
    print(df)
    df = df[[label_col]]

    scaler = StandardScaler()
    df[[label_col]] = scaler.fit_transform(df[[label_col]])

    df = time2vec(df)
    return df, scaler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')

    parser.add_argument('--target_date')
    parser.add_argument('--target_hour')
    parser.add_argument('--feeder')
    parser.add_argument('--connection')

    parser.add_argument('--mjson', default='defmodel.json')

    args = parser.parse_args()
    session_name = args.session

    with open("datafeeder.json") as f :
        feeder = json.load(f)[args.feeder]

    with open(args.mjson) as f :
        config = json.load(f)

    session = config[session_name]
    connection_key = args.connection

    with open('connections.json') as f:
        connection = json.load(f)[connection_key]
        connection = pymysql.connect(**connection)

    label_col = session['dataset']['label_col']
    scaler_path = session["scaler_output_name"]
    database = feeder["database"]
    pmtable = feeder["pmtable"]
    wg_options = session["window_generator"]
    wclass = wg_options["_class"]
    train_options = session["train_options"]
    wclass = _import(f"dataset.{wclass}")

    ts = pd.Timestamp(args.target_date)

    #start_ts = ts - pd.Timedelta(hours=25) + pd.Timedelta(hours=int(args.target_hour))
    #end_ts = ts - pd.Timedelta(hours=1) + pd.Timedelta(hours=int(args.target_hour))

    start_ts = pd.Timestamp(session["dataset"]["start_date"])
    end_ts = pd.Timestamp(session["dataset"]["start_date"]) + pd.Timedelta(days=session["dataset"]["ref_days"])

    from pump_rt_models import FitPumpPerformanceCurve
    from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector
    from pump_rt_algo import get_connection

    tags = [ '701-363-PWI-3001', '701-363-PWI-3002', '701-363-PWI-3003', '701-363-PWI-3040', '701-363-PWI-3041', '701-363-PWI-7001',
    '701-363-PWI-7111', '701-363-PWI-7211', '701-363-PWI-7311', '701-389-PWI-5001', '701-389-PWI-5101', ]

    print(tags)
    
    df, scaler = get_data(connection, table=session["input_table"], tags=tags, st_date=start_ts, end_date=end_ts, label_col=label_col)
    joblib.dump(scaler, scaler_path)

    ds = DataSets(df, label_col) #TODO
    tr, vd, tt = ds.split_data(df)

    del wg_options["_class"]
    wg = wclass(train_df=tr, val_df=vd, test_df=tt, **wg_options)

    model = load_model_from_config(config, session_name)    
    model.fit(wg.train, validation_data=wg.val, **train_options)
    model.save(session["model_output_name"])