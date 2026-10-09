from dataset import load_dataset, load_dataset_rdb_split
from cutils import _import, get_logger, load_model_from_config
import argparse
import json
import pandas as pd
from dataset import DataSets
import numpy as np

if __name__ == "__main__":
    logger = get_logger("train_model")

    parser = argparse.ArgumentParser(prog='train_model')
    parser.add_argument('--session')
    parser.add_argument('--retrain', default=False)
    parser.add_argument('--epochs', default=None)
    parser.add_argument('--source_type', default='file')
    parser.add_argument('--feeder', default=None)
    parser.add_argument('--mjson', default='defmodel.json')

    args = parser.parse_args()

    with open(args.mjson) as f:
        config = json.load(f)

    session_name = args.session
    session = config[session_name]
    logger.info(f"session: {session}")
    scaler_output_path = session["scaler_output_name"]
    train_options = session["train_options"]
    ref_days = session["dataset"]["ref_days"]
    label_col = session["dataset"]["label_col"]

    if args.source_type == 'file':
        df = load_dataset(
                session["input_file"], 
                label_col=label_col,
                days=int(ref_days), 
                start_date=session["dataset"]["start_date"],
                scaler_name=scaler_output_path,
                columns=[label_col],
                prep=True
            )
        ds = DataSets(df, label_col) #TODO
        tr, vd, tt = ds.split_data(df)
            
    elif args.source_type == 'rdb' :
        start_date = pd.Timestamp(session["dataset"]["start_date"])
        end_date = pd.Timestamp(start_date) + pd.Timedelta(days=int(ref_days))

        tr, vd, tt = load_dataset_rdb_split(
            session["connection"],
            table=session["input_table"],
            tags=[
                session["dataset"]["label_col"]
            ],
            ts_from=start_date, 
            ts_to=end_date, 
            make_new_scaler=True,
            scaler_name=session["scaler_output_name"], label_col=label_col)

    wg_options = session["window_generator"]
    wclass = wg_options["_class"]
    wclass = _import(f"dataset.{wclass}")
    
    if args.epochs is not None: train_options["epochs"] = int(args.epochs)

    del wg_options["_class"]
    print(wg_options)
    wg = wclass(train_df=tr, val_df=vd, test_df=tt, **wg_options)

    if args.retrain:
        import tensorflow as tf
        logger.info("load a existing model to retrain")
        model = tf.keras.models.load_model(session["model_output_name"])
    else:
        logger.info(f"build new model for {session_name}")
        model = load_model_from_config(config, session_name)    

    model.fit(wg.train, validation_data=wg.val, **train_options)
    model.save(session["model_output_name"])
