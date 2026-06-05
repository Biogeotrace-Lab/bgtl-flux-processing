import pandas as pd
import numpy as np


def potential_timezone_issue(df: pd.DataFrame):
    """Identify timezone issue.

    Requires the RECORD column as exported by the datalogger.
    """
    duplicates = find_timeseries_duplicates(df)
    are_four = duplicates.shape[0] == 4

    sequential = False
    if not duplicates.empty:
        sequence = np.arange(duplicates['RECORD'].iloc[0], duplicates['RECORD'].iloc[-1] + 1)
        sequential = duplicates['RECORD'].shape[0] == sequence.shape[0]
    return are_four and sequential, *np.where(df.index.isin(duplicates.index))


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
    resampled = df[~df.index.duplicated()].resample('30 min').asfreq()
    gaps = resampled.index.difference(df.index)
    gap_positions = np.where(resampled.index.isin(gaps))[0]
    return resampled, gap_positions


def fix_timezone_issue(df: pd.DataFrame, suspects: np.ndarray):
    """Correct the erroneous timezone offset existing in a subset
    of the timeseries.

    Use this function to automatically find and correct overlapping
    periods due to accidental timezone differences

    # Disclaimer
    Right now only implemented for a 1h gap per series.
    """
    resampled, gaps = find_timeseries_gaps(df)
    # Get a mutable copy of indices (Alternatively reset index and reset).
    datetime_indices = df.index.to_numpy().copy()
    # Single use case for now.
    assert len(suspects) == 4
    assert len(gaps) == 2
    # The 1st gap position is where the time change occured.
    start_index = gaps[0]
    # The middle of the suspects + 1 for slicing is the last affected record.
    end_index = suspects[1] + 1
    # Offset back to UTC from GMT+1
    datetime_indices[start_index:end_index] = datetime_indices[start_index:end_index] - pd.Timedelta("1 hour")
    # Replace index with corrected version.
    df.index = datetime_indices
    return df

