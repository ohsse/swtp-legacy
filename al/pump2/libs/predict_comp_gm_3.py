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
    # 현재 시간에서 1시간씩 더해서 총 24개의 배열을 만듬
    start_date = pd.Timestamp(start_date) 
    res = []

    for _ in range(length):
        res.append(start_date)
        start_date += pd.Timedelta(minutes=interval)
        
    return res

def get_data(conn, table, tag, st_date, end_date, scaler):
    # tag(유량)를 통해 raw데이터에서 시점에 맞는 데이터 가져오기
    sql = f"""
        select * from {table} where tagname = '{tag}' and ts >= '{st_date}' and ts < '{end_date}'
    """
    print(sql)

    cursor = conn.cursor(DictCursor)

    cursor.execute(sql)
    data = cursor.fetchall()
    startdts = pd.Timestamp(data[0]["TS"])

    if startdts.strftime('%Y-%m-%d %h:%m:%s') != st_date.strftime('%Y-%m-%d %h:%m:%s'):
        # 중간 데이터 빠졌을때 채워넣음
        frimean = sum(list( float(x["VALUE"]) for x in data)) / len(data)
        data.insert(0, { 'TAGNAME': tag, 'TS': st_date, 'VALUE': frimean, 'QUALITY': 100, 'SERVER': None }) 

    df = pd.DataFrame(data)

    df["VALUE"] = df["VALUE"].astype(np.float32)
    print(df)
    df = df.drop_duplicates(["TS", "TAGNAME"])
    df = df.pivot(index='TS', columns='TAGNAME')['VALUE']
    df = df.fillna(method='ffill')

    # 1분 간격으로 데이터 리샘플링
    df = df.resample('1min').mean()

    # 결측치 처리
    df = df.fillna(method='ffill')
    df = df.fillna(0)
    df = df[[tag]]
    df[tag] 
    df[[tag]] = scaler.transform(df[[tag]])

    df.index = pd.to_datetime(df.index)

    # 시간 성분 부착
    df = time2vec(df)
   
    return df

freqlist = []

# 각 유량 별로 구간을 반환하는 함수
# 산단계통은 한개의 수식만 적용하므로 항상 0
def getRangeCase_sd(fr):
    return 0

# 각 유량별로 회귀식 적용 구간을 반환하는 함수
# 신평 계통
def getRangeCase_sp(fr):
    if fr >= 8000:
        return 0
    elif fr >= 7400 and fr < 8000:
        return 1
    elif fr >= 6500 and fr < 7400:
        return 2
    elif fr >= 6000 and fr < 6500:
        return 3 
    elif fr >= 5400 and fr < 6000:
        return 4
    elif fr >= 4700 and fr < 5400:
        return 5
    elif fr < 4700:
        return 6

# 각 유량별로 회귀식 적용 구간을 반환하는 함수
# 원호 계통
def getRangeCase_wh(fr):
    if fr >= 1800:
        return 0
    if fr >= 1400 and fr < 1800:
        return 1
    if fr >= 1100 and fr < 1400:
        return 2
    if fr < 1100:
        return 3

# 각 구간 별로 가동 펌프 조합 및 주파수 값 적용
# 신평 계통
def func_sp(fr):
    if fr >= 8000:
        F = [60,55,55]
        return [[14,15,16], [0,1,1,1,], F]
    elif fr >= 7400 and fr < 8000:
        F = [60,53,53]
        return [[14,15,16], [0,1,1,1,], F]
    elif fr >= 6500 and fr < 7400:
        F = [60, 58]
        return [[13, 15], [1,0,1,0], F]
    elif fr >= 6000 and fr < 6500:
        F = [60, 55]
        return [[13, 15], [1,0,1,0], F]
    elif fr >= 5400 and fr < 6000:
        F = [60, 50]
        return [[13, 15], [1,0,1,0], F]
    elif fr >= 4700 and fr < 5400:
        F = [60, 48]
        return [[13, 15], [1,0,1,0], F]
    elif fr < 4700:
        F = [60, 45]
        return [[13, 15], [1,0,1,0], F]

