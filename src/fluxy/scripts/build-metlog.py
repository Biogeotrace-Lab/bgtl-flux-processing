
"""
Created on Wed May  7 15:39:15 2025

@author: 1529783

Code to append metdata from rietvell and alfacada in a one csv file. 


@reviewer: 1818910
This script appears to concatenate multiple logs vertically (time dimension). 

Ideally this only needs to happen once every time there are multiple log files
of the same thing, and then persist the results.


### Usage

For windows:
```powershell
> python .\\Met\\merge_scripts\\met_append.py $(Get-item Y:\\Data\\Rietvell\\MetData\\2025\\CR1000_Biomet*.dat)
```

For linux/mac:
```bash
> python ./Met/merge_scripts/met_append.py Path/To/Drive/Data/Rietvell/MetData/2025/CR1000_Biomet*.dat
```

TODO perhaps make it into a complete CLI tool with help message, description
and properly defined arguments.
"""
 
import pandas as pd
import sys
import warnings

from os import path

from fluxy.utils.config import ConfigDict
from fluxy.utils.config import get_config
from fluxy.utils.tz_offsets import find_timeseries_gaps
from fluxy.io.csv import load_timeseries

import click


@click.command()
@click.argument("csv-like-files", nargs=-1, required=True)
@click.option("--output", default="output.csv", help="The output file for the built meteorological dataset")
def main(csv_like_files: list[str], output):
    """Combine different datalogger files into a finalized master file for processing.

    :param csv_like_files: An array of paths for the csv files to process.
    :type csv_like_files: `list[str]`
    :param output: The desired output file name.
    :type output: `str`
    :return: Writes concatenated results on disk.
    :rtype: `None`
    """
    config = get_config()

    directory = path.dirname(csv_like_files[0])
    basename = (path.basename(csv_like_files[0])
                    # Get rid of extension to not overwrite file.
                    .split(".")[0])

    dataframes = []
    for csv_path in csv_like_files:
        df = load_timeseries(csv_path, config['general'])
        dataframes.append(df)

    # Run concatenation and sort.
    concatenated_dataframes = pd.concat(dataframes).sort_index()

    duplicated = concatenated_dataframes.index.duplicated(keep=False)
    
    # Explicitly fail on duplicate indices.
    if duplicated.any():
        raise RuntimeError(f"""{duplicated.sum()} duplicated values
                    in the timeseries. Fix before proceeding.

                    Duplicated rows:                        
{                   concatenated_dataframes[duplicated]}
                           """)


    # Upsample to the same frequency incase of missing records.
    # Do not fill values.
    resampled_concatenated_dataframes = concatenated_dataframes\
                                        .resample("30 min")\
                                        .asfreq()

    missing_rows = resampled_concatenated_dataframes.index.difference(concatenated_dataframes.index)
    if len(missing_rows):
        warnings.warn(f"""

There are {len(missing_rows)} missing rows in the timeseries.

Missing timestamps:
{pd.Series(missing_rows)}
            """)

    # Add Year, DOY, hour.
    resampled_concatenated_dataframes['Year'] = resampled_concatenated_dataframes.index.year # type: ignore
    resampled_concatenated_dataframes['DOY'] = resampled_concatenated_dataframes.index.dayofyear # type: ignore
    resampled_concatenated_dataframes['Time'] = resampled_concatenated_dataframes.index.strftime("%H%M") # type: ignore

    # 0000 is the end of day / Not start of new day.
    resampled_concatenated_dataframes.loc[resampled_concatenated_dataframes['Time'] == "0000", "DOY"] -= 1

    # Turn index to column and persist.
    # We can probably drop the RECORD column.
    resampled_concatenated_dataframes.reset_index()\
                           .to_csv(path.join(".", f"{basename}.csv"),
                                   index=False)

    return 0


if __name__ == "__main__":
    sys.exit(main(csv_paths=sys.argv[1:]))
