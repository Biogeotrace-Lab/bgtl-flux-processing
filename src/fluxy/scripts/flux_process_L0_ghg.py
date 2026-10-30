import sys
import click
import os
import zipfile

from pathlib import Path
from datetime import datetime

from ..io.csv import load_timeseries
from ..io.matlab import write_dict_to_matlab_73

from ..utils.config import load_configuration
from ..utils.config import SiteConfiguration

from ..utils.dates import date_from_year_and_doy_in_path
from ..utils.dates import timestamp_from_path
from ..utils.fs import get_daily_flux_filename
from ..utils.prompt import confirm_or_abort
from ..utils.conversions import clip_to_nan

import pandas as pd
import numpy as np

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

from collections import defaultdict

from tqdm import tqdm


@click.command(name="process-l0-ghg",
               short_help="Collect raw ghg smartflux sensor measurements "
               "into daily L0 matlab files.")
@click.option("--raw-data-folder", "-r", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The parent folder for the raw flux data to process.")
@click.option("--L0-destination-folder", "-L0", metavar="FOLDER_PATH",
              required=True,
              type=click.Path(file_okay=False),
              help="The destination folder for the processed L0 flux data.")
@click.option("--pattern", "-p", "source_pattern",
              type=str,
              help="The glob pattern for matching folder files. Use ** for "
              "multilevel globbing. Always wrap in single quotes ''.",
              default='*.ghg',
              show_default=True)
@click.option("--skip-irregular", "-k", "skip_irregular_files",
              is_flag=True,
              help="Skip files that have irregular timestamps.")
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True, type=str, help="Name of the configuration to use for " \
              "site specific information.")
