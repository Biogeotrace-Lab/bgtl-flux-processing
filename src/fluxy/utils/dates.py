from pathlib import Path
from datetime import datetime


def extract_date_string_from_path(path: str | Path):
    name = Path(path).name
    return name.split("T")[0]


def date_from_year_and_doy(year: int | str, doy: int | str) -> datetime:
    return datetime.strptime(f"{year} {doy}", "%Y %j")


def date_from_year_and_doy_in_path(path: str | Path) -> datetime:
    name = Path(path).stem
    year, doy = name.split("_")[-2:]
    return date_from_year_and_doy(year, doy)
