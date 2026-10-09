from models import VanillaLSTM
import tensorflow as tf
from keras.utils.vis_utils import plot_model
from keras.models import Sequential

if __name__ == "__main__":
    model = Sequential()

    out_features = 1 # out_features: 출력변수의 차원크기
    # Shape [batch, time, out_features] => [batch, 1(마지막), lstm_units]
    lstm_layer = tf.keras.layers.LSTM(units=32, return_sequences=False, return_state=False)
    # Shape [batch, 1, lstm_units] => [batch, 1 * lstm_units]
    flatten_layer = tf.keras.layers.Flatten()
    # Shape [batch, 1*lstm_units] => [batch, label_width * out_features // 2]
    dense_layer1 = tf.keras.layers.Dense(units=1* out_features * 4, activation='relu', kernel_initializer=tf.initializers.zeros)
    # Shape Same
    dropout_layer = tf.keras.layers.Dropout(0.1)
    # Shape [batch, label_width * out_features // 2] => [batch, label_width * out_features]
    dense_layer2 = tf.keras.layers.Dense(units=1* out_features, kernel_initializer=tf.initializers.zeros)
    # Shape [batch, label_width * out_features] => [batch, label_width, out_features]
    reshape_layer = tf.keras.layers.Reshape([1, out_features])

    model.add(lstm_layer)
    model.add(flatten_layer)
    model.add(dense_layer1)
    model.add(dropout_layer)
    model.add(dense_layer2)
    model.add(reshape_layer)

    _loss = tf.keras.losses.MeanSquaredError()

    model.compile(
        loss=_loss,
        optimizer=tf.optimizers.RMSprop(learning_rate=1e-4),
        metrics=[tf.metrics.MeanAbsoluteError()],
        run_eagerly=True,
    )
    model.build(input_shape=(16,10,9))
    model.summary()
    plot_model(model, to_file='model.png', show_shapes=True, show_layer_names=True)