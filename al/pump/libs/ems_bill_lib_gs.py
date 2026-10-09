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

def type_transform(args):
    """
    datetime type으로 변환시키는 모듈
    """
    # tuple형태로 값이 들어오기 때문에 전처리 필요
    if len(args) == 1:
        args = args[0]

    # 입력값 형태
    input_type = type(args)

    # timestamp, datetime
    if input_type == pd.pandas._libs.tslibs.timestamps.Timestamp or input_type == datetime:
        input_val = args.date()

    # str or int
    elif input_type == str or input_type == int:
        # int -> str
        input_val = str(args)
        # yyyy, mm, dd format
        try:
            input_val = datetime.strptime(input_val, '%Y%m%d')
        except Exception as e:
            # yy, mm, dd format or other format
            print("input 형식을 참고해주세요.")
            raise (e)

    # tuple
    elif input_type == tuple:
        y, m, d = args
        input_val = date(y, m, d)

    # datetime.date
    elif input_type == date:
        input_val = args

    # ?
    else:
        print("input 형식을 참고해주세요.")
        raise TypeError

    return input_val


def get_tags(wpp_code):
    if wpp_code == 'GM':
        return ['865-334-PWQ-4012', '865-334-PWQ-4013', '865-334-PWQ-4014']
    elif wpp_code == 'GM2':
        return ['865-337-PWQ-4700', '865-337-PWQ-4701']
    elif wpp_code == 'KS':
        return ['701-367-PWI-4015', '701-367-PWI-4017', '701-367-PWI-4019', '701-367-PWI-4021', '701-367-PWI-4023', '701-367-PWI-4025', '701-367-PWI-4027', '701-367-PWQ-4015', '701-367-PWQ-4017', '701-367-PWQ-4019', '701-367-PWQ-4021',
        '701-367-PWQ-4023', '701-367-PWQ-4025', '701-367-PWQ-4027', '701-367-PWI-4043', '701-367-PWI-4045', '701-367-PWI-4047', '701-367-PWI-4049', '701-367-PWQ-4043', '701-367-PWQ-4045', '701-367-PWQ-4047', '701-367-PWQ-4049']

def get_connection(connection):
    import json
    with open('connections.json') as f:
        db = json.load(f)[connection]
    return pymysql.connect(**db)
  
def _prep(data, cursor):
    try:
        col_ls = [c[0].split('.')[1] for c in cursor.description]
    except IndexError:
        col_ls = [c[0] for c in cursor.description]

    df = pd.DataFrame(data, columns=col_ls)

    tag_rgx = re.compile('\d+\-\d+\-[a-zA-Z]+\-\d+')
    df.loc[:, 'tagname'] = df.tagname.apply(lambda x: re.search(tag_rgx, x).group(0))
    df.loc[:, 'value'] = df.value.astype('float')

    return pd.pivot_table(df, index='ts', columns='tagname', values='value')

def _read(cursor, tags, st_date, end_date, table='ems_db.TB_RAWDATA'):
    tags = list(map(lambda x : "'" + x + "'", tags))
    tags_condition = ",".join(tags)

    sql = f"select ts, tagname, value from {table} where `quality` = '100' AND SECOND(`ts`) = 0 "
    sql += f"AND ts >= '{st_date}' AND ts < '{end_date}'" #TODO
    sql += f" AND tagname in ({tags_condition})"
    cursor.execute(sql)    
    print(sql)
    return cursor.fetchall()

def _no_interval(df, freq='1T'):
    """
    timestamp 공백이 없도록 지정

    Parameter
    ---------
    df: DataFrame
    freq: str
        데이터 주기 (1T = 1분)
    """
    time_df = pd.DataFrame(index=pd.date_range(df.index[0], df.index[-1], freq=freq))
    df = time_df.merge(df, left_index=True, right_index=True, how='left')

    return df

def _grubbs_stat(data):
    """
    Grubb's test

    Parameter
    ---------
    data: numpy.array
        이상치 탐색 데이터
    """
    std = np.std(data)
    mu = np.mean(data)
    abs_dev = abs(data - mu)

    g_stat = max(abs_dev) / std
    max_idx = np.argmax(abs_dev)

    return g_stat, max_idx

