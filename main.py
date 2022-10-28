import yfinance as yf
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import time as tm
import datetime as dt
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from collections import deque
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout


stock = "GOOG"
date_now = tm.strftime("%Y-%m-%d")
date_3_years_back = (dt.date.today() - dt.timedelta(days=1104)).strftime("%Y-%m-%d")

init_df = yf.Ticker(stock).history(interval="1d", start=date_3_years_back, end=date_now)
init_df = init_df.drop(
    ["Open", "High", "Low", "Volume", "Dividends", "Stock Splits"], axis=1
)
init_df["Date"] = init_df.index
init_df["Date"] = init_df["Date"].dt.date
init_df.index = init_df["Date"]

# plt.style.use(style="ggplot")
# plt.figure(figsize=(16, 10))
# plt.plot(init_df["Close"][-200:])
# plt.xlabel("days")
# plt.ylabel("price")
# plt.legend([f"Actual price for {stock}"])
# plt.show()

scaler = MinMaxScaler()
init_df["Scaled_close"] = scaler.fit_transform(
    np.expand_dims(init_df["Close"].values, axis=1)
)

n_steps = 7


def prepare_data(days):
    df = init_df.copy()
    df["Future"] = df["Scaled_close"].shift(-days)
    last_sequence = np.array(df[["Scaled_close"]].tail(days))
    df.dropna(inplace=True)
    sequence_data = []
    sequences = deque(maxlen=n_steps)

    for entry, target in zip(
        df[["Scaled_close"] + ["Date"]].values, df["Future"].values
    ):
        sequences.append(entry)
        if len(sequences) == n_steps:
            sequence_data.append([np.array(sequences), target])

    last_sequence = list([s[: len(["Scaled_close"])] for s in sequences]) + list(
        last_sequence
    )
    last_sequence = np.array(last_sequence).astype(np.float32)

    X, Y = [], []
    for seq, target in sequence_data:
        X.append(seq)
        Y.append(target)

    X = np.array(X)
    Y = np.array(Y)

    return df, last_sequence, X, Y


def get_trained_model(x_train, y_train):
    model = Sequential()
    model.add(
        LSTM(60, return_sequences=True, input_shape=(n_steps, len(["Scaled_close"])))
    )
    model.add(Dropout(0.3))
    model.add(LSTM(120, return_sequences=False))
    model.add(Dropout(0.3))
    model.add(Dense(20))
    model.add(Dense(1))

    BATCH_SIZE = 8
    EPOCHS = 80

    model.compile(loss="mean_squared_error", optimizer="adam")

    model.fit(x_train, y_train, batch_size=BATCH_SIZE, epochs=EPOCHS, verbose="1")

    model.summary()

    return model


predictions = []
lookup_steps = [1, 2, 3]

for step in lookup_steps:
    df, last_sequence, x_train, y_train = prepare_data(step)
    x_train = x_train[:, :, : len(["Scaled_close"])].astype(np.float32)

    model = get_trained_model(x_train, y_train)

    last_sequence = last_sequence[-n_steps:]
    last_sequence = np.expand_dims(last_sequence, axis=0)
    prediction = model.predict(last_sequence)
    predicted_price = scaler.inverse_transform(prediction)[0][0]

    predictions.append(round(float(predicted_price), 2))

if bool(predictions) == True and len(predictions) > 0:
    predictions_list = [str(d) + "$" for d in predictions]
    predictions_str = ", ".join(predictions_list)
    message = f"{stock} prediction for upcoming 3 days ({predictions_str})"

    print(message)

copy_df = init_df.copy()
y_predicted = model.predict(x_train)  # type: ignore
y_predicted_transformed = np.squeeze(scaler.inverse_transform(y_predicted))
first_seq = scaler.inverse_transform(np.expand_dims(y_train[:6], axis=1))  # type: ignore
last_seq = scaler.inverse_transform(np.expand_dims(y_train[-3:], axis=1))  # type: ignore
y_predicted_transformed = np.append(first_seq, y_predicted_transformed)
y_predicted_transformed = np.append(y_predicted_transformed, last_seq)
copy_df[f"Predicted_close"] = y_predicted_transformed

date_now = dt.date.today()
date_tomorrow = dt.date.today() + dt.timedelta(days=1)
date_after_tomorrow = dt.date.today() + dt.timedelta(days=2)

copy_df.loc[date_now] = [predictions[0], f"{date_now}", 0, 0]
copy_df.loc[date_tomorrow] = [predictions[1], f"{date_tomorrow}", 0, 0]
copy_df.loc[date_after_tomorrow] = [predictions[2], f"{date_after_tomorrow}", 0, 0]

plt.style.use(style="ggplot")
plt.figure(figsize=(16, 10))
plt.plot(copy_df["Close"][-150:].head(147))
plt.plot(copy_df["Predicted_close"][-150:].head(147), linewidth=1, linestyle="dashed")
plt.plot(copy_df["Close"][-150:].tail(4))
plt.xlabel("days")
plt.ylabel("price")
plt.legend(
    [
        f"Actual price for {stock}",
        f"Predicted price for {stock}",
        f"Predicted price for future 3 days",
    ]
)
plt.show()
