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
            analysis_res: float = .5,
            downsampling_res: int = 10,
            thres: float = .04,
            Xeps: float = 1e-1,
            stability_eps: float = 1e-5):
    """Hsieh2D flux footprint model implementation.

    :param zm: Height of measurement.
    :type zm: `np.ndarray`
    """
    Xr, Yr = xy_size
    zu = zm * (np.log( zm / zo + stability_eps ) - 1 + zo / (zm + stability_eps))

    # Number of samples to aggregate.
    down_scale = max(1, int(downsampling_res / analysis_res))

    # Use array of relative values `zu / zo` as
    # index for generating option arrays.
    p, d, _ = _get_config(zu / (Lo + stability_eps), thres)

    # Define the grid's X extent.
    X = np.arange(Xeps, Xr, analysis_res)[np.newaxis, ...]

    # X for the downsampled resolution.
    Xds = np.arange(Xeps, Xr, downsampling_res)[np.newaxis]

    absLop_term = abs(Lo) ** (1 - p)
    dzupabsLop_term = d * zu ** p * absLop_term

    # Common factor in the fy calculation.
    exp_term = np.divide(np.multiply((-1 / k ** 2 ),
                                      # D zu ^ P |L| ^ 1-P
                                      dzupabsLop_term)[..., np.newaxis], X)
    F_expterm = np.exp(exp_term)

    # The accuracy of this depends on resolution of X.
    # If the bin size is too large (resolution too coarse)
    # the peak contribution can be lost.
    Fy = np.multiply(-exp_term / X, F_expterm)

    # Maybe we can downsample Fy once calculated with peak identified.
    Fy = Fy.reshape(Fy.shape[0], -1, down_scale).sum(-1)

    # Y variance cube. X must lead the broadcast here.
    # 1 sy per x element per timestep.
    # This also depends on X resolution.
    # Sy close to zero leads to anomalous contribution values.
    Sy = np.multiply((zo * .3 * np.divide(sv, ustar + stability_eps))[..., np.newaxis],
                     np.divide(Xds, zo[..., np.newaxis] + stability_eps) ** 0.86)

    # Define the grid's Y extent.
    Y = np.arange(-Yr * .5, Yr * .5, analysis_res)[np.newaxis, ...]

    # Vectorized version that returns
    # a 3D array of footprints.
    # Y dispersion as a function of X.
    # Multiplying by analysis_res ensures pdf sums to 1.
    cross_wind_pdf = pdf(Y[:, np.newaxis, ...], 0, Sy[..., np.newaxis]) * analysis_res

    c_t, c_x, _ = cross_wind_pdf.shape

    # Downscale.
    cross_wind_pdf = cross_wind_pdf.reshape(c_t, c_x, -1, down_scale)\
        .sum(-1)

    # Get 2D footprints.
    footprints = Fy[..., np.newaxis] * cross_wind_pdf

    # Center tower in the footprint.
    footprints = np.pad(footprints, ((0, 0), (c_x, 0), (0, 0)))

    # I believe it's okay to normalize and force footprint to sum 1.
    # It accounts for numerical errors related to the std of Y dispersion.
    # Should apply it after testing for stability concludes.
    # footprints = footprints / footprints.sum()
    return footprints, Fy, X, Y
