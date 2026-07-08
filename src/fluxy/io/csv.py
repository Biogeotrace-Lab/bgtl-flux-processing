import pandas as pd
from ..utils.config import DefaultOpts
from ..utils.config import SiteConfig
from ..utils.config import ReadCsvOpts
from ..utils.config import get_default_config
from ..utils.prompt import prompt_yes_or_abort

from typing import cast

import os
import click

from pathlib import Path


_default_config = get_default_config()['default']


def load_timeseries(csv_path: str | Path | os.PathLike,
                    config: DefaultOpts | SiteConfig = _default_config,
                    **kwargs) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    read_csv_opts = config['read_csv_opts']
    error = "Undefined."
    for opts in read_csv_opts:
        opts = cast(dict, opts)
        opts.update(kwargs)
        try:
            return pd.read_csv(csv_path, **opts)
        except Exception as e:
            error = e

    raise RuntimeError(f"Couldn't load timeseries {csv_path} with error\n {error}")


def dataframe_verify_inplace_modification(df: pd.DataFrame,
                                           path: str) -> None:
    """Bundle mechanism for modifying CSV files in place safely.
    """
    if prompt_yes_or_abort("Modify file inplace?"):
        df.to_csv(path)


def dataframe_write_if_not_exists(df: pd.DataFrame, path: str) -> None:
    """Bundle mechanism for modifying CSV files in place safely.
    """
    if not os.path.exists(path):
        df.to_csv(path)
    else:
        click.echo("File already exists.")
        raise click.Abort()
