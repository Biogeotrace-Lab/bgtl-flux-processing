import sys
import click
import logging
import pandas as pd

from fluxy.io.csv import load_timeseries

from colorama import Fore
from colorama import Style


logger = logging.getLogger(__name__)

@click.command(name="log-diff",
               short_help="Highlight the differences between two log files.")
@click.argument("csv-like-file-1", nargs=1, required=True)
@click.argument("csv-like-file-2", nargs=1, required=True)
@click.option("--show-rows", type=int, required=False, default=100,
              help="Number of rows to print in detail.")
def main(csv_like_file_1: str, csv_like_file_2: str, show_rows: int):
    r"""Highlight the differences between two log files.

    Examine whether there are timestamps in one file that are missing the in other
    and vice versa.
    """
    pd.options.display.max_rows = show_rows

    dataframe_1 = load_timeseries(csv_like_file_1)
    dataframe_2 = load_timeseries(csv_like_file_2)

    _1vs2 = ~dataframe_1.index.isin(dataframe_2.index)
    _2vs1 = ~dataframe_2.index.isin(dataframe_1.index)

    logger.info(Fore.LIGHTRED_EX + f"Timestamps in {csv_like_file_1} "
                f"missing from {csv_like_file_2}\n"
                f"{dataframe_1[_1vs2]}")

    logger.info(Fore.LIGHTGREEN_EX + f"Timestamps in {csv_like_file_2} "
                f"missing from {csv_like_file_1}\n"
                f"{dataframe_2[_2vs1]}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
