FROM python:3.9.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# pip 업그레이드 후 설치(구버전 pip 의 의존성 해석/경고 문제 회피)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt
COPY . .
ENV TZ=Asia/Seoul PYTHONUNBUFFERED=1
EXPOSE 30092
# api_server.py 의 Flask app 을 waitress 로 서빙 (requirements 에 이미 포함)
# threads: waitress 기본값은 4 다. 펌프 성능곡선(/pump-curve/*)은 TB_RAWDATA 기간 집계라
# 한 요청이 수 분간 스레드를 점유한다. 기본 4 면 동시 요청 몇 건에 30 초 주기 /health 까지
# 슬롯을 못 잡아 컨테이너가 unhealthy 로 떨어지고, depends_on: service_healthy 때문에
# BE 가 기동 대기에 걸린다.
CMD ["waitress-serve", "--host=0.0.0.0", "--port=30092", "--threads=8", "api_server:app"]
