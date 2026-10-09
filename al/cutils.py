import logging
import tensorflow as tf
import models

def get_logger(appName):
    logger = logging.getLogger(appName)

    # 로그의 출력 기준 설정
    logger.setLevel(logging.INFO)

    # log 출력 형식
    formatter = logging.Formatter('%(asctime)s [ %(name)s ] %(levelname)s : %(message)s')

    # log 출력
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

util_logger = get_logger("cutils")

def load_model_from_config(conf, session):
    session = conf[session]
    _loss = eval(session["loss"])

    model = session["model_name"]
    model_args = session["model_args"]

    util_logger.info(
        f"model args: {model_args}"
    )

    model = _import(model)(**model_args)
    model.compile(
        loss=_loss,
        #optimizer=tf.optimizers.RMSprop(learning_rate=1e-4),
        optimizer='adam',
        metrics=[tf.metrics.MeanAbsoluteError()],
        run_eagerly=True,
    )

    return model

def _import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
    