import yaml
import os
import fluxy
import datetime
import shutil
import sys

from pathlib import Path
from typing_extensions import TypedDict
from typing import Any


class ReadCsvOpts(TypedDict):
    header: int | None
    skiprows: list | None
    parse_dates: list | None
    index_col: str | None
    na_values: list | None


class ConversionConsts(TypedDict):
    scalar: float | str
    offset: float | str
    lower: float | str
    upper: float | str
    var: str


class Opts(TypedDict):
    read_csv_opts: list[ReadCsvOpts]


class DefaultOpts(Opts):
    read_csv_opts: list[ReadCsvOpts]


class SiteConfig(Opts):
    file: str
    read_csv_opts: list[ReadCsvOpts]
    volt_conversions: dict[datetime.datetime,
                           dict[str, ConversionConsts]]


type ConfigDict = dict[str, SiteConfig]


def _read_config(path: str) -> ConfigDict:
    """Read yaml configuration file."""
    with open(path) as config_stream:
        return yaml.safe_load(config_stream)


def _get_pkg_directory():
    pkg_dir = Path(fluxy.__file__).resolve()
    return pkg_dir.parents[0]


def write_config(data: ConfigDict, path: str) -> None:
    """Write yaml configuration file."""
    with open(path, "w") as config_stream_out:
        return yaml.safe_dump(data, config_stream_out)


def get_default_config() -> ConfigDict:
    """Get the default configuration file of the package.
    """
    # Get the directory of the package.
    pkg_directory = Path(fluxy.__file__).resolve()
    pkg_directory = pkg_directory.parents[0]
    return _read_config(os.path.join(pkg_directory, "config.yaml"))


def generate_configuration_file_template(path: str) -> None:
    """Get a configuration file copy to the specified directory
    for editing.

    :param dir: The directory to copy the configuration file to.
    :type dir: `str`
    :returns:
    :rtype: `None`
    """
    # Get the directory of the package.
    pkg_directory = _get_pkg_directory()
    shutil.copyfile(os.path.join(pkg_directory, "config.yaml"),
                    os.path.join(path, "config.yaml"))


def get_config() -> ConfigDict:
    """Local or default configuration file.
    """
    try:
        config = _read_config("config.yaml")
    except FileNotFoundError:
        config = get_default_config()
    return config


def get_site_config(site: str) -> SiteConfig | None:
    """Local or default configuration file.
    """
    try:
        config = _read_config("config.yaml").get(site)
    except FileNotFoundError:
        config = get_default_config().get(site)
    return config


def print_config_file() -> None:
    pkg_directory = _get_pkg_directory()
    with open(os.path.join(pkg_directory, "config.yaml")) as f:
        shutil.copyfileobj(f, sys.stdout)


def _eval_arithmetic_value():
    ...
