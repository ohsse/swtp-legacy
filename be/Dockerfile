# [사용하지 말 것] 반출 경로는 이 파일을 쓰지 않는다. build-and-save.ps1 의 $Images 는
# ems-java-api 를 Dockerfile_new 로 만다. 이 파일은 아래 두 가지가 현실과 어긋나 있다.
#   1) build.gradle 이 'war' 플러그인을 쓰므로 Boot 산출물은 .war 인데 여기서는 .jar 를 COPY 한다.
#   2) build/libs 를 미리 빌드해 둔 것을 전제하지만 멀티스테이지가 아니라 재현되지 않는다.
# 고칠 일이 있으면 Dockerfile_new 를 고친다. 이 파일은 참고용으로만 남아 있다.
#
# OpenJDK 기반 이미지를 사용하여 Spring Boot 애플리케이션 빌드
# FROM 의 OS 접미사(-focal)는 떼거나 올리지 말 것 — glibc 2.34 이상이면 군산 서버에서
# pthread_create (EPERM) 로 기동 즉시 죽는다. 자세한 이유는 Dockerfile_new 런타임 단계 주석.
FROM eclipse-temurin:11-jre-focal AS build-spring

# 타임존 설정
ENV TZ=Asia/Seoul

WORKDIR /home/app

# java 디렉토리 생성
RUN mkdir -p /home/app
RUN mkdir -p /home/app/logs

COPY build/libs/ems-0.0.1-SNAPSHOT.jar /home/app

# 설치 및 설정을 위해 vi 편집기와 net-tools 패키지 설치
#RUN apt-get update && apt-get install -y vim net-tools git

# Spring Boot 애플리케이션 실행 포트
EXPOSE 10014

# Spring Boot 애플리케이션 실행
CMD ["java", "-jar", "/home/app/ems-0.0.1-SNAPSHOT.jar"]
