import yaml
import os
import fluxy

from pathlib import Path
from typing import TypedDict
from typing import Any


class ReadCsvOpts(TypedDict):
    header: int
    skiprows: list
    parse_dates: list
    index_col: str
    na_values: list


class ConfigDict(TypedDict):
    read_csv_opts: ReadCsvOpts
    volt_conversion: list[dict]


def read_config(path: str) -> ConfigDict:
    """Read yaml configuration file."""
    with open(path) as config_stream:
        return yaml.safe_load(config_stream)


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
    return read_config(os.path.join(pkg_directory, "config.yaml"))


def generate_configuration_file_template(path: str) -> None:
    """Get a configuration file copy to the specified directory
    for editing.

    :param dir: The directory to copy the configuration file to.
    :type dir: `str`
    :returns:
    :rtype: `None`
    """
    config = get_default_config()
    write_config(data=config, path=path)


def get_config() -> ConfigDict:
    """Local or default configuration file.
    """
    try:
        config = read_config("config.yaml")
    except FileNotFoundError:
        config = get_default_config()
    return config
    