import shutil
import os
import sys

from pathlib import Path
from ..utils.paths import get_filename
from ..utils.paths import get_parent_directory
from ..utils.paths import get_internal_backup_directory

import click
import glob


def _get_backup_path(name: str):
    """This should create new names depending on the operation or number
    of files.
    """
    backup_dir = get_internal_backup_directory()
    backups = glob.glob(str(backup_dir / ("." + name + "*")))
    version = len(backups)
    return backup_dir / str("." + name + ".bak")


def copy_file(src: str | os.PathLike,
              dst: str | os.PathLike) -> None:
    """Copy a file from source to destination.
    """
    shutil.copy(src, dst)


def move_file(src: str | os.PathLike,
              dst: str | os.PathLike) -> None:
    """Copy a file from source to destination.
    """
    shutil.move(src, dst)


def create_backup(src: str | os.PathLike) -> None:
    """Create a hidden backup file in the same directory.
    """
    src = Path(src)
    name = get_filename(src)
    directory = get_internal_backup_directory()
    destination = directory / _get_backup_path(name)
    copy_file(src, destination)
    click.echo(f"Created backup file.")


def recover_backup(src: str | os.PathLike) -> None:
    """Recover a hidden backup file from the same directory.
    """
    src = Path(src)
    name = get_filename(src)
    path = _get_backup_path(name)

    if path.exists():
        move_file(path, src)
        click.echo("Recovered file from backup.")
    else:
        click.secho(f"There is no backup file for {name}.")
        raise click.Abort()

    sys.exit(0)
