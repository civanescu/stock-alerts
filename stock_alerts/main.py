import datetime
import json
import os
import time

import app

stock_list = [
    "btce.de", "SNO"
    , "nvda.us", "IS3N.DE", "eunl.de", "sxr8.de", "eun2.de", "iqqh.de", "spy4.de", "vusa.de", "3usl.uk"
    , "ge.us", "amzn.us", "tsm.us", "irm.us", "msft.us", "cspx.uk", "suas.uk", "suws.uk", "iues.uk"
    , "udvd.uk", "meta.us", "ogn.us"
    , "BVB", "TBK"
    , "M", "EL", "SNP", "SNN", "TBK", "FP", "BUCU", "PTR"
    ]
# AI.ES missing from stooq + yFinance


if __name__ == "__main__":
    os.environ["TOPIC_ARN"] = "arn:aws:sns:us-east-1:811041629820:Test"
    os.environ["BUCKET_NAME"] = "test-bucket-keos"
    print(f"Starting {time.time()}")
    from_date = int(time.time()) - (2 * 30 * 365 * 24 * 60 * 60)  # 1 year  # hmmm
    to_date = int(time.time())  # today
    date = datetime.datetime.now()

    event = {
        "pass": "pass",
        "stock_list": stock_list,
        # "granularity": granularity,
        # "from_date": from_date,
        # "to_date": to_date
    }

    print(json.dumps(event, indent=4))

    return_data = app.lambda_handler(event, None)

    print(json.dumps(return_data, indent=4))

    print(f"Finished {time.time()}")
