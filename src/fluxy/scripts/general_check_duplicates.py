import sys
import click

from ..io.csv import load_timeseries
from ..utils.timeseries_checks import find_timeseries_duplicates
from ..utils.checks import QualityControl


@click.command(name="check-duplicates",
               short_help="Check the log file for duplicate rows.")
@click.argument("csv-log-file", nargs=1, required=True,
                type=click.Path(exists=True, dir_okay=False))
def main(csv_log_file: str):
    r"""Check log file for duplicate rows.
    
    Verify there is no timestamp duplications in the log file.
    """
    csv_dataframe = load_timeseries(csv_log_file)

    # Get duplicated timestamps regardless of measurements.
    duplicated_timestamps = find_timeseries_duplicates(csv_dataframe)

    # A subset of columns to check for measurement duplications.
    duplication_columns = csv_dataframe.columns.difference(["RECORD",
                                                            "Year",
                                                            "DOY",
                                                            "Time"])

    # Find entire duplicated rows; Ignore inserted NaN fillings.
    duplicated_measurements_mask = csv_dataframe.duplicated(
            subset=duplication_columns,
            keep=False) & \
                csv_dataframe[duplication_columns].notna().all(axis=1)

    duplicated_measurements = csv_dataframe[duplicated_measurements_mask]

    with QualityControl() as QC:
        QC.add_check("No duplicated rows",
                     duplicated_measurements.empty,
                     f"Found {duplicated_measurements.shape[0]} "
                     "duplicated measurements at \n"
                     f"{duplicated_measurements}")

        QC.add_check("No timestamp overlap",
                     duplicated_timestamps.empty,
                     f"Found {duplicated_timestamps.shape[0]} "
                     "duplicated timestamps at \n"
                     f"{duplicated_timestamps}")


if __name__ == '__main__':
    main()
