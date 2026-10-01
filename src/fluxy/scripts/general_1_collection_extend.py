import sys
import click
import logging
import pandas as pd

from ..io.csv import load_timeseries

from ..utils.conversions import add_year_doy_time
from ..utils.timeseries import find_timeseries_duplicates
from ..utils.timeseries import find_timeseries_gaps

from ..utils.fs import create_backup
from ..utils.fs import confirm_to_recover_backup
from ..utils.prompt import confirm_or_abort
from ..utils.checks import QualityControl

logger = logging.getLogger(__name__)


@click.command(name="extend-master",
               short_help="Extend a log masterfile with a csv candidate.")
@click.option("-e", "--extension", nargs=1, required=True,
              type=click.Path(exists=True),
              help="The extension log file.")
@click.option("-m", "--master", nargs=1, required=True,
              type=click.Path(exists=True),
              help="The master file to extend.")
@click.option("--recover", type=bool, required=False, is_flag=True,
              help="Undo the last changes to the master file.")
@click.option("--show-rows", type=int, required=False, default=1000,
              help="Number of rows to print in report.")
def main(extension: str, master: str, recover: bool, show_rows: int):
    r"""Safely extend a L0 meteorology timeseries.

    Asserts the extension is a continuation of the master file without jumps,
    it has not gaps, or duplicated rows. Asks for confirmation to proceed.
    """

    if recover:

        # Recover the backup file in the directory, if exists.
        confirm_to_recover_backup(master)

    with QualityControl() as QC:
        pd.options.display.max_rows = show_rows
        pd.options.display.max_columns = 0

        # Load the extension candidate and add Year DOY Time columns.
        csv_dataframe = load_timeseries(extension)

        # Extension needs to be resampled to 30 min intervals
        # and checked for duplicates.
        duplicates = find_timeseries_duplicates(csv_dataframe)

        QC.add_check("Extension has no duplicates",
                     duplicates.empty,
                     "Candidate contains duplicate timestamps.")

        # Verify extension index is sorted.
        QC.add_check("Extension index is sorted",
                     csv_dataframe.index.tolist() ==
                     csv_dataframe.sort_index().index.to_list(),
                     "Extension indices are not sorted. "
                     "Is the file corrupted?")

        # Force resampling to 30 min intervals.
        # This should not be the responsibility of this script.
        _, gaps = find_timeseries_gaps(csv_dataframe)
        QC.add_check("Extension has no gaps",
                     gaps.size == 0,
                     "The extension candidate has gaps. "
                     "It should be formatted first.")

        # Add year doy time to the extension candidate.
        csv_dataframe = add_year_doy_time(csv_dataframe)

        # Load the declared master file.
        master_dataframe = load_timeseries(master)

        # Assert the columns are synchronized.
        col_difference = csv_dataframe.columns.difference(master_dataframe.columns)
        QC.add_check("Files have matching columns",
                     col_difference.empty,
                     f"Columns don't match {col_difference.tolist()}")

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
        QC.add_check("Extension has new data",
                     csv_indices_future.size > 0,
                     "There is no new data to write.")

        # Get the indices before the master file end.
        csv_indices_past = csv_indices_non_master[
            csv_indices_non_master < ms_end
        ]

        QC.add_check("Extension is more recent than master",
                     not csv_indices_past.empty and
                     ms_start <= csv_indices_past[0],
                     "Extension contains older records than master file. "
                     "Did you choose the correct files?")

        # The start of the future timestamps.
        future_start = csv_indices_future[0]

        # Check csv_dataframe is a continuation of master file.
        time_gap = future_start - ms_end

        QC.add_check("Extension is continuation of master",
                     time_gap == pd.Timedelta("30 min"),
                     f"There is a time gap of {time_gap} between"
                     "the master file and extension file. "
                     "Are you missing data in between?")

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

    # Aborts if not verified.
    confirm_or_abort("Write changes to master file?")

    # Backup process. Make a backup before continuing.
    create_backup(master)

    # Write to disk.
    # Eventually we could explore only appending
    # instead of rewriting the file from scratch.
    extended_master_dataframe.to_csv(master)
    click.echo("Changes applied sucessfully.")
    return 0


if __name__ == '__main__':
    main()
