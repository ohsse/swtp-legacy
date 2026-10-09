import subprocess
import argparse
from time import sleep
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_date', default=None)
    parser.add_argument('--geteq', default='y')
    parser.add_argument('--getbill', default='y')
    parser.add_argument('--connection', default='maria-ems-db-gs')

    args = parser.parse_args()

    now = pd.Timestamp.now() 
    target_date = str(args.target_date) if args.target_date else now.strftime("%Y-%m-%d")
    connection = args.connection
     
    y, m = now.year, now.month

    target_date = pd.Timestamp(target_date) 

    for j in range(5):
        tds = target_date.strftime("%Y-%m-%d") 

        for i in range(0, 24):
            target_hour = str(i)

            subprocess.run(f"python3 predict_comp.py --session 701-367-FRI-4001_24_cnn --mjson defmodel_cnn_24_gs.json --target_date {tds} --target_hour {target_hour} --pumpGroup 1 --database ems_db", shell=True, check=True)
            subprocess.run(f"python3 predict_comp.py --session 701-367-FRI-4004_24_cnn  --mjson defmodel_cnn_24_gs.json --target_date {tds} --target_hour {target_hour} --pumpGroup 2 --database ems_db", shell=True,check=True)
            subprocess.run(f"python3 ems_peak.py --connection {connection} --pumpGroup 1 --target_date {tds} --target_hour {str(int(target_hour)+1)}", shell=True, check=True)
            sleep(60)

        target_date += pd.Timedelta(days=1)