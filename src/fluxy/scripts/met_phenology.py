import sys
import click


@click.command(name="met-phenology",
               short_help="Add RGB metadata columns to a meteorological file.")
@click.option("-m", "--met-file", metavar="MET_FILE",
              help="The meteorological file to edit.")
@click.option("-p", "--pheno", metavar="PHENO_FOLDER",
              help="The folder holding the phenology images.")
def main(met_file, pheno):
    """Not implemented"""
    ...

    sys.exit(0)


if __name__ == '__main__':
    main()
