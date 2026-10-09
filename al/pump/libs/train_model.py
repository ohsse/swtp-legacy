import tensorflow as tf
import pandas as pd
from dataset import load_dataset_split, ds_shape
from keras.layers import LSTM
from keras.models import Sequential
from keras.layers import Dense
import keras.backend as K
from keras.callbacks import EarlyStopping
from dataset import WindowGenerator
import json
import argparse
from tlogger import get_logger
from cutils import _import, load_model_from_config

if __name__ == "__main__":
    logger = get_logger("train_model")

    parser = argparse.ArgumentParser(prog='train_model')
    parser.add_argument('--session')

    args = parser.parse_args()

    with open("defmodel.json") as f :
        config = json.load(f)
    session = config[args.session]

    model = load_model_from_config(config, args.session)
    ref_days = session["dataset"]["ref_days"]
    train_options = session["train_options"]

    logger.info(f"read input file {session['input_file']}")

    tr, tr_y, vd, tt = load_dataset_split(session["input_file"], days=int(ref_days), start_date=session["dataset"]["start_date"])
    window_generator = session["window_generator"]
    w = WindowGenerator(train_df=tr, valid_df=vd, test_df=tt, **window_generator)

    ds = w.make_dataset(tr)
    patience = 3
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=patience,
        mode='min')

    h = model.fit(w.train, verbose=0, validation_data=w.val, callbacks=[early_stopping], **train_options) 
    model.save(session["model_output_name"])
