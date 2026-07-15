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


def dataframe_confirm_inplace_modification(df: pd.DataFrame,
                                           path: str) -> None:
    """Modify CSV file in place with confirmation.
    """
    confirm_or_abort("Modify file inplace?")
    df.to_csv(path)
    click.echo("File modified inplace.")


def dataframe_confirm_if_overwrite(df: pd.DataFrame, path: str | Path) -> None:
    """If destination exists, confirm to overwrite.
    """
    if os.path.exists(path):
        prompt_yes_or_abort("File already exists. Overwrite?")
    df.to_csv(path)
