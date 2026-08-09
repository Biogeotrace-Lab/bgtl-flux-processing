import sys
import click
import os
import zipfile

from pathlib import Path
from glob import glob

from ..io.csv import load_timeseries
import pandas as pd

@click.command(name="add-pressure",
               short_help="Add L1 flux pressure measurements to a meteorology file.")
@click.argument("met-csv", metavar="MET_CSV_FILE", required=True,
                type=click.Path(exists=True))
@click.option("--L0-flux-folder", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The folder for the L0 flux data to extract pressure " \
              "values from.")
@click.option("--column-index", "-c",
              type=int, required=True,
              help="The 0-index of the pressure column in the flux timeseries.")
@click.option("--pattern", "-p",
              type=str, required=True,
              help="The glob pattern for matching folder files. Use ** for "
              "multilevel globbing. Always wrap in single quotes ''. "
              "(e.g. '**/LicorGHG_slow/**/*.dat')")
def main(met_csv, l1_flux_folder, column_index, pattern):
    """Add L1 flux pressure measurements to a meteorology file."""
    met_dataframe = load_timeseries(met_csv)
    l1_flux_files = glob(os.path.join(l1_flux_folder, pattern),
                         recursive=True)
    print(l1_flux_files[-1])

    df = load_timeseries(l1_flux_files[-30], header=None, index_col=None)
    print(df, df.dtypes)

    sys.exit(0)


if __name__ == '__main__':
    main()
