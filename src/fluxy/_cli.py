"""Dynamically build the command line suite.
"""


import click
import importlib
import colorama

from pathlib import Path


colorama.init(autoreset=True)
SCRIPTS = Path(__file__).parent / "scripts"


@click.group()
def main():
    """Welcome to Biogeotrace Lab's Fluxy -
    The command line suite for flux processing excellence."""


for path in SCRIPTS.glob("[!_]*.py"):
    module = f"fluxy.scripts.{path.stem}"
    module = importlib.import_module(module)
    main.add_command(module.main, name=path.name.split(".")[0])


if __name__ == "__main__":
    main()

