import sys
import click
import logging

from ..io.csv import load_timeseries
from ..utils.timeseries_checks import find_timeseries_gaps


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command(name="check-gaps")
@click.argument("csv-like-files", nargs=-1, required=True)
def main(csv_like_files: list[str]):
    """Check the provided csv-like files for timeseries gaps."""
    for csv_path in csv_like_files:
        logger.info(csv_path)
        df = load_timeseries(csv_path)
        rs, gaps = find_timeseries_gaps(df)
        if gaps.size > 0:
            logger.info(f"Gaps identified \n"
                        f"{rs.iloc[gaps].index}")

    return 0


if __name__ == '__main__':
    sys.exit(main())

