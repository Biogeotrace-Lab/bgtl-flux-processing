import sys
import click
import logging

from pathlib import Path

from ..utils.conversions import recover_timestamp_from_doy
from ..utils.conversions import recover_records
from ..utils.conversions import add_year_doy_time

from ..io.csv import load_timeseries

from ..utils.paths import change_directory

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command()
@click.argument("csv-like-files", nargs=-1, required=True)
@click.option("--recover-timestamp", is_flag=True, help="Recover TIMESTAMP from Year, DOY, Time columns")
@click.option("--amend-records", is_flag=True, help="Try to amend RECORD column destruction")
@click.option("--add-doy", is_flag=True, help="Create Year, DOY, Time columns from TIMESTAMP (Day-end 2400H)")
@click.option("--outfolder", type=Path, help="Write formatted files to output folder", required=False)
@click.option("--inplace", is_flag=True, help="Modify files inplace")
def main(csv_like_files: list[str], recover_timestamp: bool,
         amend_records: bool, add_doy: bool, outfolder: Path,
         inplace: bool):
    """Format log-files and try to recover lost information
    """
    for csv_path in csv_like_files:
        logger.info(f"{csv_path}")

        df = load_timeseries(csv_path, index_col=None, parse_dates=None)

        if recover_timestamp:
            df = recover_timestamp_from_doy(df)
            logger.info("Recovered timestamp column")
        if amend_records:
            recover_records(df)
            logger.info("Added records column")
        if add_doy:
            df = add_year_doy_time(df)
            logger.info("Created Year, DOY and Time columns with 2400H as end-of-day")

        if inplace:
            df.to_csv(csv_path)
            logger.info("Modified inplace")
        
        if outfolder:
            outfolder.mkdir(parents=True, exist_ok=True)
            new_csv_path = change_directory(csv_path, outfolder)
            df.to_csv(new_csv_path)
            logger.info(f"Formatted version written at {new_csv_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
