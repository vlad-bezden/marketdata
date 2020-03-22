## Market data (marketdata) application
An example application on how to get market data and foreign exchange (FX) from https://www.alphavantage.co/
Alphavantage free account limits 5 requests to be made per minute.

It also provides examples on how to use:
- pandas
- configparser
- urllib
- logging
- json

The biggest reason for using pandas is it provides out of the box nice console output.

It also provides example on how to use __main__ and setup.py files to use command prompt to run application

## Usage
After application installed you can run it by:

```
marketdata path\to\config.ini file
```
or

```
python -m marketdata C:\config.ini
```

### Config file structure
```
[Market]
api_key="Your API key"
currencies = ["BTC USD", "USD UAH", "USD RUB"]
symbols = ["DJIA", "INX", "MSFT", "AMZN", "GOOG", "TSLA", "LM", "AAPL"]
```

Currencies are space separated 'From' 'To'

## Build
python setup.py bdist_wheel

Install:
Copy xxx.whl files from dist directory and run

```
pip install xxx.whl
```
