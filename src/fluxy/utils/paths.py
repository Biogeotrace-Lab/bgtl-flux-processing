from pathlib import Path

import os
import click

import fluxy


def get_filename(path: str | os.PathLike | Path) -> str:
    """Return the filename at the end of the complete path.
    """
    return Path(path).name


def get_parent_directory(path: str | Path | os.PathLike) -> Path:
    """Get the parent directory of a path.
    """
    return Path(path).parent


def change_directory(path: str | os.PathLike | Path,
                     directory: str | os.PathLike | Path) -> Path:
    """Replace directory of file path with `directory`.

    Useful for generating paths that change location of
    files.
    """
    name = get_filename(path)
    return Path(directory) / name


def get_package_directory():
    pkg_dir = Path(fluxy.__file__).resolve()
    return pkg_dir.parents[0]


def get_internal_app_directory():
    """Get the internal directory of the app."""
    app_name = os.environ['app-name']
    app_dir = click.get_app_dir(app_name)
    os.makedirs(app_dir, exist_ok=True)
    return Path(app_dir)


def get_or_create_subdirectory(name: str) -> Path:
    """Create and return an app subdirectory if not exists.
    """
    app_dir = get_internal_app_directory()
    subdir = app_dir / name
    os.makedirs(subdir, exist_ok=True)
    return subdir


def get_internal_backup_directory():
    return get_or_create_subdirectory("backup")


def get_internal_config_directory():
    return get_or_create_subdirectory("conf.d")
