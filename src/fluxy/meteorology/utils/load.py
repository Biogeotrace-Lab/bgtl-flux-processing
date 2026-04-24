from .config import get_default_config

from typing import ParamSpec
from typing import TypeVar
from typing import Callable
from typing import Concatenate

from functools import wraps

import warnings
import pandas as pd


P = ParamSpec("P")
R = TypeVar("R")


def _load_csv_to_dataframe_with_na_values(func: Callable[P, R]) \
    -> Callable[P, R]:
    """Wrapper function to enforce the usage of the configuration file
    `na_values`.
    """
    config = get_default_config()

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "na_values" in kwargs.keys():
            warnings.warn("The provided na_values will not be used. " \
            "Change them in the configuration file instead.")

        kwargs["na_values"] = config["na_values"]
        return func(*args, **kwargs)

    return wrapper


load_csv_with_na_values = _load_csv_to_dataframe_with_na_values(pd.read_csv)
