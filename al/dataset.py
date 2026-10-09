# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import tensorflow as tf
#import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from tlogger import get_logger
import joblib
from functools import reduce
import argparse
import json
from cutils import _import
import pymysql
from preprocessing import time2vec
from preprocessing import preprocessing

_logger = get_logger("dataset")

class DataSets:

    def __init__(self, raw_df, label_col):
        self.raw = raw_df
        self.tdf = None

        self._y_scale = None
        self._y_mean = None
        self.label_col = label_col

    def seektime(self, time, timedelta):
        start = pd.Timestamp(time)
        _logger.info(f"slice time from {start} to {start+timedelta}")
        print(self.raw)
        self.tdf = self.raw.loc[start: start+timedelta - pd.Timedelta(minutes=1)]
    
    def _scale(self, scaler, df):
        columns_to_scale = list(x for x in df.columns if x[:2] != "T2")
        columns_not_to_scale = list(x for x in df.columns if x[:2] == "T2")

        scaler.fit(df[columns_to_scale])
        
        tdf_1 = pd.DataFrame(scaler.transform(df[columns_to_scale]), index=df.index, columns=columns_to_scale)
        tdf_2 = df[columns_not_to_scale]

        return pd.concat([tdf_1, tdf_2], axis=1)

    def scale(self, scaler_save_path, make_new_scaler=False):
        if make_new_scaler:
            print('make new scaler!')
            scaler = StandardScaler()
        else:
            print('load scaler!')
            scaler = joblib.load(scaler_save_path)

        train_df, _, _ = self.split_data(self.tdf, train_rate=1)

        columns_to_scale = list(x for x in self.tdf.columns if x[:2] != "T2")
        columns_not_to_scale = list(x for x in self.tdf.columns if x[:2] == "T2")

        if make_new_scaler:
            train_df[columns_to_scale] = scaler.fit_transform(train_df[columns_to_scale])
        else:
            train_df[columns_to_scale] = scaler.transform(train_df[columns_to_scale])

        self.tdf_1 = pd.DataFrame(self.tdf[columns_to_scale], index=self.tdf.index, columns=columns_to_scale)
        self.tdf_2 = self.tdf[columns_not_to_scale]

        self.tdf = pd.concat([self.tdf_1, self.tdf_2], axis=1)

        if scaler_save_path is not None and make_new_scaler:
            joblib.dump(scaler, scaler_save_path)

        return self.tdf
    
    def filter_1st_column(self, df):
        # 이상치 제거
        q1 = df.iloc[:, 0].quantile(0.25)
        q3 = df.iloc[:, 0].quantile(0.75)
        rev_range = 5
        iqr = q3 - q1

        _max = q3 + (rev_range * iqr)
        _min = q1 - (rev_range * iqr)
        _min = max(_min, 10)

        _df = df[ (df.iloc[:, 0] < _max) & (df.iloc[:, 0] > _min)]

        _df = _df.resample('1min').mean()
        return _df

    def preprocess(self, time, timedelta, scale=True, scaler_name="_scaler", make_new_scaler=False):
        self.raw.index = pd.to_datetime(self.raw.index)
        self.seektime(time, timedelta)

        self.tdf = self.tdf.fillna(0)
        self.tdf = self.filter_1st_column(self.tdf)

        c = [self.label_col] + list(x for x in self.tdf.columns if x != self.label_col)

        self.tdf = self.tdf[c]

        if scale:
            self.scale(scaler_save_path=scaler_name, make_new_scaler=make_new_scaler)
            
        return self.tdf
    
    def split_data(self, df, train_rate=0.85):
        start_date, end_date = df.index[0], df.index[-1]
        total_days = (end_date - start_date).days
        validation_days = int(total_days * 0.1)

        train_days = int((total_days-validation_days) * train_rate)
        test_days = total_days - train_days - validation_days
        print(start_date, start_date + pd.Timedelta(days=train_days, seconds=-1))
        print(start_date + pd.Timedelta(days=train_days, seconds=-1), start_date + pd.Timedelta(days=train_days+validation_days, seconds=-1))
        print(start_date + pd.Timedelta(days=train_days+validation_days), start_date + pd.Timedelta(days=train_days+validation_days+test_days, seconds=-1))

        if train_rate == 1:
            train_df = df
        else:
            train_df = df.loc[:start_date + pd.Timedelta(days=train_days, seconds=-1)]
        valid_df = df.loc[start_date + pd.Timedelta(days=train_days): start_date + pd.Timedelta(days=train_days+validation_days, seconds=-1)]
        test_df = df.loc[start_date + pd.Timedelta(days=train_days+validation_days): start_date + pd.Timedelta(days=train_days+validation_days+test_days, seconds=-1)]

        return train_df, valid_df, test_df

