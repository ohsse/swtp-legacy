#!/usr/bin/env python
# coding: utf-8

import json
import pandas as pd
import os
import numpy as np
import re
from datetime import datetime, timedelta
import pickle
from keras.models import load_model
import tensorflow as tf
from keras.losses import mean_squared_error
import time
import pymysql
from pymysql.cursors import DictCursor
import schedule
from pytz import timezone
from sqlalchemy import create_engine

def initialization(model_name):
    print('initialization - model_name:', model_name)
    worksheet = pd.read_excel(r"/home/app/power/Gosan_taglist.xlsx")

    df = worksheet.loc[(worksheet['비고'] != 'NU')].reset_index(drop=True)
    df_variable = worksheet.loc[(worksheet['비고'] == 'variable')].reset_index(drop=True)

    load_dir =r"/home/app/power/"

    try:
        model = load_model(f"{load_dir}saved_model/{model_name}.keras", custom_objects={'custom_loss': custom_loss})
        print('model 1:',model)
    except:
        print(f'Failed to load {model_name}.keras file..., alternatively load {model_name}.h5 file ... ')
        try:
            model = load_model(f"{load_dir}saved_model/{model_name}.h5", custom_objects={'custom_loss': custom_loss})
            print('model 2:',model)
        except:
            print(f'Failed to load {model_name}.keras or {model_name}.h5 file... please ask model developer...')
    # tensorflow 버전 issue로 모델 불러오기 관련 오류 발생 시 .keras 파일 아닌 .h5 모델 사용
    
    loaded_scalers= {}
    save_path = os.path.join(load_dir, f"saved_scaler/{model_name}/Power_tot_scaler.pkl")
    with open(save_path, "rb") as f:
        loaded_scalers['Power_tot'] = pickle.load(f)
    for feature in df_variable.변수명:
        save_path = os.path.join(load_dir, f"saved_scaler/{model_name}/{feature}_scaler.pkl")
        with open(save_path, "rb") as f:
            loaded_scalers[feature] = pickle.load(f)
    
    
    return df, df_variable, model, loaded_scalers

def open_db():
    print("open_db")
    with open(r'/home/app/libs/connections.json') as f:
        connection = json.load(f)['maria-ems-db-wm']
        print('connection', connection)
        connection = pymysql.connect(**connection)
        print('connected', connection)
    return connection

def get_db_config(): # 188서버로 수정해야함
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "ems_user",
        "password": "CHANGE_ME",
        "db": "EMS_DB"
    }
    return db_config
    
    
def clean_and_convert(df):
    for column in df.columns:
        df[column] = df[column].astype(str).apply(lambda x: re.sub(r'\.0000$', '', x))  # .0000 제거
        df[column] = pd.to_numeric(df[column], errors='coerce')  # 숫자로 변환
    return df

def get_db_df(connection, tag_name, start_time, window_size): # 데이터에 맞게 수정
    print(tag_name)
    cursor = connection.cursor(DictCursor)
    cursor.execute( 
        f"""
        SELECT TS AS 'Datetime', VALUE 
        FROM EMS_DB.TB_RAWDATA tr
        WHERE TAGNAME = '{tag_name}' AND TS <= '{start_time}' 
        AND TS >= DATE_SUB('{start_time}', INTERVAL 5 DAY) 
        ORDER BY TS DESC
        LIMIT {window_size * 60}
        """
    )
    data = cursor.fetchall()
    # print(tag_name+"["+str(len(data))+"] end") # for debug
    return data

def set_index_df(df):
    df = df.reset_index(drop=True)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.set_index('Datetime')
    df = df.sort_index()
    return df

def custom_loss(y_true, y_pred):
    
    mask = tf.reduce_any(tf.not_equal(y_true, 10), axis=-1, keepdims=True)
    mask = tf.cast(mask, tf.float32)

    y_true_masked = tf.multiply(y_true, mask)
    y_pred_masked = tf.multiply(y_pred, mask)

    loss = mean_squared_error(y_true_masked, y_pred_masked)

    return tf.reduce_sum(loss) / tf.reduce_sum(mask)

def RELU(x):
    return np.maximum(0, x)

def cal_time(data_df):
    datetime_hours = data_df.index.hour
    hours_sin = np.sin(datetime_hours * (2 * np.pi / 24))
    data_df['hours_sin'] = hours_sin
    hours_cos = np.cos(datetime_hours * (2 * np.pi / 24))
    data_df['hours_cos'] = hours_cos
    return data_df

def resampling(data_df, resam_term = '1H', method = 'mean'):
    data_df_resam = data_df.copy()
    data_df_resam = data_df_resam.reset_index(drop=False)
    data_df_resam['Datetime'] = pd.to_datetime(data_df_resam['Datetime'])
    data_df_resam = data_df_resam.set_index('Datetime')
    if method == 'mean':
        data_df_resam = data_df_resam.resample(rule = resam_term).mean(numeric_only=True)
    elif method == 'sum':
        data_df_resam = data_df_resam.resample(rule = resam_term).sum(numeric_only=True)
    return data_df_resam

