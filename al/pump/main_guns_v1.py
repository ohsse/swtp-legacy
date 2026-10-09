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
import openpyxl
import threading
import subprocess

from concurrent.futures import ThreadPoolExecutor


# Initialize a thread pool executor with a maximum number of workers
executor = ThreadPoolExecutor(max_workers=10)


def initialization(sheetname, model_name, mode):
    worksheet = pd.read_excel(r"/home/app/pump3/GunS_taglist.xlsx", sheet_name = sheetname)

    if mode == 'PRES':
        df = worksheet.loc[
            (worksheet['비고'] != 'NU') &
            (worksheet['변수명'].str[0] == 'P')
            ].reset_index(drop=True)

    elif mode == 'FLUX':
        df = worksheet.loc[
            (worksheet['비고'] != 'NU') &
            (worksheet['변수명'].str[0] != 'P')
            ].reset_index(drop=True)

    elif mode == 'BOTH':
        df = worksheet.loc[
            (worksheet['비고'] != 'NU')
            ].reset_index(drop=True)

    load_dir =r"/home/app/pump3/"

    try:
        model = load_model(f"{load_dir}saved_model/{model_name}.keras", custom_objects={'custom_loss': custom_loss})
    except:
        print(f'Failed to load {model_name}.keras file..., alternatively load {model_name}.h5 file ... ')
        try:
            model = load_model(f"{load_dir}saved_model/{model_name}.h5", custom_objects={'custom_loss': custom_loss})
        except:
            print(f'Failed to load {model_name}.keras or {model_name}.h5 file... please ask model developer...')
    # tensorflow 버전 issue로 모델 불러오기 관련 오류 발생 시 .keras 파일 아닌 .h5 모델 사용

    loaded_scalers = {}
    for feature in df.변수명:
        save_path = os.path.join(load_dir, f"./saved_scaler/{model_name}/{feature}_scaler.pkl")
        with open(save_path, "rb") as f:
            loaded_scalers[feature] = pickle.load(f)
    return df, model, loaded_scalers

def open_db():
    print("open_db")
    with open(r'/home/app/pump3/libs/connections.json') as f:
        connection = json.load(f)['maria-ems-db-gs']
        print('connection', connection)
        connection = pymysql.connect(**connection)
        print('connected', connection)
    return connection

def get_db_config(): # 군산으로 수정해야함..
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "ems_user",
        "password": "CHANGE_ME",
        "db": "EMS_DB"
    }
    return db_config

def get_db_df(connection, tag_name, start_time):
    print(tag_name)
    cursor = connection.cursor(DictCursor)
    cursor.execute(
        f"""
        SELECT TS AS 'Datetime', VALUE 
        FROM EMS_DB.TB_RAWDATA tr 
        WHERE TAGNAME = '{tag_name}' AND TS <= '{start_time}' 
        ORDER BY TS DESC
        LIMIT 60
        """
    )
    data = cursor.fetchall()
    # print(tag_name+"["+str(len(data))+"] end") # for debug
    return data

def set_index_df(df, window_size = 60):
    df = df.reset_index(drop=True)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.set_index('Datetime')
    df = df.sort_index()
    return df

def custom_loss(y_true, y_pred):
    import tensorflow as tf
    from keras.losses import mean_squared_error
    mask = tf.reduce_any(tf.not_equal(y_true, 10), axis=-1, keepdims=True)
    mask = tf.cast(mask, tf.float32)

    y_true_masked = tf.multiply(y_true, mask)
    y_pred_masked = tf.multiply(y_pred, mask)

    loss = mean_squared_error(y_true_masked, y_pred_masked)

    return tf.reduce_sum(loss) / tf.reduce_sum(mask)

def RELU(x):
    return np.maximum(0, x)

