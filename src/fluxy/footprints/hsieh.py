import numpy as np



P = [.59, 1, 1.33]
D = [.28, .97, 2.44]
Mu = [100, 500, 2000]
k = .4

options = np.array([[ .59,  .28, 100],
                    [1.00, 0.97, 500],
                    [1.33, 2.44, 2000]])


def _get_config(evaluation: np.ndarray, thres: float):
    """Returns a Nx3 array of options.
    
    evaluation < - thres # This should return index 0
    np.abs(evaluation) < thres # This should return index 1
    evaluation > thres # This should return index 2
    """
    indices = np.zeros_like(evaluation)
    indices[evaluation < -thres] = 0
    indices[np.abs(evaluation) < thres] = 1
    indices[evaluation > thres] = 2
    return options[indices].T


def hsieh2d(ustar: np.ndarray,
            Lo: np.ndarray,
            sv: np.ndarray,
            zo: np.ndarray,
            zm: np.ndarray,
            thres: float = .04):
    """Hsieh2D flux footprint model implementation.

    :param zm: Height of measurement.
    :type zm: `np.ndarray`
    """
    zu = zm * (np.log( zm / zo ) - 1 + zo / zm)

    # Use array of relative values `zu / zo` as
    # index for generating option arrays.
    p, d, mu = _get_config(zu / Lo, thres)
    Lx = 100 * zm
    # Let's use the maximum estimation as a common grid.
    X = np.arange(0, Lx.max(), 1)[np.newaxis, ...]
    # Common factor in the fy calculation.
    c = np.divide(np.multiply((-1 / k ** 2 ),
                              # D zu ^ P |L| ^ 1-P
                              (d * zu ** p * abs(Lo) ** ( 1 - p))), X)
    Fc = np.exp(c)
    Fp = - np.multiply(c / X, Fc)
    Xp = ...
    F2H = ...
    # Minimum value per row, between array a and b.
    Xm = min([F2H*zm, Lx])
    b=np.floor(zo*(0.3*(sv/ustar) * (Xm / zo) ** 0.85) / 1.5);
    footprint = ...
    return footprint
