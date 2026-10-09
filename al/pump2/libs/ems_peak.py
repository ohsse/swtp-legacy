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

gnrtd_pwi_tags = ["701-367-PWI-4043", "701-367-PWI-4045", "701-367-PWI-4047", "701-367-PWI-4049"]

def _gnrtd_pwr(conn, start_date, end_date):
    """
    발생 전력량 산출

    Parameter
    ---------
    data_db: Maria DB
    exec_time: timestamp
        프로그램 시작 시간 (15min 절사)
    """

    # 데이터 load..
    gnrtd_df = get_pwi_data(conn, gnrtd_pwi_tags, start_date, end_date)

    # 발생 전력 데이터 산출
    gnrtd_df.index = pd.to_datetime(gnrtd_df["ts"])
    gnrtd_df["value"] = gnrtd_df["value"].astype(float)
    gnrtd_df["value"] = gnrtd_df["value"].cumsum()
    gnrtd_df = gnrtd_df["value"].resample('1H').sum() / 60

    #gnrtd_df = (gnrtd_df.sum(axis=1) / 60).resample('1H').sum()
    gnrtd_df = gnrtd_df.reset_index()
    gnrtd_df.columns = ['CNFRM_TIME', 'GNRTD_PWR']
    #print(gnrtd_df)

    return gnrtd_df

def get_pwi_data(conn, pwitags, start_date, end_date, database="ems_db",table='TB_RAWDATA'):
    cursor = conn.cursor(DictCursor)
    from functools import reduce
    tagcondstr =  reduce(lambda x, y: x + "'"+y+"',", pwitags, '')[:-1]

    sql = f"""
    SELECT * FROM {database}.{table} where tagname in ({tagcondstr}) and ts >= '{start_date}' and ts < '{end_date}' order by ts
    """
    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    return df

def get_peak_pwr(cursor, database='ems_db', table='TB_RT_POWER_RST'):
    sql = f"""
    SELECT PWR FROM {database}.{table}
    ORDER BY `DATA_BS_YMNTH` DESC, `RST_TYP` DESC, `RGSTR_TIME` DESC LIMIT 1;
    """
    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()[0]["PWR"]
    return data

def get_tei_data(conn, teitag, start_date, end_date, database="ems_db",table='TB_RAWDATA'):
    sql = f"""
    SELECT * FROM {database}.{table} where tagname = '{teitag}' and ts < '{end_date}' order by ts desc limit 10
    """
    
    cursor = conn.cursor(DictCursor)
    cursor.execute(sql)
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    return df.iloc[-1, :]["value"]

