import tensorflow as tf
from tensorflow.keras.layers import Input, Dropout, Dense, LSTM, TimeDistributed, RepeatVector
import numpy as np

class VanillaLSTM(tf.keras.Model):
    def __init__(self, label_width, hidden_dimension=32, out_features=1, drop_rate=0.1):
        super().__init__()

        self.label_width = label_width
        self.hidden_dimension = hidden_dimension
        self.out_features = out_features
        self.drop_rate = drop_rate
        
        self.out_features = out_features # out_features: 출력변수의 차원크기
        # Shape [batch, time, out_features] => [batch, 1(마지막), lstm_units]
        self.lstm_layer = tf.keras.layers.LSTM(units=hidden_dimension, return_sequences=False, return_state=False)
        # Shape [batch, 1, lstm_units] => [batch, 1 * lstm_units]
        self.flatten_layer = tf.keras.layers.Flatten()
        # Shape [batch, 1*lstm_units] => [batch, label_width * out_features // 2]
        self.dense_layer1 = tf.keras.layers.Dense(units=label_width * out_features * 4, activation='relu', kernel_initializer=tf.initializers.zeros)
        # Shape Same
        self.dropout_layer = tf.keras.layers.Dropout(drop_rate)
        # Shape [batch, label_width * out_features // 2] => [batch, label_width * out_features]
        self.dense_layer2 = tf.keras.layers.Dense(units=label_width * out_features, kernel_initializer=tf.initializers.zeros)
        # Shape [batch, label_width * out_features] => [batch, label_width, out_features]
        self.reshape_layer = tf.keras.layers.Reshape([label_width, out_features])

    def call(self, inputs):
        result = self.lstm_layer(inputs)
        result = self.flatten_layer(result)
        #result = self.dense_layer1(result)
        #result = self.dropout_layer(result)
        result = self.dense_layer2(result)
        result = self.reshape_layer(result)
        return result

    def get_config(self):
        config = super().get_config().copy()
        config.update({
            'label_width': self.label_width,
            'hidden_dimension': self.hidden_dimension,
            'out_features': self.out_features,
            'drop_rate': self.drop_rate
        })
        return config

class VanillaCNN(tf.keras.Model):
    def __init__(self, label_width, num_filters=16, conv_width=4, out_features=1, strides=2, padding='valid', drop_rate=0.4):
        super().__init__()
        # Shape [batch, time, out_features] => [batch, output_size, num_filters]
        # ---> output_size = (time - (2 * padding) - conv_width) / strides + 1
        # ---> (현재) padding = 0 (valid)
        # ---> (현재) strides = 2
        self.conv1d_layer = tf.keras.layers.Conv1D(
            filters=num_filters,
            kernel_size=conv_width,
            padding=padding, # "valid" means no padding.
            strides=strides,
            )
        # Shape Same
        self.dropout_layer = tf.keras.layers.Dropout(drop_rate)
        # Shape [batch, output_size, num_filters] => [batch, output_size * num_filters]
        self.flatten_layer = tf.keras.layers.Flatten()
        # Shape [batch, output_size * num_filters] => [batch, label_width * out_features]
        self.dense_layer = tf.keras.layers.Dense(units=label_width * out_features, kernel_initializer=tf.initializers.zeros)
        # Shape [batch, label_width * out_features] => [batch, label_width, out_features]
        self.reshape_layer = tf.keras.layers.Reshape([label_width, out_features])

    def call(self, inputs):
        result = self.conv1d_layer(inputs)
        result = self.dropout_layer(result)
        result = self.flatten_layer(result)
        result = self.dense_layer(result)
        result = self.reshape_layer(result)
        return result

class VanillaCNN(tf.keras.Model):
    def __init__(self, label_width, num_filters=16, conv_width=4, out_features=1, strides=2, padding='valid', drop_rate=0.4):
        super().__init__()
        # Shape [batch, time, out_features] => [batch, output_size, num_filters]
        # ---> output_size = (time - (2 * padding) - conv_width) / strides + 1
        # ---> (현재) padding = 0 (valid)
        # ---> (현재) strides = 2
        self.conv1d_layer = tf.keras.layers.Conv1D(
            filters=num_filters,
            kernel_size=conv_width,
            padding=padding, # "valid" means no padding.
            strides=strides,
            )
        # Shape Same
        self.dropout_layer = tf.keras.layers.Dropout(drop_rate)
        # Shape [batch, output_size, num_filters] => [batch, output_size * num_filters]
        self.flatten_layer = tf.keras.layers.Flatten()
        # Shape [batch, output_size * num_filters] => [batch, label_width * out_features]
        self.dense_layer = tf.keras.layers.Dense(units=label_width * out_features, kernel_initializer=tf.initializers.zeros)
        # Shape [batch, label_width * out_features] => [batch, label_width, out_features]
        self.reshape_layer = tf.keras.layers.Reshape([label_width, out_features])

    def call(self, inputs):
        result = self.conv1d_layer(inputs)
        result = self.dropout_layer(result)
        result = self.flatten_layer(result)
        result = self.dense_layer(result)
        result = self.reshape_layer(result)
        return result


class LSTMAutoEncoder(tf.keras.Model):

    def __init__(self, n_features, n_output_features, timesteps):
        super().__init__()

        self.n_output_features = n_output_features

        self.lstm_layer0 = LSTM(64, activation="relu", return_sequences=True, 
                                input_shape=(timesteps, n_features))

        self.lstm_layer1 = LSTM(32, activation="relu", return_sequences=False)
        self.repeat_vector_layer = RepeatVector(self.n_output_features)
        self.lstm_layer2 = LSTM(32, activation="relu", return_sequences=True)
        self.lstm_layer3 = LSTM(64, activation="relu", return_sequences=True)

        self.time_distributed_layer = TimeDistributed(Dense(1))
        self.reshape_layer = tf.keras.layers.Reshape((self.n_output_features,))
    
    def call(self, inputs):
        f = self.lstm_layer0(inputs)
        f = self.lstm_layer1(f)
        f = self.repeat_vector_layer(f)
        f = self.lstm_layer2(f)
        f = self.lstm_layer3(f)
        f = self.time_distributed_layer(f)
        return self.reshape_layer(f)


class BaseLine(tf.keras.Model):
    def __init__(self, input_width, shift, label_width, labels_index=0):
        super().__init__()
        self.input_width = input_width
        self.shift = shift
        self.label_width = label_width
        self.labels_index = labels_index # label_col_index와 다름. dataset에서 이미 labels의 dim은 1차원으로 해놨기 때문. 항상 0.
        
    def call(self, inputs):
        labels_slice = slice(self.labels_index, self.labels_index+1)
        ref_start_idx = self.shift # 여기서부터 참조
        # 만약에 shift가 있어서 input의 중간지점부터 참조한다면, 앞부분은 뒤에 붙어야함.(concat)
        prefix = inputs[:, slice(ref_start_idx,None), labels_slice]
        suffix = inputs[:, slice(0,ref_start_idx), labels_slice]
        result = tf.concat([prefix, suffix], axis=1) # (None, (input_width), 1)
        result = result[:, :self.label_width, :] # (None, (label_width), 1)
        result.set_shape([None, self.label_width, None]) # (None, (label_width), 1)
        return result

class CustomLoss(tf.keras.losses.Loss):

    def __init__(self, name="nle_loss"):
        super().__init__(name=name)
    
    def call(self, y_true, y_pred):
        print(y_true, y_pred)
        return np.sum((y_true - y_pred) ** 2)