from __future__ import annotations

import io
import json
import time
from datetime import datetime

import boto3
import pandas as pd
import pandas_ta as ta
import pytz


class Stock:
    """
    Class to represent a stock.
    # All functions works also by themself, but they are made to create the bigger dataframe
    Functions:
        - _calculate_macd: Calculate the MACD indicator for the stock (defaults 12 with 29, signal 9, can be changed)
        - _calculate_rsi: Calculate the RSI indicator for the stock (defaults 14, can be changed)
        - _calculate_ichimoku: Calculate the ichimoku indicator for the stock (defaults 9, 26, 52)
        - _calculate_ema: Calculate the exponential moving average indicator for the stock (default add 200, can be changed)
        - _calculate_sma: Calculate the simple moving average indicator for the stock (default 20, 50, can be added one more)
        - _calculate_supertrend: Calculate the supertrends indicators (default (10,1), (11,2), (12,3), can be added one more)
        
    Variables:
        - stock: Name of the stock
        - df: Dataframe with the stock data
        - granularity: Granularity of the stock data
        - there is an ichimoku_prediction df generated when you run the function
        - there is an alerts df that keeps only the changes from the original df
    """

    def __init__(self, stock_name: str, input_data: pd.DataFrame | str | dict, granularity: str = "D",
                 data_format: str = "json"):
        self.stock_name = stock_name
        self.df = pd.DataFrame()
        self.input_data = input_data
        self.granularity = granularity  # this should be optional, but anyway...
        self.data_format = data_format

        self._rename()
        self.calculate_all()

    def _rename(self):
        """Convert data to df"""
        if isinstance(self.input_data, dict):
            self.df = pd.DataFrame.from_dict(self.input_data)
            self.df.rename(columns={'t': 'timestamp', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume',
                                    's': 'stock'}, inplace=True)
            self.df['stock'] = self.stock_name
            self.df['date'] = pd.to_datetime(self.df['timestamp'], unit='s')
            self.df.drop_duplicates(subset=['timestamp', 'stock'], inplace=True, keep='last')
            self.df.set_index('timestamp', inplace=True)  # set the index to timestamp

    def _calculate_macd(self, n_fast=12, n_slow=26, n_signal=9):
        ema_fast = self.df['close'].ewm(span=n_fast, min_periods=n_slow).mean()
        ema_slow = self.df['close'].ewm(span=n_slow, min_periods=n_slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=n_signal, min_periods=n_signal).mean()
        histogram = macd - signal
        self.df['macd'] = macd
        self.df['signal'] = signal
        self.df['histogram'] = histogram
        return macd, signal, histogram

    def _calculate_rsi(self, n=14):
        delta = self.df['close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=n - 1, adjust=False).mean()
        ema_down = down.ewm(com=n - 1, adjust=False).mean()
        rsi = ema_up / (ema_up + ema_down) * 100
        self.df['rsi'] = rsi
        return rsi

    def _calculate_supertrend(self, other: tuple | None = None) -> pd.DataFrame:
        """
        Based on pandas_ta this: https://github.com/twopirllc/pandas-ta/blob/main/pandas_ta/overlap/supertrend.py
        * 10, 11, 12 are on plus buy, 1st on minus sell?
        """
        sti_10_1 = ta.supertrend(self.df['high'], self.df['low'], self.df['close'], length=10, multiplier=1).drop(
            ['SUPERTl_10_1.0', 'SUPERTs_10_1.0'], axis=1)
        sti_11_2 = ta.supertrend(self.df['high'], self.df['low'], self.df['close'], length=11, multiplier=2).drop(
            ['SUPERTl_11_2.0', 'SUPERTs_11_2.0'], axis=1)
        sti_12_3 = ta.supertrend(self.df['high'], self.df['low'], self.df['close'], length=12, multiplier=3).drop(
            ['SUPERTl_12_3.0', 'SUPERTs_12_3.0'], axis=1)

        if other and len(other) == 2:
            other = ta.supertrend(self.df['high'], self.df['low'], self.df['close'], length=other[0],
                                  multiplier=other[1])
            self.df = pd.concat([self.df, other], axis=1)

        self.df = pd.concat([self.df, sti_10_1, sti_11_2, sti_12_3], axis=1)
        return self.df

    def _calculate_ema(self, n=200):
        """
        * 200 EMA with Supertrend
	    * cumperi doar cand este green si este peste EMA, sell cand trece pe red
        """
        ema = self.df['close'].ewm(span=n, min_periods=n).mean()
        self.df['ema'] = ema
        return ema

    def _calculate_sma(self, other: int | None = None) -> tuple:
        """
        Will add 20, 50 SMA
        Optional we have other sma. It will use the pandas_ta library to add another sma timeframe
        """
        sma20, sma50 = pd.DataFrame(), pd.DataFrame()

        sma20['sma20'] = self.df['close'].rolling(window=20).mean()
        sma50['sma50'] = self.df['close'].rolling(window=50).mean()
        self.df = pd.concat([self.df, sma20, sma50], axis=1)

        if other and other > 0:
            sma = ta.sma(self.df['close'], length=other)
            self.df = pd.concat([self.df, sma], axis=1)
            return sma20, sma50, sma

        return sma20, sma50

    def _calculate_ichimoku(self):
        """
        * ichimoku
        """
        ichimoku_curent, self.ichimoku_prediction = ta.ichimoku(self.df['high'], self.df['low'], self.df['close'])
        # print(ichimoku_curent[['ISA_9', 'ISB_26']])
        self.df = pd.concat([self.df, ichimoku_curent[['ISA_9', 'ISB_26']]], axis=1)
        return ichimoku_curent, self.ichimoku_prediction

    def add_alerts(self) -> pd.DataFrame:
        """
        The alerts and how do we want to handle them.
        1. MACD, from histrogram move from plus to minus alert SELL, when minus to plus alert BUY
        2. RSI, when RSI is below 30 BUY, when RSI is above 70 SELL (this should be rethinked)
        3. Supertrend - when all directions go to 1 BUY, when one goes to -1 SELL
        4. Supertrend + EMA - when all directions are 1 and is close price is over EMA, BUY, when one supertrend goes -1, SELL
        5. Supertrend + Ichimoku - when all directions are 1 and is over Ichimoku, BUY, when one supertrend goes -1, SELL
        6. EMA200 + curent - when is over EMA200, BUY, when is under, SELL
        7. SMA20 or SMA50 + curent - when is over SMA20 or SMA50, BUY, when is under, SELL (slower can be better for profit)
        """
        self.df['alert_type'] = ''
        # MACD
        if 'histogram' in self.df.columns:
            # Check if the histogram is in the correct direction:
            mask_up = ((self.df['histogram'] > 0) & (self.df['histogram'].shift(1) < 0))
            mask_down = ((self.df['histogram'] < 0) & (self.df['histogram'].shift(1) > 0))
            self.df.loc[mask_up, 'alert_type'] = 'MACD UP'
            self.df.loc[mask_down, 'alert_type'] = 'MACD DOWN'

        # RSI
        if 'rsi' in self.df.columns:
            rsi_up = ((self.df['rsi'] > 30) & (self.df['rsi'].shift(1) < 30))
            self.df.loc[rsi_up, 'alert_type'] = 'RSI UP'

            rsi_watch = ((self.df['rsi'] > 70) & (self.df['rsi'].shift(1) < 70))
            self.df.loc[rsi_watch, 'alert_type'] = 'RSI WATCH'

            rsi_down = ((self.df['rsi'] < 70) & (self.df['rsi'].shift(1) > 70))
            self.df.loc[rsi_down, 'alert_type'] = 'RSI SECURE'



        #  Supertrend watch
        if all(col in self.df.columns for col in ['SUPERTd_10_1.0', 'SUPERTd_11_2.0', 'SUPERTd_12_3.0']):
            st_alert = (
                        (self.df['SUPERTd_10_1.0'] == 1) & (self.df['SUPERTd_10_1.0'].shift(1) == -1)
                        |
                        (self.df['SUPERTd_11_2.0'] == 1) & (self.df['SUPERTd_11_2.0'].shift(1) == -1)
                        |
                        (self.df['SUPERTd_12_3.0'] == 1) & (self.df['SUPERTd_12_3.0'].shift(1) == -1)
            )
            self.df.loc[st_alert, 'alert_type'] = 'Supertrend WATCH'


        # Supertrend
        if all(col in self.df.columns for col in ['SUPERTd_10_1.0', 'SUPERTd_11_2.0', 'SUPERTd_12_3.0']):
            # Check if the supertrend is in the correct direction:
            st_up = (
                    ((self.df['SUPERTd_10_1.0'] == 1) & (self.df['SUPERTd_11_2.0'] == 1) & (
                            self.df['SUPERTd_12_3.0'] == 1))
                    &
                    ((self.df['SUPERTd_10_1.0'].shift(1) == -1) | (self.df['SUPERTd_11_2.0'].shift(1) == -1) | (
                            self.df['SUPERTd_12_3.0'].shift(1) == -1))
            )
            self.df.loc[st_up, 'alert_type'] = 'Supertrend UP'

            st_down = (
                    ((self.df['SUPERTd_10_1.0'] == -1) & (self.df['SUPERTd_11_2.0'] == -1) & (
                            self.df['SUPERTd_12_3.0'] == -1))
                    &
                    ((self.df['SUPERTd_10_1.0'].shift(1) == 1) | (self.df['SUPERTd_11_2.0'].shift(1) == 1) | (
                            self.df['SUPERTd_12_3.0'].shift(1) == 1))
            )
            self.df.loc[st_down, 'alert_type'] = 'Supertrend DOWN'


        # Supertrend + Ichimoku
        if all(col in self.df.columns for col in
               ['ISA_9', 'ISB_26', 'SUPERT_10_1.0', 'SUPERT_11_2.0', 'SUPERT_12_3.0']):
            # Take the smallest value of supertrends from one row and keep it:

            st_value = self.df[['SUPERT_10_1.0', 'SUPERT_11_2.0', 'SUPERT_12_3.0']].min(axis=1)
            st_ichimoku = (
                    (self.df['ISA_9'] < st_value) &
                    (self.df['ISB_26'] < st_value) &
                    ((self.df['ISA_9'].shift(1) > st_value.shift(1)) | (self.df['ISB_26'].shift(1) > st_value.shift(1)))
            )
            self.df.loc[st_ichimoku, 'alert_type'] = 'Supertrend + Ichimoku UP'
            # Alert if is down (optional)
            # self.df.loc[st_up, 'alert_type'] = 'ichimoku_up'
            # st_down = (
            #     ((self.df['ISA_9'] > st_value) | (self.df['ISB_26'] > st_value)) &
            #     ((self.df['ISA_9'].shift(1) < st_value.shift(1)) & (self.df['ISB_26'].shift(1) < st_value.shift(1)))
            #            )
            # self.df.loc[st_down, 'alert_type'] = 'ichimoku_down'


        # Supertrend + sma20, we can also have a look on the long range sma50, ema200 ...
        if all(col in self.df.columns for col in ['ema', 'SUPERTd_10_1.0', 'SUPERTd_11_2.0', 'SUPERTd_12_3.0']):
            # Check if any of the supertrend moved in the correct direction:
            st_sma20 = (
                    (
                            (self.df['SUPERTd_10_1.0'] == 1) & (self.df['SUPERTd_10_1.0'].shift(1) == -1)
                            |
                            (self.df['SUPERTd_11_2.0'] == 1) & (self.df['SUPERTd_11_2.0'].shift(1) == -1)
                            |
                            (self.df['SUPERTd_12_3.0'] == 1) & (self.df['SUPERTd_12_3.0'].shift(1) == -1)
                    )
                    &
                    (self.df['close'] > self.df['sma20'])
            )
            self.df.loc[st_sma20, 'alert_type'] = 'supertrend + sma20 UP'


        # Return only the alerted rows:
        return self.df[self.df['alert_type'] != ''].dropna()

    def calculate_all(self):
        self._calculate_macd()
        self._calculate_rsi()
        self._calculate_ichimoku()
        self._calculate_ema()
        self._calculate_sma()
        self._calculate_supertrend()
        self.add_alerts()
        self.df.dropna()
        return self.df

    def save_to_pickle(self, storage: str | None = None, time_see: str | None = None, **kwargs) -> str:
        """
        Local saves the dataframe to a pickle file.
        Storage (str): The path to the storage folder WITHOUT trailing '/'
        time (str): The time of the data.
        """
        storage_path = f"{storage}/" if storage is not None else ""
        time_sufix = f"_{time_see}" if time is not None else ""
        self.df.to_pickle(f"{storage_path}{self.stock_name}{time_sufix}.pkl", **kwargs)
        return f"{storage_path}{self.stock_name}{time_sufix}.pkl"

    # Optional getters/setters
    def get_df(self):
        return self.df

    def get_alerts(self):
        return self.add_alerts()

    def get_name(self):
        return self.stock_name

    @staticmethod
    def _find_time():
        """
        Find the start time of the data.
        """
        eet_tz = pytz.timezone('Europe/Bucharest')

        local_time = datetime.now(eet_tz)  #
        time_now = local_time.timestamp()

        if local_time.weekday() == 0:
            if local_time.hour <= 18 and local_time.minute < 30:
                start_time = time_now - pd.Timedelta(days=3).total_seconds()
            else:
                start_time = time_now - pd.Timedelta(days=4).total_seconds()
        else:
            if local_time.hour <= 18 and local_time.minute < 30:
                start_time = time_now - pd.Timedelta(days=1).total_seconds()
            else:
                start_time = time_now - pd.Timedelta(days=2).total_seconds()

        return start_time

    def check_alerts(self, obj: Stock) -> bool:
        """
        Check if the alerts are in the dataframe.
        # this is made for the daily granularity
        """
        # # timestamp now
        start_time = self._find_time()
        df = obj.add_alerts()
        df_index_as_int = df.index.astype(int)
        try:
            if df_index_as_int[-1] > start_time:
                return True
            else:
                return False
        except IndexError:
            print(f"ERROR found in {df}")
            return False


def save_stocks_to_s3(stock_objects: list, bucket: str, key: str, type: str = "csv"):
    """
    Take a list of Stock objects concatenate all dataframes from it and save it to pickle(or csv) in a s3 bucket
    # TODO Add more saving options
    """
    df = pd.concat([obj.df for obj in stock_objects])
    s3_resource = boto3.resource('s3')
    if type == "csv":
        key += ".csv"
        file_buffer = df.to_csv().encode("utf-8")
    else:
        key = key + ".pkl"
        pickle_buffer = io.BytesIO()
        df.to_pickle(pickle_buffer)
        pickle_buffer.seek(0)
        file_buffer = pickle_buffer.getvalue()
        pickle_buffer.close()

    file_stream = io.BytesIO(file_buffer)

    try:
        s3_resource.Object(bucket, key).put(Body=file_stream.getvalue())
        print(f"Saved file {key} to {bucket}")
    except Exception as e:
        print(f"ERROR: Failed to save {[stock.stock_name for stock in stock_objects]} {bucket}/{key} to s3: {e}")
    finally:
        file_stream.close()


# TODO: New computations, actually I'm looking for "Trend Strength Index"
"""
        - calculate_stochastic_oscillator: Calculate the stochastic oscillator indicator for the stock
        - calculate_williams_r: Calculate the williams r indicator for the stock
        - calculate_adx: Calculate the adx indicator for the stock
        - calculate_aroon: Calculate the aroon indicator for the stock
        - calculate_cci: Calculate the cci indicator for the stock
        - calculate_mfi: Calculate the mfi indicator for the stock
        - calculate_obv: Calculate the obv indicator for the stock
        - calculate_roc: Calculate the roc indicator for the stock
        - calculate_stdev: Calculate
        - calculate_stochastic: Calculate the stochastic indicator for the stock (defaults 14
        - calculate_bollinger_bands: Calculate the bollinger bands indicator for the stock

"""
