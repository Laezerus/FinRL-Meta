from finrl_meta.data_processors.processor_alpaca import AlpacaProcessor
from finrl_meta.data_processors.processor_baostock import BaostockProcessor
from finrl_meta.data_processors.processor_wrds import WrdsProcessor
from finrl_meta.data_processors.processor_binance import BinanceProcessor
from finrl_meta.data_processors.processor_iexcloud import IexcloudProcessor
from finrl_meta.data_processors.processor_joinquant import JoinquantProcessor
from finrl_meta.data_processors.processor_quandl import QuandlProcessor
from finrl_meta.data_processors.processor_quantconnect import QuantconnectProcessor
from finrl_meta.data_processors.processor_ricequant import RicequantProcessor
from finrl_meta.data_processors.processor_tushare import TushareProcessor
from finrl_meta.data_processors.processor_yahoofinance import YahoofinanceProcessor
import pandas as pd
import numpy as np
import os
import pickle
from typing import List
class DataProcessor():
    def processor_None(self):
        print("Not support for {self.data_source}")

    def __init__(self, data_source: str, start_date: str, end_date: str, time_interval: str, **kwargs):
        self.data_source = data_source
        self.start_date = start_date
        self.end_date = end_date
        self.time_interval = time_interval
        self.dataframe = pd.DataFrame()
        processor_dict = {
            "alpaca": AlpacaProcessor,
            "binance": BinanceProcessor,
            "baostock": BaostockProcessor,
            "iexcloud": IexcloudProcessor,
            "joinquant": JoinquantProcessor,
            "quandl":  QuandlProcessor,
            "quantconnect":  QuantconnectProcessor,
            "ricequant":  RicequantProcessor,
            "tushare": TushareProcessor,
            "wrds":  WrdsProcessor,
            "yahoofinance":  YahoofinanceProcessor,
        }

        try:
            self.processor = processor_dict.get(self.data_source, self.processor_None())(data_source, start_date, end_date, time_interval, **kwargs)
            print(f'{self.data_source} successfully connected')
        except:
            raise ValueError(f'Please input correct account info for {self.data_source}!')


    def download_data(self, ticker_list):
        self.processor.download_data(ticker_list=ticker_list)
        self.dataframe = self.processor.dataframe


    def clean_data(self):
        self.processor.dataframe = self.dataframe
        self.processor.clean_data()
        self.dataframe = self.processor.dataframe

    def add_technical_indicator(self, tech_indicator_list: List[str], select_stockstats_talib: int = 0):
        self.tech_indicator_list = tech_indicator_list
        self.processor.add_technical_indicator(tech_indicator_list, select_stockstats_talib)
        self.dataframe = self.processor.dataframe

    def add_turbulence(self):
        self.processor.add_turbulence()
        self.dataframe = self.processor.dataframe

    def add_vix(self):
        self.processor.add_vix()
        self.dataframe = self.processor.dataframe

    def df_to_array(self, if_vix: bool) -> np.array:
        price_array, tech_array, turbulence_array = self.processor.df_to_array(self.tech_indicator_list, if_vix)
        # fill nan with 0 for technical indicators
        tech_nan_positions = np.isnan(tech_array)
        tech_array[tech_nan_positions] = 0

        return price_array, tech_array, turbulence_array

    def run(self, ticker_list: str, technical_indicator_list: List[str], if_vix: bool, cache: bool = False, select_stockstats_talib: int = 0):

        if self.time_interval == "1s" and self.data_source != "binance":
            raise ValueError("Currently 1s interval data is only supported with 'binance' as data source")

        cache_filename = '_'.join(ticker_list + [self.data_source, self.start_date, self.end_date, self.time_interval]) + '.pickle'
        cache_dir = './cache'
        cache_path = os.path.join(cache_dir, cache_filename)

        if cache and os.path.isfile(cache_path):
            print(f'Using cached file {cache_path}')
            self.tech_indicator_list = technical_indicator_list
            with open(cache_path, 'rb') as handle:
                self.processor.dataframe = pickle.load(handle)
        else:
            self.download_data(ticker_list)
            self.clean_data()
            if cache:
                if not os.path.exists(cache_dir):
                    os.mkdir(cache_dir)
                with open(cache_path, 'wb') as handle:
                    pickle.dump(self.dataframe, handle, protocol=pickle.HIGHEST_PROTOCOL)


        self.add_technical_indicator(technical_indicator_list, select_stockstats_talib)
        if if_vix:
            self.add_vix()
        price_array, tech_array, turbulence_array = self.df_to_array(if_vix)
        tech_nan_positions = np.isnan(tech_array)
        tech_array[tech_nan_positions] = 0

        return price_array, tech_array, turbulence_array


