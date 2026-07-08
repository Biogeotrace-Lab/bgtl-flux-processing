import sys
import click
import logging
import pandas as pd

from ..io.csv import load_timeseries

from ..utils.conversions import add_year_doy_time
from ..utils.timeseries_checks import find_timeseries_duplicates
from ..utils.timeseries_checks import find_timeseries_gaps

from ..utils.fs import create_backup
from ..utils.fs import recover_backup
from ..utils.prompt import prompt_yes_or_abort
from ..utils.checks import passes_check_report

logger = logging.getLogger(__name__)


@click.command(name="log-extend",
               short_help="Extend a log masterfile with a csv candidate.")
@click.option("-e", "--extension", nargs=1, required=True,
              help="The extension log file.")
@click.option("-m", "--master", nargs=1, required=True,
              help="The master file to extend.")
@click.option("--recover", type=bool, required=False, is_flag=True,
              help="Undo the last changes to the master file.")
@click.option("--show-rows", type=int, required=False, default=1000,
              help="Number of rows to print in report.")
def main(extension: str, master: str, recover: bool, show_rows: int):
    r"""Extend a log master file with a csv extension candidate.

    Safety measures:
    
    Assert the log file candidate is a natural continuation of the masterfile.
    If the candidate does not start immediately after the end of the
    masterfile, the operation is aborted, as it would imply missing data.

    The timestamps before the end of the master file will be ignored and
    assumed validated by anterior operations.

    Verbosely reports the rows that are about to be added and asks for
    confirmation by the user, before modifying the master file.

    Finally, before modifying, it makes a hidden backup in the master file's
    directory for file recovery.
    """

    if recover and prompt_yes_or_abort("Recover master file?"):

        # Recover the backup file in the directory, if exists.
        recover_backup(master)
        click.echo("Recovered master file from last backup.")

        return 0

    pd.options.display.max_rows = show_rows
    pd.options.display.max_columns = 0

    # Load the extension candidate and add Year DOY Time columns.
    csv_dataframe = load_timeseries(extension)

    # Verify extension index is sorted.
    if not passes_check_report("Index sorted in extension",
                               csv_dataframe.index.tolist() ==
                               csv_dataframe.sort_index().index.to_list()):
        raise RuntimeError("Extension indices are not sorted. "
                           "Is the file corrupted?")

    # Extension needs to be resampled to 30 min intervals
    # and checked for duplicates.
    duplicates = find_timeseries_duplicates(csv_dataframe)
    if not passes_check_report("No duplicates in extension", duplicates.empty):
        raise RuntimeError("Candidate contains duplicate timestamps.")

    # Force resampling to 30 min intervals.
    # This should not be the responsibility of this script.
    _, gaps = find_timeseries_gaps(csv_dataframe)

    if not passes_check_report("No gaps in extension", gaps.size == 0):
        raise RuntimeError("The extension candidate has gaps. "
                           "It should be formatted first.")

    # Add year doy time to the extension candidate.
    csv_dataframe = add_year_doy_time(csv_dataframe)

    # Load the declared master file.
    master_dataframe = load_timeseries(master)

    # Assert the columns are synchronized.
    col_difference = csv_dataframe.columns.difference(master_dataframe.columns)
    if not passes_check_report("Columns match between files",
                               col_difference.empty):
        raise RuntimeError(f"Columns don't match {col_difference.tolist()}")

    # The start timestamp of the master file.
    ms_start = master_dataframe.index[0]

    # The end timestamp of the master file.
    ms_end = master_dataframe.index[-1]

    # The csv timestamps that are not in the master file.
    # These seem to continue being sorted.
    csv_indices_non_master = csv_dataframe.index.difference(
        master_dataframe.index)

    # Get the indices after the master file end.
    csv_indices_future = csv_indices_non_master[
        csv_indices_non_master > ms_end]

    # There is no data to add.
    if not csv_indices_future.size:
        click.secho("No new data to be added. Aborting.", bold=True)
        raise click.Abort()

    # Get the indices before the master file end.
    csv_indices_past = csv_indices_non_master[
        csv_indices_non_master < ms_end
    ]

    if not csv_indices_past.empty and \
        not passes_check_report("Extension starts after master",
                                ms_start < csv_indices_past[0]):
        raise RuntimeError("Extension is older than master file. "
                           "Did you choose the correct files?")

    # The start of the future timestamps.
    future_start = csv_indices_future[0]

    # Check csv_dataframe is a continuation of master file.
    time_gap = future_start - ms_end
    if not passes_check_report("Continuous extension", time_gap == pd.Timedelta("30 min")):
        raise RuntimeError(
            f"There is a time gap of {time_gap} between the master file "
            "and candidate file. Are you missing data in the candidate file?\n"
        )

    # Ignore overlapping rows.
    extension_dataframe = csv_dataframe.loc[csv_indices_future]

    # FINAL CHECK and actually perform the extension here.
    # This will fail if the extension is not clean,
    # or the master for some reason.
    extended_master_dataframe = pd.concat([master_dataframe,
                                           extension_dataframe],
                                          verify_integrity=True)

    # Report all changes in detail for user verification.
    # New indices are just csv_indices_future. This is not necessary.
    new_indices = extended_master_dataframe.index.difference(
        master_dataframe.index)

    click.echo("The master file will change as follows:")

    click.echo(
        master_dataframe,
        )

    click.secho(
        extended_master_dataframe.loc[new_indices],
        fg="bright_green"
        )

    click.secho(
        f"{new_indices.size} new timestamps to be added.",
        fg="bright_green",
        bold=True
        )

    if prompt_yes_or_abort("Write changes to master file?"):
        # Backup process. Make a backup before continuing.
        create_backup(master)
        click.echo("Created a master file backup.")

        # Write to disk.
        # Eventually we could explore only appending
        # instead of rewriting the file from scratch.
        extended_master_dataframe.to_csv(master)
        click.echo("Changes applied sucessfully.")
        return 0

    raise click.Abort()


if __name__ == '__main__':
    main()
