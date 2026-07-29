"""Dynamically build the command line suite.
"""
import os
import click
import importlib
import colorama

from pathlib import Path
import logging

colorama.init(autoreset=True, wrap=True)
logging.basicConfig(level=logging.WARNING)

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
@click.pass_context
def main(ctx: click.Context):
    r"""Welcome to Biogeotrace Lab's Fluxy -
    The command line suite for flux processing excellence.

    .. code-block:: pwsh

        # Use this command to print the help message
        # and explore the commands in the terminal
        $ fluxy --help
    """
    APPDIR = click.get_app_dir(str(main.name))
    os.makedirs(APPDIR, exist_ok=True)

    if ctx.info_name:
        os.environ['app-name'] = ctx.info_name

    if ctx.invoked_subcommand is not None:
        os.environ['fluxy-command'] = ctx.invoked_subcommand


for path in sorted(SCRIPTS.glob("[!_]*.py")):
    module = f"fluxy.scripts.{path.stem}"
    module = importlib.import_module(module)
    main.add_command(module.main, module.main.name)


if __name__ == "__main__":
    main()