def create_tnk_df(df_result):
    timestamp = df_result.index
    current_time_str = datetime.now().strftime('%H%M')
    opt_idx_values = [f"565-340-SWI:{ts.strftime('%Y%m%d%H-')}{current_time_str}" for ts in timestamp]

    for col in df_result.columns:
        tnk_df = pd.DataFrame({
        'RGSTR_TIME': [datetime.now()] * len(df_result),
        'PRDCT_TIME' : timestamp,
        'PRDCT_TIME_DIFF' : [i+1 for i in range(len(df_result))],
        'PRDCT_MEAN' : [0] * len(df_result),
        'PRDCT_STD' : [0] * len(df_result),
        'TUBE_PRSR_PRDCT' : [0] * len(df_result),
        'PUMP_GRP' : [0] * len(df_result),
        'PWR_PRDCT': df_result[col].values,
        'ANLY_TIME': [datetime.now()] * len(df_result),
        'OPT_IDX' : opt_idx_values
        })
        tnk_df.set_index(['RGSTR_TIME']) ##  변경 안될 시 tnk_df.set_index(['RGSTR_TIME'], inplace = True)
        tnk_df.to_sql('TB_CTR_OPT_RST', engine, if_exists='append', index=False)
    return

def Predict(model_name, window_size):
    KST = timezone('Asia/Seoul')
    now = datetime.now().astimezone(KST) #
    test_timestamp = now.replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
    
    df, df_var, model, loaded_scalers = initialization(model_name)
    data_target = pd.DataFrame()
    data_var = pd.DataFrame()

    db_connection = open_db()
    for i in range(len(df)):
        if df['변수명'][i][:5] == 'Power':
            data_target[f"{df.변수명[i]}"] = set_index_df(pd.DataFrame(get_db_df(db_connection, f"{df.태그명[i]}", test_timestamp, window_size)))
        else:
            data_var[f"{df.변수명[i]}"] = set_index_df(pd.DataFrame(get_db_df(db_connection, f"{df.태그명[i]}", test_timestamp, window_size)))
    db_connection.close()
    print(f"Successfully imported data ...")
    
    print('data_df:',data_target)
    
    data_target = clean_and_convert(data_target)
    
    data_target = data_target.sum(axis=1).to_frame()
    data_target.columns = ['Power_tot']

    data_target = data_target.fillna(data_target.mean())
    target_resampled = resampling(data_target, resam_term = '1H', method = 'mean')

    try:
        data_var = data_var.fillna(data_var.mean())
        var_resampled = resampling(df_var, resam_term = '1H', method = 'mean')
        data_df = pd.concat([target_resampled, var_resampled], axis=1, join='inner')
    except:
        data_df = target_resampled.copy()
    data_df = cal_time(data_df)
    df_to_sequence = data_df.copy().reset_index(drop=True)
    print("------------------------------------------------------------")

    df_to_sequence['Power_tot'] = loaded_scalers['Power_tot'].transform(df_to_sequence[['Power_tot']])

    testset = df_to_sequence.copy()
    testset = testset.fillna(testset.mean())
    try:
        d_testX = testset.copy()
        testPredict = model.predict(d_testX)
    except:
        d_testX = np.expand_dims(testset, axis=0)
        testPredict = model.predict(d_testX)

    testPredict_result = testPredict[:, -step_topredict:, :] 
    if testPredict_result.ndim == 2:
        pass
    else:
        testPredict_result = np.expand_dims(testPredict_result, axis = 0)
    
    print(f"예측 시점 : {test_timestamp} (KTC)")

    # 예측 결과 데이터 프레임 구성
    df_result = pd.DataFrame(index=[datetime.strptime(test_timestamp, '%Y-%m-%d %H:%M') + timedelta(hours=i+1) for i in range(step_topredict)])  # 24시간 시간 인덱스

    scaler = loaded_scalers['Power_tot']
    #test_predict_result_numpy = testPredict_result.numpy() 
    test_predict_result_numpy = testPredict_result       
    inverse_transformed = scaler.inverse_transform(test_predict_result_numpy.reshape(-1, 1)).flatten()
    df_result[f"Power_tot_Predict"] = RELU(inverse_transformed)

    #df_result_str = df_result.copy()
    #df_result_str.columns = [df.loc[df['비고'] == 'target']['태그 설명']]

    create_tnk_df(df_result)
    #data_df.to_csv('input.csv')    
    #df_result.to_csv('predicted.csv')

    return None, df_result



def Predict_func(model_name, window_size): #전체 예측
    KST = timezone('Asia/Seoul')
    start = time.time()
    print(f"실행 시작: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")

    Predict(model_name, window_size)

    print(f"실행 완료: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")
    print(f"실행 시간 : {time.time() - start :.2f} 초")
    return None
    
window_size = 120
step_topredict = 24 # 모델 자체 예측 시간 = 5분 but 사용은 1분

model_name = 'Powerprediction_Gosan'
db_config = get_db_config() # DB 연결정보
database_connection_string = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
engine = create_engine(database_connection_string)

#schedule.every(60).minute.do(Predict_func(model_name))


#schedule.every(60).minutes.do(Predict_func, model_name)
Predict_func(model_name, window_size)

while True:
    schedule.run_pending()
    time.sleep(1)


# '''

