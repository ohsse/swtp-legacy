import logging
import json

# logger = logging

config = json.load(open('./config_logger/config.json'))

logging.config.dictConfig(config)

