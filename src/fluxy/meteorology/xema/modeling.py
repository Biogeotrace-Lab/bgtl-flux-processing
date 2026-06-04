import numpy as np
import pandas as pd


def get_global_linear_coefficient_arrays(df: pd.DataFrame,
                                         xema: pd.DataFrame):
    """Model meteo data using XEMA variables as independencies.
    
    What is the best way to compute this?
    Should this happen for each column separately or is it statistically
    enough to clean all columns at once?

    NOTE:
    Maybe using the covariance method is more suitable as the
    valid indices do not have to be matching for every column.
    """
    # Clean data for coefficient estimation.
    mutual_indices = df.index.intersection(xema.index)
    Y = df[mutual_indices].to_numpy(float)
    X = xema[mutual_indices].to_numpy(float)
    Xinv = np.linalg.inv(X.mT @ X)
    b = Xinv @ X.mT @ Y
    return b
