import yaml
import os
import datetime
import shutil
import sys
import click

from pathlib import Path

from dataclasses import dataclass
from dataclasses import fields

from typing_extensions import TypedDict
from typing import Literal

from .paths import get_package_directory
from .paths import get_internal_config_directory
from .fs import confirm_to_copy
from .paths import get_filename
from .prompt import confirm_or_abort

import pandas as pd
import urllib.request
import json
import msgspec


_CONFIG_EXT = ".yaml"


class ReadCsvOpts(TypedDict, total=False):
    header: int | None
    skiprows: list | None
    parse_dates: list | None
    index_col: str | None
    na_values: list | None
    sep: str | None
    engine: Literal["c"] | Literal["python"] | Literal["pyarrow"]
    dtype_backend: Literal['numpy_nullable'] | Literal['pyarrow']
    usecols: list[str]

# @dataclass
class ConversionConfig(TypedDict, total=False):
    scalar: float | str
    offset: float | str
    lower: float | str
    upper: float | str

type VariableName = str
type Evaluatable = str | int | float | None
type ConversionVariables = dict[VariableName, ConversionConfig]

class FluxVariableInfo(TypedDict, total=False):
    name: str
    units: str
    range: tuple[Evaluatable, Evaluatable]

type L0ProcessingLevelConfig = dict[VariableName, FluxVariableInfo | None]
type L1ProcessingLevelConfig = dict[VariableName, FluxVariableInfo]
type ValidRanges = dict[VariableName, tuple[Evaluatable, Evaluatable]]
type Conversions = dict[datetime.datetime, ConversionVariables]
type OfflinePeriod = tuple[datetime.datetime, datetime.datetime]

class SiteConfiguration(msgspec.Struct):
    site: str
    read_csv_opts: list[ReadCsvOpts] = []
    conversions: Conversions = {}
    offline: list[OfflinePeriod] = []
    L0: L0ProcessingLevelConfig = {}
    L1: L1ProcessingLevelConfig = {}


class DefaultConfiguration(msgspec.Struct):
    read_csv_opts: list[ReadCsvOpts] = []


def get_ranges(data: L1ProcessingLevelConfig) -> pd.DataFrame:
    """Collect 'range' values per variable from the immediate sublevel
    of a dictionary.
    
    :returns: A DataFrame with ranges per variable column.
    :rtype: pandas.DataFrame
    """
    return pd.DataFrame({k: v['range'] for k, v in data.items()
                         if 'range' in v}, index=['min', 'max'],
                         dtype=object)


def _read_config(path: str | Path) -> SiteConfiguration:
    """Read yaml configuration file."""
    with open(path, "rb") as config_stream:
        return msgspec.yaml.decode(config_stream.read(), type=SiteConfiguration)


def _read_default_config(path: str | Path) -> DefaultConfiguration:
    """Read yaml configuration file."""
    with open(path, "rb") as config_stream:
        return msgspec.yaml.decode(config_stream.read(),
                                   type=DefaultConfiguration)


def _get_config_name(name: str):
    """Return an internal configuration file name based on convention.
    
    #### Convention:
    The provided name is transformed to title and the file extension
    `_CONFIG_EXT` is added.
    """
    return name.title() + _CONFIG_EXT


def write_config(data: SiteConfiguration, path: str) -> None:
    """Write yaml configuration file."""
    with open(path, "wb") as config_stream_out:
        _bytes = msgspec.yaml.encode(data)
        config_stream_out.write(_bytes)
        return yaml.safe_dump(data, config_stream_out)


def get_default_config() -> DefaultConfiguration:
    """Get the default configuration file of the package.
    """
    # Get the directory of the package.
    pkg_directory = get_package_directory()
    return _read_default_config(os.path.join(pkg_directory, "config.yaml"))


def print_config_file(name: str) -> None:
    config_dir = get_internal_config_directory()
    config_name = _get_config_name(name)
    path = config_dir / config_name
    if not path.exists():
        click.echo("Configuration not found.")
        raise click.Abort()
    with open(path) as f:
        shutil.copyfileobj(f, sys.stdout)


