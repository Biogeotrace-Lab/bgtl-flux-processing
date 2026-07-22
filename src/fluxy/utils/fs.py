import shutil
import os
import sys

from pathlib import Path
from typing import NoReturn
from ..utils.paths import get_filename
from ..utils.paths import get_parent_directory
from ..utils.paths import get_internal_backup_directory
from ..utils.prompt import confirm_or_abort

import click
import glob
import re


def _get_backup_file_name(src: str | Path, version: int | None = None):
    """Create a unique name based on source path."""
    basename = re.sub(r"[/\\]", "-", str(src))
    v = version if version is None else ''
    return ".{basename}.bak~{command}~{v}".format(basename=basename,
                                                  command=
                                                  os.environ['fluxy-command'],
                                                  v=v)


def _get_backup_path(src: str | Path):
    """Return a backup file destination path based on the processed file
    and chosen operation.
    """
    src = Path(src).resolve()
    backup_dir = get_internal_backup_directory()
    # Explicitly versionless so we can glob.
    filename = _get_backup_file_name(src, version=None)
    backups = glob.glob(str(backup_dir / (filename + "*")))
    version = len(backups)
    return backup_dir / _get_backup_file_name(src, version)


def copy_file(src: str | os.PathLike,
              dst: str | os.PathLike) -> None:
    """Copy a file from source to destination.
    """
    shutil.copy(src, dst)


def confirm_to_copy(src: str | os.PathLike,
                    dst: str | os.PathLike) -> None:
    """Copy file, but ask for confirmation for overwriting.
    """
    msg = ''
    exists = os.path.exists(dst)
    if exists:
        
        confirm_or_abort("File exists. Overwrite?")
        msg = 'Overwritten.'

    copy_file(src, dst)
    click.echo(msg, nl=exists)



def move_file(src: str | os.PathLike,
              dst: str | os.PathLike) -> None:
    """Copy a file from source to destination.
    """
    shutil.move(src, dst)


def confirm_to_move(src: str | os.PathLike,
                    dst: str | os.PathLike) -> None:
    """Copy file, but ask for confirmation for overwriting.
    """
    msg = ''
    exists = os.path.exists(dst)
    if exists:
        
        confirm_or_abort("File exists. Overwrite?")
        msg = 'Overwritten.'

    move_file(src, dst)
    click.echo(msg, nl=exists)


def create_backup(src: str | os.PathLike) -> None:
    """Create a hidden backup file in the same directory.
    """
    src = Path(src)
    destination = _get_backup_path(src)
    copy_file(src, destination)
    click.echo(f"Created backup file.")


def recover_backup(src: str | os.PathLike) -> NoReturn:
    """Recover a hidden backup file from the same directory.
    """
    src = Path(src)
    path = _get_backup_path(src)

    if path.exists():
        move_file(path, src)
        click.echo("Recovered file from backup.")
    else:
        click.secho(f"There is no backup file for {src}.")
        raise click.Abort()

    sys.exit(0)


def confirm_to_recover_backup(src: str | os.PathLike) -> None:
    confirm_or_abort(f"Recover backup for {src}?")
    recover_backup(src)
