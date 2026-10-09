import tensorflow as tf
from dataset import WindowGenerator, load_dataset, load_dataset_rdb_split
from matplotlib import pyplot
import pandas as pd
import json
import argparse
from cutils import _import
import joblib
import numpy as np

from sklearn.metrics import mean_absolute_error as _mae, mean_squared_error as _mse, r2_score as _r2s

import tensorflow.keras.backend as K

def _rmse(y_true, y_pred):
    msle = tf.keras.losses.MeanSquaredLogarithmicError()
    return K.sqrt(msle(y_true, y_pred)) 

from op import psqr 

def _predict(model, input_data, scaler, unscale=False):
    y = []
    s, m = scaler.scale_[0], scaler.mean_[0]

    predictions = model.predict(input_data)

    if unscale:
        predictions = predictions * s + m

    for e in input_data.as_numpy_iterator():
        _, output = e

        if unscale:
            output = output * s + m

        output = output.tolist()
        
        y.append(output)

    return predictions, np.array(y)

def unscale_df(df, label_col, scaler):
    df[[label_col]] = scaler.fit_transform(df[[label_col]])
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')
    parser.add_argument('--start_date')
    parser.add_argument('--ref_days',default=10)
    parser.add_argument('--source_type', default='file')
    parser.add_argument('--feeder', default=None)
    parser.add_argument('--mjson', default='defmodel.json')
    parser.add_argument('--plot', default='n')
    parser.add_argument('--matrix', default='n')
    parser.add_argument('--insert', default='n')
    parser.add_argument('--slide', default=None)

    args = parser.parse_args()

    with open(args.mjson) as f :
        config = json.load(f)

    session = config[args.session]
    scaler_path = session["scaler_output_name"]
    print(f'load scaler: {scaler_path}')
    scaler = joblib.load(scaler_path)
    s, m = scaler.scale_[0], scaler.mean_[0]
    
    label_col = session["dataset"]["label_col"]

    if args.source_type == 'file':
        validation_file = session["validation_file"]
        tr = load_dataset(validation_file, label_col=label_col, start_date=args.start_date, days=int(args.ref_days), scaler_name=scaler_path, prep=True)
        #tr[label_col] -= m 
        #tr[label_col] /= s

    elif args.source_type == 'rdb' :
        start_date = pd.Timestamp(args.start_date)
        end_date = (pd.Timestamp(start_date) + pd.Timedelta(days=int(args.ref_days)))

        tr, vd, tt = load_dataset_rdb_split(
            session["connection"],
            table=session["input_table"],
            tags=[session["dataset"]["label_col"]],
            ts_from=start_date, 
            ts_to=end_date, 
            scaler_name=session["scaler_output_name"], label_col=label_col)

    window_generator_options = session["window_generator"]
    if args.slide:
        window_generator_options['slide_min'] = int(args.slide)

    wclass = window_generator_options["_class"]
    wclass = _import(f"dataset.{wclass}")
    del window_generator_options["_class"]
    print(window_generator_options)
    w = wclass(train_df=tr, val_df=None, test_df=None, train_only=True, batch_size=1, **window_generator_options)
    #inputs, outputs = w.slice_data(tr)

    model = tf.keras.models.load_model(session["model_output_name"])
    out_features = session["model_args"]["out_features"]

    predictions_raw = []
    real = []

    input_data = w.train
    y_pred, y = _predict(model, input_data, scaler, unscale=False)

    y_pred = y_pred.reshape(-1, out_features)
    y = y.reshape(-1, out_features)

    if args.insert == 'y':
        ydf = pd.DataFrame(y_pred)

    if args.plot == 'y':
        __y = y * s + m
        __y_pred = y_pred  * s + m

        # for p, y in zip(__y_pred, __y): print(p[0], p[1]) print(y[0], y[1]) exit(0)

        if len(y_pred[0]) > 1:
            for idx in range(0, 6):
                _y = list(x[idx] for x in __y)
                _y_pred = list(x[idx] for x in __y_pred)

                pyplot.subplot(6,1,idx+1, label=f'after {idx} hour')
                pyplot.plot(_y, label='y')
                pyplot.plot(_y_pred, label='pred')

        else :
            pyplot.plot(__y, label='y')
            pyplot.plot(__y_pred, label='pred')

            #pyplot.plot(y, label='y')
            #pyplot.plot(y_pred, label='p')

        pyplot.savefig('plotv2/' + args.session)
        pyplot.legend()
        pyplot.show()

    if args.matrix == 'y':
        #y = y[:-1]
        #y_pred = y_pred[1:]

        mse_v = _mse(y, y_pred)
        mae_v = _mae(y, y_pred)

        r2s_v = _r2s(y, y_pred)
        rmse_v = _rmse(y, y_pred).numpy()

        print(mse_v, mae_v, r2s_v, rmse_v)

    #df.to_csv(f"result_{args.session}.csv")
    ### TEMP!

    exit(0)
    pyplot.figure(figsize=(3, 2))

    for i in range(1, 2):
        _r = list( x[i-1] *s +m for idx, x in enumerate(real) ) #if  idx % 24 == 0)
        _p = list( x[0][i-1]*s +m for idx, x in enumerate(y_pred) ) # if idx % 24 == 0)

        pyplot.subplot(6,1,i, label=f'after {i} hour')
        pyplot.plot(_p, label='p')
        pyplot.plot(_r, label='y')

    pyplot.legend()
    pyplot.savefig(f'plotresult/{args.session}_pr.png')
    pyplot.show()