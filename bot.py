import os
import requests as rq
import alpaca_trade_api as alpaca
import yfinance as yf
import pandas_ta as ta
from dotenv import load_dotenv

load_dotenv()

PAPER_TRADING_URL = os.getenv("PAPER_TRADING_URL")
ALPACA_KEY_ID = os.getenv("ALPACA_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
TELEGRAM_URL = os.getenv("TELEGRAM_URL")
TELEGRAM_BOT_ID = os.getenv("TELEGRAM_BOT_ID")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

screener_interval = "5m"
screener_period = "250m"
screener_count = 500
take_profit_delta = 0.01
cash_limit = 26000


def send_message(message):
    response = rq.post(
        f"{TELEGRAM_URL}/bot{TELEGRAM_BOT_ID}/sendMessage?chat_id={TELEGRAM_CHANNEL_ID}&parse_mode=Markdown&text={message}"
    )

    return response


res = send_message("As super kietas")
print(res.content)
