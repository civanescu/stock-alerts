from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests


def download_stooq(stock: str, start_date: str = None, end_date: str = None,
                   timeout_seconds: int = 30) -> pd.DataFrame | None:
    """
    Stock data with timeout in seconds
    """
    end_date = datetime.today() if end_date is None else end_date
    start_date = end_date - timedelta(days=365) if start_date is None else start_date
    link = f'https://stooq.com/q/d/l/?s={stock}&d1={start_date.strftime("%Y%m%d")}&d2={end_date.strftime("%Y%m%d")}&i=d'

    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
        'Accept': '',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Accept-Language': 'en-US'
    }

    try:
        response = requests.get(link, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except requests.exceptions.Timeout:
        print(f"Request timed out after {timeout_seconds}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occured: {e}")
    except Exception as e:
        print(f"Request link error: {e}")


if __name__ == "__main__":
    result = download_stooq("btce.de")
    print(result)