class WindowGeneratorV2():

    def __init__(
        self, 
        train_df, 
        val_df, 
        test_df,
        input_time_min_unit=1, 
        input_time_min_range=120, 
        output_time_min_unit=60, 
        output_min_time=60*3,
        shift_min=20,
        batch_size=32,
        slide_min=10,
        train_only=False,
    ):

        self.input_time_min_unit = input_time_min_unit
        self.input_time_min_range = input_time_min_range

        self.output_time_min_unit = output_time_min_unit
        self.output_min_time = output_min_time
        self.shift_min = shift_min
        self.batch_size = batch_size

        self.slide_min = slide_min

        self.output_timestep = int((output_min_time / output_time_min_unit) + 0.1)
        self.total_width = len(train_df.columns) + self.output_timestep

        self.trIndex = None
        self.train = self.make_dataset(train_df)

        if not train_only:
            self.val = self.make_dataset(val_df)
            self.test = self.make_dataset(test_df)

    def split_window(self, sequences):
        inputs = sequences[:, :-self.output_timestep, :]
        outputs = sequences[:, -self.output_timestep: , :]

        return inputs, outputs

    def make_dataset(self, df, train_only=False):
        inputs, outputs = self.slice_data(df)
        return tf.data.Dataset.from_tensor_slices((inputs, outputs))
    
    def rolling(self, df, start_time, interval):
        res = []
        t = start_time
        while True:
            _df = df.loc[t: t + interval - pd.Timedelta(seconds=1)]
            if _df.index.size == 0: break

            e = _df.mean()
            res.append(e)
            t += interval

        return reduce(lambda a, b: pd.concat(a, b, axis=0), res)

    def slice_data(self, df):
        input_df = df.copy()
        input_df.index = pd.to_datetime(input_df.index) 
        input_df = input_df.fillna(method='ffill')

        input_df = input_df.resample(
            str(self.input_time_min_unit) + "min"
        ).mean()

        output_df = df.copy().fillna(method='ffill')

        ts = input_df.index.values[0]

        inputs = []
        outputs = []

        while True:
            input_end_ts = ts + pd.Timedelta(minutes=self.input_time_min_range) 

            output_start_ts = input_end_ts + pd.Timedelta(minutes=self.shift_min)
            output_end_ts = output_start_ts + pd.Timedelta(minutes=self.output_min_time) - pd.Timedelta(seconds=1)
            
            sliced_input = input_df.loc[ts: input_end_ts - pd.Timedelta(seconds=1)]
            #print('i', sliced_input.index[0], sliced_input.index[-1])

            #print(sliced_input.index.values[0])
            sliced_input = sliced_input.values

            if np.isnan(sliced_input).any():
                ts += pd.Timedelta(minutes=self.slide_min)
                print('continue1')
                continue

            #print(ts, input_df.index[-1] - pd.Timedelta(days=1))
            if ts > input_df.index[-1]: # - pd.Timedelta(days=1):
                print('break 0!', sliced_input.shape, self.input_time_min_range / self.input_time_min_unit)
                print('break 0!', ts, input_df.index[-1])
                break

            if sliced_input.shape[0] != int(self.input_time_min_range / self.input_time_min_unit): # TODO
                print('break 1!', sliced_input.shape, self.input_time_min_range / self.input_time_min_unit)
                ts += pd.Timedelta(minutes=self.slide_min)
                continue

            #if sliced_input.max() > _max or sliced_input.min() < _min: ts += pd.Timedelta(minutes=self.slide_min) continue
            # label은 항상 0으로 고정
            #if output_end_ts >= last_ts: break

            sliced_output = output_df.iloc[:, 0] \
                    .loc[output_start_ts: output_end_ts]
            #print('o', sliced_output.index[0], sliced_output.index[-1])

            if output_end_ts > input_df.index[-1]: 
                print(output_end_ts, output_df.index[-1])
                print('break 3')
                break
            
            if np.isnan(sliced_output.values).any():
                ts += pd.Timedelta(minutes=self.slide_min)
                print('continue 4')
                continue

            if sliced_output.index.size < int(self.output_min_time / self.output_time_min_unit) : 
                ts += pd.Timedelta(minutes=self.slide_min)
                print('continue 5')
                continue

            #if sliced_input.max() > _max or sliced_input.min() < _min: ts += pd.Timedelta(minutes=self.slide_min) continue
            #sliced_output = sliced_output.resample(f'{self.output_time_min_unit}min').mean() 

            steps = int(self.output_min_time / self.output_time_min_unit + 0.00001)
            _outputs = []

            for s in range(steps):
                offset_1 = pd.Timedelta(minutes=s * self.output_time_min_unit)
                offset_2 = pd.Timedelta(minutes=(s+1) * self.output_time_min_unit)
                _s = output_start_ts + offset_1
                _e = output_start_ts + offset_2

                _sliced_output = output_df.iloc[:, 0] \
                    .loc[_s: _e]
                #print(_sliced_output)
                _sliced_output = _sliced_output.mean()
                #print(_sliced_output)

                _outputs.append(_sliced_output)

            if len(_outputs) != steps: 
                ts += pd.Timedelta(minutes=self.slide_min) 
                print('continue1')
                continue

            sliced_output = np.array(_outputs)

            if np.isnan(sliced_output).any() : 
                ts += pd.Timedelta(minutes=self.slide_min) 
                print('continue1')
                continue

            #if sliced_output.max() > _max or sliced_output.min() < _min: ts += pd.Timedelta(minutes=self.slide_min) #print('filtered', sliced_output) continue
            #TEMP!
            inputs.append(sliced_input)
            outputs.append(sliced_output)
            ts += pd.Timedelta(minutes=self.slide_min)

        #for i in inputs: print(i.shape) 
        inputs = np.stack(inputs) # TODO

        batch_size = min(self.batch_size, len(inputs))
        batched_indices = int((len(inputs) / batch_size) + 0.001)

        inputs = inputs[:batched_indices*batch_size]

        inputs = inputs.reshape(
            [
                batched_indices,
                batch_size,
                *inputs.shape[1:]
        ])

        outputs = np.stack(outputs) #TODO
        outputs = outputs[:batched_indices*batch_size]
        
        outputs = outputs.reshape(
            [
                batched_indices,
                batch_size,
                *outputs.shape[1:]
        ])

        assert inputs.shape[0] == outputs.shape[0]

        _logger.info(f"input shape: {inputs.shape}")
        _logger.info(f"output shape: {outputs.shape}")

        return (inputs, outputs)

    def slice_data2(self, df):
        input_df = df.copy()
        input_df.index = pd.to_datetime(input_df.index) 

        input_df.resample(
            str(self.input_time_min_unit) + "min"
        ).mean()

        ts = input_df.index.values[0]

        inputs = []
        outputs = []
        last_ts = input_df.index[-1]
        
        input_df = input_df.resample('1min').mean()
        # 이상치 제거
        q1 = input_df.iloc[:, 0].quantile(0.25)
        q3 = input_df.iloc[:, 0].quantile(0.75)
        rev_range = 3
        iqr = q3 - q1

        _max = q3 + (rev_range * iqr)
        _min = q1 - (rev_range * iqr)

        while True:
            input_end_ts = ts + pd.Timedelta(minutes=self.input_time_min_range) 

            output_start_ts = input_end_ts + pd.Timedelta(minutes=self.shift_min)
            output_end_ts = output_start_ts + pd.Timedelta(minutes=self.output_min_time) - pd.Timedelta(seconds=1)
            
            sliced_input = input_df.loc[ts: input_end_ts - pd.Timedelta(seconds=1)]
            sliced_input = sliced_input.values

            if sliced_input.shape[0] != self.input_time_min_range: # TODO
                ts += pd.Timedelta(minutes=self.slide_min)
                continue

            # label은 항상 0으로 고정
            sliced_output = input_df.iloc[:, 0] \
                .loc[output_start_ts: output_end_ts] 

            #if output_end_ts >= last_ts: break
            print('time: ')
            print(ts, input_end_ts)
            print(output_start_ts, output_end_ts)

            if sliced_output.index.size < int(self.output_min_time / self.output_time_min_unit) : break 
            #sliced_output = sliced_output.resample(f'{self.output_time_min_unit}min').mean() 

            steps = int(self.output_min_time / self.output_time_min_unit + 0.00001)
            sliced_output = np.array([sliced_output.mean()])

            if np.isnan(sliced_output[0]) : 
                ts += pd.Timedelta(minutes=self.slide_min) 
                continue

            if sliced_output.max() > _max or sliced_output.min() < _min: 
                ts += pd.Timedelta(minutes=self.slide_min) 
                continue

            inputs.append(sliced_input)
            outputs.append(sliced_output)

            ts += pd.Timedelta(minutes=self.slide_min)

        #for i in inputs: print(i.shape) 
        inputs = np.stack(inputs) # TODO

        batch_size = min(self.batch_size, len(inputs))
        batched_indices = int((len(inputs) / batch_size) + 0.001)

        inputs = inputs[:batched_indices*batch_size]

        inputs = inputs.reshape(
            [
                batched_indices,
                batch_size,
                *inputs.shape[1:]
        ])

        outputs = np.stack(outputs) #TODO
        outputs = outputs[:batched_indices*batch_size]
        
        outputs = outputs.reshape(
            [
                batched_indices,
                batch_size,
                *outputs.shape[1:]
        ])

        assert inputs.shape[0] == outputs.shape[0]

        _logger.info(f"input shape: {inputs.shape}")
        _logger.info(f"output shape: {outputs.shape}")
        print(outputs[0][0])

        return (inputs, outputs)
    

