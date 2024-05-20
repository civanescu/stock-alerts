from io import StringIO

import pandas as pd
import requests

from stock_alerts.models.stock_requests.stooq import download_stooq


def test_successful_data_download(mocker):
    mocker.patch('requests.get')
    response_mock = mocker.MagicMock()
    response_mock.raise_for_status.return_value = None
    response_mock.text = "date,open,high,low,close,volume\n2023-01-01,100,110,90,105,10000"
    requests.get.return_value = response_mock
    result = download_stooq('AAPL')
    expected_df = pd.read_csv(StringIO("date,open,high,low,close,volume\n2023-01-01,100,110,90,105,10000"))
    pd.testing.assert_frame_equal(result, expected_df)


def test_non_existent_stock_symbol(mocker):
    mocker.patch('requests.get')
    response_mock = mocker.MagicMock()
    response_mock.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found for url")
    requests.get.return_value = response_mock
    result = download_stooq('FAKESTOCK')
    assert result is None
    print("HTTP error occurred: 404 Client Error: Not Found for url")