def _critical_value(size, alpha):
    """
    임계치 계산 모듈

    Parameter
    ---------
    size: int
        이상치 탐색 데이터 총 개수
    alpha: float
        유의 수준
    """
    t_dist = stats.t.ppf(1 - alpha / (2 * size), size - 2)
    numer = (size - 1) * np.sqrt(np.square(t_dist))
    denom = np.sqrt(size) * np.sqrt(size - 2 + np.square(t_dist))

    return numer / denom

def _g_esd_test(data, alpha, max_outliers):
    """
    Generalized Extreme Studentized Deviate test

    Parameter
    ---------
    data: pandas.Series
        이상치 탐색 데이터
    alpha: float
        유의 수준
    max_outliers: int
        최대 이상치 개수
    """

    # null, zero data drop
    data = np.array(data[(data != 0) & (data.notna())])

    outlier_ls = []
    for _ in range(max_outliers):

        # 임계치
        if len(data) == 0:
            continue
            
        g_critical = _critical_value(len(data), alpha)
        # 통계량
        g_stat, max_index = _grubbs_stat(data)
        # 이상치 여부
        is_outlier = True if g_stat > g_critical else False

        if is_outlier:
            outlier_ls.append(data[max_index])

        data = np.delete(data, max_index)

    return outlier_ls


def _anomaly(df, how='drop'):
    """
    이상치 탐지 및 noise 제거

    Parameter
    ---------
    df: pandas Dataframe
        유효전력, 유효전력량 데이터
    how: str
        전처리 방법
        drop: 이상치 및 노이즈 제거한 데이터만 사용
        fill_pwi: 이상치 및 노이즈 제거 + 순시값이 존재할 경우, 순시값으로 대체
    """

    # 총 유효전력량 데이터 --> 1분간 데이터 사용량
    total_pwq = df.filter(like='PWQ').sum(axis=1).diff(1)
    total_pwq = total_pwq.mask(total_pwq < 1e-2).mask(abs(total_pwq) > 2e2)
    # 총 유효전력 데이터 --> 1분간 데이터 사용량
    total_pwi = df.filter(like='PWI').sum(axis=1) / 60
    total_pwi = total_pwi.mask(total_pwi < 1e-2).mask(total_pwi > 2e2)

    # 이상치 추출 (G-ESD Method)
    outliers_pwi = _g_esd_test(total_pwi, 0.05, int(len(total_pwi) * 0.01))

    print('===== Data Preprocessing (Dealing Missing Value) ....')
    if how == 'drop':
        elec_usage_df = total_pwi[~total_pwi.isin(outliers_pwi)].to_frame()
        elec_usage_df.columns = ['PWR']

        return elec_usage_df

    elif how == 'fill_pwi':
        outliers_pwq = _g_esd_test(total_pwq, 0.05, int(len(total_pwq) * 0.01))

        # PWQ, PWI 이상치 제거
        clean_pwq = total_pwq[(~total_pwq.isin(outliers_pwq)) & (total_pwq != 0) & (total_pwq.notna())].to_frame('PWQ')
        clean_pwi = total_pwi[~total_pwi.isin(outliers_pwi)].to_frame('PWR')

        # 전력사용량 df
        elec_usage_df = pd.DataFrame(index=df.index)
        elec_usage_df = elec_usage_df.merge(clean_pwq, left_index=True, right_index=True, how='left')
        elec_usage_df = elec_usage_df.merge(clean_pwi, left_index=True, right_index=True, how='left')

        # PWQ값으로 대체할 수 있는 timestamp
        chg_idxs = elec_usage_df[
            ((elec_usage_df.PWR.isna()) | (elec_usage_df.PWR == 0)) & (elec_usage_df.PWQ.notna())].index
        # PWI값 대체
        for i in chg_idxs:
            elec_usage_df.loc[i, 'PWR'] = elec_usage_df.loc[i, 'PWQ']

        elec_usage_df = elec_usage_df[['PWR']]

        return elec_usage_df

def main(cursor, data):
    pass    