class WindowGenerator():
    def __init__(self, input_width:int, label_width:int,
                 train_df:pd.DataFrame, valid_df:pd.DataFrame, test_df:pd.DataFrame,
                 shift=0, label_col_index=0, verbose=1):
        self.label_col_index = label_col_index
        
        self.train_df = train_df
        self.valid_df = valid_df
        self.test_df = test_df
        
        self.input_width = input_width # window_size
        self.label_width = label_width # step_size
        self.shift = shift
        
        self.total_input_width = input_width + shift
        self.total_width = input_width + shift + label_width

        self.input_slice = slice(0, input_width)
        self.input_indices = np.arange(self.total_input_width)[self.input_slice]

        self.label_start = self.total_input_width
        self.label_slice = slice(self.label_start, None)
        self.label_indices = np.arange(self.total_width)[self.label_slice]

        self.train = self.make_dataset(self.train_df, shuffle_=True)
        self.val = self.make_dataset(self.valid_df, shuffle_=False)
        self.test = self.make_dataset(self.test_df, shuffle_=False)

        self.train_times = self.train_df.iloc[self.total_input_width:-(self.label_width-1)].index # current_time point
        self.val_times = self.valid_df.iloc[self.total_input_width:-(self.label_width-1)].index # current_time point
        self.test_times = self.test_df.iloc[self.total_input_width:-(self.label_width-1)].index # current_time point

        self.verbose = verbose

    def split_window(self, sequence):
        inputs = sequence[:,self.input_slice,:]  # inputs.shape: (batch, window_size, num_features)
        # label_col은 항상 0으로 고정시켰음!!
        labels = sequence[:,self.label_slice,0:1] # labels.shape: (batch, step_size, 1)
        # labels = sequence[:,self.label_slice,self.label_col_index:(self.label_col_index+1)] # labels.shape: (batch, step_size, 1)

        # Slicing doesn't preserve static shape information, so set the shapes
        # manually. This way the `tf.data.Datasets` are easier to inspect.
        inputs.set_shape([None, self.input_width, None])
        labels.set_shape([None, self.label_width, None])
        return inputs, labels

    def make_dataset(self, df, shuffle_=False):
        ds = tf.keras.preprocessing.timeseries_dataset_from_array(
            data=df,
            targets=None,
            sequence_length=self.total_width,
            shuffle=shuffle_,
            batch_size=16,
        )
        ds = ds.map(self.split_window) # (None, [(batch, window_size, num_features), (batch, step_size)])
        return ds

    def sample(self, df=None, n=4, numpy_seed=None):
        if numpy_seed is not None:
            np.random.seed(numpy_seed)
        if df is None:
            df = self.test_df
            times = self.test_times
        else:
            times = df.iloc[self.total_input_width:-(self.label_width-1)].index # current_time point

        print(times)
        times_idxs = list(np.random.choice(len(times), min(n,len(times)), replace=False))
        
        example_window = tf.stack([np.array(df[t:t+self.total_width]) for t in times_idxs])
        example_times = df.index.astype(str).values[times_idxs]
        example_inputs, example_labels = self.split_window(example_window)
        
        if self.verbose>0:
            print('All shapes are: (batch, time, features)')
            # print(f'* Window shape: {example_window.shape}')
            # print(f'* [Inputs shape]: {example_inputs.shape}') # ex. <class 'tensorflow.python.framework.ops.EagerTensor'> (32, 96, 2)
            # print(f'* [labels shape]: {example_labels.shape}') # ex. <class 'tensorflow.python.framework.ops.EagerTensor'> (32, 96, 1)
            # print(f'* example_times: {example_times}')

        return example_inputs, example_labels, example_times

    def __repr__(self):

        return '\n'.join([
            f'[1] Total width (per Sequence): {self.total_width}',
            f'* Input indices: {self.input_indices}',
            f'* Shift: {self.shift}',
            f'* Label indices: {self.label_indices}',
            f'[2] Label column Index: {self.label_col_index}'])

