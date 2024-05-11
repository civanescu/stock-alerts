import datetime
import json
import time

import app

# Definitions
stock = "tvbetetf"
storage = "storage"
stock_list = ["DIGI"] #, "H2O", "DIGI" ] # , "BVB", "BRD", "M", "EL", "H2O", "SNP", "SNN", "TBK", "FP", "BUCU", "PTR", "SNO"]
granularity = "day"
from_date = int(time.time()) - (30 * 365 * 24 * 60 * 60)  # 1 year  # hmmm
to_date = int(time.time())  # today
date = datetime.datetime.now()

if __name__ == "__main__":
    print(f"Starting {time.time()}")
    print(date, stock, storage, stock_list, granularity, from_date, to_date)

    event = {
        "pass": "pass",
        # "stock": stock,
        # "storage": storage,
        "stock_list": stock_list,
        "granularity": granularity,
        # "from_date": from_date,
        # "to_date": to_date
    }

    # print(json.dumps(event, indent=4))

    return_data = app.lambda_handler(event, None)

    print(json.dumps(return_data, indent=4))

    print(f"Finished {time.time()}")
