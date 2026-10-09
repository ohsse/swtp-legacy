import argparse
import pymysql
import pandas as pd
import re
import numpy as np
import scipy.stats as stats
from dateutil.relativedelta import relativedelta
from pymysql.cursors import DictCursor
from datetime import datetime, date
from pytimekr import pytimekr
import math
from pymysql.cursors import DictCursor

def _gnrtd_pwr(ptags, conn, start_date, database):
    """
    발생 전력량 산출

    Parameter
    ---------
    data_db: Maria DB
    exec_time: timestamp
        프로그램 시작 시간 (15min 절사)
    """

    # 데이터 load..
    print(pumpAttr)
    print(pumpTags)

    tags = pumpAttr.loc["PWI_TAG", :].values.tolist()
    end_date = ( pd.Timestamp(start_date) + pd.Timedelta(hours=1) ).strftime('%Y-%m-%d %H:%M:%S')
    gnrtd_df = get_pwi_data(conn, ptags, start_date, end_date, database=database)

    # 발생 전력 데이터 산출
    gnrtd_df.index = pd.to_datetime(gnrtd_df["TS"])
    gnrtd_df["VALUE"] = gnrtd_df["VALUE"].astype(float)
    gnrtd_df["VALUE"] /= 100
    gnrtd_df["VALUE"] = gnrtd_df["VALUE"].sum()
    gnrtd_df = gnrtd_df["VALUE"].resample('1H').sum() / 60

    #gnrtd_df = (gnrtd_df.sum(axis=1) / 60).resample('1H').sum()
    gnrtd_df = gnrtd_df.reset_index()
    gnrtd_df.columns = ['CNFRM_TIME', 'GNRTD_PWR']
    #print(gnrtd_df)

    return gnrtd_df

def get_pwi_data(conn, pwitags, start_date, end_date, database="ems_db",table='TB_RAWDATA'):
    cursor = conn.cursor(DictCursor)
    from functools import reduce
    tagcondstr =  reduce(lambda x, y: x + "'" + y + "',", pwitags, '')[:-1]

    sql = f"""
    SELECT * FROM {database}.{table} where tagname in ({tagcondstr}) and ts >= '{start_date}' and ts < '{end_date}' order by ts
    """
    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    return df

def get_peak_pwr(cursor, database='EMS_DB', table='TB_RT_POWER_RST'):
    sql = f"""
    SELECT PWR FROM {database}.{table}
    ORDER BY `DATA_BS_YMNTH` DESC, `RST_TYP` DESC, `RGSTR_TIME` DESC LIMIT 1;
    """
    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()[0]["PWR"]
    print('peakpwr:', data)
    return data

def get_tei_data(conn, teitag, start_date, end_date, database="EMS_DB",table='TB_RAWDATA'):
    sql = f"""
    SELECT * FROM {database}.{table} where tagname = '{teitag}' and ts < '{end_date}' order by ts desc limit 10
    """
    
    cursor = conn.cursor(DictCursor)
    cursor.execute(sql)
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    return df.iloc[-1, :]["VALUE"]

def get_pump_prep(conn, ptags, exec_time, database):
    cursor = conn.cursor(DictCursor)
    start_date = (pd.Timestamp(exec_time) - pd.Timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    end_date = (pd.Timestamp(exec_time) + pd.Timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

    sql = f"""
    SELECT T1.PRDCT_TIME, T1.OPT_IDX, T1.PUMP_GRP, T1.PRDCT_MEAN, T1.PWR_PRDCT
    FROM {database}.TB_CTR_OPT_RST T1
    WHERE 
    T1.OPT_IDX IN (SELECT MAX(OPT_IDX) FROM {database}.TB_CTR_OPT_RST GROUP BY PRDCT_TIME, PUMP_GRP) AND
          T1.PRDCT_TIME >= '{start_date}' AND T1.PRDCT_TIME < '{end_date}'
    """

    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()    
    pump_data = pd.DataFrame(data)

    pump_data.index = pump_data["PRDCT_TIME"]
    
    pump_data["PEAK_PWR"] = pump_data["PWR_PRDCT"]
    pump_data["DR_PWR"] = 0
    pump_data['TOTAL_USE_PWR'] = pump_data["PWR_PRDCT"]
    ppwr = get_peak_pwr(cursor, database=database)

    gdf = _gnrtd_pwr(ptags, conn, start_date, database=database)

    return pump_data, gdf, ppwr


def _get_connection(connection_key="maria-ems-db"): #TODO
    with open('connections.json') as f:
        db_info = json.load(f)[connection_key]

    conn = pymysql.connect(**db_info)
    return conn

def _peak(df, ppwr, exec_time, DOCKER_ID="a"):
    upload_df = df.copy()
    # peak_pwr = upload_df.PEAK_PWR.unique()[0]

    upload_df = (upload_df.TOTAL_USE_PWR).resample('1H').sum().reset_index()
    upload_df.columns = ["CNFRM_TIME", "PRDCT_PWR"]
    # 피크 여부
    print(upload_df)

    upload_df["PEAK_YN"] = upload_df.PWR_PRDCT.apply(lambda x: 1 if x >= ppwr else 0)
    # 분석일시
    upload_df['CNFRM_TIME'] = upload_df['CNFRM_TIME'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:00'))
    upload_df['ANLY_TIME'] = ( pd.Timestamp.now() ).strftime('%Y-%m-%d %H:%M:00')
    # 도커번호
    upload_df['DC_NMB'] = DOCKER_ID
    return upload_df

def _model(peak_df, gnrtd_df, ppwr, exec_time, DOCKER_ID="a") :
    return _peak(peak_df, ppwr, exec_time, DOCKER_ID)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--connection')
    parser.add_argument('--pumpGroup')
    parser.add_argument('--target_date')
    parser.add_argument('--target_hour')
    args = parser.parse_args()

    with open('connections.json') as f:
        import json
        import pymysql
        connection = json.load(f)[args.connection]
        database = connection["db"]
        conn = pymysql.connect(**connection)

    from pump_rt_algo import PumpEQ_DB_connector 
    pdbc = PumpEQ_DB_connector(conn)

    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=None, pmTable=f'{database}.TB_CTR_PRF_PUMPMST_INF')
    pwitags = pumpAttr.loc["PWI_TAG", :].values.tolist()
    #pwqtags = pumpAttr.loc["PWQ_TAG", :].values.tolist()
    tags = pwitags #+ pwqtags

    exec_time = pd.Timestamp(f'{args.target_date} 00:00:00') + pd.Timedelta(hours=int(args.target_hour))
    pdf, gdf, ppwr = get_pump_prep(conn, tags, exec_time, database)
    print(pdf)

    pdf.index = pd.to_datetime(pdf.index)
    peak_df = _model(pdf, gdf, ppwr, '')
    print(ppwr)
    
    from pump_rt_algo import get_connection_alchemy_s
    sconn = get_connection_alchemy_s(args.connection)
    print(peak_df) 
    peak_df.to_sql('TB_PEAK_PWR_PRDCT_RST', con=sconn, if_exists='append', index=False)
    print(gdf)
    gdf.to_sql('TB_PEAK_GNRTD_RST', con=sconn, if_exists='append', index=False)



