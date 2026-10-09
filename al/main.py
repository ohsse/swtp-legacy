import subprocess
import argparse
from time import sleep
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_date', default=None)
    parser.add_argument('--target_hour', default=None)
    parser.add_argument('--geteq', default='n')
    parser.add_argument('--getbill', default='n')
    parser.add_argument('--connection', default='maria-ems-db-gs')

    args = parser.parse_args()

    now = pd.Timestamp.now() 
    target_date = str(args.target_date) if args.target_date else now.strftime("%Y-%m-%d")
    target_hour = str(args.target_hour) if args.target_date else str(pd.Timestamp.now().hour)
    connection = args.connection

    hour = None
    date = None
    month = now.month
    target_date = pd.Timestamp(target_date) 

    while True:
        now = pd.Timestamp.now() 
        tds = target_date.strftime("%Y-%m-%d") 

        print('#hour',hour)
        print('#now.hour',now.hour)
        if hour != now.hour:
            print('#START#')
            if now.hour == 0:
                target_date += pd.Timedelta(days=1)
                
            month = now.month
            y, m = now.year, now.month
            n = now + pd.Timedelta(days=31)
            ny, nm = n.year, n.month

            cmd = f"python3 ems_bill_lib_gs.py --start_date {y}-{str(m).zfill(2)}-01 --end_date {ny}-{str(nm).zfill(2)}-01"
            print(f"python3 ems_bill_lib_gs.py --start_date {y}-{str(m).zfill(2)}-01 --end_date {ny}-{str(nm).zfill(2)}-01")
            subprocess.run(cmd, shell=True, check=True) 

            subprocess.run(f"python3 predict_comp_ks_RE.py --session 701-367-FRI-4004_24_cnn --mjson defmodel_cnn_24_gs.json --target_date {tds} --target_hour {str(now.hour)} --pumpGroup 2 --database EMS_DB", shell=True, check=True)
            sleep(5)
            subprocess.run(f"python3 predict_comp_ks_RE.py --session 701-367-FRI-4001_24_cnn --mjson defmodel_cnn_24_gs.json --target_date {tds} --target_hour {str(now.hour)} --pumpGroup 1 --database EMS_DB", shell=True,check=True)
            
            #subprocess.run(f"python3 ems_peak.py --connection {connection} --pumpGroup 1 --target_date {tds} --target_hour {str(now.hour)}", shell=True, check=True)
            
            hour = now.hour
            print(f'processes were excuted successfully: {tds}-{now.hour}H')
            print('#END#')

        sleep(60)
