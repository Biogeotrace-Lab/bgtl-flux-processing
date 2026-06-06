import sys
import click
import logging

from ..utils.conversions import recover_timestamp_from_doy
from ..utils.conversions import recover_records
from ..io.csv import load_timeseries


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command()
@click.argument("csv-like-files", nargs=-1, required=True)
@click.option("--recover-timestamp", is_flag=True, help="Recover TIMESTAMP from Year, DOY, Time columns")
@click.option("--amend-records", is_flag=True, help="Try to amend RECORD column destruction")
@click.option("--add-doy", is_flag=True, help="Create Year, DOY, Time columns from TIMESTAMP (Day-end 2400H)")
@click.option("--outfolder", type=str, help="Optionally write formatted files to this folder", required=False)
@click.option("--inplace", is_flag=True, help="Modify files inplace")
def main(csv_like_files: list[str], recover_timestamp: bool,
         amend_records: bool, add_doy: bool, outfolder: str,
         inplace: bool):
    """Format log-files and try to recover lost information
    """
    for csv_path in csv_like_files:
        logger.info(f"{csv_path}")

        df = load_timeseries(csv_path, index_col=None, parse_dates=None)

        if recover_timestamp:
            df = recover_timestamp_from_doy(df)
        if amend_records:
            recover_records(df)
        if add_doy:
            ...
        print(df)

    return 0


if __name__ == '__main__':
    sys.exit(main())
