import sys
import click

from ..io.csv import load_timeseries
from ..meteorology.xema.xema_dataframe import XEMADataFrame
from ..meteorology.xema.variables import xema_namings
from ..io.csv import dataframe_confirm_inplace_modification

import pandas as pd
import numpy as np

from ._options import CommaSeparatedList


@click.command(name="add-xema",
               short_help="""Add columns from the XEMA meteorological network to a
                   meteorological timeseries file.
                   """)
@click.option("-m", "--met-file", metavar="MET_FILE",
              help="The meteorological CSV file to edit.",
              type=click.Path(exists=True))
@click.option("-v", "--variables", metavar="VARCODE1,VARCODE2,...",
              help="The variable to query. See XEMA variable codes.",
              type=CommaSeparatedList(), required=False,
              default="32, 33, 34, 35, 36",
              show_default=True)
@click.option("-s", "--station", metavar="STATION",
              help="The XEMA station to query. See XEMA station codes.",
              type=str, required=False, default='DL',
              show_default=True)
def main(met_file, variables, station):
    """Add columns from the XEMA meteorological network in a
    meteorological timeseries file.
    """
    met_dataframe = load_timeseries(met_file)

    # Check if XEMA present in timeseries.
    xema_subset = met_dataframe.loc[:, [col for col in met_dataframe.columns
                                        if col.startswith("XEMA_")]]

    # Period missing from the xema_subset.
    indices = xema_subset.loc[xema_subset.last_valid_index():].index

    # Get the XEMA measurements for that period
    # and mark the columns with prefix.
    xema = XEMADataFrame(indices.to_list(), variables, station)
    xema = xema.add_prefix("XEMA_")

    # If it's the first time, the columns will need to be added,
    # so that met_data.fillna will be able to work and insert the values.
    if met_dataframe.columns.intersection(xema.columns).empty:
        met_dataframe[xema.columns] = np.nan

    # Insert data w/ label-based alignment.
    # Attention: This wil fail if chema columns do not exist in met.
    met_dataframe.fillna(xema, inplace=True)

    # Preview dataframe before persistence.
    click.echo(met_dataframe)
    click.echo(f"{xema.shape[0]} XEMA rows were populated "
               f"from {xema.index[0]} to {xema.index[-1]}.")

    # Persist changes to disk w/ confirmation.
    dataframe_confirm_inplace_modification(met_dataframe, path=met_file)
    sys.exit(0)


if __name__ == '__main__':
    main()
