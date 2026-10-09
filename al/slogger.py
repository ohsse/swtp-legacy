import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

class CustomFormatter(logging.Formatter):
    def __init__(self, site, step, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        self.site = site
        self.step = step

    def format(self, record):
        record.site = self.site
        record.step = self.step
        record.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return super().format(record)

def get_logger(appName, fileName, site='GS'):
    step='EMS_AL'
    logger = logging.getLogger(appName)
    logger.setLevel(logging.INFO)  # 최소 로그 레벨을 INFO로 설정

    log_dir = '/home/log'
    # log_dir = './log'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, fileName)

    if fileName=='ems_al.log':
        formatter = CustomFormatter(
            site=site,
            step=step,
            fmt=f'{{"time": "%(time)s", "site": "%(site)s", "step": "%(step)s", "level": "%(levelname)s", "message": %(message)s}}'
        )
    else:
        formatter = CustomFormatter(
            site=site,
            step=step,
            fmt=f'%(message)s'
        )
    
   # 파일 핸들러 설정
    file_handler = TimedRotatingFileHandler(log_file, when='D', interval=7, backupCount=4)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러 설정
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
