import asyncio
import argparse
import logging
import json
from urllib import request, parse
import pandas as pd
import configparser
from types import SimpleNamespace
from enum import IntFlag


class InfoType(IntFlag):
    FX = 1
    MARKET = 2
    ALL = 3

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_string(s):
        try:
            return InfoType[s.upper()]
        except KeyError:
            return s


class Market:
    MARKET_API_URL = r"https://fmpcloud.io/api/v3/quote/{1}?apikey={0}"
    CRYPTO_API_URL = r"https://fmpcloud.io/api/v3/quotes/crypto?apikey={0}"
    FX_API_URL = r"https://openexchangerates.org/api/latest.json?app_id={0}"

    def __init__(self, context, info_type: InfoType):
        self._context = context
        self._info_type = info_type
        self._fmp_api_key = context.fmp_api_key
        self._fx_api_key = context.fx_api_key

    def _market_data(self, symbols):
        """Get market data for list of symbols"""
        # Get stock prices
        url = self.MARKET_API_URL.format(
            self._fmp_api_key, parse.quote(",".join(symbols))
        )

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

    def _crypto_data(self):
        """Get crypto currencies data for list of cryptos"""
        url = self.CRYPTO_API_URL.format(self._fmp_api_key)

        with request.urlopen(url) as handle:
            results = [
                i
                for i in json.loads(handle.read())
                if i["symbol"] in self._context.cryptos
            ]

        # only get data that we need
        keys = ["symbol", "price", "change", "changesPercentage", "timestamp"]
        values = [[item[key] for key in keys] for item in results]
        keys[3] = "change %"

        df = pd.DataFrame(data=values, columns=keys).set_index("symbol")
        df.price = df.price.astype(float)
        df.change = df.change.astype(float)
        df.timestamp = pd.to_datetime(df.timestamp, unit="s")

        return df.round(2)

    def _exchange_rates(self):
        """Gets exchange rate for list of currencies"""
        url = self.FX_API_URL.format(self._fx_api_key)

        with request.urlopen(url) as handle:
            results = json.loads(handle.read())

        from_ = results["base"]
        timestamp = results["timestamp"]
        values = [
            (from_, k, v, timestamp)
            for k, v in results["rates"].items()
            if k in self._context.currencies
        ]
        columns = ["From", "To", "Rate", "timestamp"]

        df = pd.DataFrame(data=values, columns=columns).set_index(["From", "To"])
        df.Rate = df.Rate.astype(float)
        df.timestamp = pd.to_datetime(df.timestamp, unit="s")

        return df.round(2)

    def run(self):
        """Executes specific functions depends on the passed parameters"""

        async def inner():
            loop = asyncio.get_running_loop()

            info_type = self._info_type
            results = []

            if info_type & InfoType.MARKET:
                results.append(
                    loop.run_in_executor(None, self._market_data, self._context.indexes)
                )
                results.append(
                    loop.run_in_executor(None, self._market_data, self._context.symbols)
                )

            if info_type & InfoType.FX:
                results.append(loop.run_in_executor(None, self._crypto_data))
                results.append(loop.run_in_executor(None, self._exchange_rates))

            for df in await asyncio.gather(*results):
                print(df.to_markdown(tablefmt="psql", numalign="right"))

        asyncio.run(inner())


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
        type=InfoType.from_string,
        help="Market information",
        choices=list(InfoType),
        default=InfoType.ALL,
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )

    return parser.parse_args()


def main():
    """Called by __main__ and this module"""
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
    Market(config, args.info_type).run()


if __name__ == "__main__":
    main()
