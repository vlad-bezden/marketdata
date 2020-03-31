import asyncio
import argparse
import logging
import json
from urllib import request, parse
import pandas as pd
import configparser
from types import SimpleNamespace
from functools import partial

MARKET_API_URL = r"https://fmpcloud.io/api/v3/quote/{1}?apikey={0}"
CRYPTO_API_URL = r"https://fmpcloud.io/api/v3/quotes/crypto?apikey={0}"
FX_API_URL = r"https://openexchangerates.org/api/latest.json?app_id={0}"


def break_line():
    """Prints divide line"""

    print(f"{'=' * 54}\n")


def market_data(api_key, symbols):
    """Get market data for list of symbols"""

    # Get stock prices
    url = MARKET_API_URL.format(api_key, parse.quote(",".join(symbols)))

    with request.urlopen(url) as handle:
        results = json.loads(handle.read())

    # only get data that we need
    keys = ["symbol", "price", "change", "changesPercentage", "timestamp"]
    values = [[item[key] for key in keys] for item in results]
    keys[3] = "change %"

    df = pd.DataFrame(data=values, columns=keys).set_index("symbol")
    df.price = df.price.astype(float)
    df.change = df.change.astype(float)
    df.timestamp = pd.to_datetime(df.timestamp, unit="s")

    return df.round(2)


def crypto_data(api_key, cryptos):
    """Get crypto currencies data for list of cryptos"""

    url = CRYPTO_API_URL.format(api_key)

    with request.urlopen(url) as handle:
        results = [i for i in json.loads(handle.read()) if i["symbol"] in cryptos]

    # only get data that we need
    keys = ["symbol", "price", "change", "changesPercentage", "timestamp"]
    values = [[item[key] for key in keys] for item in results]
    keys[3] = "change %"

    df = pd.DataFrame(data=values, columns=keys).set_index("symbol")
    df.price = df.price.astype(float)
    df.change = df.change.astype(float)
    df.timestamp = pd.to_datetime(df.timestamp, unit="s")

    return df.round(2)


def exchange_rates(api_key, currencies):
    """Gets exchange rate for list of currencies"""

    url = FX_API_URL.format(api_key)

    with request.urlopen(url) as handle:
        results = json.loads(handle.read())

    from_ = results["base"]
    timestamp = results["timestamp"]
    values = [
        (from_, k, v, timestamp) for k, v in results["rates"].items() if k in currencies
    ]
    columns = ["From", "To", "Rate", "timestamp"]

    df = pd.DataFrame(data=values, columns=columns).set_index(["From", "To"])
    df.Rate = df.Rate.astype(float)
    df.timestamp = pd.to_datetime(df.timestamp, unit="s")

    return df.round(2)


async def runner(info_type, context):
    """Executes specific functions depends on the passed parameters"""

    loop = asyncio.get_running_loop()

    if info_type == "market":
        market_data_ = partial(market_data, context.fmp_api_key)

        results = [
            loop.run_in_executor(None, market_data_, i)
            for i in [context.indexes, context.symbols]
        ]

        for result in await asyncio.gather(*results):
            print(result)
            break_line()

    elif info_type == "fx":
        result1 = loop.run_in_executor(
            None, crypto_data, context.fmp_api_key, context.cryptos
        )
        result2 = loop.run_in_executor(
            None, exchange_rates, context.fx_api_key, context.currencies
        )

        for result in await asyncio.gather(result1, result2):
            print(result)
            break_line()

    elif info_type == "all":
        await asyncio.gather(runner("market", context), runner("fx", context))
    else:
        logging.error(
            "Invalid info_type %s. It must be 'market', 'fx' or 'all'", info_type
        )


def config_parser(config_file, env_file):
    """Loads configuration data from config file to the context object"""

    config = configparser.ConfigParser()
    config.read_file(config_file)
    config.read_file(env_file)
    market_sec = config["Market"]
    return SimpleNamespace(
        currencies=json.loads(market_sec["currencies"]),
        symbols=json.loads(market_sec["symbols"]),
        indexes=json.loads(market_sec["indexes"]),
        cryptos=json.loads(market_sec["cryptos"]),
        fx_api_key=market_sec["fx_api_key"],
        fmp_api_key=market_sec["fmp_api_key"],
    )


def parse_args():
    """Parses command line parameters"""

    parser = argparse.ArgumentParser(
        description="Provides market value for securities and exchange rates "
        "provided in configuration file"
    )
    parser.add_argument(
        "config_file",
        type=argparse.FileType("r", encoding="UTF-8"),
        help="Path to configuration file. "
        "Read more README.md document about structure of the file",
    )
    parser.add_argument(
        "env_file",
        type=argparse.FileType("r", encoding="UTF-8"),
        help="Path to .env file. "
        "Read more README.md document about structure of the file",
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
    """Called by __main__ and this function"""

    args = parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING, format="%(message)s"
    )
    logging.info("config file: %s, info: %s", args.config_file, args.info_type)

    config = config_parser(args.config_file, args.env_file)
    logging.info("Config: %s", config)

    # files handles are created by argparse. After we done we need to close them
    args.config_file.close()
    args.env_file.close()

    # run coroutine
    asyncio.run(runner(args.info_type, config))


if __name__ == "__main__":
    main()
