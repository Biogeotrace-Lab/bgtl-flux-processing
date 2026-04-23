import numpy as np


def orient_footprints(footprints, angles):
    return footprints


def wdirection_radians_to_origin_thetas(radians: np.ndarray):
    return - radians * np.pi / 180


def get_rotation_matrices(thetas: np.ndarray):
    """ndarray of size (b, 2, 2)
    """
    return np.array([[np.cos(thetas), -np.sin(thetas)],
                     [np.sin(thetas),  np.cos(thetas)]])
