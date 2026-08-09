import sys
import click
import logging

from ..io.csv import load_timeseries
from ..utils.timeseries_checks import find_timeseries_gaps
from ..utils.checks import QualityControl

logger = logging.getLogger(__name__)


@click.command(name="check-gaps")
@click.argument("csv-log-file", nargs=1, required=True,
                type=click.Path(exists=True))
def main(csv_log_file: str):
    """Check the provided log file for gaps."""
    logger.info(csv_log_file)
    df = load_timeseries(csv_log_file)
    resampled, gaps = find_timeseries_gaps(df)

    with QualityControl() as QC:
        QC.add_check("Check for gaps", gaps.size == 0,
                     f"{gaps.size} gaps were found in timeseries")

    sys.exit(0)

if __name__ == '__main__':
    main()
