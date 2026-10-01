import sys
import click
import logging
import pandas as pd

from ..io.csv import load_timeseries
from ..utils.checks import ComparisonReport

logger = logging.getLogger(__name__)

@click.command(name="compare",
               short_help="Compare two log files for differences.")
@click.argument("csv-like-file", nargs=1, required=True,
                metavar="CSV_FILE", type=click.Path(exists=True))
@click.option("-r", "--reference", nargs=1, required=True,
              metavar="REFERECE_CSV_FILE", type=click.Path(exists=True))
@click.option("--show-rows", type=int, required=False, default=1000,
              help="Number of rows to print in detail.")
def main(csv_like_file: str, reference: str, show_rows: int):
    r"""Compare two log files for differences.
    """
    pd.options.display.max_rows = show_rows

    dataframe_1 = load_timeseries(csv_like_file)
    reference_dataframe = load_timeseries(reference)

    _1vs2_rows = ~dataframe_1.index.isin(reference_dataframe.index)
    _2vs1_rows = ~reference_dataframe.index.isin(dataframe_1.index)
    _1vs2_cols = ~dataframe_1.columns.isin(reference_dataframe.columns)
    _2vs1_cols = ~reference_dataframe.columns.isin(dataframe_1.columns)

    CR = ComparisonReport(candidates=[csv_like_file, reference],
                          columns=["Comparisons", "Results"])

    CR.add_comparison(f"{csv_like_file} ++Extra Timestamps",
                      f"{dataframe_1.index[_1vs2_rows].to_frame() if any(_1vs2_rows) else []}",
                      style="bright_green" if any(_1vs2_rows) else None)
    CR.add_comparison(f"{csv_like_file} --Missing Timestamps",
                      f"{reference_dataframe.index[_2vs1_rows] if any(_2vs1_rows) else []}",
                      style="bright_red" if any(_2vs1_rows) else None)
    CR.add_comparison(f"{csv_like_file} ++Extra Columns",
                      f"{dataframe_1.columns[_1vs2_cols].tolist()}",
                      style="bright_green" if any(_1vs2_cols) else None)
    CR.add_comparison(f"{csv_like_file} --Missing Columns",
                      f"{reference_dataframe.columns[_2vs1_cols].tolist()}",
                      style="bright_red" if any(_2vs1_cols) else None)
    CR.report()
    sys.exit(1)


if __name__ == '__main__':
    main()
