import numpy as np

from scipy.ndimage import median_filter
from scipy.ndimage import vectorized_filter


def median_filtering_1d(data: np.ndarray, window_size: int,
                        thresholds: np.ndarray | list[float],
                        axis: int = 1) -> np.ndarray:
    """Perform local outlier filtering using a median window value.

    :param data: The data to filter (2D) of dimensions row x variables.
    :type data: `numpy.ndarray`
    """
    thresholds = np.array(thresholds)
    median = median_filter(data, size=window_size, axes=axis, mode='reflect')
    data_copy = data.copy()
    data_copy[abs(data_copy - median) > thresholds] = np.nan
    return data_copy


def local_median_fillna(data: np.ndarray, size: int | tuple[int]) -> np.ndarray:
    return vectorized_filter(data, np.nanmedian, size=size,
                             mode='constant', cval=np.nan)