def get_pump_prep(conn, exec_time, teitag, database, pumpGroup):
    cursor = conn.cursor(DictCursor)
    start_date = (pd.Timestamp(exec_time) - pd.Timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    end_date = (pd.Timestamp(exec_time) + pd.Timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

    sql = f"""
    SELECT T1.OPT_IDX, T1.PRDCT_TIME, T1.PUMP_GRP, T1.PRDCT_MEAN, T2.PUMP_IDX, T2.PUMP_TYP, T2.FREQ 
    FROM {database}.TB_CTR_OPT_RST T1 
    LEFT JOIN (SELECT OPT_IDX, PUMP_IDX, PUMP_GRP, PUMP_TYP, FREQ FROM {database}.TB_CTR_PUMPYN_RST WHERE PUMP_YN = '1') T2 
    ON T1.OPT_IDX = T2.OPT_IDX AND T1.PUMP_GRP = T2.PUMP_GRP
    WHERE T1.OPT_IDX IN (SELECT MAX(OPT_IDX) FROM {database}.TB_CTR_OPT_RST GROUP BY PRDCT_TIME, PUMP_GRP) AND 
          T2.PUMP_TYP IS NOT NULL AND 
          T1.PRDCT_TIME >= '{start_date}' AND T1.PRDCT_TIME < '{end_date}'
          
    """

    print(sql)
    cursor.execute(sql)
    data = cursor.fetchall()    
    pump_data = pd.DataFrame(data)

    #tei_last = get_tei_data(conn, teitag, start_date, end_date)
    tei_last = 20.
    tei_last = round(float(tei_last))

    pump_data["TEI"] = tei_last
    print(pump_data)
    pmp_idx_df = pump_data.groupby(['PRDCT_TIME', 'PUMP_GRP'])['PUMP_IDX'].apply(list).reset_index()
    print(pmp_idx_df)
    pmp_freq_df = pump_data.groupby(['PRDCT_TIME', 'PUMP_GRP'])['FREQ'].apply(list).reset_index()
    
    pump_data = pump_data.drop('PUMP_IDX', axis=1).drop_duplicates()
    pump_data = pump_data.merge(pmp_idx_df, on=['PRDCT_TIME', 'PUMP_GRP'], how='left')
    pump_data = pump_data.drop('FREQ', axis=1).merge(pmp_freq_df, on=['PRDCT_TIME', 'PUMP_GRP'], how='left')

    pump_grp_df = pump_data.set_index(['PRDCT_TIME', 'PUMP_GRP']).unstack()
    pump_grp_df.columns = list(map(lambda x: ''.join([str(x1) for x1 in x]), pump_grp_df.columns))

    pump_data = pump_grp_df
    from pump_rt_models import FitPumpPerformanceCurve
    from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector

    pdbc = PumpEQ_DB_connector(conn)
    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=None, pmTable="ems_db.TB_CTR_PRF_PUMPMST_INF") #TODO

    CPP = Calc_pump_properties(conn, pumpAttr, pumpTags, database=database)

    pump_data.loc[:, "PRDCT_MEAN1"] = pump_data["PRDCT_MEAN1"].fillna(0)
    pump_data["PUMP_PWR1"] = pump_data.apply(lambda x : CPP.power_given_QnT(x["PUMP_IDX1"], x["PRDCT_MEAN1"], tei_last)[0] , axis=1)

    pump_data.loc[:, "PRDCT_MEAN2"] = pump_data["PRDCT_MEAN2"].fillna(0)
    pump_data["PUMP_PWR2"] = pump_data.apply(lambda x : CPP.power_given_QnT(x["PUMP_IDX2"], x["PRDCT_MEAN2"], tei_last)[0] , axis=1)
    #pump_data = pump_data[["PUMP_PWR"]]
    pump_data["DR_PWR"] = 0

    pump_data['TOTAL_USE_PWR'] = pump_data.PUMP_PWR1 * 1.08 + pump_data.PUMP_PWR2 * 1.08
    print(pump_data)

    ppwr = get_peak_pwr(cursor)
    pump_data["PEAK_PWR"] = ppwr * 1.07
    gdf = _gnrtd_pwr(conn, start_date, end_date)

    return pump_data, gdf

def _peak(df, exec_time, DOCKER_ID="a"):
    upload_df = df.copy()
    peak_pwr = upload_df.PEAK_PWR.unique()[0]

    upload_df = (upload_df.TOTAL_USE_PWR).resample('1H').sum().reset_index()
    upload_df.columns = ["CNFRM_TIME", "PRDCT_PWR"]
    # 피크 여부
    upload_df["PEAK_YN"] = upload_df.PRDCT_PWR.apply(lambda x: 1 if x >= peak_pwr else 0)
    # 분석일시
    upload_df['CNFRM_TIME'] = upload_df['CNFRM_TIME'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:00'))
    upload_df['ANLY_TIME'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:00')
    # 도커번호
    upload_df['DC_NMB'] = DOCKER_ID
    return upload_df

def _model(peak_df, gnrtd_df, exec_time, DOCKER_ID="a") :
    return _peak(peak_df, exec_time, DOCKER_ID)

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
        conn = pymysql.connect(**connection)

    tei_tag = "701-367-TEI-4068"
    exec_time = pd.Timestamp(f'{args.target_date} 00:00:00') + pd.Timedelta(hours=int(args.target_hour))

    pdf, gdf = get_pump_prep(conn, exec_time, tei_tag, 'ems_db', pumpGroup=args.pumpGroup)
    pdf.index = pd.to_datetime(pdf.index)
    peak_df = _model(pdf, gdf, '')
    from pump_rt_algo import get_connection_alchemy_s
    sconn = get_connection_alchemy_s(args.connection)
    peak_df.to_sql('TB_PEAK_PWR_PRDCT_RST', con=sconn, if_exists='append', index=False)
    print(peak_df)
    print(gdf)
    gdf.iloc[:1, :].to_sql('TB_PEAK_GNRTD_RST', con=sconn, if_exists='append', index=False)