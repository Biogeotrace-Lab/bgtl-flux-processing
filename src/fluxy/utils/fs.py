import shutil
import os

from pathlib import Path
from fluxy.utils.paths import get_filename
from fluxy.utils.paths import get_parent_directory


def _get_backup_name(name: str) -> str:
    return "." + name + ".bak"


def copy_file(src: str | os.PathLike,
              dst: str | os.PathLike) -> None:
    """Copy a file from source to destination.
    """
    shutil.copy(src, dst)


def create_backup(src: str | os.PathLike) -> None:
    """Create a hidden backup file in the same directory.
    """
    src = Path(src)
    name = get_filename(src)
    directory = get_parent_directory(src)
    copy_file(src, directory / _get_backup_name(name))


def recover_backup(src: str | os.PathLike) -> None:
    """Recover a hidden backup file from the same directory.
    """
    src = Path(src)
    name = get_filename(src)
    directory = get_parent_directory(src)
    copy_file(directory / _get_backup_name(name), src)
