"""
__main__ is required if it's called as a package

>>> python -m marketdata

or

>>> marketdata
"""

import marketdata.main as marketdata


def main():
    marketdata.main()


if __name__ == "__main__":
    main()
