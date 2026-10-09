import os
import re
import pandas as pd
from functools import reduce
import numpy as np
import argparse
import json

def remove_outliers(df, fri_hh=2e4, ss_cutoff=200, pt_cutoff=500):
    # 화성 소스 그대로 사용하였음
    # 유량이 2000 넘어가는 경우 이상치로 보고 제거
    # 현재는 사용하지 않음
    for c in df.columns:
        x = df[c].values
        if "FRI" in c:
            df[c] = x * ((x>=0) & (x < fri_hh))
        elif "TEI" in c:
            df[c] = x * ((x>=10) & (x <50))

    return df

def merge_data_frames(dfs): 
    return reduce(lambda df, ndf: pd.merge(df, ndf, left_index=True, right_index=True, how="left"), dfs[1:], dfs[0])

def read_csv_files_from_regex(target_dir, expr, **options):
    # 정규식을 이용하여 폴더내 정규식 패턴에 해당하는 모든 파일을 읽어서 합산
    # 현재는 사용하지 않고 있음
    files = os.listdir(target_dir)
    m = re.compile(expr)
    result = []

    for file in files:
        if not m.match(file): continue

        _file = os.path.join(target_dir, file)
        df = pd.read_csv(_file, index_col=0)
        col_name = options["col_identify_func"](file)
        print(col_name)
        df.columns = [col_name]

        if "filter_func" in options: df = options["filter_func"](df)
        if df.index.size == 0: continue
        
        result.append( df )
        print(len(df.index))

    return result

def check_missing_rows(df, interval_minutes):
    return;    

def preprocessing(df, label_col):
    df.index = pd.to_datetime(df.index)
    #df = remove_outliers(df)    
    df = df.resample('1min').mean().fillna(0)
    df = df[ df[label_col] > 0 ]
    
    df = time2vec(df)

    return df

def time2vec(df):
    # 시간 정보를 수치화하여 학습시 피쳐로 사용가능하게끔 전처리 함.
    df2 = df.copy()

    d = df2.index.dayofyear
    w = df2.index.weekday
    h = df2.index.hour
    m = df2.index.minute

    day_minute = h * 60 + m 
    week_minute = ((w*1440) + (h*60) + m)
    year_minute = ((d*1440) + (h*60) + m)

    # 일간 시간 sin 성분 부착
    df2.loc[:,'T2DS'] = np.sin((day_minute * 2 * np.pi) / 1440) 
    # 일간 시간 cos 성분 부착
    df2.loc[:,'T2DC'] = np.cos((day_minute * 2 * np.pi) / 1440)
    # 주간 시간 sin 성분 부착
    df2.loc[:,'T2WS'] = np.sin((week_minute * 2 * np.pi) / (1440*7))
    # 주간 시간 cos 성분 부착
    df2.loc[:,'T2WC'] = np.cos((week_minute * 2 * np.pi) / (1440*7))
    # 연간 시간 sin 성분 부착
    df2.loc[:,'T2YS'] = np.sin((year_minute * 2 * np.pi) / (1440*365.25))
    # 연간 시간 cos 성분 부착
    df2.loc[:,'T2YC'] = np.cos((year_minute * 2 * np.pi) / (1440*365.25))

    return df2

def load_config(config_dir, session):
    with open(config_dir) as f:
        config = json.load(f)
        session = config[session] 

    return session  

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--session')
    args = parser.parse_args()

    config = load_config("defpipe.json", args.session)

    start_date, end_date = config["start_date"], config["end_date"]
    start_date += " 00:00:00"
    end_date += " 23:59:59"

    include_regex = config["include_regex"]
    base_dir = config["base_dir"]
    output_path = config["output_path"]
    label_column = config["label_column"]

    print(config)
    options = {
        "col_identify_func": eval(config['col_identify_func']),
        "filter_func": lambda df: df.loc[start_date:end_date],
    }
    
    dfs = read_csv_files_from_regex(base_dir, include_regex, **options)
    df = merge_data_frames(dfs)

    for c in config["drop_columns"]: df = df.drop(c, axis=1)

    df = preprocessing(df, config["label_column"])

    columns = df.columns.tolist()
    label_idx = columns.index(label_column)
    del columns[label_idx]
    df = df[ [label_column] + columns ]

    df.to_csv(output_path)
