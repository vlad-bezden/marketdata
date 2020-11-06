## Market data (marketdata) application
An example application on how to get foreign exchange (FX) from
https://openexchangerates.org and market data from https://fmpcloud.io

All data loads are done via asyncio and executed on separate threads

It also provides examples on how to use:
- pandas
- configparser
- urllib
- logging
- json
- print pandas in a nice tabulated format

It also provides example on how to use __main__ and setup.py files to use command prompt to run application

## Installation

```
pip install -r requirements.txt
```

## Usage
After application installed you can run it by:

```
marketdata path\to\config.ini path\to\.env -i ALL
```
By default all market data and foreign exchange will be return
```
marketdata path\to\config.ini path\to\.env
```
or

```
python -m marketdata path\to\config.ini path\to\.env
```

### Valid Flags for info_type
By default marketdata return both market data as well as foreign exchange information
That can be changed by passing different values for -i

#### -i values
* FX - foreign exchange
* MARKET - market information
* ALL - Both market and foreign exchange (default value)

### Config file structure
```
[Market]
currencies = ["UAH", "RUB"]
symbols = ["MSFT", "AMZN", "GOOG", "TSLA", "LM", "AAPL"]
indexes = ["^DJI", "^GSPC"]
cryptos = ["BTCUSD", "ETHUSD"]
```

### .env file structure
```
[Market]
fmp_api_key = your_api_key
fx_api_key = your_api_key
```

Currencies are space separated 'From' 'To'

## Build
python setup.py bdist_wheel

Install:
Copy xxx.whl files from dist directory and run

```
pip install xxx.whl
```
