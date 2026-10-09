# ---- build stage : 컨테이너 안에서 지정 프로파일로 bootJar ----
FROM eclipse-temurin:21-jdk-jammy AS build
# 빌드 프로파일(resources-env/<profile> 오버레이). docker-compose 의 build.args.PROFILE 로 주입, 미지정 시 ubuntu.
ARG PROFILE=ubuntu
WORKDIR /src
# 빌드 컨텍스트는 inpEditor/BE 다(compose 2개 모두). Gradle 프로젝트는 그 아래 editor/ 이므로
# editor/ 의 내용물을 /src 루트로 올려야 아래 gradlew 가 /src/gradlew 에 놓인다.
# (컨텍스트가 editor/ 인 Dockerfile.multistage 는 COPY . . 를 쓴다 — 서로 붙여넣지 말 것)
COPY editor/ ./
RUN chmod +x gradlew && ./gradlew --no-daemon bootJar -Pprofile=${PROFILE}

# ---- runtime stage ----
FROM eclipse-temurin:21-jre-jammy
# 런타임 기본 경로(컴포즈의 STORAGE_PATH/LOG_PATH 로 오버라이드). 이미지에 동일 경로를 미리 만들어 두어야
# 네임드 볼륨이 app 사용자 소유권을 상속한다. 기본 STORAGE_PATH=/app/files (PY config.docker.json 과 일치).
ENV TZ=Asia/Seoul LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    EDITOR_STORAGE_BASE_PATH=/app/files LOG_PATH=/app/logs JAVA_OPTS=""
RUN groupadd -r app && useradd -r -g app -d /app app \
 && mkdir -p /app /app/files /app/logs && chown -R app:app /app /app/files /app/logs
WORKDIR /app
COPY --from=build --chown=app:app /src/build/libs/api.jar /app/api.jar
USER app
EXPOSE 30091
ENTRYPOINT ["sh","-c","exec java $JAVA_OPTS -jar /app/api.jar"]