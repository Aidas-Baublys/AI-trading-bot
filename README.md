# AI-trading-bot

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/Aidas-Baublys/AI-trading-bot/blob/master/LICENSE.md)

<!-- TOC -->
* [AI-trading-bot](#AI-trading-bot)
  * [About](#about)
    * [Usage](#usage)
      * [Screener](#screener)
      * [Oracle](#oracle)
      * [Trader](#trader)
      * [GCP](#gcp)
    * [Conclusion](#conclusion)
<!-- TOC -->

## About

My very first trading bot! Let the money-burning begin! This is not investment advice. Use at your own risk.

Currently, it is trading in a paper account on Alpaca Markets, which is more a test of the overall concept (automated day trading using AI with basic technical analysis) than proof of any trading strategy. 

Alpaca markets were chosen for their superb API, real market data for paper accounts, and low to no trading costs.

If you want to try it on your own, be sure to test it extensively with fake money and fully understand what the code does.

### Usage

The project is split into 3 notebooks and hosted on Google Cloud Platform (GCP). 

#### Screener

Gets around 500 individual stock info and applies two technical indicators - Bolinger Bands and RSI. These indicators help guess the potential general movement of a stock, up or down. In essence, this part helps increase AI model accuracy by providing 3 stocks that meet certain favorable conditions. This also saves time and computing power, because the current project's size and resources could not predict the price of 500 stocks.

#### Oracle

Takes the 3 screened stocks and applies an LSTM AI model to predict the closing stock price for the upcoming 3 days. This part implements a basic model for time series data prediction.

Model architecture:
  - Define a Sequential model which consists of a linear stack of layers.
  - LSTM layer by giving it 60 network units. Set the return_sequence to true so that the output of the layer will be another sequence of the same length.
  - 30% dropout layer.
  - Another LSTM layer with 120 network units. But we set the return_sequence to false this time to only return the last output in the sequence.
  - Another 30% dropout layer.
  - Densely connected neural network layer with 20 network units.
  - Finally, a densely connected layer specifies the output of 1 network unit.

Mean squared error is used for loss and adam optimizer functions. These parameters were the result of blind, unmotivated guessing experiments and proved to be the most accurate for the time being.

#### Trader

The bot itself. Takes the screened stocks from the screener and predictions from the oracle and does the trading with simple stop losses set as a safeguard from unexpected price changes. Looks more difficult than actually is. If stock is moving up, the trader buys, if down, shorts, if the market is closed, it does not trade, also no trading if insufficient funds, etc.  

#### GCP

GCP was chosen both out of curiosity, the high quality of their services, and low to no operating costs. Only a few services are needed to launch and operate the bot. 

Cloud functions host the separate tree code parts with the relevant requirements and environment variables. 5 cloud schedulers run the cloud functions at set times. Due to the expensive nature and long duration of AI operations, the oracle part needs 3 separate launch times to apply the model to all screened stocks, so it has 3 schedulers.

Publisher/subscriber services help the 3 code parts communicate asynchronously. There are 2 topics - oracle and screener. The screener function publishes the screened stocks to the screener topic. Oracle function reads the screener topic and publishes predictions to the oracle topic. Trader reads both topics and trades.


### Conclusion

The biggest obstacle was the comparatively low-level implementation of the bot. The actions are simple but need a lot of nitty-gritty coding. The AI part was surprisingly easy to accomplish, thanks to the wonderful APIs and their ease of use. Deploying to the cloud was also straightforward.

My experience showed that it is possible and not that hard to successfully launch a trading bot, but, ironically, predicting stock price is far from an automated process. For now, the bot is trading at a loss. The strategy and technical indicators need constant human monitoring and continuous adjustment to be profitable, which in turn requires professional knowledge and dedication.

The very idea of an LSTM model predicting future time series data with past data is contrary to market dogma - past price and performance do not indicate future price and performance. I would even go so far as to call TA at best an overly complicated educated guess

And of course, even with perfect prediction, there is the question of capital - earning an annual 10% return on 100$ will not make you a millionaire.

