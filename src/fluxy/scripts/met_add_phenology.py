import sys
import click
import os

from tqdm import tqdm
from collections import defaultdict
from pathlib import Path
from datetime import datetime

from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_if_overwrite

import fileinput
import pandas as pd


@click.command(name="add-phenology",
               short_help="Add phenocam RGB metadata columns to a " \
               "meteorological file.")
@click.option("-m", "--met-file", metavar="MET_FILE",
              help="The meteorological CSV file to edit.",
              type=click.Path(exists=True))
@click.option("-p", "--phenocam-folder", "pheno_folder",
              metavar="PHENOCAM_FOLDER",
              help="The folder holding the phenology images.",
              type=click.Path(exists=True, dir_okay=True, file_okay=False))
def main(met_file, pheno_folder):
    """StarDot Netcams: Provide a folder with phenocam images and metadata to be joined
    to a meteorological log file."""

    phenocam_metadata_paths = []

    # For potential future use.
    # pattern = re.compile(r".*(?!IR).*\.meta$", re.IGNORECASE)

    met_dataframe = load_timeseries(met_file)
    last_date = met_dataframe.index[-1]

    for root, dirs, files in os.walk(pheno_folder):
         dirs.sort()
         files.sort()
         for f in files:
            if f.endswith(".meta") and "IR" not in f.split("_"):
                phenocam_metadata_paths.append(os.path.join(root, f))

    data = defaultdict(list)
    indices = []

    with fileinput.FileInput(files=phenocam_metadata_paths, mode='rb') as f:
        with tqdm(phenocam_metadata_paths,
                  desc="Loading phenology info...",
                  total=len(phenocam_metadata_paths),
                  unit="files") as pbar:
            for line in f:
                bkey, bvalue = line.split(b'=', 1)

                if bkey not in [b'red', b'green', b'blue']:
                    continue

                data[bkey.decode('utf-8')].append(int(bvalue))

                if bkey == b'red':
                    name = Path(f.filename()).stem
                    datestring = name.split("_", 1)[-1]
                    timestamp = datetime.strptime(datestring, "%Y_%m_%d_%H%M%S")
                    indices.append(timestamp)
                    pbar.update()

    # Resample to averaged 30 minutes on endtime.
    phenology_dataframe = pd.DataFrame(
        data=data,
        index=indices
        ).resample('30 min', label='right', closed='right').mean()

    phenology_dataframe = phenology_dataframe.loc[
        phenology_dataframe.index <= met_dataframe.index[-1]]

    # This operation only joins columns.
    # To undo you simply have to drop them.
    # It is a reversible modification of timeseries.
    phenology_added = pd.concat([met_dataframe, phenology_dataframe],
                                axis=1)

    # dataframe_confirm_if_overwrite(phenology_added, met_file)

    sys.exit(0)


if __name__ == '__main__':
    main()
