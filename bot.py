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
TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME")
TELEGRAM_BOT_ID = os.getenv("TELEGRAM_BOT_ID")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


def send_message(message):
    response = rq.post(
        f"{TELEGRAM_URL}/bot{TELEGRAM_BOT_ID}/sendMessage?chat_id={TELEGRAM_CHANNEL_ID}&parse_mode=Markdown&text={message}"
    )

    return response


screener_interval = "5m"
screener_period = "250m"


def check_stock(stock):
    data = {}
    try:
        df = yf.download(stock, period=screener_period, interval=screener_interval)
        if len(df) > 0:
            df["RSI"] = ta.rsi(df["Close"], timeperiod=14)
            bbands = ta.bbands(df["Close"], length=20, std=2.3)
            df["L"] = bbands["BBL_20_2.3"]  # type: ignore
            df["M"] = bbands["BBM_20_2.3"]  # type: ignore
            df["U"] = bbands["BBU_20_2.3"]  # type: ignore

            previous2_bar = df[-3:].head(1)
            previous_bar = df[-2:].head(1)
            current_bar = df[-1:]

            if (
                current_bar["RSI"].values[0] > 70
                and current_bar["Close"].values[0] > current_bar["U"].values[0]
            ):
                data = {
                    "direction": "DOWN",
                    "stock": stock,
                    "stop_loss": round(
                        max(
                            previous_bar["High"].values[0],
                            previous2_bar["High"].values[0],
                            previous_bar["U"].values[0],
                        ),
                        2,
                    ),
                    "take_profit": round(
                        min(
                            previous_bar["Low"].values[0],
                            previous2_bar["Low"].values[0],
                            previous_bar["M"].values[0],
                        ),
                        2,
                    ),
                }
            elif (
                current_bar["RSI"].values[0] < 30
                and current_bar["Close"].values[0] < current_bar["L"].values[0]
            ):
                data = {
                    "direction": "UP",
                    "stock": stock,
                    "stop_loss": round(
                        min(
                            previous_bar["Low"].values[0],
                            previous2_bar["Low"].values[0],
                            previous_bar["L"].values[0],
                        ),
                        2,
                    ),
                    "take_profit": round(
                        max(
                            previous_bar["High"].values[0],
                            previous2_bar["High"].values[0],
                            previous_bar["M"].values[0],
                        ),
                        2,
                    ),
                }
    except Exception as e:
        print(e)

    return data


screener_count = 500
take_profit_delta = 0.01


def screen_stocks(trader_api):
    assets = trader_api.list_assets(status="active", asset_class="us_equity")
    assets = [x for x in assets if x.shortable == True and x.exchange == "NASDAQ"]
    stocks = [x.symbol for x in assets][:screener_count]

    screened = []

    for st in stocks:
        _stock = check_stock(st)
        if _stock != {}:
            screened.append(_stock)

    screened = [
        x
        for x in screened
        if abs(x["stop_loss"] - x["take_profit"])
        > min(x["stop_loss"], x["take_profit"]) * take_profit_delta
    ]

    return screened


def trade(api, stock, operation, shares_to_trade, take_profit, stop_loss):
    api.submit_order(
        symbol=stock,
        qty=shares_to_trade,
        side=operation,
        type="market",
        order_class="bracket",
        time_in_force="day",
        take_profit={"limit_price": take_profit},
        stop_loss={"stop_price": stop_loss},
    )
    message = f"\n\t*{stock}*, qty _{shares_to_trade}_ \n\t\twere {operation}"
    send_message(f"{TELEGRAM_BOT_NAME}: we entered the market with:" + message)
    return True


cash_limit = 26000


def predict(stock):
    predictions = [100.24, 155.33, 140.55]
    return predictions


def activate_trader(request):
    trader_api = alpaca.REST(ALPACA_KEY_ID, ALPACA_SECRET_KEY, PAPER_TRADING_URL)  # type: ignore
    account = trader_api.get_account()
    clock = trader_api.get_clock()

    if bool(account) == True:
        message = f"""{TELEGRAM_BOT_NAME}: for *{account.account_number}*
    current capital is _{account.portfolio_value}$_ 
    and non marginable buying power is _{account.non_marginable_buying_power}$_"""
        send_message(message)

    if clock.is_open == True:
        if float(account.non_marginable_buying_power) < cash_limit:  # type: ignore
            message = f"{TELEGRAM_BOT_NAME}: there is no cash on the account or limit reached!"
            send_message(message)
        else:
            screened = screen_stocks(trader_api)
            if len(screened) > 0:
                CASH_FOR_TRADE_PER_SHARE = (
                    float(account.non_marginable_buying_power) - cash_limit  # type: ignore
                ) / len(screened)

                for item in screened:
                    predictions = predict(item["stock"])
                    STOCK = item["stock"]
                    OPERATION = "buy" if item["direction"] == "UP" else "sell"
                    STOP_LOSS = (
                        min([item["stop_loss"]] + predictions)
                        if item["direction"] == "UP"
                        else max([item["stop_loss"]] + predictions)
                    )
                    TAKE_PROFIT = (
                        max([item["take_profit"]] + predictions)
                        if item["direction"] == "UP"
                        else min([item["take_profit"]] + predictions)
                    )
                    SHARE_PRICE = round(min(STOP_LOSS, TAKE_PROFIT), 2)
                    SHARES_TO_TRADE = int(CASH_FOR_TRADE_PER_SHARE / SHARE_PRICE)

                    try:
                        if (
                            abs(STOP_LOSS - TAKE_PROFIT)
                            > SHARE_PRICE * take_profit_delta
                            and SHARES_TO_TRADE > 0
                        ):
                            trade(
                                alpaca,
                                STOCK,
                                OPERATION,
                                SHARES_TO_TRADE,
                                TAKE_PROFIT,
                                STOP_LOSS,
                            )
                            print(
                                f"\n{STOCK}: {STOP_LOSS}, {TAKE_PROFIT}, {OPERATION}, {SHARES_TO_TRADE}"
                            )
                    except Exception as e:
                        print(e)

    portfolio = trader_api.list_positions()

    if bool(portfolio) == True:
        message = f"{TELEGRAM_BOT_NAME}: we have {len(portfolio)} opened positions."
        for i in portfolio:
            message = (
                message
                + f"\n\t*{i.symbol}*: qty {i.qty} {i.side} for _{i.market_value}$_ \n\t\t\tcurrent price _{i.current_price}$_ \n\t\t\tprofit _{i.unrealized_pl}$_"
            )
        send_message(message)

    if clock.is_open == False:
        message = f"{TELEGRAM_BOT_NAME}: the market is *CLOSED*, let's try later on!"
        send_message(message)

    return f"{TELEGRAM_BOT_NAME}: DONE!"