def ds_shape(dataset):
    dataset_to_numpy = list(dataset.as_numpy_iterator())
    return tf.shape(dataset_to_numpy)

def select_data_from_rdb_sc(conn, table, columns, ts_from, ts_to):
    inc_tags = reduce(lambda x, y: x + ', ' + "'" + y + "'", columns, '')[1:]

    sql = f"select ts, tagname, value from {table} where tagname in ({inc_tags}) and ts >= '{ts_from.strftime('%Y-%m-%d %H:%M:%S')}' and ts < '{ts_to.strftime('%Y-%m-%d %H:%M:%S')}'"
    print(sql)

    from pymysql.cursors import DictCursor
    cursor = conn.cursor(DictCursor)
    cursor.execute(sql)
    data = cursor.fetchall()
    conn.close()
    return data

def select_data_from_rdb(conn, table, tags, ts_from, ts_to):
    inc_tags = reduce(lambda x, y: x + ', ' + "'" + y + "'", tags, '')[1:]

    sql = f"select ts, tagname, value from {table} where tagname in ({inc_tags}) and ts >= '{ts_from.strftime('%Y-%m-%d %H:%M:%S')}' and ts < '{ts_to.strftime('%Y-%m-%d %H:%M:%S')}'"
    print(sql)

    from pymysql.cursors import DictCursor
    cursor = conn.cursor(DictCursor)
    cursor.execute(sql)
    data = cursor.fetchall()
    conn.close()
    return data

