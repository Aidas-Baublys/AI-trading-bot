import os
import yfinance as yf
import pandas as pd
from matplotlib import pyplot as plt
from dotenv import load_dotenv
import alpaca_trade_api as alpaca
import numpy as np
import time as tm
import datetime as dt
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from collections import deque
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout


load_dotenv()

# PAPER_TRADING_URL = os.getenv("PAPER_TRADING_URL")
# ALPACA_KEY_ID = os.getenv("ALPACA_KEY_ID")
# ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# Window size or the sequence length, 7 (1 week)
# N_STEPS = 7

lookuo_steps = [1, 2, 3]

stock = "GOOG"

date_now = tm.strftime("%Y-%m-%d")
date_3_years_back = (dt.date.today() - dt.timedelta(days=1104)).strftime("%Y-%m-%d")

init_df = yf.Ticker(stock).history(interval="1d", start=date_3_years_back, end=date_now)

init_df = init_df.drop(
    ["Open", "High", "Low", "Volume", "Dividends", "Stock Splits"], axis=1
)
init_df["Date"] = init_df.index


# plt.style.use(style="ggplot")
# plt.figure(figsize=(16, 10))
# plt.plot(init_df["Close"][-200:])
# plt.xlabel("days")
# plt.ylabel("price")
# plt.legend([f"Actual price for {stock}"])
# plt.show()

scaler = MinMaxScaler()
init_df["Close"] = scaler.fit_transform(np.expand_dims(init_df["close"].values, axis=1))

print(init_df)
