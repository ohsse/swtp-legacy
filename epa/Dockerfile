# 1. 기본 이미지 선택 (가벼운 slim 버전 사용)
FROM python:3.10-slim

# 2. 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Seoul

# 3. [추가] 시스템(OS) 시간대 설정
RUN apt-get update && \
apt-get install -y --no-install-recommends tzdata build-essential && \
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
echo $TZ > /etc/timezone && \
rm -rf /var/lib/apt/lists/*

# 4. 작업 디렉토리 설정
WORKDIR /app

RUN mkdir /app/logs && chmod -R 777 /app/logs

# 5. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. [HTTPS 수정 1] 변환된 SSL 인증서 파일 복사 <-- 이 두 줄을 삭제합니다!
# COPY server.crt /etc/ssl/certs/ems_epa.crt
# COPY server.key /etc/ssl/certs/ems_epa.key

# 7. 소스 코드 복사
COPY . .

# 8. 컨테이너가 노출할 포트 설정 (포트 23002번)
EXPOSE 23002

# 9. 서버 실행
# Gunicorn 실행 명령어는 그대로 유지합니다. (경로가 고정되어 있음)
CMD ["gunicorn", "--bind", "0.0.0.0:23002", "--worker-class", "gthread", "--timeout", "900", "--workers", "1", "--threads", "4", "--graceful-timeout", "30", "run:app"]
