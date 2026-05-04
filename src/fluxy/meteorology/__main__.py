"""The meteo python package for sensor meteorological data
assembly and preparation for processing.


"""

import os
import sys



# Enter directory to load default configuration file.
# os.chdir(pkg_directory)

# Get configuration.
from ..utils.config import get_config
from ..utils.config import generate_configuration_file_template
from ..utils.load import load_csv_with_na_values
from ..meteorology.xema.xema_dataframe import XEMADataFrame
from ..meteorology.copernicus.ndvi_series import NDVISeries

import pandas as pd
import argparse


argument_parser = argparse.ArgumentParser("EC-meteo",
                                          description="Assemble and clean " \
                                          "meteorological data from EC " \
                                          "towers. Infuse with ancillary " \
                                          "data for processing (XEMA, NDVI)",
                                          epilog="Use before gap filling " \
                                          "and/or met sensor value " \
                                          "conversions.")

argument_parser.add_argument("--met-file", type=str, required=True,
                             help="path to the Met file to preprocess.")
argument_parser.add_argument("--config", type=str, required=False,
                             help="path to yaml configuration file. " \
                             "If not provided, a default configuration file " \
                             "will be used.")
argument_parser.add_argument("--generate-config", action="store_true",
                             help="generate a configuration file in the " \
                             "current directory for editing and exit.")


def main():
    # Get command line arguments.
    options = argument_parser.parse_args(sys.argv[1:])

    if options.generate_config:
        generate_configuration_file_template(".")
        return 0

    # Read met and parse na values as indicated by the `invalid` config array.
    met_dataframe = load_csv_with_na_values(options.met_file)
    # Construct xema dataframe based on met timeseries index.
    xema_dataframe = XEMADataFrame(index=met_dataframe.index) # type: ignore
    # Construct ndvi series based on met timeseries index.
    ndvi_series = NDVISeries(index=[])
    # Concatenate the result column-wise for output.
    result = pd.concat([met_dataframe,
                        xema_dataframe,
                        ndvi_series], axis=1)
    result.to_csv("./test_records.csv")
    return 0


if __name__ == "__main__":
    main()