# 각 구간 별로 가동 펌프 조합 및 주파수 값 적용
# 원호 계통
def func_wh(fr):
    if fr >= 1800:
        F = [56, ]
        return [[18, 19], [0,1,1], F]
    elif fr >= 1400 and fr < 1800:
        F = [53, ]
        return [[18, 19], [0,1,1], F]
    if fr >= 1100 and fr < 1400:
        F = [59, ]
        return [[18], [0,1,0], F]
    if fr < 1100:
        F = [55, ]
        return [[18], [0,1,0], F]

# 각 구간 별로 가동 펌프 조합 및 주파수 값 적용
# 산단 계통
def func_sd(fr):
    return [[11,], [1,0], None]

# 신평 계통에 해당하는 중간 결과 값 리스트
# 각 함수는 추후 각 구간에됨매핑됨
f0_0_sp = lambda fr: (-0.0000001689*fr*fr) + (0.0023388701*fr) + (-1.1436969732)
f0_1_sp = lambda fr: (-0.0000001077*fr*fr) + (0.0013670937*fr) + 2.4737599733
f0_2_sp = lambda fr: (-0.0000000945*fr*fr) + (0.0002752396*fr) + 8.5366717987
f0_3_sp = lambda fr: (-0.0000000046*fr*fr) + (-0.0004559493*fr) + 9.2197354259
f0_4_sp = lambda fr: (-0.0000000039*fr*fr) + (-0.0004584844*fr) + 8.6818632639
f0_5_sp = lambda fr: (0.0000003033*fr*fr) + (-0.0030696022*fr) + 13.6253807448
f0_6_sp = lambda fr: (0.0000000487*fr*fr) + (-0.0009955224*fr) + 9.2049565148

f0list_sp = [ f0_0_sp, f0_1_sp, f0_2_sp, f0_3_sp, f0_4_sp, f0_5_sp, f0_6_sp, ]

# 원호 계통에 해당하는 중간 결과 값 리스트
# 각 함수는 추후 각 구간에됨매핑됨
f0_0_wh = lambda fr: (-0.000877*fr) + 10.231893	
f0_1_wh = lambda fr: (-0.000745*fr) + 9.494065	
f0_2_wh = lambda fr: (-0.000952*fr) + 9.229633	
f0_3_wh = lambda fr: (-0.0000001287*fr*fr) + (-0.0016172832*fr) + 9.22217426586	

f0list_wh = [ f0_0_wh, f0_1_wh, f0_2_wh, f0_3_wh, ]

