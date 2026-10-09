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

    if args.geteq == 'y':
        pumpeq_start_date = (pd.Timestamp(target_date) - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        #pump1_eq_cmd = f"python3 get_pump_eq.py --feeder gs --start_date {pumpeq_start_date} --end_date {target_date} --pumpGroup 1"
        #pump2_eq_cmd = f"python3 get_pump_eq.py --feeder gs --start_date {pumpeq_start_date} --end_date {target_date} --pumpGroup 2"

        #print('call: ' + pump1_eq_cmd)
        #subprocess.run(pump1_eq_cmd, shell=True, check=True) 
        #print('call: ' + pump2_eq_cmd)
        #subprocess.run(pump2_eq_cmd, shell=True, check=True) 
     
    y, m = now.year, now.month
    n = now + pd.Timedelta(days=31)
    ny, nm = n.year, n.month

    #if args.getbill == 'y':
    #    cmd = f"python3 ems_bill_lib_gs.py --start_date {y}-{str(m).zfill(2)}-01 --end_date {ny}-{str(nm).zfill(2)}-01"
    #    subprocess.run(cmd, shell=True, check=True) 

    hour = None
    date = None
    month = now.month
    target_date = pd.Timestamp(target_date) 

    while True:
        now = pd.Timestamp.now() 
        tds = target_date.strftime("%Y-%m-%d") 
        '''
        if month != now.month:
            month = now.month

            y, m = now.year, now.month
            ny, nm = now + pd.Timdelta(days=31)
            cmd = f"python3 ems_bill_lib_gs.py --start_date {y}-{m}-01 --end_date {ny}-{nm}-01"
            print("call: "+ cmd)
            subprocess.run(cmd, shell=True, check=True)
        '''
        if hour != now.hour:

            if now.hour == 0:
                pumpeq_start_date = (pd.Timestamp(now) - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
                #pump1_eq_cmd = f"python3 get_pump_eq.py --feeder gs --start_date {pumpeq_start_date} --end_date {tds} --pumpGroup 1"
                #pump2_eq_cmd = f"python3 get_pump_eq.py --feeder gs --start_date {pumpeq_start_date} --end_date {tds} --pumpGroup 2"

                #print('call: ' + pump1_eq_cmd)
                #subprocess.run(pump1_eq_cmd, shell=True, check=True) 
                #print('call: ' + pump2_eq_cmd)
                #subprocess.run(pump2_eq_cmd, shell=True, check=True) 

                target_date += pd.Timedelta(days=1)

            #cmd = f"TZ=UTC-9 python3 ems_bill_lib_gs.py --start_date {y}-{str(m).zfill(2)}-01 --end_date {ny}-{str(nm).zfill(2)}-01"
            #print(f"TZ=UTC-9 python3 ems_bill_lib_gs.py --start_date {y}-{str(m).zfill(2)}-01 --end_date {ny}-{str(nm).zfill(2)}-01")
            #subprocess.run(cmd, shell=True, check=True) 

            subprocess.run(f"TZ=UTC-9 python3 predict_comp_ks_RE.py --session 701-367-FRI-4001_24_cnn --mjson defmodel_cnn_24_gs.json --target_date {tds} --target_hour {str(now.hour)} --pumpGroup 2 --database EMS_DB", shell=True, check=True)
            subprocess.run(f"TZ=UTC-9 python3 predict_comp_ks_RE.py --session 701-367-FRI-4004_24_cnn  --mjson defmodel_cnn_24_gs.json --target_date {tds} --target_hour {str(now.hour)} --pumpGroup 1 --database EMS_DB", shell=True,check=True)
            subprocess.run(f"TZ=UTC-9 python3 ems_peak.py --connection {connection} --pumpGroup 1 --target_date {tds} --target_hour {str(now.hour)}", shell=True, check=True)
            
            hour = now.hour
            print(f'processes were excuted successfully: {tds}-{now.hour}H')

        sleep(60)
