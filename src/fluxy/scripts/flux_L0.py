import sys
import click
import os
import zipfile

from pathlib import Path
from datetime import datetime

from ..io.csv import load_timeseries
from ..io.matlab import write_dict_to_matlab_73

from ..utils.config import load_configuration
from ..utils.config import get_default_config
from ..utils.config import SiteConfiguration

from ..utils.evaluate import MathEvaluator
from ..utils.dates import date_from_year_and_doy_in_path
from ..utils.fs import get_daily_flux_filename

import pandas as pd
import numpy as np

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

from collections import defaultdict

from tqdm import tqdm


@click.command(name="process-L0",
               short_help="Collect raw ghg smartflux sensor measurements "
               "into daily L0 files.")
@click.option("--raw-ghg-folder", "-r", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The parent folder for the raw flux data to process.")
@click.option("--L0-destination-folder", "-L0", metavar="FOLDER_PATH",
              required=True,
              type=click.Path(file_okay=False),
              help="The destination folder for the processed L0 flux data.")
@click.option("--pattern", "-p", "source_pattern",
              type=str,
              help="The glob pattern for matching folder files. Use ** for "
              "multilevel globbing. Always wrap in single quotes ''. "
              "(Defaults to '**/*.ghg')",
              default='**/*.ghg')
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True, help="Name of the configuration to use.")
def main(raw_ghg_folder, l0_destination_folder, source_pattern, config_name):
    """Collect raw ghg sensor measurements into daily L0 files.
    
    It performs timestamp deduplication, alignment, and reindexing for spanning
    the entire day of the year.
    """
    config = load_configuration(config_name)
    output_folder = Path(l0_destination_folder) / config.site
    os.makedirs(output_folder, exist_ok=True)

    source_pattern = os.path.join(raw_ghg_folder, source_pattern)

    last_date = datetime.fromtimestamp(0)
    for root, dirs, files in os.walk(l0_destination_folder):
        dirs.sort(reverse=True)
        files.sort(reverse=True)
        for f in files:
            if f.endswith(".mat"):
                last_date = date_from_year_and_doy_in_path(f)
                click.echo("Continuing from {}.".format(last_date))
                break

    raw_flux_files = []
    flux_data_names = []
    grouped_files_by_date = defaultdict(list)
    for root, dirs, files in os.walk(raw_ghg_folder):
        if 'error' in root: continue

        dirs.sort()
        files.sort()

        for f in files:
            if f.endswith(".ghg"):
                datestring = f.split("T")[0]
                date = datetime.strptime(datestring, "%Y-%m-%d")

                # Only redo last date, if any files found
                # in destination.
                if date < last_date: continue


                raw_flux_files.append(os.path.join(root, f))
                flux_data_names.append(Path(f).with_suffix('.data').name)
                grouped_files_by_date[datestring].append((raw_flux_files[-1],
                                                          flux_data_names[-1]))


    with ProcessPoolExecutor(max_workers=4) as executor:
        try:
            futures = [
                executor.submit(process_date, date, files, config,
                                output_folder)
                for date, files in grouped_files_by_date.items()
            ]

            with tqdm(as_completed(futures), desc="Processing dates...",
                      total=len(futures), unit='DOY') as pbar:
                for future in pbar:
                    pbar.set_postfix_str(future.result())

        except KeyboardInterrupt:
            click.echo("Shutting down.")
            executor.shutdown(wait=False, cancel_futures=True)

    sys.exit(0)


def process_date(date: str, files: list[str], config: SiteConfiguration,
                 output_folder: Path) -> str:
    """Each L0 date has to be processed together for concatenation.
    """
    try:
        
        columns = list(config.L0.keys())
        column_mappings = {
            k: v['name'] for k, v in config.L0.items()
            if v and 'name' in v
            }
        column_units = {
            'units': [v['units'] for k, v in config.L0.items()
                      if v and 'units' in v]
                      }

        # Build output filename here and check if exists
        # in outputs. Skip iteration if exists.
        start_of_day_timestamp = datetime.strptime(date, "%Y-%m-%d")
        t_info = start_of_day_timestamp.timetuple()
        year = t_info.tm_year
        doy = t_info.tm_yday
        output = get_daily_flux_filename(site=config.site,
                                         desc='20hz',
                                         year=year,
                                         doy=doy,
                                         ext='mat')

        output_year = output_folder / str(year)

        # Create year directory.
        os.makedirs(output_year, exist_ok=True)

        output = output_year / output

        flux_dataframes: list[pd.DataFrame] = []
        for raw_file, csv_data_path in files:
            with zipfile.ZipFile(raw_file) as z:
                csv_data = z.open(csv_data_path, "r")

                dataframe = load_timeseries(csv_data, header=7, sep="\t",
                                            parse_dates=None,
                                            index_col=None,
                                            engine='pyarrow',
                                            dtype_backend='pyarrow',
                                            na_values=["-9999"],
                                            skiprows=None,
                                            usecols=columns)

                dataframe['TIMESTAMP'] = dataframe.Date.astype(str) +\
                    " " +\
                    dataframe.Time

                dataframe['TIMESTAMP'] = pd.to_datetime(
                    dataframe['TIMESTAMP'],
                    format="%Y-%m-%d %H:%M:%S:%f"
                    )

                flux_dataframes.append(dataframe)

        # Concatenated 24H timeseries.
        daily_collection = pd.concat(flux_dataframes, sort=False)

        # Properly align timestamps to expected frequency.
        daily_collection.index = pd.DatetimeIndex(
            daily_collection['TIMESTAMP']).round("50ms")

        # Keep last occurrences as GPS corrected anchors.
        duplicate_stamps = daily_collection.index.duplicated(keep='last')
        daily_collection = daily_collection[~duplicate_stamps]

        # This catches timeflow issues.
        # Run AFTER deduplication.
        intervals = daily_collection["TIMESTAMP"].diff()
        t_issues = intervals < pd.Timedelta(seconds=.02)

        # If anything is caught here,
        # the index is not sorted.
        if t_issues.any():
            click.echo(f"Date {date} has timestamps out of order.", err=True)

        # Reindex dataframe to have timestamps for the entire doy.
        # Missing stamps are inserted with NaN values.
        full_day_index = pd.date_range(start_of_day_timestamp,
                                       periods=24 * 60 * 60 * 20,
                                       freq='50ms')
        daily_collection = daily_collection.reindex(full_day_index)

        # Only include columns that have mappings defined.
        daily_collection = daily_collection[column_mappings.keys()]
        daily_collection.rename(columns=column_mappings, inplace=True)

        # Configure data for saving.
        mdict: dict = {
            col: daily_collection[col].to_numpy(dtype=np.float32)
            for col in daily_collection.columns
            }

        mdict['units'] = column_units['units']
        mdict['names'] = daily_collection.columns.to_numpy()
        mdict['basetime'] = f"{year:04d} {doy:03d} 00:00:00.0"

        write_dict_to_matlab_73(output, mdict)

        return date

    except Exception as e:
        click.echo(e, err=True)
        return "Failed %s" % date


if __name__ == '__main__':
    main()
