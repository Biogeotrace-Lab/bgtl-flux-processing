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
    indices = np.zeros_like(evaluation, dtype=int)
    indices[evaluation < -thres] = 0
    indices[np.abs(evaluation) < thres] = 1
    indices[evaluation > thres] = 2
    return options[indices].T


def pdf(x, mu, sigma):
    return np.divide(np.exp(-0.5 * ((x - mu) / sigma) ** 2),
                     (np.sqrt(2 * np.pi) * sigma))


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

    # Can we support variable resolution
    # in a vectorized implementation?
    res = 1 # np.maximum(1, Lx // 500)

    # Let's use the maximum estimation as a common grid.
    # Lx.max then is the extend of the grid X axis.
    X_extents = (Lx // res).astype(np.int32)
    X = np.linspace(0, 1, X_extents.max())[np.newaxis, ...]
    print(X.shape)

    # Scale values and broadcast.
    # What should the out of range values be?
    X = X * Lx[..., np.newaxis]
    print(X.shape)
    # Lx actually controls the grid dimensions via `step`.
    # For that, we need to write to different extents.
    # Simply scaling X by Lx is not enough. (Only Lx.max is correct)


    absLop = abs(Lo) ** (1 - p)
    dzupLop = d * zu ** p * absLop
    print(absLop.shape, dzupLop.shape)

    # Common factor in the fy calculation.
    c = np.divide(np.multiply((-1 / k ** 2 ),
                              # D zu ^ P |L| ^ 1-P
                              dzupLop)[..., np.newaxis],
                  X)
    Fc = np.exp(c)
    Fp = - np.multiply(c / X, Fc)
    # Never used.
    # Xp = np.multiply(1 / 2 / k / k, dzupLop)
    F2H = np.multiply(d / .105 / k / k, zm ** -1 * absLop * zu ** p)

    # Minimum value per row, between array a and b.
    # This constraints F2H * zm to grid extent (X axis).
    # It is the X axis spread.
    Xm = np.minimum(F2H * zm, Lx)

    print("X", X.shape, zo.shape, sv.shape, ustar.shape)
    # Y variance cube. X must lead the broadcast here.
    # 1 sy per x element per timestep.
    Sy = (zo * .3 * sv / ustar)[..., np.newaxis] * (X / zo[..., np.newaxis]) ** 0.85

    # Y limits are dependent on b and b depends on Xm.
    b = zo * .3 * np.divide(sv, ustar) * np.divide(Xm, zo) ** 0.85 // 1.5

    # This will not work for every grid
    # as this is fed directly to PDF for
    # the distribution estimation.
    # All Y vectors have to be constructed
    # simaltaneously so relationship between
    # footprints remains intact.
    # These are index extents per time step.
    Y_extents = (4 * b // res).astype(np.int32)
    print(Y_extents)

    # This is the grid extend based on resolution
    # and maximum Y limits. Should there be different sized
    # grids or just value scaling is enough for PDF?
    Ymax = Y_extents.max()
    Ycentre = round(Ymax * .5)
    Y = np.linspace(-2, 2, Ymax)[np.newaxis, ...]

    # Range scaling and broadcasting.
    # This is a (T, Y) matrix.
    Y = Y * b[..., np.newaxis]

    # Y_extents is a vector of size T.
    # This increases linearly for T.
    for i, ext in enumerate(Y_extents):
        # Y has dimensions (T, Y)
        # ext represents Y_ext for the Timestep T.
        Y[i, Ycentre - ext // 2:Ycentre + ext // 2] = np.nan

    # Why is this necessary?
    # This is literally to calculate number of rows.
    # The array should be predefined.
    # Should it not be len(X) or len(Fp)?
    # This can be less than len(Fp) (i.e. min(f2h*zm, Lx)),
    # I guess signifying end of reach.
    # End of reach should probably be portrayed in 
    # the PDF instead, to avoid this mechanism.
    nn = X_extents # This is X_extents pretty much.

    # How many footprints are we looking for produce?
    # Length of input many.
    # Do we need to create a zeroed cube?
    # I think we can just create it ready to be passed
    # to the probability density function as X * Y.
    # No need to preallocate.
    # Dimensions (T, X, Y).
    #
    # This says that nn is expected to be len(Fp) ?
    # footprints = np.zeros(ustar.shape[0], nn, Y.shape[-1])

    # Vectorized version that returns
    # a 3D array of footprints.
    # Fp must have dimensions N x Time
    # Fp scales the row according to value.
    # Goal is to pass a ready T, X, Y array in pdf (nan for out of bounds)
    # that returns the footprint distributions ready.
    print("Y", Y.shape, Y_extents.shape)
    # sy must be 1 scalar per Y column times T.
    # i.e. (T, Y)
    footprints = Fp[..., np.newaxis] * pdf(Y[:, np.newaxis, ...], 0, Sy[..., np.newaxis])
    return footprints, Fp, X, Y
