import sys
import click

from ..io.csv import load_timeseries
from ..utils.timeseries_checks import find_timeseries_duplicates


@click.command(name="check-duplicates",
               short_help="Check log file for duplicate rows.")
@click.argument("csv-log-file", nargs=1, required=True)
def main(csv_log_file: str):
    r"""Check log file for duplicate rows.
    
    Verify there is no timestamp duplications in the log file.
    """
    csv_dataframe = load_timeseries(csv_log_file)
    duplicates = find_timeseries_duplicates(csv_dataframe)

    if not duplicates.empty:
        click.secho(f"Found {duplicates.shape[0]} duplicated timestamps at \n"
                    f"{duplicates}", fg="bright_yellow")
        return click.get_current_context().exit(1)

    click.secho("Pass!", fg="bright_green")
    return 0


if __name__ == '__main__':
    main()
