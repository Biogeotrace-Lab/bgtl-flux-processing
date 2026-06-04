# -*- coding: utf-8 -*-
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


def concatenate_csvs(csv_paths: list[str]):
    """Receive a list of csv paths and concatenate their content.

    Writes merged content to the same folder, as a csv file.

    :param csv_paths: An array of paths for the csv files to process.
    :type csv_paths: `list[str]`
    :return: Writes concatenated results on disk.
    :rtype: `None`
    """
    config = get_config()

    if len(csv_paths) < 2: return 0

    directory = path.dirname(csv_paths[0])
    basename = (path.basename(csv_paths[0])
                    # Get rid of extension to not overwrite file.
                    .split(".")[0])

    dataframes = [pd.read_csv(csv_path, **config['general']['read_csv_opts'])
                  for csv_path in csv_paths]

    # Run concatenation and sort.
    concatenated_dataframes = pd.concat(dataframes).sort_index()

    duplicated = concatenated_dataframes.index.duplicated(keep=False)
    
    # Explicitly fail on duplicate indices.
    if duplicated.any():
        raise RuntimeError(f"""{duplicated.sum()} duplicated values
in the timeseries. Fix before proceeding.

Duplicated rows:                        
{concatenated_dataframes[duplicated]}
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
    resampled_concatenated_dataframes['DOY'] = resampled_concatenated_dataframes.index.dayoftheyear # type: ignore
    resampled_concatenated_dataframes['Time'] = resampled_concatenated_dataframes.index.strftime("%H%M") # type: ignore

    resampled_concatenated_dataframes['DOY'][
        resampled_concatenated_dataframes['Time'] == "0000"
        ] -= 1

    # Turn index to column and persist.
    # We can probably drop the RECORD column.
    resampled_concatenated_dataframes.reset_index()\
                           .drop(columns=["RECORD"])\
                           .to_csv(path.join(".", f"{basename}.csv"),
                                   index=False)

    return 0


if __name__ == "__main__":
    sys.exit(concatenate_csvs(csv_paths=sys.argv[1:]))
