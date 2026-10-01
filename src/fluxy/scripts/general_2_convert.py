import sys
import click
import pandas as pd
import msgspec

from ..io.csv import load_timeseries
from ..io.csv import dataframe_confirm_inplace_modification_with_backup
from ..utils.config import load_configuration
from ..utils.evaluate import get_math_evaluator_fn
from ..utils.paths import get_parent_directory

import numpy as np
import msgspec


@click.command(name="convert-to-units",
               short_help="Convert raw volt measurements captured by a "
               "datalogger to meteorological units.")
@click.option("-m", "--met-file", "met_file",
              type=click.Path(exists=True, dir_okay=False),
                metavar="MET_CSV_FILE", required=True)
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True)
def main(met_file, config_name):
    """Convert raw volt measurements captured by a datalogger to 
    meteorological units.

    This module using the `conversions` section of the provided configuration
    file to apply the defined transformations.

    WARNING: This cannot be used to a masterfile more than once, as you cannot
    skip already transformed values. It should be used as a transformation
    pipeline for its extensions.
    """
    # This is the entire dataframe.
    # We can either keep track of the timestamps we convert,
    # so the conversions are not reapplied, or only permit usage for batches.
    met_dataframe = load_timeseries(met_file)

    if "processed_to_units" not in met_dataframe.columns:
        met_dataframe.insert(0, column="processed_to_units", value=False)

    # Only get unprocessed rows.
    met_dataframe_subset = met_dataframe[~met_dataframe.processed_to_units]
    met_dataframe_subset['processed_to_units'] = True

    config = load_configuration(config_name)
    evaluator_fn = get_math_evaluator_fn(met_dataframe)

    if not config.convert_to_units: sys.exit(0)

    # Pressure has to be attached before this step.
    # The conversion step.
    for start_date, variables in config.convert_to_units.items():

        # Construct the transformation dataframe based on the configuration.
        constants = pd.DataFrame(index=tuple(variables.keys()),
                                 data=tuple(msgspec.structs.asdict(vopt) 
                                            for vopt in variables.values()),
                                 dtype='str')

        constants.index.name = start_date

        # Temporary; TOGO
        # PA has to be in the Met DataFrame, but it's not right now.
        # Remove this line when `add-pressure` is completed.
        constants.drop(index="PA", inplace=True)

        # The columns that are going to be converted.
        conversion_columns = constants.index

        # Update transformation matrix with config.
        # conversion_df.loc[constants.index] = constants
        # conversion_df.fillna("None", inplace=True)

        # Evaluate math expressions in transformation matrix.
        # Transpose the resulting matrix so the columns are on top.
        evaluated = constants.map(evaluator_fn, na_action='ignore').T

        # Format the conversion constants in a dictionary.
        # We can unify this loop with the actual conversion operations
        # for efficiency in the future.
        conversion_constants = {}
        for row_id, serie in evaluated.iterrows():
            serie = serie.to_frame().T
            cols_to_explode = [
                col for col in serie.columns
                if isinstance(serie[col].iloc[0],
                              (pd.Series, list, tuple, np.ndarray))
                ]
            serie = serie.explode(cols_to_explode) if cols_to_explode else serie
            serie = serie.values.astype('float32')
            conversion_constants[row_id] = serie

        # This is not the most efficient operation but it is safe.
        # We can convert this to numpy for speed if we think it is needed.
        met_dataframe_subset.loc[start_date:, conversion_columns] *=\
              conversion_constants['scalar']
        met_dataframe_subset.loc[start_date:, conversion_columns] +=\
              conversion_constants['offset']
        met_dataframe_subset.loc[start_date:, conversion_columns] =\
              met_dataframe_subset.loc[start_date:, conversion_columns]\
                .clip(conversion_constants['lower'],
                      conversion_constants['upper'])

    # Rejoin the processed subset.
    met_dataframe[~met_dataframe.processed_to_units] = met_dataframe_subset

    # Preview the complete met dataframe.
    click.echo(met_dataframe)

    # Backup and modify the entire met dataframe inplace.
    dataframe_confirm_inplace_modification_with_backup(met_dataframe, met_file)

    sys.exit(0)


if __name__ == '__main__':
    main()
