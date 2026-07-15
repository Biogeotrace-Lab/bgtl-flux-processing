from pathlib import Path

import os
import click

from .._cli import main


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


def get_internal_app_directory():
    """Get the internal directory of the app."""
    app_name = str(main.name)
    app_dir = click.get_app_dir(app_name)
    os.makedirs(app_dir, exist_ok=True)
    return Path(app_dir)


def get_internal_backup_directory():
    app_dir = get_internal_app_directory()
    backup_dir = app_dir / "backup"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir
