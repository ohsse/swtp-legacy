#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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
from concurrent.futures import ThreadPoolExecutor

# Initialize a thread pool executor with a maximum number of workers
executor = ThreadPoolExecutor(max_workers=100)

def initialization(sheetname, model_name, mode):
    worksheet = pd.read_excel(r'/home/app/pump3/GS_taglist.xlsx', sheet_name = sheetname, header=0)
    
    if mode == 'PRES':
        df = worksheet.loc[
            (worksheet['비고'] != 'NU') &
            (worksheet['사용'] == 'Y') &
            (worksheet['변수명'].str[0] == 'P')
            ].reset_index(drop=True)

    elif mode == 'FLUX':
        df = worksheet.loc[
            (worksheet['비고'] != 'NU') &
            (worksheet['사용'] == 'Y') &
            (worksheet['변수명'].str[0] != 'P')
            ].reset_index(drop=True)

    elif mode == 'BOTH':
        df = worksheet.loc[
            (worksheet['비고'] != 'NU') &
            (worksheet['사용'] == 'Y')
            ].reset_index(drop=True)

    load_dir ="/home/app/pump3/"
    
    keras_file = f"{load_dir}saved_model/{model_name}.keras"
    if os.path.exists(keras_file):
        print(f"파일이 존재합니다: {keras_file}")
    else:
        print(f"파일이 존재하지 않습니다: {keras_file}")
        
    try:
        model = load_model(f"{load_dir}saved_model/{model_name}.keras", custom_objects={'custom_loss': custom_loss})
    except Exception as e:
        print(f'Failed to load {model_name}.keras file..., alternatively load {model_name}.h5 file ..., error: {e} ')
        try:
            model = load_model(f"{load_dir}saved_model/{model_name}.h5", custom_objects={'custom_loss': custom_loss})
        except Exception as e:
            print(f'Failed to load {model_name}.keras or {model_name}.h5 file... please ask model developer..., error: {e}')
    # tensorflow 버전 issue로 모델 불러오기 관련 오류 발생 시 .keras 파일 아닌 .h5 모델 사용
    model.summary()    
    loaded_scalers = {}
    for feature in df.변수명:
        save_path = os.path.join(load_dir, f"/home/app/pump3/saved_scaler/{model_name}/{feature}_scaler.pkl")
        with open(save_path, "rb") as f:
            loaded_scalers[feature] = pickle.load(f)
  
    return df, model, loaded_scalers

def open_db():
    print("open_db")
    with open(r'/home/app/pump3/libs/connections.json') as f:
        # 커넥션 정보를 불러옴
        connection = json.load(f)['maria-ems-db-gs']
        print('connection', connection)
        connection = pymysql.connect(**connection)
        print('connected', connection)
    return connection

def get_db_config():
    db_config = {               ## DB 연결정보 #--#
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
    print(tag_name+"["+str(len(data))+"] end") # for debug
    return data

def set_index_df(df, window_size = 30):
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

def pred_pump(df_result, mode):
    if mode == 'OLD':
        pump_dfs = []
        print('####pred_pump')
        
        columns_checked = {'Q_GS_OLD_Predict': 'Q_GS_OLD_Predict' in df_result.columns,
                           'P_GS_OLD_Predict': 'P_GS_OLD_Predict' in df_result.columns} # 예측값 존재여부 확인
        print(f"{df_result['Q_GS_OLD_Predict']}")
        print(f"{df_result['P_GS_OLD_Predict']}")


        for timestamp, row in df_result.iterrows():
            print('row', row)
            pump_yn = []
            # 조건 수정
            if all(columns_checked.values()):
                freqs= [None, None, None, None, None, None, None] # else 조건 (default)
                Q = row['Q_GS_OLD_Predict']
                P = row['P_GS_OLD_Predict']
                print('Q:',Q)
                print('P:',P)
                if P >= 58.6613373258886 - 0.00527586346649821*Q + 1.2957874682855E-07*Q**2:
                    pump_yn = [0, 0, 0, 1, 1, 1, 1] # 4, 5, 6, 7 가동
                elif -3.43193582761012 + 0.00120472303735243*Q - 4.08245928068585E-08*Q**2 <= P < 58.66133732588860 - 0.00527586346649821*Q + 1.2957874682855E-07*Q**2:
                    pump_yn = [0, 1, 0, 1, 0, 1, 1] # 2, 4, 6, 7 가동
                elif 2.95 + 0.000497*Q - 0.0000000229*Q**2 <= P < -3.43193582761012 + 0.00120472303735243*Q - 4.08245928068e-08*Q**2:
                    pump_yn = [0, 1, 0, 1, 1, 0, 1] # 2, 4, 5, 7 가동
                elif 0.120821964429389 + 0.000853219487279097*Q - 3.52433865423429E-08*Q**2 <= P < 2.95 + 0.000497*Q - 0.0000000229*Q**2:
                    pump_yn = [0, 0, 0, 1, 1, 1, 0] # 4, 5, 6 가동
                elif 0.46770987097162 + 0.000872862970476709*Q - 3.89262100721736E-08*Q**2 <= P < 0.120821964429389 + 0.000853219487279097*Q - 3.52433865423429E-08*Q**2:
                    pump_yn = [0, 0, 0, 1, 1, 0, 1] # 4, 5, 7 가동
                elif -0.759451815235986 + 0.0010218039074961*Q - 4.43777727901476E-08*Q**2 <= P < 0.46770987097162 + 0.000872862970476709*Q - 3.89262100721736E-08*Q**2:
                    pump_yn = [0, 1, 0, 1, 0, 1, 0] # 2, 4, 6 가동
                elif P < -0.759451815235986 + 0.0010218039074961*Q - 4.43777727901476E-08*Q**2:
                    pump_yn = [0, 1, 0, 0, 1, 0, 1] # 2, 5, 7 가동
                
                if P < 0:
                    print(f"WARNING: Predicted pressure has negative value of {P}")
                print('pump_yn:',pump_yn)
                pump_df = create_pump_df(timestamp, row['Q_GS_OLD_Predict'], row['P_GS_OLD_Predict'], range(1, 8), pump_yn, freqs, 1) # range 입력 시 range(a, a+n) 형태로 사용 (n: 펌프 개수)
                pump_dfs.append(pump_df)
                print('*'*30 + 'pump_dfs' + '*'*30)
                print(pump_dfs)
            

    elif mode == 'NEW':
        pump_dfs = []
        columns_checked = {'Q_GS_NEW_Predict': 'Q_GS_NEW_Predict' in df_result.columns,
                           'P_GS_NEW_Predict': 'P_GS_NEW_Predict' in df_result.columns} # 예측값 존재여부 확인

        for timestamp, row in df_result.iterrows():
            print('row', row)
            # 조건 수정
            if all(columns_checked.values()):
                freqs, pump_yn = [None, None, None, None], [0, 0, 1, 0] # else 조건 (default)

                pump_df = create_pump_df(timestamp, row['Q_GS_NEW_Predict'], row['P_GS_NEW_Predict'], range(1, 5), pump_yn, freqs, 2) # range 입력 시 range(a, a+n) 형태로 사용 (n: 펌프 개수)
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
        'PRDCT_TIME_DIFF' : 5
        })
    timestamp_fmt = '%Y-%m-%d %H:%M:%S'
    timestamp_temp = datetime.strptime(timestamp, timestamp_fmt)
    #pump_df['OPT_IDX'] = timestamp.strftime(f'701-367-FRI:%Y%m%d%H-') + datetime.now().strftime('%H%M')
    pump_df['OPT_IDX'] = f'701-367-FRI-{pump_grp}:{timestamp_temp.strftime("%Y%m%d%H-")}-{datetime.now().strftime("%H%M")}'
    #pump_df.to_sql('TB_CTR_PUMPYN_RST', engine, if_exists='append', index=False)
    #print('pump_df- ',pump_df)
    return pump_df

def create_tnk_df(df_result, test_timestamp):
    for col in df_result.columns:
        tnk_df = pd.DataFrame({
        'DSTRB_ID': [col] * len(df_result),
        'PRDCT_VALUE': df_result[col].fillna(0).values,
        'RGSTR_TIME': df_result.index
        })
        tnk_df.set_index(['DSTRB_ID', 'RGSTR_TIME'])        
        print(tnk_df)
        tnk_df.to_sql('TB_CTR_TNK_RST', engine, if_exists='append', index=False)
    return

def Predict_5min_test_old(name, model_name, mode='FLUX'):
    KST = timezone('Asia/Seoul')
    now = datetime.now().astimezone(KST) 
    test_timestamp = now.strftime('%Y-%m-%d %H:%M:%S') 
    
    df, model, loaded_scalers = initialization(name, model_name, mode=mode)
    data_df = pd.DataFrame()

    db_connection = open_db()
    for i in range(len(df)):
        data_df[f"{df.변수명[i]}"] = set_index_df(pd.DataFrame(get_db_df(db_connection, f"{df.태그명[i]}", test_timestamp)))
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
    testPredict_result = testPredict[:, -step_topredict, :]  # 마지막 시간 인덱스 (00분) 결과만 사용
    
    if testPredict_result.ndim == 2:
        pass
    else:
        testPredict_result = np.expand_dims(testPredict_result, axis = 0)
    
    start_time_predict_str = str(test_timestamp)
    print(f"예측 시점 : {start_time_predict_str} (KTC)")

    # 예측 결과 데이터 프레임 구성
    df_result = pd.DataFrame(index=[test_timestamp + timedelta(minutes=1)])  # 00분 시간 인덱스

    for k in range(testPredict_result.shape[1]):
        df_result[f"{list(df.loc[df['비고'] == 'target'].변수명)[k]}_Predict"] = RELU(loaded_scalers[list(df.loc[df['비고'] == 'target'].변수명)[k]].inverse_transform(testPredict_result[:, k].reshape(-1, 1)).flatten())

    print(f"{step_topredict}분 후 예측 : ")
    df_result_str = df_result.copy()
    df_result_str.columns = [df.loc[df['비고'] == 'target']['태그 설명']]

    create_tnk_df(df_result, test_timestamp)

    return df_result_str, df_result, data_df
    
def Predict_5min_test(name, model_name, mode='FLUX'):
    # 현재 시간의 초를 구합니다.
    current_seconds = time.localtime().tm_sec
    # 10초 이전이면 10초까지 대기
    if current_seconds < 10:
        time_to_wait = 10 - current_seconds
        print(f"Waiting for {time_to_wait} seconds...")
        time.sleep(time_to_wait)
    
    KST = timezone('Asia/Seoul')
    now = datetime.now().astimezone(KST)
    test_timestamp = now.strftime('%Y-%m-%d %H:%M:00')  # 문자열로 현재 시간 포맷
    print('######test_timestamp:',test_timestamp)
    df, model, loaded_scalers = initialization(name, model_name, mode=mode)
    data_df = pd.DataFrame()

    db_connection = open_db()
    for i in range(len(df)):
        data_df[f"{df.변수명[i]}"] = set_index_df(pd.DataFrame(get_db_df(db_connection, f"{df.태그명[i]}", test_timestamp)))
    db_connection.close()
    print("Successfully imported data ...")

    df_to_sequence = data_df.copy().reset_index(drop=True)
    print("------------------------------------------------------------")

    for feature in df.변수명:
        df_to_sequence[feature] = loaded_scalers[feature].transform(df_to_sequence[[feature]])

    testset = df_to_sequence.copy()
    testset = testset.fillna(testset.mean())
    d_testX = np.expand_dims(np.array(testset[list(df.loc[df['비고'] != 'NU'].변수명)]), axis=0)
    testPredict = model.predict(d_testX)
    testPredict_result = testPredict[:, -5, :]  # 마지막 시간 인덱스 (00분) 결과만 사용

    if testPredict_result.ndim == 2:
        pass
    else:
        testPredict_result = np.expand_dims(testPredict_result, axis=0)
    
    # 예측 시점 출력
    start_time_predict_str = test_timestamp
    print(f"예측 시점 : {start_time_predict_str} (KTC)")

    # 예측 결과 데이터 프레임 구성
    future_time = datetime.strptime(test_timestamp, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
    df_result = pd.DataFrame(index=[future_time.strftime('%Y-%m-%d %H:%M:%S')])

    for k in range(testPredict_result.shape[1]):
        scaler_key = list(df.loc[df['비고'] == 'target'].변수명)[k]
        inverse_transformed = loaded_scalers[scaler_key].inverse_transform(testPredict_result[:, k].reshape(-1, 1)).flatten()
        df_result[f"{scaler_key}_Predict"] = np.maximum(0, inverse_transformed)  # Assuming RELU is intended to apply np.maximum(0, x)

    print(f"5분 후 예측 : ")
    df_result_str = df_result.copy()
    df_result_str.columns = [df.loc[df['비고'] == 'target']['태그 설명']]
    
    print('df_result:',df_result)

    
     
    return df_result_str, df_result, data_df.iloc[-1]
 
 # old code 
'''
def pred_and_upload_gs_test(): #고산정수장 예측(구,신)
    _, df_result_flux = Predict_5min_test('Gosan','gs_v10_0805', mode = 'FLUX')
    _, df_result_pres = Predict_5min_test('Gosan','gs_v11', mode = 'PRES')

    df_result_old = pd.concat([df_result_flux['Q_GS_OLD_Predict'], df_result_pres['P_GS_OLD_Predict']], axis = 1)
    df_result_new = pd.concat([df_result_flux['Q_GS_NEW_Predict'], df_result_pres['P_GS_NEW_Predict']], axis = 1)

    pred_pump(df_result_old, 'OLD') #구정수장 펌프예측
    pred_pump(df_result_new, 'NEW') #신정수장 펌프예측
    return 
'''

def pred_and_upload_gs_test(): #고산정수장 예측(구,신)
    '''
    기존 유량 모델명 : gs_v10_mini
    기존 압력 모델명 : gs_v11_mini
    -> 241011 변경
    23년 5월(패턴) 이후 유량 모델명 : gs_flux_241011_since230513
    23년 5월(패턴) 이후 압력 모델명 : gs_pres_241011_since230513
    23년 5월(패턴) 이전 유량 모델명 : gs_flux_241011_until230513
    23년 5월(패턴) 이전 압력 모델명 : gs_pres_241011_until230513
    '''
    
    _, df_result_flux, cur_flux = Predict_5min_test('Gosan_mini','gs_flux_241011_until230513', mode = 'FLUX')
    _, df_result_pres, cur_pres = Predict_5min_test('Gosan_mini','gs_pres_241011_until230513', mode = 'PRES')
    cur_flux = cur_flux.to_frame().T
    cur_flux = cur_flux.iloc[:, :2].reset_index(drop=True)
    cur_flux.columns = ['Q_GS_NEW_Predict', 'Q_GS_OLD_Predict']
    cur_flux.index = df_result_flux.index #실제 인덱스는 아니지만 시점이라고 보면 될듯?
    cur_flux = cur_flux.astype(float)
    cur_pres = cur_pres.to_frame().T
    cur_pres = cur_pres.iloc[:, :2].reset_index(drop=True)
    cur_pres.columns = ['P_GS_NEW_Predict', 'P_GS_OLD_Predict']
    cur_pres.index = df_result_pres.index
    cur_pres = cur_pres.astype(float)
    print(cur_flux)
    
    error_flux = abs((df_result_flux - cur_flux) / cur_flux)
    beta_features = error_flux.mean(axis=0)  # 각 피처별로 평균 절대 오차를 계산
    
    # Calculate - 피처별 보정 적용
    corrected_df_result_flux = pd.DataFrame(columns=df_result_flux.columns)
    for feature in df_result_flux.columns:
        beta = beta_features[feature]
        if beta > 0.2:
            corrected_df_result_flux[feature] = (1-beta)*df_result_flux[feature] + beta*cur_flux[feature]
        else:
            corrected_df_result_flux[feature] = 0.8*df_result_flux[feature] + 0.2*cur_flux[feature]
    
    error_pres = abs((df_result_pres - cur_pres) / cur_pres)
    beta_features = error_pres.mean(axis=0)  # 각 피처별로 평균 절대 오차를 계산

    corrected_df_result_pres = pd.DataFrame(columns=df_result_pres.columns)
    for feature in df_result_pres.columns:
        beta = beta_features[feature]
        if beta > 0.2:
            corrected_df_result_pres[feature] = (1-beta)*df_result_pres[feature] + beta*cur_pres[feature]
        else:
            corrected_df_result_pres[feature] = 0.8*df_result_pres[feature] + 0.2*cur_pres[feature]

    df_result_old = pd.concat([corrected_df_result_flux['Q_GS_OLD_Predict'], corrected_df_result_pres['P_GS_OLD_Predict']], axis = 1)
    df_result_new = pd.concat([corrected_df_result_flux['Q_GS_NEW_Predict'], corrected_df_result_pres['P_GS_NEW_Predict']], axis = 1)

    create_tnk_df(df_result_old, df_result_old.index)
    create_tnk_df(df_result_new, df_result_new.index)
    pred_pump(df_result_old, 'OLD') #구정수장 펌프예측
    pred_pump(df_result_new, 'NEW') #신정수장 펌프예측

    return  df_result_old, df_result_new

def pred_and_upload_gs_test_2(): #고산정수장 예측(구,신)
    '''
    241011 메모
    23년 5월 이전 패턴 모델명(통합) : gs_241011_until230513
    23년 5월 이후 패턴 모델명(통합) : gs_241011_since230513
    '''

    _, df_result = Predict_5min_test('Gosan_mini', 'gs_241011_until230513', mode = 'FLUX')

    df_result_old = pd.concat([df_result['Q_GS_OLD_Predict'], df_result['P_GS_OLD_Predict']], axis = 1)
    df_result_new = pd.concat([df_result['Q_GS_NEW_Predict'], df_result['P_GS_NEW_Predict']], axis = 1)

    pred_pump(df_result_old, 'OLD') #구정수장 펌프예측
    pred_pump(df_result_new, 'NEW') #신정수장 펌프예측
    return 

def predict_and_upload_flux_test(taglist): #하위 배수지 예측
    i = 0
    for sheetname in taglist.sheetnames[2:]:
        print(f"---Predicting {sheetname}---")
        _, df_result, _ = Predict_5min_test(sheetname, f'gs_{sheetname}', mode = 'BOTH')
        create_tnk_df(df_result, df_result.index)
        i += 1
    return
    
    
def run_threaded(job_func, args):
    time.sleep(5)  # 10초 딜레이
    job_thread = threading.Thread(target=job_func, args=args)
    job_thread.start()
    
def run_subprocess(command):
    time.sleep(2)  # 2초 딜레이
    subprocess.run(command, shell=True, check=True)

def schedule_job(taglist):
    executor.submit(predict_gs_test, taglist)

def predict_gs_test(taglist): #전체 예측

    
    KST = timezone('Asia/Seoul')
    start = time.time()
    print(f"실행 시작: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")

    # Caution : 아래 두 Line 중 하나만 주석 해제 되어있어야 함
    pred_and_upload_gs_test()              # 241011 유량 및 압력을 각각 따로 예측하는 방식(기존)
    # pred_and_upload_gs_test_2()          # 241011 유량+압력을 한번에 예측하는 방식
    
    predict_and_upload_flux_test(taglist)

    print(f"실행 완료: {str(datetime.now().astimezone(KST)).split('.')[0]} (KTC)")
    print(f"실행 시간 : {time.time() - start :.2f} 초")
    '''
    exec0 = f"python /home/app/pump3/epanet/test.py --startDt '{prdct_time}' --endDt '{prdct_time}' --pre False"
    exec1 = f"python /home/app/pump3/epanet/test.py --startDt '{test_timestamp}' --endDt '{test_timestamp}' --pre True"
    time.sleep(2)
    threading.Thread(target=run_subprocess, args=(exec0,)).start()
    time.sleep(10)
    threading.Thread(target=run_subprocess, args=(exec1,)).start()
    '''
    return
    
window_size = 60
step_topredict = 5 # 예측할 시간 = 5분

taglist_name = r"/home/app/pump3/GS_taglist.xlsx"
taglist = openpyxl.load_workbook(taglist_name)
db_config = get_db_config() # DB 연결정보
database_connection_string = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
engine = create_engine(database_connection_string)
print('##CHECKN')
#schedule.every().minute.do(predict_gs_test(taglist))
#predict_gs_test(taglist)
schedule.every().minute.do(schedule_job, taglist)


while True:
    schedule.run_pending()
    time.sleep(1)


# '''

