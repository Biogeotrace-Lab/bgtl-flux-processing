import sys
import click
import pandas as pd

from ..io.csv import load_timeseries
from ..utils.timeseries_checks import potential_timezone_issue
from ..utils.timeseries_checks import find_timezone_shift
from ..utils.timeseries_checks import fix_timezone_issue
from ..utils.prompt import confirm_or_abort
from ..utils.fs import create_backup
from ..utils.fs import recover_backup
from ..io.csv import dataframe_confirm_inplace_modification_with_backup


@click.command(name="check-tz",
               short_help="Check the log file for potential timezone shifts.")
@click.argument("csv-log-file", nargs=1, required=True)
@click.option("--fix", is_flag=True, help="Attempt to fix the error.")
@click.option("--recover", is_flag=True, help="Undo last changes to log file.")
def main(csv_log_file: str, fix: bool, recover: bool):
    r"""Check log file for duplicate rows.
    
    Verify there is no timestamp duplications in the log file.
    """
    if recover: recover_backup(csv_log_file)

    corrected_csv_dataframe = pd.DataFrame([])
    still_issue = False

    csv_dataframe = load_timeseries(csv_log_file)
    issue, tz_suspects = potential_timezone_issue(csv_dataframe)

    if issue:
        resampled, all_gaps, tz_occurence = find_timezone_shift(csv_dataframe,
                                                            tz_suspects)
        tz_occurence = [tz_occurence[0]-1, tz_occurence[-1]+1]

        click.secho("A timezone shift potentially occured between:",
                    fg="bright_yellow", bold=True)
        click.secho(resampled.iloc[tz_occurence], fg="bright_yellow")
        click.echo()
        click.secho("And lasted until:", fg="bright_yellow", bold=True)
        click.secho(csv_dataframe.iloc[tz_suspects], fg="bright_yellow")

    if issue and not fix: sys.exit(1)

    if fix:
        corrected_csv_dataframe, (start, end, delta) = fix_timezone_issue(
            csv_dataframe, tz_suspects)

        click.secho(f"The records between:\n"
                    f"{csv_dataframe.iloc[start:end].iloc[[0, -1]]}\n"
                    f"Will be shifted back by {delta}.", fg='bright_green')

        still_issue, tz_suspects = potential_timezone_issue(
            corrected_csv_dataframe)

    if still_issue:
        click.secho("Fix did not work. Aborting.", fg='bright_red')
        raise click.Abort()
    
    click.secho("Pass!", fg="bright_green")

    if fix and not corrected_csv_dataframe.empty:
        dataframe_confirm_inplace_modification_with_backup(
            corrected_csv_dataframe, csv_log_file)

    return 0


if __name__ == '__main__':
    main()
