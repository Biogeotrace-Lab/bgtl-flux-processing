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

    # Overlaps due to timezone change must be hourly
    # (even number x2 - an hour is 4 records in this case)
    assert not len(suspects) % 4
    # The gaps must be of length half that of the overlap suspects.
    assert not len(candidate_gaps) % (len(suspects) // 2), candidate_gaps
    
    # Turn all gaps into a list for using the convenience of
    # using the `.index` method.
    raw_end = suspects[suspects.size // 2]
    raw_start = candidate_gaps[0]

    # Calculate the end index of the affected period.
    # Add any unrelated gap (single gaps) between the last candidate gap
    # and the inclusive period end. These will push the `end_index` further
    # during resampling and they need to be subtracted.
    post_voids_count = sum(map(lambda x: candidate_gaps[-1] < x < raw_end,
                               all_gaps))
    end_index = raw_end - post_voids_count

    # Calculate the starting index of the affected period.
    pre_voids_count = sum(map(lambda x: x < raw_start , all_gaps))
    start_index = candidate_gaps[0] - pre_voids_count

    # Modify the affected period in place.
    datetime_indices[start_index:end_index] = \
        datetime_indices[start_index:end_index] - \
            pd.Timedelta(f"{len(suspects) // 4} hour")

    # Replace index with corrected version.
    df.index = datetime_indices
    df.index.name = 'TIMESTAMP'
    return df

