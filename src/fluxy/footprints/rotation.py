import numpy as np


def rotate_footprints(footprints: np.ndarray, thetas: np.ndarray,
                      center: tuple[int, int]):
    shape = footprints.shape
    # Bx2x3
    t_matrix = get_reverse_rotation_matrices(thetas, center)
    backwards_rotation_map = get_backwards_rotation_map(shape, t_matrix)
    rotated_footprints = get_bilinearly_resampled_footprint(footprints,
                                                            backwards_rotation_map)    
    return rotated_footprints


def get_reverse_rotation_matrices(thetas: np.ndarray, center: tuple[int, int]):
    """ndarray of size (b, 2, 3)
    """
    cy, cx = center
    radians = np.radians(-thetas)
    cos_t = np.cos(radians)
    sin_t = np.sin(radians)
    ty = cy - (cy * cos_t + cx * sin_t)
    tx = cx - (cy * sin_t + cx * cos_t)
    return np.array([[cos_t, -sin_t, ty],
                     [sin_t, cos_t, tx]]).transpose(-1, 0, 1)


def get_backwards_rotation_map(shape: tuple[int, int, int],
                               transform_matrix: np.ndarray):
    # B H W
    _, h, w = shape

    # np.indices outputs a 3D array for a single grid.
    # Move the coordinate dimension to the end.
    coords = np.indices((h, w)).transpose(1, 2, 0)

    # Add the dummy Z dimension for center offset.
    coords = np.pad(coords, ((0, 0), (0, 0), (0, 1)), constant_values=1)

    # Einstein notation calculation. collapse j to i.
    return np.einsum('bij, hwj -> bhwi', transform_matrix, coords)


def get_bilinearly_resampled_footprint(footprints: np.ndarray,
                                       backwards_map: np.ndarray):
    """Perform bilinear resampling.
    """
    b, h, w, _ = backwards_map.shape

    batch_idx = np.arange(b)[:, None, None]
    rows = backwards_map[..., 0]
    cols = backwards_map[..., 1]

    # Top left of a 2x2 window.
    idx_rows = np.floor(rows).astype(int)
    idx_cols = np.floor(cols).astype(int)

    # Distance from top == How close to bottom
    frac_bottom = rows - idx_rows
    # Distance from left == How close to right
    frac_right = cols - idx_cols
    # Distance from bottom == How close to top
    frac_top = 1 - frac_bottom
    # Distance from right == How close to left
    frac_left = 1 - frac_right

    # This is an element shorter than the original valid range,
    # because we will also inspect one element further.
    valid_mask = ((idx_rows >= 0) & (idx_rows < h - 1) &
                  (idx_cols >= 0) & (idx_cols < w - 1))

    # Get the top-bottom and left-rigth combinations for element indices.
    idx_rows_t = np.clip(idx_rows, 0, h - 1)
    idx_rows_b = np.clip(idx_rows + 1, 0, h - 1)
    idx_cols_l = np.clip(idx_cols, 0, w - 1)
    idx_cols_r = np.clip(idx_cols + 1, 0, w - 1)

    # Get the 4 adjacent pixels for bilinear interpolation.
    tl = footprints[batch_idx, idx_rows_t, idx_cols_l]
    tr = footprints[batch_idx, idx_rows_t, idx_cols_r]
    bl = footprints[batch_idx, idx_rows_b, idx_cols_l]
    br = footprints[batch_idx, idx_rows_b, idx_cols_r]

    # Calculate bilinear interpolation result.
    resampled_footprints = (tl * frac_top * frac_left +
                            tr * frac_top * frac_right +
                            bl * frac_bottom * frac_left +
                            br * frac_bottom * frac_right)

    # Remove out of bounds values.
    resampled_footprints[~valid_mask] = 0
    return resampled_footprints