def _applied_power(cursor, df, exec_time, DOCKER_ID, wpp_code):
    """
    요금적용전력 계산 --> 1달에 1회씩 실행
    DB에 업로드하도록 코드 수정 필요료

    Parameter
    ---------
    db : DB
        Maria DB
    df : pandas DataFrmae
        전처리 완료된 Data Table
    exec_time: timestamp
        모듈 실행 시간
    DOCKER_ID: str
    """
  #  print('===== Applied Power (Calculate) ....')

    # 요금적용전력 딕셔너리 산출 (적산데이터 기준 15분 단위)
    rolling_df = df.rolling(window=15).sum() * 4
    rolling_df = rolling_df[rolling_df.notna()]
    max_monthly = rolling_df.resample('1M').max()
    print(max_monthly)

    applied_power_dict = {}

    for ymd in max_monthly.index:
        candidates = _maximum_peak(ymd)
        candidates = list(map(lambda x: x.strftime('%Y-%m-%d'), candidates))[-1:]

        try:
            applied_power_dict[ymd.strftime('%Y%m')] = int(max_monthly.loc[candidates].max()) #TODO
        except KeyError:
            continue

    print(applied_power_dict)

    cursor.execute("SELECT current_timestamp;")
    time_now = cursor.fetchall()[0]['current_timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    #print('apd')
    #print(applied_power_dict)

    applied_df = pd.DataFrame(applied_power_dict.items(), columns=['DATA_BS_YMNTH', 'PWR'])
    applied_df['RST_TYP'] = 1
    applied_df['DC_NMB'] = DOCKER_ID
    applied_df['ANLY_DATE'] = time_now
    applied_df["WPP_CODE"] = wpp_code

    applied_df[['ANLY_DATE', 'DATA_BS_YMNTH', 'RST_TYP', 'PWR','DC_NMB']]
    """
    if len(applied_df) == 0:
        return

    applied_df.to_sql()

    query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"
    query = query_form.format(TB_NM='TB_RT_POWER_RST',
                              COLUMNS='`, `'.join(applied_df.columns.tolist()),
                              VALS=(",".join(["%s"] * applied_df.shape[1])))
    print(query) 

    cursor.executemany(query, applied_df.values.tolist())
    """
    
    return applied_df

def _maximum_peak(end):
    """
    검침 기간에 해당하는 데이터 추출 (검침 당월을 포함한 직전 12개월 중 12/1/2/7/8/9월분의 최대수요전력 중 가장 큰 최대수요전력을 요금적용전력)

    Parameter
    ---------
    end: Timestamp
        요금적용전력을 구하기 위한 시점 날짜 정보
    """
    start = end - relativedelta(months=11)
    candidates = list(
        filter(lambda x: x.month in [1, 2, 7, 8, 9, 12], pd.date_range(start, end, freq='1m'))) + [end]
    return candidates
  
def _preprocess(cursor, df):
    df = _no_interval(df)
    #df = _actn_p0001(cursor, df)
    return _anomaly(df, how='fill_pwi')

def get_applied_pwr_table(cursor):
    query = f"""
    SELECT `DATA_BS_YMNTH`, `PWR` FROM ems_db.TB_RT_POWER_RST
    WHERE `RST_TYP`='1' AND 
      (`DATA_BS_YMNTH`, `RGSTR_TIME`) IN (SELECT `DATA_BS_YMNTH`, MAX(`RGSTR_TIME`) AS `RGSTR_TIME` 
      FROM ems_db.TB_RT_POWER_RST GROUP BY `DATA_BS_YMNTH`)
    """
    print(query)

    cursor.execute(query)
    elems = cursor.fetchall()
    return pd.DataFrame(elems)

def _get_table(cursor, config_key):
    """
    테이블 조회 후 dataframe 변환

    Parameters
    ----------
    db: Database
        maria_db
    conconfig_keyfig: str
        query config key
    """

    query = """
    SELECT t1.`RATE_IDX`, t1.`RATE_CD`, t2.`MNTH`, t2.`STN_TM`, t2.`SSN`, t2.`TIMEZONE`, t2.`BASE_RATE`, t2.`ELCTR_RATE`
    FROM ems_db.TB_RT_MSTR_INF t1
    INNER JOIN (SELECT * FROM ems_db.TB_RT_RATE_INF) t2
    ON t1.`RATE_IDX` = t2.`RATE_IDX`
    WHERE t1.`USE_YN`='1';
    """

    cursor.execute(query)
    elems = cursor.fetchall()
    df = pd.DataFrame(elems)

    return df

# 관공서 공휴일 유무(폐쇠망) --> 확인 결과 pytimekr의 holidays 결과가 관공서 공휴일이 반영된 결과로 나옴 [2020, 2021 확인]
def is_holiday(*args):
    """
    관공서 공휴일 유무 제공 (일요일, 3.1, 광복절, 개천절, 한글날, 1.1, 부처님오신날[음력4.8], 5.5, 6.6, 추석전/당일/다음[음력 8.14, 15, 16], 12.25)
    input: 날짜
        - type:
            1) pandas._libs.tslibs.timestamps.Timestamp
            2) datetime.date
            3) datetime.datetime
            4) yyyymmdd (ex. 20200101)
            5) (yyyy, mm, dd) 년월일 int로 (ex. 2020, 1, 1)

    output: 공휴일 유무
    """
    # data type transformation
    date_val = type_transform(args)

    # Sunday
    if date_val.weekday() == 6:
        return True

    # Other cases
    else:
        # 해당년도의 공휴일 날짜 추출
        holiday_ls = pytimekr.holidays(date_val.year)
        if date_val in holiday_ls:
            return True
        else:
            return False

def get_timezone(timestamp, ssn_tz_df):
    """
    시간대 정보 추출

    Parameter
    ---------
    timestamp: timestamp
    ssn_tz_df: pandas dataframe
        계절, 부하시간 정보 테이블
    """
    # 시간대, 계절 정보 획득
    mnth = '%.2d' % (timestamp.month)
    hour = '%.2d' % (timestamp.hour)

    try:
        result = ssn_tz_df[(ssn_tz_df.MNTH == mnth) & (ssn_tz_df.STN_TM == hour)].values[0]
        ssn, tz = result[-2], result[-1]

    except IndexError:
        raise IndexError

    # 공휴일 유무
    holiday_check = is_holiday(timestamp)
    # 공휴일일 경우 --> 경부하로 할당 (한전 정책)
    if holiday_check:
        tz = 'L'

    # 공휴일이 아닌 토요일 --> 한전 정책
    if timestamp.weekday() == 5 and tz == 'H':
        tz = 'M'

    return ssn, tz


def _optimal_payment(df, adf, maria_db, exec_time, DOCKER_ID, wpp_code):
    """
    -*- 최적전력요금제 산출 알고리즘 -*-

    Parameters
    ----------
    df: pandas Dataframe
        정제가 완료된 1분 단위 전력량 적산 데이터
    maria_db: maria_db변수
    exec_time: timestamp
        모듈 실행 시간
    DOCKER_ID: str
    """

    print('===== Optimal Payment (Calculate) ....')

    if len(df) == 0:
        print('데이터 없어요!')
        raise ValueError

    result_date = df.index[-1].strftime('%Y%m')
    print("result_date: ", result_date)

    ## 데이터 누락율 계산
    total_length = len(pd.date_range(df.index[0], df.index[-1], freq='1T'))
    missing_length = len(df[df.PWR.isna()]) + (total_length - len(df))
    missing_rate = round(missing_length / total_length * 100, 5)

    ## 데이터 가져오기
    ### 요금 정보
    rate_info_df = _get_table(maria_db, 'RATE_INFO')
    print("rate_info_df:", rate_info_df)

    # 1시간 단위 전력 사용량 테이블
    pwr_1hour_df = df.PWR.resample('1H').sum().to_frame()
    pwr_1hour_df['SSN'] = None
    pwr_1hour_df['TIMEZONE'] = None
    print("pwr_1hour_df:", pwr_1hour_df)

    # 계절, 부하시간 정보 테이블
    ssn_tz_df = rate_info_df[['MNTH', 'STN_TM', 'SSN', 'TIMEZONE']].drop_duplicates()

    for ts in pwr_1hour_df.index:
        ssn, tz = get_timezone(ts, ssn_tz_df)
        pwr_1hour_df.loc[ts, 'SSN'] = ssn
        pwr_1hour_df.loc[ts, 'TIMEZONE'] = tz

    # 요금제별 전기료 테이블
    elctr_info_df = rate_info_df[['RATE_IDX', 'SSN', 'TIMEZONE', 'ELCTR_RATE']]
    elctr_info_df = pd.pivot_table(elctr_info_df, index=['SSN', 'TIMEZONE'], columns='RATE_IDX',
                                   values='ELCTR_RATE').reset_index()

    # 전력사용량 데이터 테이블
    elctr_tmp_df = pwr_1hour_df.reset_index().merge(elctr_info_df, on=['SSN', 'TIMEZONE'], how='left').set_index('index')
    # elctr_tmp_df = pwr_1hour_df.reset_index().merge(elctr_info_df, on=['SSN', 'TIMEZONE'], how='left').set_index('ts')
    # 전력사용량 계산 테이블
    elctr_calc_df = elctr_tmp_df.iloc[:, 3:].multiply(elctr_tmp_df.PWR, axis=0)
    # 전력사용량 계산 결과 부착
    elctr_fee_df = elctr_tmp_df.iloc[:, :3].merge(elctr_calc_df, left_index=True, right_index=True, how='left')
    # 년월 정보 추출
    elctr_fee_df['DATA_BS_YMNTH'] = list(map(lambda x: x.strftime('%Y%m'), elctr_fee_df.index))
    # 불필요 칼럼 버리기
    elctr_fee_df = elctr_fee_df.drop(['SSN'], axis=1)
    # 테이블 변환
    elctr_fee_df = pd.melt(elctr_fee_df, id_vars=['DATA_BS_YMNTH', 'TIMEZONE', 'PWR'], var_name='RATE_IDX',
                           value_name='ELCTR_FEE')

    # 월, 요금제, 부하시간대별 총 전력량, 전력사용요금 합계 테이블 생성
    output_df = elctr_fee_df.groupby(['DATA_BS_YMNTH', 'RATE_IDX', 'TIMEZONE'])[
        ['PWR', 'ELCTR_FEE']].sum().reset_index()
    output_df = pd.pivot_table(output_df, index=['DATA_BS_YMNTH', 'RATE_IDX'], columns='TIMEZONE',
                               values=['PWR', 'ELCTR_FEE'])

    # column 명 변환
    cols = output_df.columns.tolist()
    col_ls = []
    for e in cols:
        if 'ELCTR_FEE' == e[0]:
            col_ls.append(e[1] + '_ELCTR_FEE')
        else:
            col_ls.append(e[1] + '_PWR')

    output_df.columns = col_ls
    output_df = output_df.reset_index()

    # 총 사용전력량
    output_df['TOT_PWR'] = output_df[['H_PWR', 'L_PWR', 'M_PWR']].sum(axis=1)
    # 총 전력사용요금
    output_df['ELCTR_FEE'] = output_df[['H_ELCTR_FEE', 'L_ELCTR_FEE', 'M_ELCTR_FEE']].sum(axis=1)
    # 기본요금 정보 추출
    base_fee_df = rate_info_df[['RATE_IDX', 'BASE_RATE']].drop_duplicates()
    # 기본요금단가 부착
    output_df = output_df.merge(base_fee_df, on='RATE_IDX', how='left')
    # 요금적용전력 정보 부착
    ### 요금적용전력 정보
    #applied_df = get_applied_pwr_table(cursor)
    applied_df = adf
    applied_df = applied_df.rename(columns={'PWR': 'APPLIED_PWR'})
    print("applied_df:", applied_df)
    print("output_df", output_df)
    output_df = output_df.merge(applied_df, on='DATA_BS_YMNTH', how='left')

    # 기본요금 산출
    output_df['BASE_FEE'] = output_df['BASE_RATE'] * output_df['APPLIED_PWR']
    # 예비기본요금 - 기본요금 * 10%
    output_df['TMP_BASE_FEE'] = output_df.loc[:, 'BASE_FEE'] * 0.1
    # 역률요금 - 기본요금 * 1%
    output_df['PWR_FACTOR_FEE'] = output_df.loc[:, 'BASE_FEE'] * 0.01
    # 전기요금계: 기본 요금 + 예비 기본 요금 + 전력 사용량 요금 - 역률 요금
    output_df['TOT_ELECTRIC_CHRG'] = output_df[['BASE_FEE', 'TMP_BASE_FEE', 'ELCTR_FEE']].sum(
        axis=1) - output_df.PWR_FACTOR_FEE
    # 부가가치세: 전기요금계 * 10%
    output_df['VAT'] = output_df.loc[:, 'TOT_ELECTRIC_CHRG'] * 0.1
    # 전력기금: 전기요금계 * 3.7%
    output_df['ELECTRIC_FUND'] = output_df.loc[:, 'TOT_ELECTRIC_CHRG'] * 0.037
    # 청구요금: 전기요금계 + 부가가치세 + 전력기금 & 원단위 절사
    output_df['TOT_FEE'] = output_df[['TOT_ELECTRIC_CHRG', 'VAT', 'ELECTRIC_FUND']].sum(axis=1).apply(
        lambda x: math.trunc(x)).to_list()
    # 기타 요금 (총 요금 - 기본 요금 - 전력사용 요금)
    output_df['ETC_FEE'] = output_df.TOT_FEE - output_df.BASE_FEE - output_df.ELCTR_FEE

    # 6개월 기반 최저 요금제 추출
    minimum_rate = output_df.groupby('RATE_IDX')['TOT_FEE'].sum().idxmin()

    # 최저요금제 표기
    output_df['OPT_RATE_YN'] = 0
    idx_num = output_df[(output_df.DATA_BS_YMNTH == result_date) & (output_df.RATE_IDX == minimum_rate)].index[0]
    output_df.loc[idx_num, 'OPT_RATE_YN'] = 1

    # 데이터 누락율 부착
    output_df['DT_MSN_PRCNT'] = missing_rate
    # 코드가 Run된 기준 시간 부착
    output_df['ANLY_DATE'] = datetime.now()

    # DB에 올릴 columns
    col_ls = ["ANLY_DATE", "DATA_BS_YMNTH", "RATE_IDX", "OPT_RATE_YN", "DT_MSN_PRCNT", "TOT_PWR",
              "TOT_FEE", "BASE_FEE", "ETC_FEE", "L_PWR", "M_PWR", "H_PWR", "L_ELCTR_FEE", "M_ELCTR_FEE", "H_ELCTR_FEE"]

    # upload할 테이블
    upload_df = output_df.loc[:, col_ls]
    print("output_df[col_ls]:", output_df.loc[:, col_ls])
    upload_df.loc[:, 'DC_NMB'] = DOCKER_ID

    upload_df = upload_df[upload_df.DATA_BS_YMNTH == result_date]
    upload_df.loc[:, 'ANLY_DATE'] = upload_df.ANLY_DATE.apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    upload_df.rename(columns={ 'DT_MSN_PRCNT': 'DATA_MSN_PRCNT' }, inplace = True)

    return upload_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date')
    parser.add_argument('--end_date')
    parser.add_argument('--connection', default='maria-ems-db-gs')
    args = parser.parse_args()

    start_date = args.start_date
    end_date = args.end_date

    wpp_code = 'KS'

    tags = get_tags(wpp_code)
    # ex : [ 701-]
    conn = get_connection(args.connection)
    cursor = conn.cursor(DictCursor)

    data = _read(cursor, tags, start_date, end_date)
    df = _prep(data, cursor)
    print('preprocess data')
    df = _preprocess(cursor, df)
    df = df.fillna(0)
    print(df)
    print('applied power data')
    adf = _applied_power(cursor, df,0 ,"a", "KSSCADA")

    from pump_rt_algo import get_connection_alchemy_s
    sconn = get_connection_alchemy_s(args.connection)
    adf.to_sql("TB_RT_POWER_RST", con=sconn, if_exists="append", index=False)
    sconn.commit()

    upload_df = _optimal_payment(df, adf, cursor, datetime.now(), 'a', wpp_code=wpp_code)
    upload_df['WPP_CODE'] = wpp_code
    upload_df.to_sql('TB_RT_RATE_RST', con=sconn, if_exists="append", index=False)
    sconn.commit()

    upload_df["RST_TYP"] = 1
    upload_df["PWR"] = upload_df["TOT_PWR"] / 1000
    upload_df["FLAG"] = 0
    
    upload_df = upload_df.copy()[['ANLY_DATE', 'RST_TYP', 'DATA_BS_YMNTH', 'PWR', 'DC_NMB', 'FLAG']]

    conn.close()
    sconn.close()
    
    """
    query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"
    query = query_form.format(TB_NM='TB_RT_POWER_RST',
                              COLUMNS='`, `'.join(upload_df.columns.tolist()),
                              VALS=(",".join(["%s"] * upload_df.shape[1])))

    cursor.executemany(query, upload_df.values.tolist())
    conn.commit()
    conn.close()

    """

    