from pathlib import Path

import os


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

