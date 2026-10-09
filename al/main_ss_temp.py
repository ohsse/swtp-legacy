import subprocess
import argparse
from time import sleep
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_date', default=None)
    parser.add_argument('--target_hour')
    parser.add_argument('--connection', default='maria-ems-db-ss')

    args = parser.parse_args()

    now = pd.Timestamp.now() 
    target_date = str(args.target_date) if args.target_date else now.strftime("%Y-%m-%d")
    target_hour = str(args.target_hour) if args.target_hour else None
    connection = args.connection
     
    y, m = now.year, now.month
    n = now + pd.Timedelta(days=31)
    ny, nm = n.year, n.month

    hour = None
    date = None
    month = now.month
    target_date = pd.Timestamp(target_date) 

    if target_hour is None:
        for i in range(5):
            for h in range(24):
                tds = target_date.strftime("%Y-%m-%d") 

                subprocess.run(f"python3 predict_pw_ss.py  --target_date {tds} --target_hour {str(h)} --feeder ss --session ss_tot_pwi_24_cnn --mjson defmodel_cnn_24_ss.json", shell=True, check=True)
                subprocess.run(f"python3 ems_peak_ss.py --connection {connection} --pumpGroup 1 --target_date {tds} --target_hour {h}", shell=True, check=True)
                
                print(f'processes were excuted successfully: {tds}-{h}H')
                sleep(60)
            target_date += pd.Timedelta(days=1)

            
