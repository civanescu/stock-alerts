from datetime import datetime, timedelta

import pandas as pd
from pandas import DataFrame


def download_stooq(stock: str, start_date: str = None, end_date: str = None) -> DataFrame:
    """
    Downloads stock data from https://stooq.com/q/d/?s=nvda.us&c=0&d1=20230122&d2=20240510
                            https://stooq.com/q/d/l/?s=nvda.us&d1=20230122&d2=20240510&i=d
    Have no idea what is c=0
    """
    end_date = datetime.today() if end_date is None else end_date
    start_date = end_date - timedelta(days=365) if start_date is None else start_date
    link = f'https://stooq.com/q/d/l/?s={stock}&d1={start_date.strftime("%Y%m%d")}&d2={end_date.strftime("%Y%m%d")}&i=d'
    return pd.read_csv(link)
    # return r.json()


if __name__ == "__main__":
    result = download_stooq("nvda.us")
    print(result)
