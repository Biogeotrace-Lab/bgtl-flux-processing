import sys
import click
import os
import zipfile

from glob import glob
from pathlib import Path
from datetime import datetime
from datetime import timedelta

from ..io.csv import load_timeseries

from ..utils.config import load_configuration
from ..utils.config import get_default_config
from ..utils.evaluate import MathEvaluator
from ..utils.dates import date_from_year_and_doy_in_path

import pandas as pd

from collections import defaultdict


@click.command(name="process-L1",
               short_help="Not implemented.")
@click.option("--L0-source-folder", "-l0", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The parent folder for the raw flux data to process.")
@click.option("--L1-destination-folder", "-l1", metavar="FOLDER_PATH",
              required=True,
              type=click.Path(file_okay=False),
              help="The destination folder for the processed L0 flux data.")
@click.option("--pattern", "-p",
              type=str, required=True,
              help="The glob pattern for matching folder files. Use ** for "
              "multilevel globbing. Always wrap in single quotes ''. "
              "(e.g. '**/*.ghg')")
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True)
def main(raw_flux_folder, l0_destination_folder, pattern, config_name):
    """Collect raw flux measurements into daily L0 files."""
    evaluator = MathEvaluator()
    config = load_configuration(config_name)
    ranges = {k: v['range'] for k, v in config.L1.items() if 'range' in v}
    ranges = pd.DataFrame(ranges, index=['min', 'max'], dtype=object)
    # ranges = ranges.map(evaluator.eval).astype(object)
    # ranges.fillna(None, inplace=True)

    print(ranges)
    exit()

    pattern = os.path.join(raw_flux_folder, pattern)
    raw_flux_files = sorted(glob(pattern, recursive=True))
    flux_data_names = list(map(lambda x: Path(x).with_suffix(".data").name,
                               raw_flux_files))
    flux_dates = list(map(lambda x: x.split("T")[0], flux_data_names))

    dest_pattern = os.path.join(l0_destination_folder, "**", "*.mat")
    sorted_dest_files = sorted(glob(dest_pattern, recursive=True))

    last_date = date_from_year_and_doy_in_path(sorted_dest_files[-1])

    grouped_files_by_date = defaultdict(list)

    out_template = "{site}_{desc}_{year:04d}_{doy:03d}.{ext}"

    # Filter out already processed data.
    dates_to_process = filter(

        # Compare flux date to last processed date. Last date will be partial,
        # so it can be included in processing.
        lambda x: datetime.strptime(x[0], "%Y-%m-%d") >= last_date,

        # date          zip file        csv inside zip
        zip(flux_dates, raw_flux_files, flux_data_names, strict=True)

    )
    # Get new L0 dates to process.
    for date, raw_file, flux_data_name in dates_to_process:
        grouped_files_by_date[date].append((raw_file, flux_data_name))


    with click.progressbar(grouped_files_by_date.items(),
                           label="Processing data",
                           length=len(grouped_files_by_date.keys())) as progress:
        for date, files in progress:
            ...

    sys.exit(0)


if __name__ == '__main__':
    main()
