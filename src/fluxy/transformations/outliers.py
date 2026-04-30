import numpy as np

from scipy.ndimage import median_filter


def median_filtering_1d(data: np.ndarray, N: int,
                        thresholds: np.ndarray | list[float],
                        axis: int = 1) -> np.ndarray:
    """Perform local outlier filtering using a median window value.

    :param data: The data to filter (2D) of dimensions row x variables.
    :type data: `numpy.ndarray`
    """
    thresholds = np.array(thresholds)
    median = median_filter(data, size=N, axes=axis, mode='reflect')
    data_copy = data.copy()
    data_copy[abs(data_copy - median) > thresholds] = np.nan
    return data_copy
