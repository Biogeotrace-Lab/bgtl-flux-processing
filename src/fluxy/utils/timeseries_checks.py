import pandas as pd
import numpy as np


def potential_timezone_issue(df: pd.DataFrame):
    """Identify timezone issue.

    Requires the RECORD column as exported by the datalogger.
    """
    duplicates = find_timeseries_duplicates(df)
    # Duplicates returns 4 rows per 1 hour of overlap.
    are_even = not duplicates.shape[0] % 4
    sequential = False
    if not duplicates.empty:
        sequence = np.arange(duplicates['RECORD'].iloc[0], duplicates['RECORD'].iloc[-1] + 1)
        # If the sequences are of the same length, no jumps should exist
        # and the records should be sequential.
        sequential = duplicates['RECORD'].shape[0] == sequence.shape[0]
    return are_even and sequential, *np.where(df.index.isin(duplicates.index))


def find_timeseries_duplicates(df: pd.DataFrame):
    """Return duplicated dataframe rows.
    """
    duplicates = df.index.duplicated(False)
    return df[duplicates]


def find_timezone_shift(df: pd.DataFrame, tz_suspects: np.ndarray):
    """Find the last corresponding gap that is likely caused by a
    timezone shift as described by `tz_suspects`.

    # TODO Testing
    """
    assert not len(tz_suspects) % 4, "Not full hour shift"
    N = len(tz_suspects) // 2 - 1
    resampled = df[~df.index.duplicated()].resample('30 min').asfreq()
    gaps = resampled.index.difference(df.index)
    gap_mask = resampled.index.isin(gaps)
    gap_positions = np.where(gap_mask)[0]

    # From all the gap positions check which for distance N
    # have difference N (are sequential). Choose the most recent.
    N_sized_gaps = np.where(
            gap_positions[N:] - gap_positions[:-N] == N
            )[0]
    last_matching_gap = N_sized_gaps[-1]
    offset = N + 1
    return (resampled,
            gap_positions,
            gap_positions[last_matching_gap:last_matching_gap+offset])


def find_timeseries_gaps(df: pd.DataFrame):
    """Identify timeseries gaps.

    Return the resampled gap-filled timeseries dataframe
    together with the gap-filled indices.
    """
    resampled = df[~df.index.duplicated()].resample('30 min').asfreq()
    gaps = resampled.index.difference(df.index)
    gap_mask = resampled.index.isin(gaps)
    gap_positions = np.where(gap_mask)[0]
    return resampled, gap_positions


def fix_timezone_issue(df: pd.DataFrame, suspects: np.ndarray):
    """Correct the erroneous timezone offset existing in a subset
    of the timeseries.

    Use this function to automatically find and correct overlapping
    periods due to accidental timezone differences.

    Objectives:

    **1. End index.**
    
    The end index must be the exclusive end of
    the duplicated period. That means position of `end_date + 1`.
    In an array of even number of elements, that is `len(array) // 2`.

    The count of gaps after this date (index) has to be subtracted from
    the final number.

    **2. Start index.**

    The first element of candidate gaps. The count of gaps before this date
    (index) has to be subtracted from the final number.
    """
    _, all_gaps, candidate_gaps = find_timezone_shift(df, suspects)
    # Get a mutable copy of indices (Alternatively reset index and reset).
    datetime_indices = df.index.to_numpy().copy()
    # Single use case for now.
    assert not len(suspects) % 4
    assert not len(candidate_gaps) % (len(suspects) // 2), candidate_gaps
    # The 1st gap position is where the time change occured.
    start_index = candidate_gaps[0]
    # Get any number of other gaps not related to TZ shift inbetween.
    off_idx = np.where(all_gaps == candidate_gaps[-1])[0][0] + 1
    end_index_negative_offset = all_gaps[off_idx:].size
    # The middle of the suspects + 1 for slicing is the last affected record.
    # Subtract any unrelated gaps from end_index.
    end_index = suspects[-1] - len(suspects) // 2 + 1 - \
        end_index_negative_offset

    # Offset back to UTC from GMT+1
    # We need to get half the duplicates 
    datetime_indices[start_index:end_index] = \
        datetime_indices[start_index:end_index] - \
            pd.Timedelta(f"{len(suspects) // 4} hour")

    # Replace index with corrected version.
    df.index = datetime_indices
    df.index.name = 'TIMESTAMP'
    return df

