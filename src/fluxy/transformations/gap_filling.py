
import pandas as pd
import numpy as np


def timebased_fill(dataframe: pd.DataFrame, timesteps: int) -> pd.DataFrame:
    """Gap fill a timeseries based on time intervals.
    """
    return dataframe.interpolate("time", limit=timesteps)


