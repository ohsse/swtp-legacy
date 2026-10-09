#!/usr/bin/env python
# coding: utf-8

import json
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import pickle
from keras.models import load_model
import time
import pymysql
from pymysql.cursors import DictCursor
import schedule
from pytz import timezone
from sqlalchemy import create_engine
import functools

window_size = 60
step_topredict = 5 # 예측할 시간 = 5분

def initialization(sheetname):
    worksheet = pd.read_excel('/home/app/pump/gosan_taglist.xlsx', sheet_name = sheetname).dropna(axis=1)
    dir_base = 'Rawdata/KSSCADA.'

    worksheet.columns = worksheet.values[0]
    worksheet = worksheet.drop(worksheet.index[0]).dropna(axis = 1)
    df = worksheet.loc[worksheet['변수명'] != 'NU'].reset_index(drop=True)

    model_name = 'gosan_p1_v1' #모델 이름(확장자를 제외한 모델 파일명)
    load_dir ="/home/app/pump/content/"

    model = load_model(f"{load_dir}saved_model/{model_name}.h")

    loaded_scalers = {}
    for feature in df.변수명:
        save_path = os.path.join(load_dir, f"saved_scaler/{model_name}/{feature}_scaler.pkl")
        with open(save_path, "rb") as f:
            loaded_scalers[feature] = pickle.load(f)
    return df, model, loaded_scalers, dir_base


def open_db():
    print("open_db")
    with open('/home/app/pump/libs/connections.json') as f:
        # 커넥션 정보를 불러옴
        connection = json.load(f)['maria-ems-db-gs']
        print('connection', connection)
        connection = pymysql.connect(**connection)
        print('connected', connection)
    return connection

def get_db_df(connection, tag_name):
    print(tag_name)
    cursor  = connection.cursor(DictCursor)
    cursor.execute(
        f"""
            select date_sub(MAX(TS), INTERVAL '1' hour) as tag1hour from EMS_DB.TB_RAWDATA tr where TAGNAME = '{tag_name}' 
        """
    )
    data = cursor.fetchall()
    print('tag1hour', data[0]['tag1hour'])
    cursor.execute(
        f"""
            select TS as Datetime, VALUE from EMS_DB.TB_RAWDATA tr where TAGNAME = '{tag_name}' and TS > '{data[0]['tag1hour']}'
        """
    )
    # cursor.execute(
    #     f"""
    #         select TS as Datetime, VALUE from EMS_DB_GR.TB_RAWDATA tr where TAGNAME = '{tag_name}' and TS > cast('2024-01-31 23:00:00' as DATETIME)
    #     """
    # )
    
    data = cursor.fetchall()

    print(tag_name +" end " , len(data))
    return data

def set_index_df(df, window_size = 60):    # DataFrame의 인덱스를 재설정하고 Datetime 열을 날짜/시간 형식으로 변환
    df = df.reset_index(drop=True)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.iloc[-window_size:]  # 'Datetime' 열을 기준으로 지난 60분간의 데이터만 가져오기
    df = df.set_index('Datetime')
    return df

