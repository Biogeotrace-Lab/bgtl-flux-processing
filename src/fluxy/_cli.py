"""Dynamically build the command line suite.
"""

import re
import click
import importlib
import colorama

from pathlib import Path


colorama.init(autoreset=True)
SCRIPTS = Path(__file__).parent / "scripts"


class SphinxCleanGroup(click.Group):
    def format_help(self, ctx, formatter):
        """
        Intercepts the terminal help output and cleans up Sphinx/RST syntax 
        so terminal users don't see raw directives.
        """
        # 1. Grab the raw docstring (Click treats this as self.help)
        raw_help = self.help or ""
        
        # 2. Clean up the Sphinx directives for the terminal
        # Remove ".. code-block:: powershell" lines
        cleaned_help = raw_help.split(".. code-block::")[0]

        # 3. Temporarily swap the help text to the clean version for the terminal output
        original_help = self.help
        self.help = cleaned_help.strip()
        
        # 4. Call Click's native help formatter with our clean text
        super().format_help(ctx, formatter)
        
        # 5. Restore the original so Sphinx can still read the raw RST later
        self.help = original_help


@click.group(name="fluxy", cls=SphinxCleanGroup)
def main():
    r"""Welcome to Biogeotrace Lab's Fluxy -
    The command line suite for flux processing excellence.

    .. code-block:: pwsh

        # Use this command to print the help message
        # and explore the commands in the terminal
        $ fluxy --help
    """


for path in SCRIPTS.glob("[!_]*.py"):
    module = f"fluxy.scripts.{path.stem}"
    module = importlib.import_module(module)
    main.add_command(module.main)


if __name__ == "__main__":
    main()

