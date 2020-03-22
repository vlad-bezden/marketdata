import argparse
import logging
import json
from urllib import request
import pandas as pd
import time
import configparser
from types import SimpleNamespace


MARKET_API_URL = (
    r"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={1}&apikey={0}"
)
FX_API_URL = (
    r"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&"
    "from_currency={1}&to_currency={2}&apikey={0}"
)

api_key = ""


def get_json_data(url, params):
    results = []
    for i, param in enumerate(params):
        url_path = url.format(api_key, *param.split())
        handle = request.urlopen(url_path)
        results.append(json.loads(handle.read()))
        logging.info("Loaded data for '%s'", param)
        if (i + 1) % 5 == 0:
            logging.info("Reached limit 5 requests per minutes. Pausing for 1 minute")
            time.sleep(60)
    return results


def market_data(symbols):
    """Get market data for list of symbols."""
    # Get market and stock prices
    data = get_json_data(MARKET_API_URL, symbols)
    data = [i["Global Quote"].values() for i in data]
    # remove open, high, low volume and prev.close columns
    values = [[v for i, v in enumerate(_) if i in {0, 4, 6, 8, 9}] for _ in data]
    columns = ["symbol", "price", "latest trade day", "change", "change %"]
    df = pd.DataFrame(data=values, columns=columns).set_index("symbol")
    df.price = df.price.astype(float)
    df.change = df.change.astype(float)
    df = df.round(2)
    return df


def exchange_rates(currencies):
    """Gets exchange rate for list of currencies."""
    data = get_json_data(FX_API_URL, currencies)
    data = [i["Realtime Currency Exchange Rate"].values() for i in data]
    values = [[v for i, v in enumerate(_) if i in {0, 2, 4, 5}] for _ in data]
    columns = ["From", "To", "Rate", "Last Refreshed (UTC)"]
    df = pd.DataFrame(data=values, columns=columns).set_index(["From", "To"])
    df.Rate = df.Rate.astype(float)
    return df


def runner(info_type, config):
    symbols = config.symbols
    currencies = config.currencies
    if info_type == "market":
        data = market_data(symbols)
        print(data)
    elif info_type == "fx":
        data = exchange_rates(currencies)
        print(data)
    elif info_type == "all":
        runner("fx", config)
        time.sleep(60)
        print()
        runner("market", config)
    else:
        logging.error(
            "Invalid info_type %s. It must be 'market', 'fx' or 'all'", info_type
        )


def config_parser(file):
    config = configparser.ConfigParser()
    config.read(file)
    market_sec = config["Market"]
    return SimpleNamespace(
        api_key=market_sec["api_key"],
        currencies=json.loads(market_sec["currencies"]),
        symbols=json.loads(market_sec["symbols"]),
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Provides market value for securities and exchange rates "
        "provided in configuration file"
    )
    parser.add_argument(
        "config_file",
        help="Path to configuration file with keys CURRENCIES and SYMBOLS",
    )
    parser.add_argument(
        "-i",
        "--info_type",
        help="Market information",
        choices=["market", "fx", "all"],
        default="all",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )

    return parser.parse_args()


def main():
    global api_key
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING, format="%(message)s"
    )
    logging.debug("config file: %s, info: %s", args.config_file, args.info_type)
    config = config_parser(args.config_file)
    logging.debug("Config: %s", config)
    api_key = config.api_key
    runner(args.info_type, config)


if __name__ == "__main__":
    main()