# 산단 계통에 해당하는 중간 결과 값 리스트
# 산단의 경우 1개의 경우만 존재
f0_0_sd = lambda fr: (0.0000022086*fr*fr) + (-0.0109265495*fr) + 19.5231489260
f0list_sd = [f0_0_sd, ]

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
        # 커넥션 정보를 불러옴
        connection = json.load(f)[connection_key]
        connection = pymysql.connect(**connection)

    def _get(session, subGroup):
        label_col = session['dataset']['label_col']
        scaler_path = session["scaler_output_name"]
        database = args.database

        # 데이터 정규화에 사용될 스케일러 로드
        scaler = joblib.load(scaler_path)
        s, m = scaler.scale_[0], scaler.mean_[0]

        ts = pd.Timestamp(args.target_date)

        # 참조할 시작 날짜 (시간)
        start_ts = ts - pd.Timedelta(hours=24) + pd.Timedelta(hours=int(args.target_hour))
        # 참조할 마지막 날짜 (시간)
        end_ts = ts + pd.Timedelta(hours=int(args.target_hour))

        # db에서 raw 데이터 불러옴
        df = get_data(connection, table=session["input_table"], tag=session["dataset"]["label_col"], st_date=start_ts, end_date=end_ts, scaler=scaler)

        # 60*24 = 1440
        # 유량태그1개,+ 시간 성분 컬럼 6개 = 7
        # (1440, 7) 로 reshape함
        v = df.values.reshape((-1, 1440, 7)).astype(np.float32)

        model = tf.keras.models.load_model(session["model_output_name"])
        result = model.predict(v)

        result = result.reshape(-1, 1) * s + m
        df = pd.DataFrame(data=result, columns=['PRDCT_MEAN'])

        # 각 행에 예측 시점 값 넣어줌 (총 24개)
        df["PRDCT_TIME"] = get_ts( pd.Timestamp(args.target_date) + pd.Timedelta(hours=int(args.target_hour)+1), 60, 24)
        # 현재시간을 분석 시간으로 값을 넣음
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
        pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=int(args.pumpGroup), pmTable=f'{database}.TB_CTR_PRF_PUMPMST_INF')

        # subGroup == 1: 신평
        # subGroup == 2: 원호
        # subGroup == 3: 산단

        if subGroup == 3:
            # 산단 계통
            getRangeCase = getRangeCase_sd
            func = func_sd
            pumpidxs = [11, 12]
            f0list = f0list_sd
        else :
            getRangeCase = getRangeCase_sp if subGroup == 1 else getRangeCase_wh
            func = func_sp if subGroup == 1 else func_wh
            pumpidxs = [13, 14, 15, 16] if subGroup == 1 else [17, 18, 19]
            f0list = f0list_sp if subGroup == 1 else f0list_wh

        def predict_pwr(fr, freqs):
            rangeCase = getRangeCase(fr)
            f0 = f0list[rangeCase]

            if subGroup == 1:
                # 케이스별 중간계산식을 통한 최종 산출 회귀식 등록
                f1_0 = lambda tmp, fr, f2, f3, f4: (261.1384*tmp) + (0.0971*fr) + (4.3322*f4) + (3.7568*f3) + (7.3756*f2) +(-1539.1384) # 신평 구간 1에 해당하는 최종 회귀식
                f1_1 = lambda tmp, fr, f1, f3: (261.1384*tmp) + (0.0971*fr) + (3.7568*f3) + (7.4607*f1) +(-1539.1384) # 신평 구간 2에 해당하는 최종 회귀식

            elif subGroup == 2:
                f1_0 = lambda tmp, fr, f2: (206.6165*tmp) + (0.0547*fr) + (0.7646*60) + (3.0695*f2) + (-1585.2680) # 원호 구간 1에 해당하는 최종 회귀식
                f1_1 = lambda tmp, fr, f2: (206.6165*tmp) + (0.0547*fr) + (3.0695*f2) + (-1585.2680) # 원호 구간 2에 해당하는 최종 회귀식

            # 국가 산단 계통
            elif subGroup == 3:
                f1_0 = lambda tmp, fr : (27.2425*tmp) + (-0.0105*fr) + (2.8369*60) + (-5.8539) # # 산단 구간 1에 해당하는 최종 회귀식
                tmp = f0(fr)
                return f1_0(tmp, fr)

            if rangeCase < 2:
                tmp = f0(fr)
                return f1_0(tmp, fr, *freqs)

            else :
                tmp = f0(fr)
                return f1_1(tmp, fr, *freqs)
         
        idxs = df["PRDCT_MEAN"].apply(lambda x : func(x)).values.tolist()
        F = 0

        df["FREQ"] = F
        freq = df["FREQ"].values.tolist()

        #df['TUBE_PRSR_PRDCT'] = [CPP.head_given_QnT(idxs[0], Q, 20)[0]*FPPC.rho_water(20)/1e4 for idxs, Q in zip(idxs, df['PRDCT_MEAN'].values)] # 2개 이상이면 예측 관압이 0이 나오는 이유 확인 해야 함 
        #df['TUBE_PRSR_PRDCT'] = 0

        # df['PWR_PRDCT'] = [CPP.power_given_QnF(idxs[0], Q, [0.1,])[0] for idxs, Q in zip(idxs, df['PRDCT_MEAN'].values)]
        # subGroup에 따른 회귀식 계산
        df['PWR_PRDCT'] = [ predict_pwr(Q, freqs) for (idxs, _, freqs), Q in zip(idxs, df['PRDCT_MEAN'].values)] 

        ttag = str(pd.Timestamp.now().hour) + str(pd.Timestamp.now().minute)
        df["OPT_IDX"] = df["PRDCT_TIME"].apply(lambda x: "865-337-FRI:" + x.strftime("%Y%m%d%H") + "-" +  ttag)
        df["PUMP_GRP"] = args.pumpGroup

        df = df.drop('FREQ', axis=1)

        # 펌프 동작 여부 데이터 취합
        pmp_idxs = list(x[1] for x in idxs)
        pump_yn_df = pd.DataFrame(pmp_idxs, columns=pumpidxs) #TODO
        pump_yn_df["OPT_IDX"] = df["OPT_IDX"]

        # opt_idx 별로 그루핑
        ctr_optfk_rst = pump_yn_df.melt('OPT_IDX', var_name="PUMP_IDX", value_name="PUMP_YN")
        
        ctr_optfk_rst["PUMP_TYP"] = 1
        ctr_optfk_rst["DC_NMB"] = 'test'
        ctr_optfk_rst["FLAG"] = 0
        ctr_optfk_rst["PUMP_GRP"] = args.pumpGroup

        ctr_optfk_rst['PUMP_YN'] = ctr_optfk_rst['PUMP_YN'].astype(int)
        # 중복 제거
        ctr_optfk_rst = ctr_optfk_rst.drop_duplicates(['OPT_IDX', 'PUMP_GRP', 'PUMP_IDX'])

        print(df)
        return df, ctr_optfk_rst

    # 신평, 원호, 산단 계통에 대한 유량,전력 예측값 산출
    df_1, opt_1 = _get(config['865-337-FRI-4308_cnn_24'], 1)
    df_2, opt_2 = _get(config['865-337-FRI-4302_cnn_24'], 2)
    df_3, opt_3 = _get(config['865-337-FRI-4600_cnn_24'], 3)

    # 3개통 모두 pumpGroup 3에 해당하므로, 3개의 결과값을 하나로 합친다.
    # 유량값과 전력값은 모두 더함.
    tdf = pd.concat([df_1, df_2, df_3]).sort_values('OPT_IDX')
    tdf = tdf.groupby('OPT_IDX').agg({
        'PRDCT_MEAN': 'sum',
        'PRDCT_TIME': 'max',
        'ANLY_TIME': 'max',
        'PRDCT_TIME_DIFF': 'max',
        'PWR_PRDCT': 'sum',
    })

    tdf['PUMP_GRP'] = 3
    tdf = tdf.sort_index()
    tdf['PRDCT_TIME_DIFF'] = range(1, tdf.index.size + 1)
    tdf['OPT_IDX'] = tdf.index.values

    # 펌프 가동 여부 데이터 합산
    optdf = pd.concat([opt_1, opt_2, opt_3]).sort_values('OPT_IDX')

    # 3개의 결과를 하나의 정수장으로 봐야 하기 때문에 3으로 값을 넣어줌
    optdf['PUMP_GRP'] = 3

    cursor = connection.cursor()
    query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"
    query = query_form.format(TB_NM='TB_CTR_OPT_RST',
                                COLUMNS='`, `'.join(tdf.columns.tolist()),
                                VALS=(",".join(["%s"] * tdf.shape[1])))

    cursor.executemany(query, tdf.values.tolist())

    from pump_rt_algo import get_connection_alchemy_s
    aconn = get_connection_alchemy_s(connection_key)
    optdf.to_sql('TB_CTR_PUMPYN_RST', if_exists="append", con=aconn, index=False)
    
    connection.commit()

    connection.close()
    exit(0)
