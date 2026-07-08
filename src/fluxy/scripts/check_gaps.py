import sys
import click
import logging

from ..io.csv import load_timeseries
from ..utils.timeseries_checks import find_timeseries_gaps


logger = logging.getLogger(__name__)


@click.command(name="check-gaps")
@click.argument("csv-log-file", nargs=1, required=True)
def main(csv_log_file: str):
    """Check the provided log file for gaps."""
    logger.info(csv_log_file)
    df = load_timeseries(csv_log_file)
    resampled, gaps = find_timeseries_gaps(df)
    
    if gaps.size > 0:
        click.secho(f"{gaps.size} gaps identified at:\n"
                    f"{resampled.iloc[gaps].index}",
                    fg="bright_yellow")
        
        click.get_current_context().exit(1)

    click.secho("Pass!", fg="bright_green")
    return 0


if __name__ == '__main__':
    main()