def list_configurations():
    """Lists all internal configurations.
    """
    config_dir = get_internal_config_directory()
    list_dir = os.listdir(config_dir)
    # File extensions must be dropped here.
    configuration_list = map(
        lambda x: Path(x).stem + f" (@{str(config_dir / x)})",
        list_dir
        )
    configuration_list = list(configuration_list) or \
        ["No configuration files found."]
    click.echo("\n".join(configuration_list))



CONFIG_REGISTRY = "https://api.github.com/repos/Biogeotrace-Lab/bgtl-flux-processing/contents/site_configurations/{endpoint}"


REGISTRY_REQUEST = urllib.request.Request(
    CONFIG_REGISTRY.format(endpoint=""),
    headers={"User-Agent": "fluxy"}
)


@dataclass()
class GithubFile:
    name: str
    download_url: str

    @classmethod
    def from_dict(cls, data: dict):
        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}        
        return cls(**filtered_data)
    
    def __repr__(self) -> str:
        return f"{Path(self.name).stem} (@{self.download_url})"


def get_configurations_registry():
    """Return a list of available configuration files in the repository 
    registry.
    """
    with urllib.request.urlopen(REGISTRY_REQUEST) as response:
        json_string = response.read().decode("utf-8")
        config_registry = json.loads(json_string)
        config_registry = map(lambda x: GithubFile.from_dict(x), config_registry)
        config_registry = list(config_registry)

    return config_registry or []


def list_configurations_registry():
    """List the official configuration files available on the repository.
    """
    config_registry = get_configurations_registry()
    click.echo("\n".join(map(str, config_registry)))


def save_configuration(src: str | os.PathLike):
    """Save a configuration internally.
    """
    name = get_filename(src)
    config_dir = get_internal_config_directory()
    confirm_to_copy(src, config_dir /  name)
    click.echo(f"Configuration '{name}' saved successfully.")


def delete_configuration(name: str):
    config_dir = get_internal_config_directory()
    config_name = _get_config_name(name)
    path = config_dir / config_name
    if not path.exists():
        click.echo("Configuration not found.")
        raise click.Abort()

    confirm_or_abort(f"Delete configuration {name}?")
    os.remove(path)
    click.echo(f"Configuration {name} deleted successfully.")


def get_configuration_path(name: str) -> Path:
    config_dir = get_internal_config_directory()
    config_name = _get_config_name(name)
    path = config_dir / config_name
    if not path.exists():
        click.echo("Configuration not found.")
        raise click.Abort()

    return config_dir / config_name


def create_configuration(name: str):
    """Create a new configuration file in the current working directory using
    the internal configuration template.
    """
    name = name.title()
    config_file = name + _CONFIG_EXT
    confirm_or_abort(f"Create configuration file {config_file}?")
    pkg_dir = get_package_directory()
    wd = Path(os.getcwd())
    confirm_to_copy(pkg_dir / "config_template.yaml", wd / config_file)

    click.echo(f"Configuration file '{config_file}' created successfully.")
    click.echo("When you are finished editing "
               "the file make sure you save it by using "
               f"'fluxy config --save-config {config_file}'")


def load_configuration(name: str) -> SiteConfiguration:
    """Load the requested configuration in memory.
    """
    config_dir = get_internal_config_directory()
    config_name = _get_config_name(name)
    path = config_dir / config_name

    if not path.exists():
        click.echo("Configuration not found.")
        raise click.Abort()

    return _read_config(path)


def download_configuration(name: str):
    """Download a configuration file from the repository."""
    config_registry = get_configurations_registry()
    name = _get_config_name(name)
    config_file = filter(lambda x: x.name == name, config_registry)
    config_file = list(config_file)
    
    if not len(config_file) == 1:
        click.echo(f"Configuration {name} not found.")
        raise click.Abort()
    request = urllib.request.Request(
        config_file[0].download_url,
        headers={}
    )
    with urllib.request.urlopen(request) as response:
        content = response.read().decode('utf-8')
    
    config_dir = get_internal_config_directory()
    path = config_dir / name

    confirm_or_abort(f"Download and install/replace {name}?")
    with open(path, "w") as destination_file:
        destination_file.write(content)
    
    click.echo(f"The configuration file {name} was downloaded successfully.")
