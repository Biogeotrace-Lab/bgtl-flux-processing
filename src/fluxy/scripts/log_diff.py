import sys
import click
import logging
import pandas as pd

from fluxy.io.csv import load_timeseries


logger = logging.getLogger(__name__)

@click.command(name="log-diff",
               short_help="Highlight the differences between two log files.")
@click.argument("csv-like-file-1", nargs=1, required=True)
@click.argument("csv-like-file-2", nargs=1, required=True)
@click.option("--show-rows", type=int, required=False, default=1000,
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

    click.secho(f"{csv_like_file_1}++ Extra Timestamps\n"
                f"{dataframe_1[_1vs2]}", fg='bright_green')

    click.secho(f"{csv_like_file_1}-- Missing Timestamps\n"
                f"{dataframe_2[_2vs1]}", fg='bright_red') 

    return 0


if __name__ == '__main__':
    sys.exit(main())
