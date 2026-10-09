#!/bin/bash
for i in 11 12 1
do 
		python3 main_temp.py --target_date 2023-11-17 --geteq n --getbill n --target_hour $i
		sleep 60
done

