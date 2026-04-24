from typing import Any

import numpy as np



P = [.59, 1, 1.33]
D = [.28, .97, 2.44]
Mu = [100, 500, 2000]
k = .4

options = np.array([[ .59,  .28, 100],
                    [1.00, 0.97, 500],
                    [1.33, 2.44, 2000]])


def _get_config(stability: np.ndarray, thres: float):
    """Returns a Nx3 array of options.
    
    evaluation < - thres # This should return index 0
    np.abs(evaluation) < thres # This should return index 1
    evaluation > thres # This should return index 2
    """
    indices = np.zeros_like(stability, dtype=int)
    # indices[stability < -thres] = 0
    indices[np.abs(stability) < thres] = 1
    indices[stability > thres] = 2
    return options[indices].T


def pdf(x, mu, sigma):
    """Implementation of the gaussian kernel."""
    return np.divide(np.exp(-0.5 * ((x - mu) / sigma) ** 2),
                     (np.sqrt(2 * np.pi) * sigma))


class Hsieh2000:
    """State persistent Hsieh model implementation.
    """
    def __init__(self, X_dim, Y_dim, resolution,
                 stab_thres: float) -> None:
        pass
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


def hsieh2d(ustar: np.ndarray,
            Lo: np.ndarray,
            sv: np.ndarray,
            zo: np.ndarray,
            zm: np.ndarray,
            xy_size: tuple[int, int],
            resolution: float = 1.,
            thres: float = .04,
            eps: float = 1e-3):
    """Hsieh2D flux footprint model implementation.

    :param zm: Height of measurement.
    :type zm: `np.ndarray`
    """
    Xr, Yr = xy_size
    zu = zm * (np.log( zm / zo ) - 1 + zo / zm)

    # Use array of relative values `zu / zo` as
    # index for generating option arrays.
    p, d, mu = _get_config(zu / Lo, thres)

    # Define the grid's X extent.
    X = np.arange(eps, Xr, resolution)[np.newaxis, ...]

    absLop = abs(Lo) ** (1 - p)
    dzupLop = d * zu ** p * absLop

    # Common factor in the fy calculation.
    exp_term = np.divide(np.multiply((-1 / k ** 2 ),
                                      # D zu ^ P |L| ^ 1-P
                                      dzupLop)[..., np.newaxis], X)
    F_expterm = np.exp(exp_term)
    Fy = np.multiply(-exp_term / X, F_expterm)

    # Y variance cube. X must lead the broadcast here.
    # 1 sy per x element per timestep.
    Sy = np.multiply((zo * .3 * sv / ustar)[..., np.newaxis],
                     (X / zo[..., np.newaxis]) ** 0.86)

    # Define the grid's Y extent.
    Y = np.arange(-Yr * .5, Yr * .5, resolution)[np.newaxis, ...]

    # Vectorized version that returns
    # a 3D array of footprints.
    footprints = Fy[..., np.newaxis] *\
        pdf(Y[:, np.newaxis, ...], 0, Sy[..., np.newaxis])

    # Center tower in the footprint.
    footprints = np.pad(footprints, ((0, 0), (footprints.shape[1], 0), (0, 0)))
    return footprints, Fy, X, Y
