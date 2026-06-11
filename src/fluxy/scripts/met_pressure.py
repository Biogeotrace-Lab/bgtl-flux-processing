import sys
import click


@click.command(name="met-pressure")
def main(argv):
    """Not implemented"""
    for filename in argv:
        ...

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
