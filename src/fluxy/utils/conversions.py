import pandas as pd
import numpy as np

from typing import Sequence

from .config import SiteConfiguration
from .timeseries import find_timeseries_gaps


def scale_dataframe(x: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Linearly project one dataframe onto another using linear regression.

    The dataframe inputs must have the same dimensions.
    """
    dx = x - x.mean()
    dy = reference - reference.mean()
    a = (dx * dy).sum() / (dx ** 2).sum()
    b = reference.mean() - a * x.mean()
    a[a == 0] = 1.
    b.fillna(0, inplace=True)
    return a * x + b


def clip_to_nan(
    data: pd.DataFrame,
    lower_limits: np.ndarray | Sequence | float | None = None,
    upper_limits: np.ndarray | Sequence | float | None = None,
):
    """Discard values out of predefined range and replace with NaN.

    # TODO parameters documentation
    """
    # None inequality assessment supported for dataframes.
    return data.mask((data < lower_limits) | (data > upper_limits),
                     inplace=True)


def add_timestamp_from_doy(df: pd.DataFrame):
    """Try to undo TIMESTAMP drop. Assumes series is timestamp-filled and
    tries to get rid of empty rows.
    """
    # Remove EMPTY rows first.
    # Except the first one if it's empty for some
    # bloody reason. It sets start of era.
    first_row = df.iloc[[0]]
    df = df.iloc[1:]
    # Assume empty rows in the middle of the timeseries were artificially added.
    df = df.dropna(how="all", subset=df.columns.difference(["Year", "DOY", "Time"]))
    df = pd.concat([first_row, df])
    # Assume DOY has only been tampered with in case of 2400H
    # If not, these two lines have no effect.
    DOY = df.DOY.copy()
    DOY[df.Time == 24] += 1
    Time = df.Time.copy()
    Time[Time == 24] = 0
    Time = pd.to_timedelta(Time, "h")
    # Convert to datetime to be able to use the parsing later # to improve.
    Time = (pd.to_datetime("00:00:00") + Time).dt.strftime("%H%M")
    # Build datetime string for the datetime parser.
    datetime_string = df.Year.astype(str) + "-" + DOY.astype(str) + " " + Time
    df["TIMESTAMP"] = pd.to_datetime(datetime_string, format="%Y-%j %H%M")
    return df.set_index("TIMESTAMP")


def add_records_column(df: pd.DataFrame):
    """Try to amend a broken RECORD column.

    Should this require a TIMESTAMPed dataframe?
    """
    assert df.index.name == "TIMESTAMP"
    _, gaps = find_timeseries_gaps(df)
    if gaps.size:
        raise RuntimeError("Can't add RECORD column "
                           "to a timeseries with gaps.")
    df.insert(0, "RECORD", range(df.shape[0]))
    return df


def add_year_doy_time(df: pd.DataFrame):
    """Use the TIMESTAMP column as a reference for Year, DOY and Time.

    Changes 00H to 24H and defines moment as end-of-day.
    """
    assert df.index.name == "TIMESTAMP" and isinstance(df.index, pd.DatetimeIndex)
    df["Year"] = df.index.year
    df["DOY"] = df.index.dayofyear
    df["Time"] = df.index.hour + df.index.minute / 60
    df.loc[df.Time == 0, "DOY"] -= 1
    df.loc[df.Time == 0, "Time"] = 24
    return df
