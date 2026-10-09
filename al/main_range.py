import subprocess
import argparse
from time import sleep
import pandas as pd

def schedule_tasks(start_datetime, end_datetime, connection, database):
    current_datetime = start_datetime
    
    while current_datetime <= end_datetime:
        target_date = current_datetime.strftime("%Y-%m-%d")
        target_hour = current_datetime.hour
        print(f"Processing for {target_date} at hour {target_hour}")

        subprocess.run(f"python3 predict_comp_ks_RE_range.py --session 701-367-FRI-4004_24_cnn --mjson defmodel_cnn_24_gs.json --target_date {target_date} --target_hour {target_hour} --pumpGroup 2 --database EMS_DB", shell=True, check=True)
        subprocess.run(f"python3 predict_comp_ks_RE_range.py --session 701-367-FRI-4001_24_cnn  --mjson defmodel_cnn_24_gs.json --target_date {target_date} --target_hour {target_hour} --pumpGroup 1 --database EMS_DB", shell=True,check=True)

        #exec1 = f"python3 ems_peak_gu.py --connection {connection} --pumpGroup 1 --target_date {target_date} --target_hour {target_hour}"
        #print('call: ', exec1)
        #subprocess.run(exec1, shell=True, check=True)
        
        # 5초 대기
        sleep(5)
        
        # 다음 시간으로 업데이트
        current_datetime += pd.Timedelta(hours=1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_datetime', type=str, help="Start datetime in YYYY-MM-DD HH format", default='2024-03-11 0')
    parser.add_argument('--end_datetime', type=str, help="End datetime in YYYY-MM-DD HH format", default='2024-03-15 10')

    args = parser.parse_args()

    # 설정된 연결 및 데이터베이스
    connection = 'maria-ems-db-gs'
    database = 'EMS_DB'

    # 시작일시와 종료일시를 pandas의 Timestamp로 변환합니다.
    start_datetime = pd.Timestamp(args.start_datetime + ':00')  # 분과 초를 추가하여 포맷을 맞춤
    end_datetime = pd.Timestamp(args.end_datetime + ':00')

    schedule_tasks(start_datetime, end_datetime, connection, database)
