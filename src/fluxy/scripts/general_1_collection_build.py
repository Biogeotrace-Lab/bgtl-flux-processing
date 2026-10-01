import pandas as pd
import sys
import logging

from pathlib import Path

from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_if_overwrite
from ..utils.conversions import add_year_doy_time
from ..utils.timeseries import find_timeseries_duplicates
from ..utils.timeseries import potential_timezone_issue
from ..utils.timeseries import find_timeseries_gaps
from ..utils.timeseries import find_timezone_shift
from ..utils.timeseries import fix_timezone_issue
from ..utils.prompt import confirm_or_abort

import click


logger = logging.getLogger(__name__)


@click.command(name="assemble-master",
               short_help="Build a complete timeseries master file "
               "from multiple csv sources.")
@click.argument("csv-like-files", nargs=-1, required=True,
                type=click.Path(exists=True))
@click.option("--output", default="Met30min.csv",
              help="The output file for the built meteorological dataset.",
              show_default=True,
              type=click.Path(dir_okay=False))
@click.pass_context
def main(ctx: click.Context, csv_like_files: list[str], output):
    """Build a complete timeseries master file from multiple csv sources.

    This command reliably builds a finalized timeseries
    csv file from multiple raw source files and adds Year DOY and Time columns.

    Various checks deduct whether these files can be merged. Because these
    source files must be kept intact, potential needed corrections are only
    attempted in-memory.
    """
    source_dataframes = []
    for csv_path in csv_like_files:
        click.echo(f"Processing {csv_path}")

        # Raw source files must have a timestamp column as direct
        # data logger outputs.
        df = load_timeseries(csv_path)

        # Check tz issues
        tzcheck, tzsuspects = potential_timezone_issue(df)

        if tzcheck:

            click.secho("Potential timezone issue at rows: \n" +
                       f"{df.iloc[tzsuspects]}. " +
                       "Add 'TZ_issue' in config.yaml", fg='bright_red')

            rs, all_gaps, tz_gaps = find_timezone_shift(df, tzsuspects)
            click.secho(
                f"""Likely occured at\n\n{pd.Series(rs.iloc[tz_gaps].index)}""",
                fg='bright_yellow')

            confirm_or_abort("Attempt fixing timezone issue?")

            # Fix tz issues
            df, (start, end, delta) = fix_timezone_issue(df, tzsuspects)


        if find_timeseries_duplicates(df).shape[0] > 0:
            click.secho(
                f"{csv_path} omitted due to persisting duplicate values. "
                "Fix it and repeat the process if you need it included.",
                fg="bright_yellow")
            continue

        source_dataframes.append(df)

    # Run concatenation and sort.
    # We can sort because incase of duplicates it fails later.
    concatenated_dataframes = pd.concat(source_dataframes, axis=0).sort_index()
    include_cols = concatenated_dataframes.columns.difference(["ea_Avg"])

    concatenated_dataframes.drop_duplicates(
        # Don't include record in the duplication equality check.
        subset=include_cols,
        inplace=True)

    # Get persisting duplicated indices.
    duplicated = concatenated_dataframes.index.duplicated(keep=False)

    # Explicitly fail on persistent duplicate indices.
    if duplicated.any():
        pd.options.display.max_columns = 100
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

    if tz_gaps.size > 0:
        missing_rows = resampled_concatenated_dataframes.index[tz_gaps]
        click.secho(f"""
There will be {len(missing_rows)} missing rows in the timeseries
that will be filled with NaN values:            
{pd.Series(missing_rows)}\n""")
        confirm_or_abort("Continue?")

    # Break timestamp to Year, DOY, Time.
    resampled_concatenated_dataframes = \
        add_year_doy_time(resampled_concatenated_dataframes)

    # Turn index to column and persist.
    # We can probably drop the RECORD column.
    dataframe_confirm_if_overwrite(resampled_concatenated_dataframes, output)
    click.secho("Successfully created a new master file containing "
                f"{resampled_concatenated_dataframes.shape[0]} rows.",
                fg="bright_green")


    sys.exit(0)


if __name__ == "__main__":
    main()
