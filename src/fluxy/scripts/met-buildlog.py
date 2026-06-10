import pandas as pd
import sys
import logging

from fluxy.utils.config import get_config
from fluxy.io.csv import load_timeseries
from fluxy.utils.conversions import recover_records
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


@click.command()
@click.argument("csv-like-files", nargs=-1, required=True)
@click.option("--output", default="Met30min.csv", help="The output file for the built meteorological dataset")
def main(csv_like_files: list[str], output):
    """Build a complete timeseries csv from multiple partial sources.
    """
    config = get_config()
    dataframes = []
    for csv_path in csv_like_files:
        logger.info(f"{csv_path}")

        df = load_timeseries(csv_path)

        # Check tz issues
        tzcheck, tzsuspects = potential_timezone_issue(df)

        while tzcheck:

            logger.info(Fore.LIGHTRED_EX + "Potential timezone issue at rows: \n"
                        f"{df.iloc[tzsuspects]}. "
                        "Add 'TZ_issue' in config.yaml")

            rs, gaps = find_timezone_shift(df, tzsuspects)
            logger.info(f"\nLikely occured at\n{pd.Series(rs.iloc[gaps].index)}")
            
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
    concatenated_dataframes.drop_duplicates(inplace=True)

    # Get persisting duplicated indices.
    duplicated = concatenated_dataframes.index.duplicated(keep=False)

    # Explicitly fail on persistent duplicate indices.
    if duplicated.any():
        raise RuntimeError(f"""{duplicated.sum()} duplicated values
                    in the timeseries of shape {concatenated_dataframes.shape}. Fix before proceeding.

                    Duplicated rows:                        
                    {concatenated_dataframes[duplicated]}
                           """)

    # Upsample to the same frequency incase of missing records.
    # Do not fill values.
    # This will also fail for duplicate timestamps.
    resampled_concatenated_dataframes, gaps = find_timeseries_gaps(concatenated_dataframes)

    if len(gaps):
        missing_rows = resampled_concatenated_dataframes.index[gaps]
        logger.warning(Fore.LIGHTYELLOW_EX + f"""
There were {len(missing_rows)} missing rows in the timeseries:
{pd.Series(missing_rows)}""")

    # Add Year, DOY, hour.
    resampled_concatenated_dataframes['Year'] = resampled_concatenated_dataframes.index.year # type: ignore
    resampled_concatenated_dataframes['DOY'] = resampled_concatenated_dataframes.index.dayofyear # type: ignore
    resampled_concatenated_dataframes['Time'] = resampled_concatenated_dataframes.index.strftime("%H%M") # type: ignore

    # 0000 is the end of day / Not start of new day.
    resampled_concatenated_dataframes.loc[resampled_concatenated_dataframes['Time'] == "0000", "DOY"] -= 1
    resampled_concatenated_dataframes.loc[resampled_concatenated_dataframes['Time'] == "0000", "Time"] = "2400"

    # Turn index to column and persist.
    # We can probably drop the RECORD column.
    resampled_concatenated_dataframes.to_csv(output)
    logger.info(Fore.LIGHTGREEN_EX + "Successfully created a new log file containing "
                f"{resampled_concatenated_dataframes.shape[0]} rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

