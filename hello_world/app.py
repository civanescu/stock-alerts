from __future__ import annotations

import json
import os
import time
from datetime import datetime

import pytz

import models.stock_requests as stock_requests
import models.stocks as stocks

eet_tz = pytz.timezone('Europe/Bucharest')


def yield_stocks(stock_list: list, from_time: int | None = None, to_time: int | None = None, granularity: str = "D") \
        -> tuple:
    """
    Yields stock data from online structure in json/dict format.
    :param stock_list:
    :param from_time:
    :param to_time:
    :param granularity:
    :return: [1]- name of stock, [2] - stock data in json/dict format
    """
    for stock in stock_list:
        try:
            print(f"Downloading {stock}")
            stock_data_json = stock_requests.download_bvb(stock)  # , granularity, from_time, to_time)
            yield stock, stock_data_json
        except Exception as e:
            print(f"ERROR downloading {stock} due to {e}")


def check_alert(stock_obj):
    """
    Will read the stock_obj look at it's last 5 records, and if there are any alerts it will save return it as a short
    :param stock_obj:
    :return: The object if is the case
    """
    try:
        if stock_obj.check_alerts(stock_obj):
            print(
                f"ATTENTION: {stock_obj.stock_name}, {stock_obj.df.iloc[-1]['date']} {stock_obj.df.iloc[-1]['alert_type']}")
            print(f"""More details: \n '{stock_obj.df.iloc[-5:]['date', 'close', 'histogram', 'rsi', 'ISA_9', 'ISB_26',
            'ema', 'sma20', 'sma50', 'SUPERT_10_1.0', 'SUPERTd_10_1.0', 'SUPERT_11_2.0', 'SUPERTd_11_2.0',
            'SUPERT_12_3.0', 'SUPERTd_12_3.0']}'""")
            return stock_obj
    except Exception as e:
        print(f"ERROR checking {stock_obj} due to {e}")


def account_check(event):
    if event.get('pass') == "pass":
        return True
    else:
        return False


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # try:
    #     ip = stock_requests.get("http://checkip.amazonaws.com/")
    # except stock_requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e
    # check if come from API:

    start_time = time.time()
    print(f"Event: {event}")
    print(f"Context: {context}")

    bucket_name = os.getenv("BUCKET_NAME", "test-bucket-keos")
    key_prefix = os.getenv("KEY_PREFIX", "alerts")
    file_type = os.getenv("FILE_TYPE", "csv")

    # Check how the event is coming!
    event = event.get("body", event)
    if type(event) is str:
        event = json.loads(event)

    if not account_check(event):
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": {
                "message": "Wrong pass",
                # "location": ip.text.replace("\n", "")
            },
        }

    # catch everything if is the case:
    stock_objects = []
    for stock in yield_stocks(event['stock_list']):
        stock = stocks.Stock(stock[0], stock[1])
        alert_obj = check_alert(stock)
        stock_objects.append(alert_obj) if alert_obj else None

    alerts = [
        {stock.stock_name: stock.df.iloc[-1]['alert_type']} for stock in stock_objects
    ]

    if len(stock_objects):
        stocks.save_stocks_to_s3(stock_objects,
                                 bucket=bucket_name,
                                 key=f"{key_prefix}-{datetime.now().strftime('%Y-%m-%d_%H%M')}",
                                 type=file_type
                                 )

    # except Exception as e:
    #     print(f"ERROR: For event {event} failed with {e}")
    #     message = f"Failed for event {event} with error: {e}"
    #     alerts = f"Error"

    alerts = alerts if alerts else "No alerts"
    message = (
        f"""At {datetime.now(eet_tz)} have the following: {alerts}""")
    retur = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": {
            "message": message,
            "event": {
                "time": str(datetime.now(eet_tz)),
                "alerts": alerts,
                "granularity": event.get('granularity'),
                "stock_list": event.get('stock_list'),
                "execution_time_seconds": int(time.time() - start_time)
            }
            # "location": ip.text.replace("\n", "")
        },
    }

    print("RESULT", retur)
    return retur
