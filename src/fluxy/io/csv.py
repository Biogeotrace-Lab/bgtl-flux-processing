import pandas as pd
from ..utils.config import SiteConfiguration
from ..utils.config import DefaultConfiguration
from ..utils.config import ReadCsvOpts
from ..utils.config import get_default_config
from ..utils.prompt import confirm_or_abort
from ..utils.fs import create_backup

from typing import Unpack
from typing import IO

import os
import click

from pathlib import Path


_default_config = get_default_config()


def load_timeseries(csv_path: str | Path | os.PathLike | IO[bytes],
                    config: SiteConfiguration | DefaultConfiguration = _default_config,
                    **kwargs: Unpack[ReadCsvOpts]) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    # Extract read_csv opts from configuration
    read_csv_opts = config.read_csv_opts
    errors = []

    for opts in read_csv_opts:
        try:
            # Update opts with kwargs overload.
            opts.update(kwargs)

            # Load the actual file with updated opts.
            timeseries = pd.read_csv(csv_path, **opts) 

            if timeseries.dtypes.isin(["object", "str"]).any():
                raise ArithmeticError(
                    "Non numerical data in timeseries. " \
                    "Check your na_values declaration.")

            return timeseries
        except Exception as e:
            errors.append(e.__repr__())

    click.echo()
    click.echo(f"Couldn't load timeseries {csv_path} with errors:")
    click.echo(f"{"\n\n".join(errors)}")
    raise click.Abort()


def load_flux_timeseries(csv_path: str | Path | os.PathLike | IO[bytes]):
    ...


def dataframe_confirm_inplace_modification_with_backup(df: pd.DataFrame,
                                                       path: str) -> None:
    """Bundle mechanism for modifying CSV files in place safely.
    """
    confirm_or_abort("Create backup and modify file inplace?")
    create_backup(path)
    df.to_csv(path)
    click.echo("File modified inplace.")


def dataframe_confirm_inplace_modification(df: pd.DataFrame,
                                           path: str) -> None:
    """Modify CSV file in place with confirmation.
    """
    confirm_or_abort(f"Modify {path} inplace?")
    df.to_csv(path)
    click.echo("File modified inplace.")


def dataframe_confirm_if_overwrite(df: pd.DataFrame, path: str | Path) -> None:
    """If destination exists, confirm to overwrite.
    """
    msg = "CSV file saved successfully."
    if os.path.exists(path):
        confirm_or_abort(f"{path} already exists. Overwrite?")
        msg = f"Overwritten {path}."
    df.to_csv(path)
    click.echo(msg)
