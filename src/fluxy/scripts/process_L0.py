import sys
import click
import os
import zipfile

from glob import glob
from pathlib import Path
from datetime import datetime

from ..io.csv import load_timeseries

from ..utils.config import load_configuration
from ..utils.config import get_default_config
from ..utils.config import SiteConfiguration

from ..utils.evaluate import MathEvaluator
from ..utils.dates import date_from_year_and_doy_in_path
from ..utils.fs import get_daily_flux_filename

import pandas as pd

import hdf5storage
import threading
import time

from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from click._termui_impl import ProgressBar


@click.command(name="process-L0",
               short_help="Collect raw sensor measurements into daily L0 files.")
@click.option("--raw-source-folder", "-r", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The parent folder for the raw flux data to process.")
@click.option("--L0-destination-folder", "-l0", metavar="FOLDER_PATH",
              required=True,
              type=click.Path(file_okay=False),
              help="The destination folder for the processed L0 flux data.")
@click.option("--pattern", "-p", "source_pattern",
              type=str, required=True,
              help="The glob pattern for matching folder files. Use ** for "
              "multilevel globbing. Always wrap in single quotes ''. "
              "(e.g. '**/*.ghg')")
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True)
def main(raw_source_folder, l0_destination_folder, source_pattern, config_name):
    """Collect raw sensor measurements into daily L0 files."""
    config = load_configuration(config_name)
    output_folder = Path(l0_destination_folder) / config.site
    os.makedirs(output_folder, exist_ok=True)
    
    source_pattern = os.path.join(raw_source_folder, source_pattern)
    raw_flux_files = sorted(glob(source_pattern, recursive=True))
    flux_data_names = list(map(lambda x: Path(x).with_suffix(".data").name,
                               raw_flux_files))
    flux_dates = list(map(lambda x: x.split("T")[0], flux_data_names))

    dest_pattern = os.path.join(l0_destination_folder, "**", "*.mat")
    sorted_dest_files = sorted(glob(dest_pattern, recursive=True))

    last_date = datetime.fromtimestamp(0)
    if sorted_dest_files:
        last_date = date_from_year_and_doy_in_path(sorted_dest_files[-1])
        click.echo("Continueing from {}.".format(last_date))

    grouped_files_by_date = defaultdict(list)

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
                           label="Processing L0 data ...",
                           length=len(grouped_files_by_date.keys())) as progress:
        lock = threading.Lock()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(process_date, date, files, config,
                                progress, output_folder, lock)
                for date, files in grouped_files_by_date.items()
            ]
            for future in futures:
                future.result()

    sys.exit(0)


def process_date(date: str, files: list[str], config: SiteConfiguration,
                 progress: ProgressBar, output_folder: Path,
                 lock: threading.Lock) -> None:
    try:
        
        progress.label = "Processing L0 data %s" % date
        progress.render_progress()
        columns = list(config.L0.keys())
        column_mappings = {
            k: v['name'] for k, v in config.L0.items() if v and 'name' in v
            }
        column_units = {
            'units': [v['units'] for k, v in config.L0.items()
                      if v and 'units' in v]
                      }
        
        flux_dataframes = []

        # Build output filename here and check if exists
        # in outputs. Skip iteration if exists.
        timestamp = datetime.strptime(date, "%Y-%m-%d")
        t_info = timestamp.timetuple()
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

        daily_collection = pd.concat(flux_dataframes)
        daily_collection.set_index("TIMESTAMP", inplace=True)
        daily_collection = daily_collection[column_mappings.keys()]
        daily_collection.rename(columns=column_mappings, inplace=True)

        mdict = {
            col: daily_collection[col].to_numpy(dtype=float)
            for col in daily_collection.columns
            }
        mdict['units'] = column_units['units']
        mdict['names'] = daily_collection.columns.to_numpy()

        hdf5storage.savemat(output,
                            mdict=mdict,
                            fmt='7.3',
                            store_python_metadata=False,
                            truncate_existing=True)

    except Exception as e:
        click.echo(raw_file)
        click.echo(e, err=True)

    finally:
        with lock:
            progress.update(1)


if __name__ == '__main__':
    main()
