from fluxy.io.matlab import pd

from scipy.ndimage import vectorized_filter

import numpy as np
import matplotlib.pyplot as plt


DATA = ("h", "z0", "d", )
ZM = 4.64
K = .4
D_H = .6
Z0_H = .1


def prepare_inputs_for_footprint_calculations(data: pd.DataFrame, z: float):
    """Prepare flux data for footprint estimation.

    :param z: Tower height.
    :type z: `float`
    """
    # This can produce nan elements.
    h = z / (D_H + Z0_H * np.exp(K * data.ubar / data.ustar.add(1e-8)))
    # Smooth to local median in a window of 7 elements.
    h = vectorized_filter(h, np.nanmedian, size=(1, 7),
                          mode='constant', cval=np.nan)
    ...


def pdf(x, mu, sigma):
    """Implementation of the gaussian kernel."""
    return np.divide(np.exp(-0.5 * ((x - mu) / sigma) ** 2),
                     (np.sqrt(2 * np.pi) * sigma))


def plot_footprint(footprint: np.ndarray):
    plt.imshow(footprint)
    plt.close()
