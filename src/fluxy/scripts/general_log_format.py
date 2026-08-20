import sys
import click
import logging

from pathlib import Path

from ..utils.conversions import add_timestamp_from_doy
from ..utils.conversions import add_records_column
from ..utils.conversions import add_year_doy_time

from ..io.csv import load_timeseries

from ..utils.paths import change_directory
from ..io.csv import dataframe_confirm_inplace_modification_with_backup
from ..io.csv import dataframe_confirm_if_overwrite
from ..utils.timeseries_checks import find_timeseries_gaps
from ..utils.fs import recover_backup

from ._options import CommandWithMutuallyExclusiveOptions

logger = logging.getLogger(__name__)


@click.command(name="format",
               cls=CommandWithMutuallyExclusiveOptions,
               mutex=["--inplace", "--output"],
               short_help="Format log files.")
@click.argument("csv-log-file", nargs=1, required=True,
                type=click.Path(exists=True))
@click.option("--add-missing-rows", is_flag=True,
              help="Fill in missing timestamps with empty rows (resample).")
@click.option("--add-timestamp", is_flag=True,
              help="Recover TIMESTAMP from Year, DOY, Time columns.")
@click.option("--add-records", is_flag=True,
              help="Add a RECORD column that enumerates rows.")
@click.option("--add-doy", is_flag=True,
              help="Create Year, DOY, Time columns from TIMESTAMP "
              "(End of day @2400H).")
@click.option("--inplace", is_flag=True,
              help="Modify file inplace.")
@click.option("--output", type=click.Path(dir_okay=False), required=False,
              help="Write formatted file to destination.")
@click.option("--recover", is_flag=True, help="Undo last changes to log file.")
def main(csv_log_file: Path, add_timestamp: bool, add_missing_rows: bool,
         add_records: bool, add_doy: bool, output: Path, inplace: bool,
         recover: bool):
    """Format log files to specification as needed.
    """
    if recover: recover_backup(csv_log_file)

    click.echo(f"{csv_log_file}")
    df = load_timeseries(csv_log_file)

    if add_timestamp:
        df = add_timestamp_from_doy(df)
        click.echo("Added timestamp column")

    if add_missing_rows:
        df, _ = find_timeseries_gaps(df)
        click.echo(f"Added {_.size} missing rows")

    if add_records:
        add_records_column(df)
        click.echo("Added records column")

    if add_doy:
        df = add_year_doy_time(df)
        click.echo("Created Year, DOY and Time columns.")

    # Show modified DataFrame.
    click.echo(df)

    # Persistance. No modification beyond this point.
    if output:
        dataframe_confirm_if_overwrite(df, output)
    elif inplace:
        dataframe_confirm_inplace_modification_with_backup(df, csv_log_file)
    else:
        click.secho("Changes not saved. Use --inplace or define --output.",
                    bold=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())