def pred_pump(df_result):
    pump_dfs = []

    columns_checked = {'P_GunS_Predict': 'P_GunS_Predict' in df_result.columns,
                        'Q_GunS_Predict': 'Q_GunS_Predict' in df_result.columns} # 예측값 존재여부 확인

    for timestamp, row in df_result.iterrows():
        print('row', row)
        if all(columns_checked.values()):
            freqs= [None, None, None, None] # else 조건 (default)
            Q = row['Q_GunS_Predict']
            P = row['P_GunS_Predict']

            if P >= 58.6613373258886 - 0.00527586346649821*Q + 1.2957874682855E-07*Q**2:
                pump_yn = [0, 0, 0, 1]
            elif -3.43193582761012 + 0.00120472303735243*Q - 4.08245928068585E-08*Q**2 <= P < 58.66133732588860 - 0.00527586346649821*Q + 1.2957874682855E-07*Q**2:
                pump_yn = [0, 1, 0, 1]
            elif 2.95 + 0.000497*Q - 0.0000000229*Q**2 <= P < -3.43193582761012 + 0.00120472303735243*Q - 4.08245928068e-08*Q**2:
                pump_yn = [0, 1, 0, 1]
            elif 0.120821964429389 + 0.000853219487279097*Q - 3.52433865423429E-08*Q**2 <= P < 2.95 + 0.000497*Q - 0.0000000229*Q**2:
                pump_yn = [0, 0, 0, 1]
            elif 0.46770987097162 + 0.000872862970476709*Q - 3.89262100721736E-08*Q**2 <= P < 0.120821964429389 + 0.000853219487279097*Q - 3.52433865423429E-08*Q**2:
                pump_yn = [0, 0, 0, 1]
            elif -0.759451815235986 + 0.0010218039074961*Q - 4.43777727901476E-08*Q**2 <= P < 0.46770987097162 + 0.000872862970476709*Q - 3.89262100721736E-08*Q**2:
                pump_yn = [0, 1, 0, 1]
            elif P < -0.759451815235986 + 0.0010218039074961*Q - 4.43777727901476E-08*Q**2:
                pump_yn = [0, 1, 0, 0]
                
            if P < 0:
                print(f"WARNING: Predicted pressure has negative value of {P}")
            pump_df = create_pump_df(timestamp, row['Q_GunS_Predict'], row['P_GunS_Predict'], range(5, 9), pump_yn, freqs, 2) # range 입력 시 range(a, a+n) 형태로 사용 (n: 펌프 개수)
            pump_dfs.append(pump_df)
    return pump_dfs

def create_pump_df(timestamp, Q_pred, P_pred, pump_idxs, pump_yn, freqs, pump_grp):
    pump_df =  pd.DataFrame({
        'RGSTR_TIME': [timestamp] * len(pump_idxs),
        'pump_idx': list(pump_idxs),
        'pump_yn': pump_yn,
        'FREQ': freqs,
        'PUMP_GRP': pump_grp,
        'TUBE_PRSR_PRDCT' : Q_pred,
        'PRDCT_MEAN' : P_pred,
        'PRDCT_TIME_DIFF' : 1
        })
    pump_df['OPT_IDX'] = timestamp.strftime(f'780-344-PRI:%Y%m%d%H-' + datetime.now().strftime('%H%M'))

    #pump_df.to_sql('TB_CTR_PUMPYN_RST', engine, if_exists='append', index=False)
    return pump_df

def create_tnk_df(df_result):
    for col in df_result.columns:
        tnk_df = pd.DataFrame({
        'DSTRB_ID': [col] * len(df_result),
        'PRDCT_VALUE': df_result[col].values,
        'RGSTR_TIME': df_result.index
        })
        tnk_df.set_index(['DSTRB_ID', 'RGSTR_TIME'])        
        tnk_df.to_sql('TB_CTR_TNK_RST', engine, if_exists='append', index=False)
    return

def Predict_1min_test(name, model_name, now_timestamp , mode='FLUX'):
    KST = timezone('Asia/Seoul')
    now = datetime.now().astimezone(KST) #
    test_timestamp = now.strftime('%Y-%m-%d %H:%M') #
    test_timestamp_re = now.strftime('%Y-%m-%d %H:%M:%S') 
    
    df, model, loaded_scalers = initialization(name, model_name, mode=mode)
    data_df = pd.DataFrame()

    db_connection = open_db()
    for i in range(len(df)):
        data_df[f"{df.변수명[i]}"] = set_index_df(pd.DataFrame(get_db_df(db_connection, f"{df.태그명[i]}", now_timestamp)))
    db_connection.close()
    print(f"Successfully imported data ...")

    df_to_sequence = data_df.copy().reset_index(drop=True)
    print("------------------------------------------------------------")

    for feature in df.변수명:
        df_to_sequence[feature] = loaded_scalers[feature].transform(df_to_sequence[[feature]])

    testset = df_to_sequence.copy()
    testset = testset.fillna(testset.mean())
    d_testX = np.expand_dims(np.array(testset[list(df.loc[df['비고'] != 'NU'].변수명)]), axis=0)
    testPredict = model.predict(d_testX)
    testPredict_result = testPredict[:, -step_topredict, :] 
    
    if testPredict_result.ndim == 2:
        pass
    else:
        testPredict_result = np.expand_dims(testPredict_result, axis = 0)
    
    print(f"예측 시점 : {now_timestamp} (KTC)")

    # 예측 결과 데이터 프레임 구성
    df_result = pd.DataFrame(index=[datetime.strptime(now_timestamp, '%Y-%m-%d %H:%M') + timedelta(minutes=1)])  # 00분 시간 인덱스

    for k in range(testPredict_result.shape[1]):
        df_result[f"{list(df.loc[df['비고'] == 'target'].변수명)[k]}_Predict"] = RELU(loaded_scalers[list(df.loc[df['비고'] == 'target'].변수명)[k]].inverse_transform(testPredict_result[:, k].reshape(-1, 1)).flatten())

    print(f"{step_topredict}분 후 예측 :")
    df_result_str = df_result.copy()
    df_result_str.columns = [df.loc[df['비고'] == 'target']['태그 설명']]

    create_tnk_df(df_result)

    return df_result_str, df_result

