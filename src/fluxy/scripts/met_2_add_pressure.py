import sys
import click
import os
import pandas as pd

from pathlib import Path
from glob import glob
from tqdm import tqdm

from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_inplace_modification

from concurrent.futures import ProcessPoolExecutor


@click.command(name="add-pressure",
               short_help="""Add L0 flux pressure measurements from a smart-flux
               system to a meteorology file.""")
@click.option("-m", "--metfile", "met_csv",
              metavar="MET_CSV_FILE", required=True,
              type=click.Path(exists=True))
@click.option("-L0", "--L0-flux-folder", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The folder for the L0 flux data to extract pressure " \
              "values from.")
@click.option("--column", "-c", "pressure_column",
              type=str, required=False,
              help="The pressure column in the target files.",
              default="P_li77", show_default=True)
@click.option("--search-pattern", "-p",
              type=str, required=True,
              help="The glob pattern for matching folder files. Use ** for "
              "multilevel globbing. Always wrap in single quotes ''.",
              default="**/30m/**/*.csv",
              show_default=True)
def main(met_csv, l0_flux_folder, search_pattern, pressure_column):
    """Add L1 flux pressure measurements to a meteorology file."""
    met_dataframe = load_timeseries(met_csv)
    full_search_pattern = os.path.join(l0_flux_folder, search_pattern)
    l0_averaged_flux_files = glob(full_search_pattern, recursive=True)

    if not l0_averaged_flux_files:
        click.echo(f"No pressure files were found with "
                   f"the pattern {search_pattern}.")
        raise click.Abort()

    # Pressure gathering container.
    pressure_dataframes = []

    with ProcessPoolExecutor(4) as executor:
        processes = executor.map(extract_pressure,
                                 l0_averaged_flux_files,
                                 [pressure_column] *
                                 len(l0_averaged_flux_files))

        for result in tqdm(processes, total=len(l0_averaged_flux_files),
                            desc=f"Extracting {pressure_column} data...",
                            unit="csv"):
            pressure_dataframes.append(result)

    # Assemble pressure values in a single time series.
    pressure_output = pd.concat(pressure_dataframes)

    # Label guided alignment.
    # This should work but maybe we can make it more robust to bugs.
    met_dataframe['PA'] = pressure_output

    # Modify inplace without backup.
    dataframe_confirm_inplace_modification(met_dataframe, met_csv)

    sys.exit(0)


def extract_pressure(flux_csv: str, pressure_column: str) -> pd.DataFrame:
    flux_dataframe = load_timeseries(flux_csv)
    pressure = flux_dataframe[[pressure_column]]
    return pressure


if __name__ == '__main__':
    main()
