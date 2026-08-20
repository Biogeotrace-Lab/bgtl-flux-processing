import sys
import click


@click.command(name="add-phenology",
               short_help="Add phenocam RGB metadata columns to a " \
               "meteorological file.")
@click.option("-m", "--met-file", metavar="MET_FILE",
              help="The meteorological CSV file to edit.",
              type=click.Path(exists=True))
@click.option("-p", "--pheno", metavar="PHENO_FOLDER",
              help="The folder holding the phenology images.",
              type=click.Path(exists=True, dir_okay=True, file_okay=False))
def main(met_file, pheno):
    """Provide a folder with phenocam images and metadata to be joined
    to a meteorological log file."""
    ...

    sys.exit(0)


if __name__ == '__main__':
    main()
