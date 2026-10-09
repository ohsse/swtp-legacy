import tensorflow as tf
from dataset import WindowGenerator, load_dataset_split, load_dataset_rdb_split
from matplotlib import pyplot
import pandas as pd
import json
import argparse
from cutils import _import
import joblib
import numpy as np
from op import psqr 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')
    parser.add_argument('--start_date')
    parser.add_argument('--ref_days',default=10)
    parser.add_argument('--source_type', default='file')
    parser.add_argument('--feeder', default=None)

    args = parser.parse_args()

    with open("defmodel.json") as f :
        config = json.load(f)

    session = config[args.session]
    scaler_path = session["scaler_output_name"]
    label_col = session["dataset"]["label_col"]

    if args.source_type == 'file':
        validation_file = session["validation_file"]
        tr, vd, tt = load_dataset_split(validation_file, label_col=label_col, start_date=args.start_date, days=int(args.ref_days), scaler_name=scaler_path, prep=True) #Temp

    elif args.source_type == 'rdb' :
        start_date = pd.Timestamp(args.start_date)
        end_date = (pd.Timestamp(start_date) + pd.Timedelta(days=int(args.ref_days)))

        tr, vd, tt = load_dataset_rdb_split(session['feeder'], start_date, end_date, label_col)

    window_generator_options = session["window_generator"]
    window_generator_options['slide_min'] = 60

    wclass = window_generator_options["_class"]
    wclass = _import(f"dataset.{wclass}")
    del window_generator_options["_class"]

    print(f'load scaler: {scaler_path}')
    scaler = joblib.load(scaler_path)
    
    w = wclass(train_df=tr, val_df=vd, test_df=tt, **window_generator_options)
    #inputs, outputs = w.slice_data(tr)

    model = tf.keras.models.load_model(session["model_output_name"])

    predictions_raw = []
    real = []

    input_data = w.train

    s, m = scaler.scale_[0], scaler.mean_[0]

    print('scale: ', s, m)

    def time2vec(ts):
        d = ts.dayofyear
        w = ts.weekday
        h = ts.hour
        m = ts.minute

        day_minute = h*60 + m 

        s = np.sin((day_minute * 2 * np.pi) / 1440)
        c = np.cos((day_minute * 2 * np.pi) / 1440)

        return (s, c)

    for e in input_data.as_numpy_iterator():
        intput, output = e
        output = output * scaler.scale_[0] + scaler.mean_[0]

        output = output.tolist()
        
        real.extend(output)

    predictions = model.predict(input_data)
    predictions = predictions.reshape((-1, 1)) #TODO

    def _f(r, p, i) :
        #y = list( x[i] for x in r)
        y = list( x for x in r)
        p = p * scaler.scale_[0] + scaler.mean_[0]
        p = p.tolist()
        _p = list(x[i] for x in p)

        if "adj_callbacks" in session: 
            for _call in session["adj_callbacks"] : 
                _p = list(eval(_call) for p in _p)

        return (y, _p)

    print(predictions.shape) 
    _res = list( _f(real, predictions, i) for i in range(0, 1)) # TODO
    
    def _v(res):
        y, p = res
        p = np.array(p)

        print(len(y))
        print(len(p))

        pyplot.plot(y, label="real")
        #pyplot.plot( cwf + p + swf, label="composed")
        pyplot.plot( p, label="predict")
        #pyplot.plot( swf , label="sin")
        #pyplot.plot( cwf, label="cos")
        
        pyplot.legend()
    
    _v(_res[0])
    pyplot.savefig(f'plotresult15min/{args.session}')
    pyplot.show() 