def select_data_from_rdb_with_tags(conn, total_tags, ts_from, ts_to, table='ems_data.rawdata'):
    inc_tags = reduce(lambda x, y: x + ', ' + "'" + y + "'", total_tags, '')[1:]

    sql = f"select ts, tagname, value from {table} where tagname in ({inc_tags}) and ts >= '{ts_from.strftime('%Y-%m-%d %H:%M:%S')}' and ts < '{ts_to.strftime('%Y-%m-%d %H:%M:%S')}'"
    print(sql)

    from pymysql.cursors import DictCursor
    cursor = conn.cursor(DictCursor)
    cursor.execute(sql)
    data = cursor.fetchall()
    conn.close()
    return data

def load_dataset_rdb_1c(session, label_col, ts_from, ts_to, output_file=None, scaler_name=None):
    with open('datafeeder.json') as f:
        feeder = json.load(f)[session]

    connection = feeder["connection"]

    with open('connections.json') as f:
        db = json.load(f)[connection]

    conn = pymysql.connect(**db)

    data = select_data_from_rdb_sc(conn, table=feeder["table"], columns=[label_col], ts_from=ts_from, ts_to=ts_to)

    df = pd.DataFrame(data)
    df = df.pivot(index='ts', columns='tagname')['value']
    df = df.resample('1min').mean()

    df.index = pd.to_datetime(df.index)
    df = time2vec(df)
    print(df)

    if output_file:
        df.to_csv(f'{output_file}.csv')    

    ds = DataSets(df, label_col) #TODO
    d = ts_to - ts_from
    return ds.preprocess(ts_from, d, scaler_name=scaler_name)


