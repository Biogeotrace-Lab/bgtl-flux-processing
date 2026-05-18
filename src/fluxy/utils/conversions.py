import pandas as pd
import numpy as np

from typing import Sequence
from .config import ConfigDict


def project_analog_values_to_units(data: pd.DataFrame, config: ConfigDict):
    """Convert analog sensor readings (volts) into applicable
    meteorological units.

    Proposed functionality:
    Scale iteratively each column mentioned in config.

    # TODO parameters
    """
    data_copy = data.copy()
    conversions = config['volt_conversions']
    periods = sorted(conversions.keys())

    for period in periods:

        # Get column dicts for the period.
        column_dicts = conversions[period]
        columns = column_dicts.keys()

        # Iterate over the columns and indepedent options.
        for column, conv_consts in column_dicts.items():
            print(column)

            scalar = conv_consts.get('scalar', 1)
            offset = conv_consts.get('offset', 0)
            variable = conv_consts.get('var', None)

            lower_limits = conv_consts.get('lower', None)
            upper_limits = conv_consts.get('upper', None)

            if variable:
                globals()[variable] = data[variable]
            if isinstance(scalar, str):
                scalar = eval(scalar)
            if isinstance(offset, str):
                offset = eval(offset)

            # Project column.
            data_copy[[column]] = data_copy[[column]].multiply(scalar).add(offset)

            if lower_limits or upper_limits:
                data_copy[[column]] = clip_to_nan(data_copy[[column]], lower_limits, upper_limits)
    return data_copy


def clip_to_nan(data: pd.DataFrame,
                lower_limits: np.ndarray | Sequence | float | None = None,
                upper_limits: np.ndarray | Sequence | float | None = None):
    """Discard values out of predefined range and replace with NaN.

    # TODO parameters documentation
    """
    # None inequality assessment supported for dataframes.
    return data.mask((data < lower_limits) | (data > upper_limits),
                     inplace=True)


def get_projection_arrays(data: pd.DataFrame, config: ConfigDict):

    scalars = data.copy()
    offsets = data.copy()
    scalars[:] = 1
    offsets[:] = 1

    for period, constants in config['volt_conversions'].items():
        # List of length must be number of columns
        scalars[period:] = []
        offsets[period:] = []

    scalars = ...
    offsets = ...

    return scalars, offsets


def get_minmax_arrays(config: ConfigDict):
    lower_limits = ...
    upper_limits = ...
    return lower_limits, upper_limits
