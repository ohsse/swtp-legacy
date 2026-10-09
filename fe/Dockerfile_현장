# Vue 파일을 서빙하기 위해 Nginx를 사용합니다.
FROM nginx:stable-alpine

# (선택 사항) Nginx의 html 디렉토리를 초기화합니다.
RUN rm -rf /usr/share/nginx/html/*

# 로컬에서 빌드된 결과물을 복사합니다.
# Dockerfile이 있는 현재 폴더의 dist 폴더를 Nginx의 html 폴더로 복사합니다.
COPY ./dist /usr/share/nginx/html

# 커스텀 Nginx 설정 파일을 복사합니다.
COPY ./default.conf /etc/nginx/conf.d/default.conf

# Nginx가 리슨할 포트입니다.
EXPOSE 10013

# 컨테이너 실행 시 Nginx 데몬을 포그라운드에서 실행합니다.
CMD ["nginx", "-g", "daemon off;"]