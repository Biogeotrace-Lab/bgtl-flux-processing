import sys
import click
import os

from typing import cast

from tqdm import tqdm
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_inplace_modification

import pandas as pd
import simplejpeg


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
    to a meteorological log file. It currently only utilizes the bottom half
    of the provided phenocam image."""

    # Undo mechanism.
    if False:
        ...

    phenocam_jpeg_paths = []

    # For potential future use.
    # pattern = re.compile(r".*(?!IR).*\.meta$", re.IGNORECASE)

    met_dataframe = load_timeseries(met_file)

    if {'red', 'green', 'blue'}.difference(met_dataframe.columns):
        last_date = datetime.fromtimestamp(0)
    else:
        last_date = met_dataframe[['red', 'green', 'blue']].last_valid_index()

    for root, dirs, files in os.walk(pheno_folder):
         dirs.sort()
         files.sort()
         for f in files:
            if f.endswith(".jpg") and "IR" not in f.split("_"):
                phenocam_jpeg_paths.append(os.path.join(root, f))

    data = defaultdict(list)
    indices = []

    with ProcessPoolExecutor(4) as executor:
        processes = executor.map(decode_jpeg, phenocam_jpeg_paths)

        for result in tqdm(processes, total=len(phenocam_jpeg_paths),
                           desc="Extracting phenology data...",
                           unit="jpeg"):
            idx, red, green, blue = result
            indices.append(idx)
            data['red'].append(red)
            data['green'].append(green)
            data['blue'].append(blue)

    # Resample to averaged 30 minutes on endtime.
    phenology_dataframe = pd.DataFrame(
        data=data,
        index=indices
        ).resample('30 min', label='right', closed='right').mean()

    # Correct local time without daylight savings (GMT+1) to UTC.
    phenology_dataframe.index -= pd.Timedelta("1H") # type: ignore

    phenology_dataframe = phenology_dataframe.loc[
        # Puts a limit incase we have more phenology rows
        # than meterology rows, for some reason.
        phenology_dataframe.index <= met_dataframe.index[-1]
        ]

    # Label-based alignment.
    met_dataframe[phenology_dataframe.columns] = phenology_dataframe

    # Preview dataframe.
    click.echo(met_dataframe)

    # Modify inplace without backup.
    dataframe_confirm_inplace_modification(met_dataframe, met_file)

    sys.exit(0)


def decode_jpeg(jpeg_file):
    name = Path(jpeg_file).stem
    datestring = name.split("_", 1)[-1]
    timestamp = datetime.strptime(datestring, "%Y_%m_%d_%H%M%S")
    with open(jpeg_file, 'rb') as jpg:
        b = jpg.read()
        array = simplejpeg.decode_jpeg(b, min_factor=8, min_height=100)
        # Use the bottom half of the image for now.
        array = array[array.shape[0] // 2:]
    return timestamp, *array.mean((0, 1))


if __name__ == '__main__':
    main()
