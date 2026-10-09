import pandas as pd
from matplotlib import pyplot as plt

if __name__ == "__main__":
    df = pd.read_csv("DJEPGS0_input_fri8100_2021_2022_filtered.csv", index_col=0)
    df.index = pd.to_datetime(df.index)

    df = df.resample(
            "60min"
        ).mean()
    df = df[ df["511-FRI-8100"] > 0 ]

    plt.plot(df["511-FRI-8100"].values)
    plt.show()
    
