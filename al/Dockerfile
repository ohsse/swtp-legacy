FROM tensorflow/tensorflow

ENV TZ="Asia/Seoul"

WORKDIR /home/app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    joblib \
    matplotlib \
    dateutils \
    scikit-learn \
    schedule \
    openpyxl \
    pytz

COPY . /home/app

#CMD ["python3", "main.py", "--geteq", "y", "--getbill", "n"]

#2026.07.06 기존에 컨테이너 접속 후 각각 실행하던것을 bash 스크립트로 변경 
#CMD ["python3", "main_gm.py"]

CMD ["bash", "-c", "(cd /home/app && python3 main_gm.py) & (cd /home/app/power && python3 predictpower_Gosan_main.py) & (cd /home/app/pump3 && python3 main_e.py) & wait -n"]