def load_dataset_rdb(connection_key, ts_from, ts_to, output_file=None, scaler_name=None):
    with open('connections.json') as f:
        db = json.load(f)[connection]
    conn = pymysql.connect(**db)

    data = select_data_from_rdb(conn, feeder, ts_from, ts_to)

    df = pd.DataFrame(data)
    df = df.pivot(index='ts', columns='tagname')['value']
    df = df.resample('1min').mean()

    df = df[feeder['tags']]
    df.index = pd.to_datetime(df.index)
    df = time2vec(df)
    print(df)

    if output_file:
        df.to_csv(f'{output_file}.csv')    

    ds = DataSets(df, '701-367-FRI-2004') #TODO
    d = ts_to - ts_from
    return ds.preprocess(ts_from, d, scaler_name=scaler_name)

def load_dataset_rdb_split(connection_key, table, tags, ts_from, ts_to, label_col, output_file=None, scaler_name=None, make_new_scaler=False):
    with open('connections.json') as f:
        db = json.load(f)[connection_key]

    conn = pymysql.connect(**db)

    data = select_data_from_rdb(conn, table, tags, ts_from, ts_to)

    df = pd.DataFrame(data)
    df = df.pivot(index='ts', columns='tagname')['value']
    df = df.resample('1min').mean()

    df = df[tags]
    df.index = pd.to_datetime(df.index)
    df = time2vec(df)

    ds = DataSets(df, label_col) #TODO
    d = ts_to - ts_from
    df = ds.preprocess(ts_from, d, scaler_name=scaler_name, make_new_scaler=make_new_scaler)
    return ds.split_data(df)

def load_dataset(dataset_path, start_date, label_col, days=10, scale=True, scaler_name=None, prep=False, columns=None):
    df = pd.read_csv(dataset_path, index_col=0, header=None)

    df.rename(columns={ df.columns[0]: label_col }, inplace = True) # Temporary

    if columns:
        df.columns = columns

    if prep:
        df = preprocessing(df, label_col)
        

    df = df.resample('1min').mean()
    ds = DataSets(df, label_col)
    return ds.preprocess(start_date, pd.Timedelta(days=days), scaler_name=scaler_name, scale=scale)

def load_dataset_split(dataset_path, start_date, label_col, days=10, scaler_name=None, prep=None, nosplit=False):
    df = load_dataset(dataset_path, start_date, label_col=label_col, days=days, scaler_name=scaler_name, prep=prep)

    if nosplit:
        return df

    ds = DataSets(df, label_col)
    tr, vd, tt = ds.split_data(df)

    return tr, vd, tt

if __name__ == "__main__":
    #load_dataset_rdb('fri_gs', '2020-01-01 00:00:00', '2020-01-01 02:00:00')
    load_dataset_rdb('fri_gs', pd.Timestamp('2020-01-01 00:00:00'), pd.Timestamp('2021-01-01 00:00:00'), output_file='gs_input_fri2004.csv')

    logger = get_logger("train_model")

    parser = argparse.ArgumentParser(prog='train_model')
    parser.add_argument('--session')
    parser.add_argument('--retrain', default=False)

    with open("defmodel.json") as f:
        config = json.load(f)

    args = parser.parse_args()
    session_name = args.session
    session = config[session_name]
    logger.info(f"session: {session}")
    scaler_output_path = session["scaler_output_name"]
    train_options = session["train_options"]
    ref_days = session["dataset"]["ref_days"]
    label_col = session["dataset"]["label_col"]

    (
        tr, 
        vd, 
        tt
    ) = load_dataset(
            session["input_file"], 
            label_col=label_col,
            days=int(ref_days), 
            start_date=session["dataset"]["start_date"],
            scaler_name=scaler_output_path
        )
    print(tr)

    wg_options = session["window_generator"]
    wclass = wg_options["_class"]
    wclass = _import(f"dataset.{wclass}")

    del wg_options["_class"]
    print(wg_options)
    wg = wclass(train_df=tr, val_df=vd, test_df=tt, **wg_options)
