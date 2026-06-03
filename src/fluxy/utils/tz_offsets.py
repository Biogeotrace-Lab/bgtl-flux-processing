import pandas as pd
import numpy as np


def potential_timezone_issue(df: pd.DataFrame):
    """Identify timezone issue.

    Requires the RECORD column as exported by the datalogger.
    """
    duplicates = df.index.duplicated(keep=False)
    are_four = duplicates.sum() == 4
    duplicate_rows = df[duplicates]
    sequential = (
        # Verify the duplicate rows are together.
        duplicate_rows['RECORD'] ==
        # Range from first to last record (sequence)
        np.arange(duplicate_rows['RECORD'].iloc[0],
                  duplicate_rows['RECORD'].iloc[-1] + 1)).all()
    return are_four and sequential


def find_timeseries_duplicates(df: pd.DataFrame):
    """Return duplicated dataframe rows.
    """
    duplicates = df.index.duplicated(False)
    return df[duplicates]


def find_timeseries_gaps(df: pd.DataFrame):
    """Identify timeseries gaps.

    Return the resampled gap-filled timeseries dataframe
    together with the gap-filled indices.
    """
    resampled = df.resample('30 min').asfreq()
    gaps = resampled.index.difference(df.index)
    return resampled, gaps
