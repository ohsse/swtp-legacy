import subprocess
import argparse
from time import sleep
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_date', default=None)
    args = parser.parse_args()

    #TODO CHECK!
    connection = 'maria-ems-db-gr'
    database = 'ems_db'

    now = pd.Timestamp.now() 
    target_date = str(args.target_date) if args.target_date else now.strftime("%Y-%m-%d")

    y, m = now.year, now.month
    n = now + pd.Timedelta(days=31)
    ny, nm = n.year, n.month

    cmd = f"python3 ems_bill_lib_gr.py --start_date {y}-{m}-01 --end_date {ny}-{nm}-01 --connection {connection}"
    #cmd = f"python3 ems_bill_lib_gr.py --start_date 2023-10-01 --end_date 2023-11-01 --connection {connection}"
    print('call: ', cmd)
    subprocess.run(cmd, shell=True, check=True) 
    eq_start_date = (pd.Timestamp(target_date) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

    pumpeqcmd1 = f"python3 get_pump_eq_gr.py --feeder gr --start_date {eq_start_date} --end_date {target_date} --pumpGroup 1"
    print('call: ', pumpeqcmd1)
    subprocess.run(pumpeqcmd1, shell=True, check=True) 

    hour = None
    date = None

    month = now.month
    target_date = pd.Timestamp(target_date)

    while True:
        now = pd.Timestamp.now() 
        tds = target_date.strftime("%Y-%m-%d")

        if False and month != now.month:
            month = now.month
            y, m = now.year, now.month
            ny, nm = now + pd.Timdel(days=31)
            cmd = f"python3 ems_bill_lib_gr.py --start_date {y}-{m}-01 --end_date {ny}-{nm}-01"
            print("call: " + cmd)
            subprocess.run(cmd, shell=True, check=True)

        if hour != now.hour:
            exec0 = f"python3 predict_comp_gr.py --session 780-344-FIT-2502_24_cnn  --mjson defmodel_cnn_24_gr.json --target_date {tds} --target_hour {str(now.hour)} --pumpGroup 1 --database {database}"
            print('call: ', exec0)
            subprocess.run(exec0, shell=True, check=True)

            exec1 = f"python3 ems_peak_gr.py --connection {connection} --pumpGroup 1 --target_date {tds} --target_hour {str(now.hour)}"
            print('call: ', exec1)
            subprocess.run(exec1, shell=True, check=True)

            if now.hour == 0:
                target_date += pd.Timedelta(days=1)

            hour = now.hour
            print(f'processes were excuted successfully: {tds}-{now.hour}H')

        sleep(60)
