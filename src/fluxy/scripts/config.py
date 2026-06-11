import sys
import click
import yaml

from ..utils.config import print_config_file


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


@click.command(name="config")
@click.option("-p", "--print", "pprint", is_flag=True,
              help="Print the default configuration")
def main(pprint):
    """Configuration module
    """

    if pprint:
        print_config_file()

    return 0


if __name__ == '__main__':
    sys.exit(main())