def pred_pump(df_result):
    pump_dfs = []
    print(df_result)
    for timestamp, row in df_result.iterrows():
        print(row)
        Q_GS_predict = row['Q_GS_Predict']
        P_GS_predict = row['P_GS_Predict']

        Reg_P1 = 58.6613373258886 - 0.00527586346649821 * Q_GS_predict + 1.29578746828551E-07 * Q_GS_predict**2
        Reg_P2 = -3.43193582761012 + 0.00120472303735243 * Q_GS_predict - 4.08245928068585E-08 * Q_GS_predict**2
        Reg_P4 = 2.95 + 0.000497 * Q_GS_predict - 0.0000000229 * Q_GS_predict**2
        Reg_P5 = 0.120821964429389 + 0.000853219487279097 * Q_GS_predict - 3.52433865423429E-08 * Q_GS_predict**2
        Reg_P6 = 0.46770987097162 + 0.000872862970476709 * Q_GS_predict - 3.89262100721736E-08 * Q_GS_predict**2
        Reg_P7 = -0.759451815235986 + 0.0010218039074961 * Q_GS_predict - 4.43777727901476E-08 * Q_GS_predict**2
        Reg_P8 = -13.5501934770404 + 0.00300980057376775 * Q_GS_predict - 1.23001244874999E-07 * Q_GS_predict**2

        if P_GS_predict >= Reg_P1:
            pump_yn = [0, 0, 0, 1, 1, 1, 1]
        elif Reg_P1 > P_GS_predict >= Reg_P2:
            pump_yn = [0, 1, 0, 1, 0, 1, 1]
        elif Reg_P2 > P_GS_predict >= Reg_P4:
            pump_yn = [0, 1, 0, 1, 1, 0, 1]
        elif Reg_P4 > P_GS_predict >= Reg_P5:
            pump_yn = [0, 0, 0, 1, 1, 1, 0]
        elif Reg_P5 > P_GS_predict >= Reg_P6:
            pump_yn = [0, 0, 0, 1, 1, 0, 1]
        elif Reg_P6 > P_GS_predict >= Reg_P7:
            pump_yn = [0, 1, 0, 1, 0, 1, 0]
        elif Reg_P7 > P_GS_predict >= Reg_P8:
            pump_yn = [0, 1, 0, 0, 1, 0, 1]
        else:  # P_GS_predict < Reg_P8
            pump_yn = [0, 0, 0, 0, 1, 0, 1]

        pump_df = pd.DataFrame({
            'timestamp': [timestamp] * 7, 
            'pump_idx': [1, 2, 3, 4, 5, 6, 7],
            'pump_yn': pump_yn,
            'FREQ': [None] * 7 
        })

        pump_dfs.append(pump_df)

    # 모든 시점에 대한 pump_df를 하나의 DataFrame으로 합치기
    final_pump_df = pd.concat(pump_dfs).reset_index(drop=True)

    # 데이터베이스 연결 정보
    '''
    db_config = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "CHANGE_ME",
            "db": "EMS_DB"
    }
    '''
    db_config = {
            "host": "localhost",
            "port": 3306,
            "user": "ems_user",
            "password": "CHANGE_ME",
            "db": "EMS_DB"
    }
    nowStr = datetime.now().strftime('%H%M')
    final_pump_df['OPT_IDX'] = final_pump_df['timestamp'].dt.strftime('780-344-PRI:%Y%m%d%H%M-'+nowStr)
    final_pump_df['PRDCT_TIME_DIFF'] = final_pump_df['timestamp'].dt.strftime('%M').astype(int) - int(final_pump_df.iloc[0]['timestamp'].strftime('%M')) + 1
    final_pump_df['PUMP_GRP'] = 1
    del final_pump_df['timestamp']

    database_connection_string = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
    engine = create_engine(database_connection_string)

    final_pump_df.to_sql('TB_CTR_PUMPYN_RST', engine, if_exists='append', index=False)


def Predict_5min(name = '', model_name=''):
    KST = timezone('Asia/Seoul')
    start = time.time()
    print(f"실행 시작: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")

    df, model, loaded_scalers, dir_base = initialization(name)
    data_df = pd.DataFrame()

    db_connection = open_db()
    for i in range(len(df)):
        data_df[f"{df.변수명[i]}"] = set_index_df(pd.DataFrame(get_db_df(db_connection, f"{df.태그명[i]}")))
    print(f"imported data ...")
    db_connection.close()
    df_datetime = data_df.reset_index(drop=False)['Datetime']

    df_to_sequence = data_df.copy().reset_index(drop=True)    # 데이터셋 준비
    print("------------------------------------------------------------")

    for feature in df.변수명:
        df_to_sequence[feature] = loaded_scalers[feature].transform(df_to_sequence[[feature]]) # 데이터 스케일링

    testset = df_to_sequence.copy() # 실제 적용 시 주석 해제
    testset = testset.fillna(testset.mean())

    d_testX = np.expand_dims(np.array(testset[list(df.loc[df['비고'] != 'NU'].변수명)]), axis=0)

    testPredict = model.predict(d_testX)
    testPredict_result = testPredict[:,-step_topredict:,:]

    start_time_predict_str = str(df_datetime.values[-1]).split('.')[0]
    print(f"예측 시점 : {start_time_predict_str} (KTC)")
    start_time_predict = datetime.strptime(start_time_predict_str, '%Y-%m-%dT%H:%M:%S')

    datetime_list = []
    for i in range(step_topredict+1):
        current_time = start_time_predict + i * timedelta(minutes=1)
        datetime_list.append(current_time)
    df_result = pd.DataFrame(datetime_list[1:], columns = ['Datetime'])
    df_result = df_result.set_index('Datetime')

    for k in range(testPredict.shape[2]):
         df_result[f"{list(df.loc[df['비고'] == 'target'].변수명)[k]}_Predict"] = loaded_scalers[list(df.loc[df['비고'] == 'target'].변수명)[k]].inverse_transform(testPredict_result[:,:,k]).flatten()

    print(f"실행 시간 : {time.time() - start :.2f} 초")
    print(f"{step_topredict}분 후 예측 : ")
    print(df_result)
    
    pred_pump(df_result)

    return df_result

df_result = Predict_5min(name = 'GS', model_name = 'gosan_p1_v2')

for minute in range(0, 55, 5):
    scheduled_function = functools.partial(Predict_5min, name='GS', model_name='gosan_p1_v2')
    schedule.every().hour.at(f":{minute:02}").do(scheduled_function)

while True:
    schedule.run_pending()
    time.sleep(1)
