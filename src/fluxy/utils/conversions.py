import pandas as pd
import numpy as np

from typing import Sequence
from .config import ConfigDict


def project_analog_values_to_units(data: pd.DataFrame,
                                   scalars: list,
                                   offsets: list | None = None):
    """Convert analog sensor readings (volts) into applicable
    meteorological units.

    # TODO parameters
    """
    data = data.multiply(scalars).add(offsets or 0)
    return data


def clip_to_nan(data: pd.DataFrame,
                lower_limits: np.ndarray | Sequence | None = None,
                upper_limits: np.ndarray | Sequence | None = None):
    """Discard values out of predefined range and replace with NaN.

    # TODO parameters documentation
    """
    # None inequality assessment supported for dataframes.
    return data.mask((data < lower_limits) | (data > upper_limits),
                     inplace=True)


def get_projection_arrays(config: ConfigDict):
    scalars = ...
    offsets = ...
    return scalars, offsets


def get_minmax_arrays(config: ConfigDict):
    lower_limits = ...
    upper_limits = ...
    return lower_limits, upper_limits
