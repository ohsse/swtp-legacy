from pump_rt_algo import get_tags, PumpEQ_DB_connector, PumpControl, get_connection, get_connection_alchemy_s
from dataset import select_data_from_rdb, select_data_from_rdb_with_tags
import pandas as pd
import argparse
import numpy as np
import json

def main(args, conn, feeder):

    with open('datafeeder.json') as w:
        feeder = json.load(w)[feeder]
        print(feeder)

    database = feeder['database']
    ctr_df = get_tags(conn, pumpGroup=args.pumpGroup, pmTable=feeder['pmtable'])
    pdbc = PumpEQ_DB_connector(conn);
    pumpAttr, pumpTags = pdbc.getPumpAttribute(pumpGroup=args.pumpGroup, pmTable=feeder['pmtable']);
        
    pt = pumpAttr.loc["PUMP_TYP", : ].values
    nixs = np.where( pt == 1 )
    normpumps = pumpAttr.columns.values[nixs]
    iixs = np.where( pt == 2 )
    invpumps = pumpAttr.columns.values[iixs]

    st_date = pd.Timestamp(args.start_date) 
    end_date = pd.Timestamp(args.end_date)

    raw_data = select_data_from_rdb_with_tags(conn, pumpTags, st_date, end_date, table=feeder['rawtable'])
    raw_df = pd.DataFrame(raw_data).pivot(index='ts', columns='tagname')['value']

    for c in raw_df.columns:
        raw_df[c] = raw_df[c].astype(float)

    df = raw_df.resample('1min').mean().fillna(0)

    df.index = pd.to_datetime(df.index)

    pc = PumpControl(conn, None, ctr_df, pumpAttr, pumpTags, init=False, database=database)
    _df = pc.FPPC.calc_diff_head(df) # proc


    connection = feeder["connection"]
    engine = get_connection_alchemy_s(connection)

    """
    QH = pc.FPPC.calc_equationTable_Inv(_df, 'h',invpumps, st_date=st_date)
    QP = pc.FPPC.calc_equationTable_Inv(_df, 'p',invpumps, st_date=st_date)
    inv_eq = pc.FPPC.write_eqTable(QH, QP, PumpType='Inv')
    inv_eq.to_sql(name='TB_PRF_INVRT_RST', con=engine, if_exists='append', index=False)
    """

    QH = pc.FPPC.calc_equationTable_NonInv(_df, 'h',normpumps, st_date=st_date)
    QP = pc.FPPC.calc_equationTable_NonInv(_df, 'p',normpumps, st_date=st_date)
    ninv_eq = pc.FPPC.write_eqTable(QH, QP, date=pd.Timestamp.now().strftime('%Y-%m-%d'))
    ninv_eq = ninv_eq.sort_values(['ANLY_DATE','EQ_TYP', 'WTR_TE', 'PUMP_IDX'])
    print('ninv_eq')
    print(ninv_eq)

    ninv_eq.to_sql(name='TB_PRF_PRFRM_RST', con=engine, if_exists='append', index=False)
    engine.commit()
    engine.close()


if __name__ == "__main__":
    print('hi%')
    parser = argparse.ArgumentParser(prog='pump_rt_algo')

    parser.add_argument('--session')
    parser.add_argument('--start_date')
    parser.add_argument('--pumpGroup', default=1)
    parser.add_argument('--tablename', default='ems_db.rawdata')
    parser.add_argument('--end_date', default=None)
    parser.add_argument('--source_type', default='rdb')
    parser.add_argument('--input_file', default=None)
    parser.add_argument('--feeder', default=None)

    args = parser.parse_args()
    conn = get_connection(args)

    main(args, conn=conn, feeder=args.feeder)