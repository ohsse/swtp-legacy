import subprocess
import argparse
from time import sleep
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_date', default=None)
    parser.add_argument('--target_hour')
    parser.add_argument('--getbill', default='y')
    parser.add_argument('--connection', default='maria-ems-db-ss')

    args = parser.parse_args()

    now = pd.Timestamp.now() 
    target_date = str(args.target_date) if args.target_date else now.strftime("%Y-%m-%d")
    target_hour = str(args.target_hour)
    connection = args.connection
     
    y, m = now.year, now.month
    n = now + pd.Timedelta(days=31)
    ny, nm = n.year, n.month

    if args.getbill == 'y':
        cmd = f"python3 ems_bill_lib_ss.py --start_date {y}-{m}-01 --end_date {ny}-{nm}-01 --connection {connection}"
        subprocess.run(cmd, shell=True, check=True) 

    hour = None
    date = None
    month = now.month
    target_date = pd.Timestamp(target_date) 

    while True:
        now = pd.Timestamp.now() 

        if month != now.month:
            month = now.month

            y, m = now.year, now.month
            ny, nm = now + pd.Timdelta(days=31)
            cmd = f"python3 ems_bill_lib_ss.py --start_date {y}-{m}-01 --end_date {ny}-{nm}-01 --connection {connection}"
            print("call: "+ cmd)
            subprocess.run(cmd, shell=True, check=True)

        if hour != now.hour:
            tds = target_date.strftime("%Y-%m-%d") 

            if now.hour == 0:
                target_date += pd.Timedelta(days=1)

            subprocess.run(f"python3 predict_pw_ss.py  --target_date {tds} --target_hour {str(now.hour)} --feeder ss --session ss_tot_pwi_24_cnn --mjson defmodel_cnn_24_ss.json", shell=True, check=True)
            subprocess.run(f"python3 ems_peak_ss.py --connection {connection} --pumpGroup 1 --target_date {tds} --target_hour {now.hour}", shell=True, check=True)
            
            hour = now.hour
            print(f'processes were excuted successfully: {tds}-{now.hour}H')

        sleep(60)