def test_joinquant():
    # TRADE_START_DATE = "2019-09-01"
    TRADE_START_DATE = "2020-09-01"
    TRADE_END_DATE = "2021-09-11"

    # supported time interval: '1m', '5m', '15m', '30m', '60m', '120m', '1d', '1w', '1M'
    TIME_INTERVAL = '1d'
    TECHNICAL_INDICATOR = ['macd', 'boll_ub', 'boll_lb', 'rsi_30', 'dx_30', 'close_30_sma', 'close_60_sma']

    kwargs = {'username': 'xxx', 'password': 'xxx'}
    p = DataProcessor(data_source='joinquant', start_date=TRADE_START_DATE, end_date=TRADE_END_DATE, time_interval=TIME_INTERVAL, **kwargs)

    ticker_list = ["000612.XSHE", "601808.XSHG"]

    p.download_data(ticker_list=ticker_list)

    p.clean_data()
    p.add_turbulence()
    p.add_technical_indicator(TECHNICAL_INDICATOR)
    p.add_vix()

    price_array, tech_array, turbulence_array = p.run(ticker_list, TECHNICAL_INDICATOR, if_vix=False, cache=True)
    pass

def test_binance():
    ticker_list = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT']
    start_date = '2021-09-01'
    end_date = '2021-09-20'
    time_interval = '5m'

    dp = DataProcessor('binance', start_date, end_date, time_interval)
    technical_indicator_list = ['macd', 'rsi', 'cci', 'dx']  # self-defined technical indicator list is NOT supported yet
    if_vix = False
    price_array, tech_array, turbulence_array = dp.run(ticker_list, technical_indicator_list, if_vix, cache=True, select_stockstats_talib=1)
    print(price_array.shape, tech_array.shape)

def test_yfinance():

    start_date = '2021-01-01'
    end_date = '2021-09-20'
    time_interval = '1D'

    dp = DataProcessor('yahoofinance', start_date, end_date, time_interval)
    ticker_list = [
        "MTX.DE",
        "MRK.DE",
        "LIN.DE",
        "ALV.DE",
        "VNA.DE",
    ]

    technical_indicator_list = ['macd', 'rsi', 'cci', 'dx']  # self-defined technical indicator list is NOT supported yet
    if_vix = False
    price_array, tech_array, turbulence_array = dp.run(ticker_list, technical_indicator_list, if_vix, cache=True, select_stockstats_talib=1)
    print(price_array.shape, tech_array.shape)

def test_baostock():
    TRADE_START_DATE = "2020-09-01"
    TRADE_END_DATE = "2021-09-11"

    TIME_INTERVAL = 'd'
    TECHNICAL_INDICATOR = ['macd', 'boll_ub', 'boll_lb', 'rsi_30', 'dx_30', 'close_30_sma', 'close_60_sma']
    kwargs = {}
    p = DataProcessor(data_source='baostock', start_date=TRADE_START_DATE, end_date=TRADE_END_DATE, time_interval=TIME_INTERVAL, **kwargs)

    ticker_list = ["600000.XSHG"]

    p.download_data(ticker_list=ticker_list)

    p.clean_data()
    p.add_turbulence()
    p.add_technical_indicator(TECHNICAL_INDICATOR)
    p.add_vix()

    price_array, tech_array, turbulence_array = p.run(ticker_list, TECHNICAL_INDICATOR, if_vix=False, cache=True)
    pass

def test_quandl():
    TRADE_START_DATE = "2020-09-01"
    TRADE_END_DATE = "2021-09-11"

    TIME_INTERVAL = '1d'
    TECHNICAL_INDICATOR = ['macd', 'boll_ub', 'boll_lb', 'rsi_30', 'dx_30', 'close_30_sma', 'close_60_sma']
    kwargs = {}
    p = DataProcessor(data_source='quandl', start_date=TRADE_START_DATE, end_date=TRADE_END_DATE, time_interval=TIME_INTERVAL, **kwargs)

    ticker_list = ['AAPL', 'MSFT']

    p.download_data(ticker_list=ticker_list)

    p.clean_data()
    p.add_turbulence()
    p.add_technical_indicator(TECHNICAL_INDICATOR)
    p.add_vix()

    price_array, tech_array, turbulence_array = p.run(ticker_list, TECHNICAL_INDICATOR, if_vix=False, cache=True)
    pass

if __name__ == "__main__":
    # test_joinquant()
    # test_binance()
    # test_yfinance()
    # test_baostock()
    # test_quandl()
    # test_quandl()
    test_quandl()