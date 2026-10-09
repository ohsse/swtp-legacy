import argparse
import pandas as pd
import json
from matplotlib import pyplot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='predict_plot')

    parser.add_argument('--session')
    parser.add_argument('--start_date')
    parser.add_argument('--ref_days',default=10)
    parser.add_argument('--source_type', default='file')
    parser.add_argument('--feeder', default=None)

    args = parser.parse_args()

    with open("defmodel.json") as f :
        config = json.load(f)

    session = config[args.session]
    scaler_path = session["scaler_output_name"]
    label_col = session["dataset"]["label_col"]

    if args.source_type == 'file':
        validation_file = session["validation_file"]
        df = pd.read_csv(validation_file, index_col=0)
    
    def _f(x):
        return pd.Timestamp(x.name).hour

    df.columns = ['F'] 
    
    df['h'] = df.apply(_f, axis=1)

    df = df.groupby('h').mean('F')
    df['F'].plot(kind='bar',label=label_col)
    pyplot.legend()
    pyplot.show()

    pyplot.savefig(f'plotresult/{label_col}_hour_agg.png')
    print(df) 

