from pathlib import Path


def get_filename(path: str | Path) -> str:
    """Return the filename at the end of the complete path.
    """
    return Path(path).name


def get_parent_directory(path: str) -> Path:
    """Get the parent directory of a path.
    """
    return Path(path).parent


def change_directory(path, directory) -> Path:
    """Replace directory of file path with `directory`.

    Useful for generating paths that change location of
    files.
    """
    name = get_filename(path)
    return Path(directory) / name

