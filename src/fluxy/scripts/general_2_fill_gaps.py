import sys
import click
import os

from ._options import CommaSeparatedList
from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_inplace_modification
from ..utils.plotting import PlotterMP
from ..meteorology.xema.variables import xema_meteo_mappings

import numpy as np
import pandas as pd



@click.command(name="fill-gaps",
               short_help="Fill gaps in a meteorological timeseries.")
@click.option("--met-file", "-m", metavar="MET_FILE", required=True,
              type=click.File(),
              help="The timeseries to gap-fill.")
@click.option("--columns", "-c", metavar="COL1,COL2,...",
              required=False,
              type=CommaSeparatedList(),
              help="Columns to gap-fill. [default: all]")
@click.option("--xema", "-x", "xema_flag", is_flag=True,
              required=False,
              help="Use XEMA columns to fill gaps.")
def main(met_file, columns, xema_flag):
    """Convert a processed flux timeseries into flux footprints."""
    met_dataframe = load_timeseries(met_file)

    # Default to a full slice.
    columns = columns or slice(None, None, None)

    # Insert non existent columns.
    met_dataframe[
        [c for c in list(xema_meteo_mappings.keys()) if c not in met_dataframe]
        ] = np.nan

    # Gather known columns irrelevant to gap filling.
    drop_columns = ['RECORD', 'BattV_Avg', 'DOY', 'Year', 'Time']

    # Make a copy for the interpolated array
    # so we can make a comparison.
    interpolated = met_dataframe.copy().drop(columns=drop_columns)

    # Calculate cap lengths to isolate the ones within range.
    # This should go in a utils function.
    # Without this the interpolation gap-fills 8 max out of any number.
    is_na = interpolated.isna()
    cumfwd = is_na.cumsum(axis=0)
    fwd = cumfwd - cumfwd.where(~is_na).ffill(axis=0).fillna(0)
    cumbwd = is_na.iloc[::-1].cumsum(axis=0)
    bwd = (cumbwd - cumbwd.where(~is_na.iloc[::-1]).ffill(axis=0).fillna(0)).iloc[::-1]
    gap_lengths = (fwd + bwd - 1).where(is_na, 0)

    # Execute the built-in interpolation,
    # for specific length and only for closed spaces.
    interpolated[columns] = interpolated[columns]\
        .interpolate(method='linear',
                     axis=0,
                     limit=8,
                     limit_direction='forward',
                     limit_area="inside")\
        .mask(gap_lengths > 8)

    
    # XEMA filling.
    # Xema columns we should be looking at.
    meteo = interpolated[xema_meteo_mappings.keys()]
    xema = interpolated[xema_meteo_mappings.values()]
    xema.columns = meteo.columns

    # This calculation can go in a function in utils.
    dx = xema - xema.mean()
    dy = meteo - meteo.mean()
    a = (dx * dy).sum() / (dx ** 2).sum()
    b = meteo.mean() - a * xema.mean()
    a[a == 0] = 1.
    b.fillna(0, inplace=True)
    # Until here.

    # Scale ancillary data.
    xema = a * xema + b

    # Fill missing values using formatted ancillary data.
    interpolated.fillna(xema, inplace=True)

    # Preview comparison,
    comparison = met_dataframe.drop(columns=drop_columns)\
        .compare(interpolated,
                 keep_equal=False,
                 keep_shape=True).xs("other", level=1, axis=1)

    # Put updates back to the original dataframe.
    met_dataframe[interpolated.columns] = interpolated

    plotter = PlotterMP("Gap filling report")
    rng = np.random.default_rng(seed=0)
    for column in interpolated.columns:
        color = rng.integers(low=0, high=256, size=3).tolist()
        
        plotter.add_line(met_dataframe.index,
                         met_dataframe[column].to_list(),
                         column, color=color, weight=1)

        plotter.add_scatter(comparison.index,
                            comparison[column].tolist(),
                            f"{column} fill",
                            fill_color=(255, 0, 0, 255),
                            outline_color=color,
                            size=10, outline_weight=2)

    plotter.show()

    # Persist changes.
    dataframe_confirm_inplace_modification(met_dataframe, met_file.name)

    sys.exit(0)


if __name__ == '__main__':
    main()
