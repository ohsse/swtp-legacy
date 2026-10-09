from flask import Flask, request, has_request_context
import logging.handlers
import logging.config
import json
from core.OnlineRun import OnlineRun
from core.OnlineGaRun import OnlineGaRun
from core.OnlineInterpolationRun import OnlineInterpolationRun
from core.OnlineLowFlowRun import OnlineLowFlowRun
from core.OnlineWqualChlorineRun import OnlineWqualChlorineRun
from core.OnlineCaseSimulationRun import OnlineCaseSimulationRun

logging.config.dictConfig(json.load(open('./config_logger/config.json')))


# class NewFormatter(logging.Formatter):
#     def format(self, record):
#         if has_request_context():
#             record.url = request.url
#             record.remote = request.remote_addr
#         else:
#             record.url = None
#             record.remote = None
#         return super().format(record)
#
#
# logFormatter = NewFormatter("[%(asctime)s] %(url) - %(remote)s %(module)s:%(levelname)s:%(message)s", datefmt="%Y-%m-%d %H:%M:%S")

logger = logging.getLogger(__name__)


app = Flask(__name__)


@app.before_request
def before_request():
    app.logger.info(f'request from: {request.url} {request.remote_addr}')
    # logger.debug('요청 들어올 때 마다 로깅1')


@app.after_request
def after_request(response):
    app.logger.info('로깅 요청 끝나면')
    return response


@app.route('/')
def index():
    # app.logger.info('instance successfully loaded')
    msg = "welcome wntr4wn!!!"

    return msg


@app.route('/onlineRun')
def onlineRun():
    msg = "success"

    inpNumber = request.args.get('inpNumber', '')

    if inpNumber == '':
        app.logger.error('inpNumber 지정되지 않음')
        msg = 'fail'
    else:
        try:
            # 온라인 관망해석(수리해석)
            onlineRun = OnlineRun()
            onlineRun.proc(inpNumber)
        except Exception as ex:
            # print("[ERROR] app: ", ex)
            app.logger.error(ex)
            msg = "fail"

    return msg


@app.route('/onlineGaRun')
def onlineGaRun():
    msg = "success"
    rptNumber = request.args.get('rptNumber', '')
    print('onlineGaRun-rptNumber: ' + rptNumber)
    app.logger.info('onlineGaRun-rptNumber: %s', rptNumber)

    try:
        # 온라인 유전자 알고리즘(수리해석)
        onlineGaRun = OnlineGaRun()
        onlineGaRun.proc(rptNumber)
    except Exception as ex:
        # print("[ERROR] app: ", ex)
        app.logger.error(ex)
        msg = "fail"

    return msg


@app.route('/interpolationRun')
def interpolationRun():
    msg = "success"

    # 분석순번
    analsNo = request.args.get('analsNo', '')
    # print('interpolationRun-analsNo: ' + analsNo)
    app.logger.info('interpolationRun-analsNo: %s', analsNo)

    try:
        # 안심확인제 보간법
        onlineInterpolationRun = OnlineInterpolationRun()
        onlineInterpolationRun.proc(analsNo)
    except Exception as ex:
        # print("[ERROR] app: ", ex)
        app.logger.error(ex)
        msg = "fail"

    return msg


@app.route('/onlineLowFlowRun')
def onlineLowFlowRun():
    msg = "success"
    analsNo = request.args.get('analsNo', '')
    if analsNo == '':
        app.logger.error('analsNo 지정되지 않음')
        msg = 'fail'
    else:
        app.logger.info('onlineLowFlowRun-analsNo: ' + analsNo)

        try:
            # 온라인 관망해석(수리해석-저유속)
            onlineLowFlowRun = OnlineLowFlowRun()
            onlineLowFlowRun.proc(analsNo)
        except Exception as ex:
            # print("[ERROR] app: ", ex)
            app.logger.error(ex)
            msg = "fail"

    return msg


@app.route('/onlineWqualChlorineRun')
def onlineWqualChlorineRun():
    msg = "success"
    rptNumber = request.args.get('rptNumber', '')
    # print('onlineWqualChlorineRun-rptNumber: ' + rptNumber)
    app.logger.info('onlineWqualChlorineRun-rptNumber: %s', rptNumber)

    try:
        # 온라인 관망해석(수질해석-잔류염소)
        onlineWqualChlorineRun = OnlineWqualChlorineRun()
        onlineWqualChlorineRun.proc(rptNumber)
    except Exception as ex:
        # print("[ERROR] app: ", ex)
        app.logger.error(ex)
        msg = "fail"

    return msg


@app.route('/onlineCaseSimulationRun')
def onlineCaseSimulationRun():
    msg = "success"
    analsNo = request.args.get('analsNo', '')
    # print('onlineCaseSimulationRun-analsNo: ' + analsNo)
    app.logger.info('onlineCaseSimulationRun-analsNo: %s', analsNo)

    try:
        # 사고모의 수질영향 유량분석
        onlineCaseSimulationRun = OnlineCaseSimulationRun()
        onlineCaseSimulationRun.proc(analsNo)
    except Exception as ex:
        # print("[ERROR] app: ", ex)
        app.logger.error(ex)
        msg = "fail"

    return msg
