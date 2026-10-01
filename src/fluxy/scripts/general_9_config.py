import sys
import click

from ..utils.config import print_config_file
from ..utils.config import list_configurations
from ..utils.config import create_configuration
from ..utils.config import save_configuration
from ..utils.config import delete_configuration
from ..utils.config import get_configuration_path
from ..utils.config import download_configuration
from ..utils.config import list_configurations_registry

from ._options import CommandWithMutuallyExclusiveOptions


@click.command(name="config",
               cls=CommandWithMutuallyExclusiveOptions,
               mutex=["--list-config",
                      "--list-config-registry",
                      "--print-config",
                      "--create-config",
                      "--save-config",
                      "--edit-config",
                      "--delete-config",
                      "--download-config",
                      "-l", "-c", "-s", "-p", "-d", "-e", "-D", "-r"],
               short_help="The configuration module.")
@click.option("-c", "--create-config", metavar="NAME",
              help="Create a configuration file in directory.")
@click.option("-s", "--save-config", metavar="CONFIG_FILE",
              type=click.Path(exists=True),
              help="Provide the configuration file to save.")
@click.option("-e", "--edit-config", metavar="NAME",
              help="Edit an internal configuration file.")
@click.option("-d", "--delete-config", metavar="NAME",
              help="Delete an internal configuration file.")
@click.option("-p", "--print-config", metavar="NAME",
              help="Print the default configuration.")
@click.option("-l", "--list-config", is_flag=True,
              help="List all saved configurations.")
@click.option("-r", "--list-config-registry", is_flag=True,
              help="List all officially available site-configurations "
              "in the fluxy repository.")
@click.option("-D", "--download-config", metavar="NAME",
              help="Download an official configuration file from the " \
              "fluxy repository.")
def main(create_config, save_config, edit_config, list_config,
         list_config_registry, print_config, delete_config, download_config):
    """The configuration module.
    """
    if list_config:
        list_configurations()

    if list_config_registry:
        list_configurations_registry()

    if create_config is not None:
        create_configuration(create_config)

    if print_config is not None:
        # Provide name to the print config function;
        print_config_file(print_config)

    if save_config is not None:
        save_configuration(save_config)

    if edit_config is not None:
        click.edit(filename=str(get_configuration_path(edit_config)))

    if delete_config is not None:
        delete_configuration(delete_config)

    if download_config is not None:
        download_configuration(download_config)

    sys.exit(0)


if __name__ == '__main__':
    main()
