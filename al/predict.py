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

def get_ts(start_date, interval, length):
    start_date = pd.Timestamp(start_date) 
    res = []

    for _ in range(length):
        res.append(start_date)
        start_date += pd.Timedelta(minutes=interval)
        
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')
    parser.add_argument('--start_date')
    parser.add_argument('--ref_minutes',default=60*32)
    parser.add_argument('--source_type', default='file')
    parser.add_argument('--feeder', default=None)
    parser.add_argument('--slide', default=None)
    parser.add_argument('--ref_days',default=10)
    parser.add_argument('--mjson', default='defmodel.json')

    args = parser.parse_args()
    session_name = args.session

    with open(args.mjson) as f :
        config = json.load(f)

    session = config[session_name]
    label_col = session['dataset']['label_col']
    scaler_path = session["scaler_output_name"]

    scaler = joblib.load(scaler_path)
    s, m = scaler.scale_[0], scaler.mean_[0]

    with open('datafeeder.json') as f:
        feeder = json.load(f)[args.feeder]

    connection = feeder["connection"]

    ts = pd.Timestamp(args.start_date)
    end_ts = ts + pd.Timedelta(minutes=int(args.ref_minutes))
    
    start_date = pd.Timestamp(args.start_date)
    end_date = (pd.Timestamp(start_date) + pd.Timedelta(minutes=int(args.ref_minutes)))

    window_generator_options = session["window_generator"]

    if args.slide:
        window_generator_options['slide_min'] = int(args.slide)

    wclass = window_generator_options["_class"]
    wclass = _import(f"dataset.{wclass}")
    del window_generator_options["_class"]

    if args.source_type == 'rdb' :
        start_date = pd.Timestamp(args.start_date)
        end_date = (pd.Timestamp(start_date) + pd.Timedelta(days=int(args.ref_days)))

        tr, vd, tt = load_dataset_rdb_split(
            session["connection"],
            table=session["input_table"],
            tags=[session["dataset"]["label_col"]],
            ts_from=start_date, 
            ts_to=end_date, 
            scaler_name=session["scaler_output_name"], label_col=label_col)

    elif args.source_type == 'file':
        validation_file = session["validation_file"]
        tr = load_dataset(validation_file, label_col=label_col, start_date=args.start_date, days=int(args.ref_days), scaler_name=scaler_path, prep=True, scale=False) #Temp

    else:
        assert('source type is invalid')

    w = wclass(train_df=tr, val_df=None, test_df=None, train_only=True, **window_generator_options)

    model = tf.keras.models.load_model(session["model_output_name"])

    scaler = joblib.load(scaler_path)
    s, m = scaler.scale_[0], scaler.mean_[0]

    predict = model.predict(w.train)
    predict = predict.reshape((-1)) * s + m

    df = pd.DataFrame(data=predict, columns=['PRDCT_MEAN'])

    df["ANLY_TIME"] = get_ts(args.start_date, session["window_generator"]["input_time_min_range"], predict.shape[0])

    #df["INF_REF_END"] = get_ts( pd.Timestamp(args.start_date) + pd.Timedelta(minutes=session["window_generator"]["input_time_min_range"]), session["window_generator"]["input_time_min_range"], predict.shape[0])
    df["PRDCT_TIME_DIFF"] = session["window_generator"]["input_time_min_range"]

    df["PRDCT_TIME"] = get_ts(
        pd.Timestamp(args.start_date) 
        + pd.Timedelta(
            minutes=session["window_generator"]["input_time_min_range"]
            + int(args.slide)
          ), 
        session["window_generator"]["input_time_min_range"], predict.shape[0]
        )

    #df["RST_DURATION"] = session["window_generator"]["output_min_time"]
    #df["PRDT_TYPE"] = 'AVG'
    d = args.start_date.replace('-', '') 
    df['OPT_IDX'] = d + "_" + df['ANLY_TIME'].apply(lambda x : x.strftime("%h%m")) + "_" + label_col

    df['DC_NMB'] = 'a'
    df['FLAG'] = 1

    from pump_rt_models import FitPumpPerformanceCurve
    from pump_rt_algo import Calc_pump_properties, PumpEQ_DB_connector
    from pump_rt_algo import get_connection
    import pymysql

    def get_connection(cname):
        with open('connections.json') as f:
            db = json.load(f)[connection]
            return pymysql.connect(**db)

    conn = get_connection('maria-dev2')
    pdbc = PumpEQ_DB_connector(conn)
    wcode = "KSSCADA"
    pumpAttr, pumpTags = pdbc.getPumpAttribute(wppcode=wcode, pumpGroup=1)

    FPPC = FitPumpPerformanceCurve(pumpAttr, pumpTags)
    CPP = Calc_pump_properties(conn, pumpAttr, pumpTags, wppcode=wcode)

    idxs = [[1,2,3]] * df.index.size # TODO

    df['TUBE_PRSR_PRDCT'] = [CPP.head_given_QnT(idxs, Q, 20)[0]*FPPC.rho_water(20)/1e4 for idxs, Q in zip(idxs, df['PRDCT_MEAN'].values)] # 2개 이상이면 예측 관압이 0이 나오는 이유 확인 해야 함 
    df['PWR_PRDCT'] = [CPP.power_given_QnT(idxs, Q, 20)[0] for idxs, Q in zip(idxs, df['PRDCT_MEAN'].values)]
    df["OPT_IDX"] = session["dataset"]["label_col"]
    df["WPP_CODE"] = wcode

    query_form = "INSERT IGNORE INTO `{TB_NM}` (`{COLUMNS}`) VALUES ({VALS})"
    query = query_form.format(TB_NM='ems_db.TB_CTR_OPT_RST',
                              COLUMNS='`, `'.join(df.columns.tolist()),
                              VALS=(",".join(["%s"] * df.shape[1])))

    cursor = conn.cursor()
    cursor.executemany(query, df.values.tolist())
    #conn.commit()

    ctr_optfk_rst = 0
    ctr_optfk_rst["FREQ"] = 0

    print(df)
    exit(0)

    #df = df[["INF_REF_START", "INF_REF_END", "INF_REF_MIN", 'RST_TIME', 'RST_DURATION', "TARGET_TAG", "PRDT_TYPE", "PRDT_VAL"]]

    """
    with open('connections.json') as f:
        db = json.load(f)[connection]

    engine = create_engine(
        "mysql://{user}:{password}@{host}:{port}/{db}".format(**db)
    )

    df.to_sql('FRI_PRDT_RST', con=engine, if_exists='append')
    """

