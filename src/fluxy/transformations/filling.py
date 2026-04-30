import numpy as np

from scipy.ndimage import vectorized_filter


def median(values: np.ndarray, *, axis) -> float:
    return np.nanmedian(values, axis=axis)


def local_median_fillna(data: np.ndarray, size: int | tuple[int]) -> np.ndarray:
    return vectorized_filter(data, median, size=size,
                             mode='constant', cval=np.nan)
