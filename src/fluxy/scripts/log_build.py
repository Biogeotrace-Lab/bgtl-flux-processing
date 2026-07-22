import pandas as pd
import sys
import logging

from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_if_overwrite
from ..utils.conversions import add_year_doy_time
from ..utils.timeseries_checks import find_timeseries_duplicates
from ..utils.timeseries_checks import potential_timezone_issue
from ..utils.timeseries_checks import find_timeseries_gaps
from ..utils.timeseries_checks import find_timezone_shift
from ..utils.timeseries_checks import fix_timezone_issue
from ..utils.prompt import confirm_or_abort

import click


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command(name="log-build",
               short_help="Build a complete timeseries "
               "from multiple csv sources.")
@click.argument("csv-like-files", nargs=-1, required=True,
                type=click.Path(exists=True))
@click.option("--output", default="Met30min.csv",
              help="The output file for the built meteorological dataset. "
              "Defaults to 'output.csv'")
def main(csv_like_files: list[str], output):
    """Build a complete timeseries from multiple csv-like sources.

    This command reliably builds a finalized timeseries
    csv file from multiple source files of raw and uncertain nature.

    It individually checks every provided CSV for overlaps and tries to handle
    them and if duplicate timestamps pass into the concatenated file, the
    process fails.
    """
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

            click.secho("Potential timezone issue at rows: \n" +
                       f"{df.iloc[tzsuspects]}. " +
                       "Add 'TZ_issue' in config.yaml", fg='bright_red')

            rs, all_gaps, tz_gaps = find_timezone_shift(df, tzsuspects)
            click.secho("Likely occured at\n"
                       f"{pd.Series(rs.iloc[tz_gaps].index)}",
                       fg='bright_yellow')

            confirm_or_abort("Attempt fixing timezone issue?")

            # Fix tz issues
            df, (start, end, delta) = fix_timezone_issue(df, tzsuspects)
            tzcheck, tzsuspects = potential_timezone_issue(df)

        
        dupl = find_timeseries_duplicates(df)
        
        if dupl.size:
            raise RuntimeError(click.style(
                f"Duplicate rows in file {csv_path}\n {dupl}",
                bold=True
                ))

        df = add_year_doy_time(df)
        dataframes.append(df)

    # Run concatenation and sort.
    # We can sort because incase of duplicates it fails later.
    concatenated_dataframes = pd.concat(dataframes).sort_index()
    concatenated_dataframes.drop_duplicates(
        # Don't include record in the duplication equality check.
        subset=concatenated_dataframes.columns.difference(["RECORD"]),
        inplace=True)

    # Get persisting duplicated indices.
    duplicated = concatenated_dataframes.index.duplicated(keep=False)

    # Explicitly fail on persistent duplicate indices.
    if duplicated.any():
        raise RuntimeError(f"{duplicated.sum()} duplicated values "
            f"in the timeseries of shape {concatenated_dataframes.shape}."
            "\nFix before proceeding."
            " Duplicated rows:        "                
            f"\n{concatenated_dataframes[duplicated]}")

    # Upsample to the same frequency incase of missing records.
    # Do not fill values.
    # This will also fail for duplicate timestamps.
    resampled_concatenated_dataframes, tz_gaps = \
        find_timeseries_gaps(concatenated_dataframes)

    if len(tz_gaps):
        missing_rows = resampled_concatenated_dataframes.index[tz_gaps]
        logger.warning(click.style(f"\nThere were {len(missing_rows)} missing "
                       "rows in the timeseries:\n"
                       f"\n{pd.Series(missing_rows)}"), fg="bright_yellow")

    # Break timestamp to Year, DOY, Time.
    resampled_concatenated_dataframes = \
        add_year_doy_time(resampled_concatenated_dataframes)

    # Turn index to column and persist.
    # We can probably drop the RECORD column.
    dataframe_confirm_if_overwrite(resampled_concatenated_dataframes, output)
    click.secho("Successfully created a new log file containing "
                f"{resampled_concatenated_dataframes.shape[0]} rows.",
                fg="bright_green")
    return 0


if __name__ == "__main__":
    main()
