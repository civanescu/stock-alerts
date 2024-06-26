from __future__ import annotations

import json
import os
import time
from datetime import datetime

import boto3
import pytz
import yfinance

from models import stock_requests, stocks
from models.stocks import Stock

eet_tz = pytz.timezone('Europe/Bucharest')


def yield_stocks(stock_list: list, from_time: int | None = None, to_time: int | None = None, granularity: str = "1D") \
        -> tuple:
    """
    Yields stock data from online structure in json/dict format.
    :param stock_list: Because the stocks are from european xtb not all are in yfinance
    :param from_time: Timestamp
    :param to_time: Timestamp
    :param granularity: String: Must be in the yfinance format
    :return: [1]- name of stock, [2] - stock data in json/dict/pd.Dataframe format
    """
    for stock in stock_list:
        try:
            print(f"Downloading {stock}")
            if "." in stock:
                try:  # Try yfinance
                    if from_time is None or to_time is None:
                        stock_data = yfinance.Ticker(stock.split(".")[0]).history(
                            period="2y", interval=granularity, raise_errors=True)
                    stock_data.reset_index(inplace=True)
                except Exception as e:  # failed use stooq
                    print(f"Failed yfinance request {e}, fallback to stooq")
                    stock_data = stock_requests.download_stooq(stock)
            else:  # this can be used for other kind of sources:
                pass
            yield stock, stock_data
        except Exception as e:
            print(f"ERROR downloading {stock} due to {e}")


def check_alert(stock_obj: stocks.Stock) -> Stock | None:
    """
    Will read the stock_obj look at it's last 5 records, and if there are any alerts it will save return it as a short
    :param stock_obj:
    :return: The object if is the case
    """
    # print(f"Checking -> {stock_obj.stock_name} {stock_obj} {stock_obj.df}")
    try:
        if stock_obj.check_alerts(stock_obj):
            print(
                f"""{stock_obj.df.iloc[-5:][['date', 'close', 'histogram',
                                             'alert_type', 'sma20', 'SUPERTd_10_1.0', 'SUPERTd_10_1.0', 'SUPERTd_11_2.0']]}"""
            )
            return stock_obj
    except Exception as e:
        print(f"ERROR checking {stock_obj.stock_name} due to {e}")
        return None


def account_check(event):
    """
    # TODO: add a realistic authentication
    This function check account validity and return
    """
    return bool(event.get('pass') == "pass")


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

    key_prefix = os.getenv("KEY_PREFIX", "alerts")
    file_type = os.getenv("FILE_TYPE", "csv")
    topic_arn = os.getenv("TOPIC_ARN")
    bucket_name = os.getenv("BUCKET_NAME")

    # Check how the event is coming!
    event = event.get("body", event)
    if isinstance(event, str):
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

    alerts = message = "No alerts"
    # catch everything if is the case:
    stock_objects = []
    for stock in yield_stocks(event['stock_list']):
        stock = stocks.Stock(stock[0], stock[1])
        alert_obj = check_alert(stock)
        stock_objects.append(alert_obj) if alert_obj else None

    if len(stock_objects) > 0:
        alerts = [
            {stock.stock_name: stock.df.iloc[-1]['alert_type']} for stock in stock_objects
        ]
        message = (
            f"""At {datetime.now(eet_tz)} have the following: {alerts}""")

        # Send SMS to Topic
        if topic_arn:
            sns_client = boto3.client('sns')
            response = sns_client.publish(
                TopicArn=topic_arn,
                Message=message
            )
            print(f"INFO: SENT SMS {response}")

        # Save to bucket
        if bucket_name:
            stocks.save_stocks_to_s3(stock_objects,
                                     bucket=bucket_name,
                                     key=f"{key_prefix}-{datetime.now().strftime('%Y-%m-%d_%H%M')}",
                                     file_type=file_type
                                     )
            print(f"INFO: Saved {len(stock_objects)} in "
                  f"https://{bucket_name}.s3.us-east-1.amazonaws.com/{key_prefix}-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv")

    result = {
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

    print("RESULT", result)
    return result