def pred_and_upload_guns_test(now_timestamp):
    _, df_result = Predict_1min_test('gunsan', 'guns_gunsan', now_timestamp, mode = 'BOTH')

    pred_pump(df_result) #생활정수장 펌프예측
    return None

def predict_and_upload_flux_test(taglist, now_timestamp): #하위 배수지 예측
    i = 0
    for sheetname in taglist.sheetnames[1:]:
        print(f"---Predicting {sheetname}---")
        Predict_1min_test(sheetname, f'guns_{sheetname}', now_timestamp, mode = 'BOTH')
        i += 1
    return None
    
def getNowRawDate():
    connection = open_db()
    cursor = connection.cursor(DictCursor)
    cursor.execute("select DATE_FORMAT(MAX(TS), '%Y-%m-%d %H:%i:00') AS 'TS'  FROM TB_RAWDATA where TS >= DATE_SUB(now(), INTERVAL 10 MINUTE)")
    data = cursor.fetchall()
    nowTs = ''
    if data:
        nowTs = data[0]['TS']
    return nowTs

def predict_guns_test(taglist): #전체 예측
    KST = timezone('Asia/Seoul')
    start = time.time()
    print(f"실행 시작: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")
    
    KST = timezone('Asia/Seoul')
    now = datetime.now().astimezone(KST)
    now_minus_two_minutes = now - timedelta(minutes=2)
    now_minus_one_minutes = now - timedelta(minutes=1)
    now_timestamp = now_minus_two_minutes.strftime('%Y-%m-%d %H:%M')
    pre_now_timestamp = now_minus_one_minutes.strftime('%Y-%m-%d %H:%M')

    test_timestamp = pred_and_upload_guns_test(now_timestamp)
    print('#'*50)
    print(taglist)
    print('#'*50)
    predict_and_upload_flux_test(taglist, now_timestamp)
    prdct_time = getNowRawDate()
    
    print('#EPANET_TIME:',test_timestamp)
    #pythone test.py —startDt 2023-10-27 00:00:00 —endDt 2023-10-27 00:00:00 —pre True
    exec0 = f"python /home/app/pump3/epanet_ks/test.py --startDt '{prdct_time}' --endDt '{prdct_time}' --pre False"
    print('call: ', exec0)
    #subprocess.run(exec0, shell=True, check=True)
    #print('EPANET PRE False End')
    
    exec1 = f"python /home/app/pump3/epanet_ks/test.py --startDt '{pre_now_timestamp}' --endDt '{pre_now_timestamp}' --pre True"
    print('call: ', exec1)
    #subprocess.run(exec1, shell=True, check=True)
    #print('EPANET PRE True End:',pre_now_timestamp)
    time.sleep(2)
    threading.Thread(target=run_subprocess, args=(exec0,)).start()
    time.sleep(2)
    threading.Thread(target=run_subprocess, args=(exec1,)).start()

    print(f"실행 완료: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")
    print(f"실행 시간 : {time.time() - start :.2f} 초")
    return None
    
    
def run_threaded(job_func, args):
    time.sleep(5)  # 10초 딜레이
    job_thread = threading.Thread(target=job_func, args=args)
    job_thread.start()
    
def run_subprocess(command):
    time.sleep(2)  # 2초 딜레이
    subprocess.run(command, shell=True, check=True)

def schedule_job(taglist):
    executor.submit(predict_guns_test, taglist)
    
window_size = 60
step_topredict = 5 # 모델 자체 예측 시간 = 5분 but 사용은 1분

taglist_name = '/home/app/pump3/GunS_taglist.xlsx'
taglist = openpyxl.load_workbook(taglist_name)
db_config = get_db_config() # DB 연결정보
database_connection_string = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
engine = create_engine(database_connection_string)


schedule.every().minute.do(schedule_job, taglist)
while True:
    schedule.run_pending()
    time.sleep(1)


# '''

