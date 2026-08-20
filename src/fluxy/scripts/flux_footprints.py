import sys
import click


@click.command(name="footprints",
               short_help="Not implemented.")
@click.option("--flux-folder", "-f", metavar="FOLDER_PATH", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="The parent folder for the raw flux data to process.")
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True)
def main(flux_folder, config_name):
    """Convert a processed flux timeseries into flux footprints."""

    sys.exit(0)


if __name__ == '__main__':
    main()