def main(raw_data_folder: str, l0_destination_folder: str,
         source_pattern: str, config_name: str, skip_irregular_files: bool):
    """Collect raw ghg sensor measurements into daily L0 files.
    
    It performs timestamp deduplication, alignment, and reindexing for spanning
    the entire day of the year.
    """
    config = load_configuration(config_name)

    if not config.L0:
        click.echo("Please define a 'L0' section "
                   f"in the {config_name} site configuration.")
        raise click.Abort()

    if config_name not in Path(raw_data_folder).parts:
        click.echo(f"Site name {config} must be present in raw data path.")
        click.echo("Are you sure you provided the correct paths?")
        raise click.Abort()

    # The ouput folder must already be site specific.
    output_folder = Path(l0_destination_folder) / config_name
    output_folder.mkdir(exist_ok=True, parents=True)

    last_date = datetime.fromtimestamp(0)
    for root, dirs, files in os.walk(output_folder):

        # Force newer dates first.
        dirs.sort(reverse=True)
        files.sort(reverse=True)

        for f in files:
            if f.endswith(".mat"):
                last_date = date_from_year_and_doy_in_path(f)
                click.echo("Continuing from {}.".format(last_date))
                break

        if last_date != datetime.fromtimestamp(0):
            break

    raw_flux_files = []
    flux_data_names = []
    grouped_files_by_date = defaultdict(list)
    date = None

    target_file_ext = source_pattern.split(".")[-1]

    for root, dirs, files in os.walk(raw_data_folder):
        if 'error' in root: continue

        dirs.sort()
        files.sort()

        for f in files:
            f = Path(f)
            if f.match(source_pattern):

                # Date parsing.
                datestring = f.name.split("T")[0]
                date = datetime.strptime(datestring, "%Y-%m-%d")

                if skip_irregular_files:
                    timestamp = timestamp_from_path(f)

                    if timestamp.minute % 30 or not timestamp.second == 0:
                        click.echo(f"WARNING: {f} will be skipped due to "
                                "having an irregular timestamp.", err=True)
                        continue

                # Only redo last date, if any files found
                # in destination.
                if date < last_date: continue
            
                # Date is ambiguous. Skip.
                # Verified dates agree with year folder.
                if str(date.year) not in root: continue

                # If it's new, append to TODO container.
                raw_flux_files.append(os.path.join(root, f))
            
                # Append the expected internal CSV name.
                flux_data_names.append(f.with_suffix('.data').name)
            
                # Add files to the DOY (datestring) key.
                grouped_files_by_date[datestring].append((raw_flux_files[-1],
                                                          flux_data_names[-1]))

    if raw_flux_files:
        click.echo(f"The process will be initiated for {config_name} " +
                (f"from {last_date} " 
                    if last_date > datetime.fromtimestamp(0) 
                    else "")
                + f"until {date}.")
        click.echo()
    else:
        click.echo("No new dates.")
        raise click.Abort()

    confirm_or_abort("Proceed?")

    with ProcessPoolExecutor(max_workers=4) as executor:
        try:
            futures = [
                # Select the corresponding process based on file extension.
                executor.submit(process_doy_ghg,
                                date, files, config, output_folder)
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


def process_doy_ghg(date: str, files: list[str], config: SiteConfiguration,
                    output_folder: Path) -> str:
    """A processor function for compressed ghg smartflux files.

    Each L0 full day of year has to be processed together for concatenation.
    """

    # Sort by timestamp on stem.
    files = sorted(files, key=lambda x: Path(x[0]).stem.split("_")[0])

    try:

        column_mappings = {
            k: v.name for k, v in config.L0.items() if v is not None

            }
        column_units = {
            'units': [v.units for k, v in config.L0.items() if v is not None]
                        }
        
        # We need a series of minimum bounds and a series of maximum bounds.
        lower_limits = pd.Series({
                k: v.range[0] if v else None
                for k, v in config.L0.items()
            }, dtype=float)

        upper_limits = pd.Series({
                k: v.range[1] if v else None
                for k, v in config.L0.items()
            }, dtype=float)

        # Build output filename here and check if exists
        # in outputs. Skip iteration if exists.
        date_format = "%Y-%m-%d"
        start_of_day_timestamp = datetime.strptime(date, date_format)

        t_info = start_of_day_timestamp.timetuple()
        year = t_info.tm_year
        doy = t_info.tm_yday


        # Collection container for 30min bundles.
        flux_dataframes: list[pd.DataFrame] = []

        for compressed_file, interior_csv_name in files:
            with zipfile.ZipFile(compressed_file) as z:
                csv_data = z.open(interior_csv_name, "r")
                try:
                    dataframe = load_timeseries(csv_data, header=7, sep="\t",
                                                parse_dates=None,
                                                index_col=None,
                                                engine='pyarrow',
                                                dtype_backend='pyarrow',
                                                na_values=["-9999"],
                                                skiprows=None)
                except Exception as e:
                    click.echo(e, err=True)
                    click.echo(f"Error reading data. {compressed_file} is skipped.", err=True)
                    continue
    
                dataframe['TIMESTAMP'] = date + " " + dataframe.Time
    
                dataframe['TIMESTAMP'] = pd.to_datetime(
                    dataframe['TIMESTAMP'],
                    format="%Y-%m-%d %H:%M:%S:%f")
        
                flux_dataframes.append(dataframe)

        # Concatenated 24H timeseries.
        daily_collection = pd.concat(flux_dataframes, sort=False)
        
        # Properly align timestamps to expected frequency.
        daily_collection['TIMESTAMP'] =\
              daily_collection['TIMESTAMP'].dt.round("50ms")
        daily_collection.set_index("TIMESTAMP", inplace=True)

        daily_collection = clip_to_nan(daily_collection
                                       .select_dtypes(exclude=['string',
                                                               "datetime"]),
                                       lower_limits,
                                       upper_limits)

        # Keep last occurrences as GPS corrected anchors.
        duplicate_stamps = daily_collection.index.duplicated(keep='last')
        daily_collection = daily_collection[~duplicate_stamps]

        # Catch timeflow issues:
        # Sees if any timestamps are very close to each other
        # or in reverse order (negative intervals).
        # Run AFTER deduplication.
        intervals = daily_collection.index.to_series().diff()
        t_issues = intervals < pd.Timedelta(seconds=.02) # Close or negative time.

        # It's impossible to catch interval == 0,
        # because the index was deduplicated.
        # If anything is caught here,
        # the index is not sorted.
        if t_issues.any():
            click.echo(f"Date {date} has {t_issues.sum()} timestamps out of order.", err=True)
            raise click.Abort()

        # Calculate frequency.
        Hz = int(round(daily_collection # type: ignore
                       .resample("1s")
                       .count()
                       .pipe(lambda s: s[s > 0])
                       .median(axis=None), 
                       0))

        # If Hz unexpected.
        if Hz not in [20, 10]:
            click.echo(f"\nBad frequency estimation for {date}: {Hz}")
            raise click.Abort()

        # Reindex dataframe to have timestamps for the entire doy.
        # Missing stamps are inserted with NaN values.
        full_day_index = pd.date_range(start_of_day_timestamp,
                                       end=start_of_day_timestamp +
                                       pd.Timedelta('1D'),
                                       freq='50ms',
                                       name="TIMESTAMP",
                                       inclusive='left')

        # Forces output to 20hz if slower (by filling gaps as NaN).
        # This causes reordering if index is out of order. WARNING.
        daily_collection = daily_collection.reindex(full_day_index)

        # Round values to less decimals.
        daily_collection = daily_collection.round(3)

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

        high_freq_label = f'{Hz}Hz'
        output_high_freq = get_daily_flux_filename(site=config.site,
                                                   desc='L0',
                                                   year=year,
                                                   doy=doy,
                                                   ext='mat')
        output_30m = get_daily_flux_filename(site=config.site,
                                             desc='Avg',
                                             year=year,
                                             doy=doy,
                                             ext='csv')
        output_year_dir = output_folder / f"{config.site}_{year}" / "DailyMAT"

        # Build the year folder if not exists.
        output_dir_high_freq = output_year_dir / "Raw"
        output_dir_30m = output_year_dir / "Avg"

        # Create output directories.
        output_year_dir.mkdir(exist_ok=True, parents=True)
        output_dir_high_freq.mkdir(exist_ok=True)
        output_dir_30m.mkdir(exist_ok=True)

        # Final output path.
        output_high_freq = output_dir_high_freq / output_high_freq
        output_30m = output_dir_30m / output_30m


        write_dict_to_matlab_73(output_high_freq, mdict)
        daily_collection.resample("30 min",
                                  closed="left",
                                  label="left").mean().round(3)\
                                    .to_csv(output_30m)
        return date

    except Exception as e:
        click.echo(e, err=True)
        return "Failed %s" % date


def process_doy_dat(date: str, files: list[str], config: SiteConfiguration,
                    output_folder: Path) -> str:
    """A processor function for sensor logs in csv format (campbell dataloggers)

    This function must be loading and processing both EC100 and Li7700 sensor
    tables and merging them in a single dataframe.
    """

    # Sort by timestamp on stem.
    files = sorted(files, key=lambda x: Path(x[0]).stem.split("_")[0])

    try:

        columns = list(config.L0.keys())
        column_mappings = {
            k: v.name for k, v in config.L0.items() if v is not None

            }
        column_units = {
            'units': [v.units for k, v in config.L0.items() if v is not None]
                      }

        # Build output filename here and check if exists
        # in outputs. Skip iteration if exists.
        date_format = "%Y %j %H%M"
        start_of_day_timestamp = datetime.strptime(date, date_format)

        t_info = start_of_day_timestamp.timetuple()
        year = t_info.tm_year
        doy = t_info.tm_yday


        # Collection container for 30min bundles.
        flux_dataframes: list[pd.DataFrame] = []

        for csv_file, _ in files:
            try:
                dataframe = load_timeseries(csv_file, header=1, sep=",",
                                            parse_dates=None,
                                            index_col=None,
                                            engine='pyarrow',
                                            dtype_backend='pyarrow',
                                            na_values=["-9999"],
                                            usecols=columns)
                dataframe.drop(index=[2, 3], inplace=True)
    
            except Exception as e:
                click.echo(e, err=True)
                click.echo(f"Error reading data. {csv_file} is skipped.", err=True)
                continue
    
            dataframe['TIMESTAMP'] = date + " " + dataframe.Time
    
            dataframe['TIMESTAMP'] = pd.to_datetime(
                dataframe['TIMESTAMP'],
                format="%Y-%m-%d %H:%M:%S:%f")
    
            flux_dataframes.append(dataframe)

        # Concatenated 24H timeseries.
        daily_collection = pd.concat(flux_dataframes, sort=False)

        # Properly align timestamps to expected frequency.
        daily_collection['TIMESTAMP'] =\
              daily_collection['TIMESTAMP'].dt.round("50ms")
        daily_collection.set_index("TIMESTAMP", inplace=True)

        # Keep last occurrences as GPS corrected anchors.
        duplicate_stamps = daily_collection.index.duplicated(keep='last')
        daily_collection = daily_collection[~duplicate_stamps]

        # Catch timeflow issues:
        # Sees if any timestamps are very close to each other
        # or in reverse order (negative intervals).
        # Run AFTER deduplication.
        intervals = daily_collection.index.to_series().diff()
        t_issues = intervals < pd.Timedelta(seconds=.02) # Close or negative time.

        # It's impossible to catch interval == 0,
        # because the index was deduplicated.
        # If anything is caught here,
        # the index is not sorted.
        if t_issues.any():
            click.echo(f"Date {date} has {t_issues.sum()} timestamps out of order.", err=True)
            raise click.Abort()

        # Calculate frequency.
        Hz = int(round(daily_collection # type: ignore
                       .resample("1s")
                       .count()
                       # Only keep non zero counts.
                       .pipe(lambda counts: counts[counts > 0])
                       .median(axis=None), 
                       0))

        # If Hz unexpected.
        if Hz not in [20, 10]:
            click.echo(f"\nBad frequency estimation for {date}: {Hz}")
            raise click.Abort()

        # Reindex dataframe to have timestamps for the entire doy.
        # Missing stamps are inserted with NaN values.
        full_day_index = pd.date_range(start_of_day_timestamp,
                                       end=start_of_day_timestamp +
                                       pd.Timedelta('1D'),
                                       freq='50ms',
                                       name="TIMESTAMP",
                                       inclusive='left')

        # Forces output to 20hz if slower (by filling gaps as NaN).
        # This causes reordering if index is out of order. WARNING.
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

        output_high_freq = get_daily_flux_filename(site=config.site,
                                                   desc='L0',
                                                   year=year,
                                                   doy=doy,
                                                   ext='mat')
        output_30m = get_daily_flux_filename(site=config.site,
                                             desc='Avg',
                                             year=year,
                                             doy=doy,
                                             ext='csv')
        output_year_dir = output_folder / f"{config.site}_{year}" / "DailyMAT"

        # Build the year folder if not exists.
        output_dir_high_freq = output_year_dir / "Raw"
        output_dir_30m = output_year_dir / "Avg"

        # Create output directories.
        output_year_dir.mkdir(exist_ok=True, parents=True)
        output_dir_high_freq.mkdir(exist_ok=True)
        output_dir_30m.mkdir(exist_ok=True)

        # Final output path.
        output_high_freq = output_dir_high_freq / output_high_freq
        output_30m = output_dir_30m / output_30m


        write_dict_to_matlab_73(output_high_freq, mdict)
        daily_collection.resample("30 min",
                                  closed="left",
                                  label="left").mean().to_csv(output_30m)
        return date

    except Exception as e:
        click.echo(e, err=True)
        return "Failed %s" % date


def parse_dat_files(f: Path, skip_irregular_files: bool, last_date: datetime,
                    root: str, raw_flux_files: list, flux_data_names: list,
                    grouped_files_by_date: dict):
    datestring_parts = f.stem.split("_")[-3:]
    datestring = " ".join(datestring_parts)

    date = datetime.strptime(datestring, "%Y %j %H%M")

    if skip_irregular_files:
        timestamp = timestamp_from_path(f)

        if timestamp.minute % 30 or not timestamp.second == 0:
            click.echo(f"WARNING: {f} will be skipped due to "
                    "having an irregular timestamp.", err=True)
            return
    
    # Only redo last date, if any files found
    # in destination.
    if date < last_date: return

    # Date is ambiguous. Skip.
    # Verified dates agree with year folder.
    if str(date.year) not in root: return

    # If it's new, append to TODO container.
    raw_flux_files.append(os.path.join(root, f))

    # Append the expected internal CSV name.
    # NOTE: This is irrelevant for DAT files and is unused throughout.
    flux_data_names.append(f.with_suffix('.data').name)

    # Add files to the DOY (datestring) key.
    grouped_files_by_date[datestring].append((raw_flux_files[-1],
                                              flux_data_names[-1]))


if __name__ == '__main__':
    main()
