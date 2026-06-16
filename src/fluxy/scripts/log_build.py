import pandas as pd
import sys
import logging

from fluxy.utils.config import get_config
from fluxy.io.csv import load_timeseries
from fluxy.utils.conversions import add_year_doy_time
from fluxy.utils.timeseries_checks import find_timeseries_duplicates
from fluxy.utils.timeseries_checks import potential_timezone_issue
from fluxy.utils.timeseries_checks import find_timeseries_gaps
from fluxy.utils.timeseries_checks import find_timezone_shift
from fluxy.utils.timeseries_checks import fix_timezone_issue

import click

from colorama import Fore
from colorama import Style


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command(name="log-build",
               short_help="Build a complete timeseries csv "
               "from multiple partial sources.")
@click.argument("csv-like-files", nargs=-1, required=True)
@click.option("--output", default="Met30min.csv", help="The output file for the built meteorological dataset")
def main(csv_like_files: list[str], output):
    """This command reliably builds a finalized timeseries
    csv file from multiple source files of raw and uncertain nature.

    It individually checks every provided CSV for overlaps and tries to handle
    them and if duplicate timestamps pass into the concatenated file, the process
    fails.
    """
    config = get_config()
    dataframes = []
    for csv_path in csv_like_files:
        logger.info(f"{csv_path}")

        df = load_timeseries(csv_path)

        if df.index.name != 'TIMESTAMP' or \
            not isinstance(df.index, pd.DatetimeIndex):
            raise RuntimeError("File does not have a 'TIMESTAMP' index.")

        # Check tz issues
        tzcheck, tzsuspects = potential_timezone_issue(df)

        while tzcheck:

            logger.info(Fore.LIGHTRED_EX + "Potential timezone issue at rows: \n" +
                        f"{df.iloc[tzsuspects]}. " +
                        "Add 'TZ_issue' in config.yaml")

            rs, all_gaps, tz_gaps = find_timezone_shift(df, tzsuspects)
            logger.info(f"\nLikely occured at\n{pd.Series(rs.iloc[tz_gaps].index)}")

            proceed = input("Attempt fixing? y/n: ")
            
            if proceed == "y":
                # Fix tz issues
                df = fix_timezone_issue(df, tzsuspects)
                tzcheck, tzsuspects = potential_timezone_issue(df)
            else:
                logger.info("Aborting.")
                sys.exit(1)

        dataframes.append(df)

    # Run concatenation and sort.
    # We can sort because incase of duplicates it fails later.
    concatenated_dataframes = pd.concat(dataframes).sort_index()
    concatenated_dataframes.drop_duplicates(
        subset=concatenated_dataframes.columns.difference(["RECORD"]),
        inplace=True)

    # Get persisting duplicated indices.
    duplicated = concatenated_dataframes.index.duplicated(keep=False)

    # Explicitly fail on persistent duplicate indices.
    if duplicated.any():
        raise RuntimeError(f"""
            {duplicated.sum()} duplicated values
            in the timeseries of shape {concatenated_dataframes.shape}.
            Fix before proceeding.

            Duplicated rows:                        
            {concatenated_dataframes[duplicated]}
            """)

    # Upsample to the same frequency incase of missing records.
    # Do not fill values.
    # This will also fail for duplicate timestamps.
    resampled_concatenated_dataframes, tz_gaps = \
        find_timeseries_gaps(concatenated_dataframes)

    if len(tz_gaps):
        missing_rows = resampled_concatenated_dataframes.index[tz_gaps]
        logger.warning(Fore.LIGHTYELLOW_EX +
                       f"\nThere were {len(missing_rows)} missing "
                       "rows in the timeseries:"
                       f"\n{pd.Series(missing_rows)}")

    # Break timestamp to Year, DOY, Time.
    resampled_concatenated_dataframes = \
        add_year_doy_time(resampled_concatenated_dataframes)

    # Turn index to column and persist.
    # We can probably drop the RECORD column.
    resampled_concatenated_dataframes.to_csv(output)
    logger.info(Fore.LIGHTGREEN_EX +
                "Successfully created a new log file containing "
                f"{resampled_concatenated_dataframes.shape[0]} rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

