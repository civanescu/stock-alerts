### BVB source
from __future__ import annotations

import pandas as pd
import time
import requests


def download_bvb(stock, granularity="D", from_time: int | None = None, to_time: int | None = None, **kwargs):
    """
    Granularity may be D, M, H, 15min, 1min

    :param to_time:
    :param from_time:
    :param stock:
    :param granularity:
    """
    url_core = 'https://wapi.bvb.ro/api/history'
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
        'Accept': '',
        'Origin': 'https://www.bvb.ro',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.bvb.ro/',  # this is the real one
        'Accept-Language': 'en-US, en; q=0.9, ro; q=0.8'
    }

    if granularity in ["D", "day"]:
        dt = "DAILY"
        p = "day"
    elif granularity in ["M", "month"]:
        dt = "MONTHLY"
        p = "month"
    elif granularity in ["H", "hour"]:
        dt = "INTRA"
        p = "intraday_60"
    elif granularity == "15min":
        dt = "INTRA"
        p = "intraday_15"
    elif granularity == "1min":
        dt = "INTRA"
        p = "intraday_1"
    else:
        raise Exception("Granularity not supported")

    if from_time:
        from_time = from_time
    else:  # get the last year
        from_time = int(time.time() - (
                10 * 365 * 24 * 60 * 60))  # 1629820736 ani*zile*ore*min*sec

    if to_time:
        to_time = to_time
    else:
        to_time = int(time.time())  # Today

    params_core = {
        "dt": dt,  # INTRA, DAILY, MONTHLY
        "p": p,  # only for INTRA, intraday_60 (1h), intraday_15 (15 min), intraday_1 (1min)
        "ajust": "1",
        # this should be changed inside the app ### for the moment I left next key to be sure it's working.
        "symbol": stock,
        "from": from_time,
        "to": to_time  # Wednesday, March 14, 2255 16:00:00
    }

    r = requests.get(url_core, headers=headers, params=params_core, **kwargs)
    return r.json()
