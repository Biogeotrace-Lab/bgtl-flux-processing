import sys
import click
import simpleeval
import pandas as pd
import msgspec
import ast
import operator

from ..io.csv import load_timeseries
from ..utils.config import load_configuration
from ..utils.evaluate import get_math_evaluator_fn


@click.command(name="process-met")
@click.argument("met-csv", type=click.Path(exists=True, dir_okay=False),
                metavar="MET_CSV_FILE", required=True)
@click.option("--config", "-c", "config_name", metavar="CONFIG_NAME",
              required=True)
def main(met_csv, config_name):
    """Not implemented"""
    met_dataframe = load_timeseries(met_csv)
    config = load_configuration(config_name)
    evaluator_fn = get_math_evaluator_fn(met_dataframe)

    if not config.conversions: sys.exit(0)

    # Pressure has to be attached before this step.
    # The conversion step.
    for start_date, variables in config.conversions.items():
        # Construct default transformation matrix for all columns.
        conversion_df = pd.DataFrame(index=met_dataframe.columns,
                                     data={'scalar': 1., 'offset': 0.,
                                           'lower': None, 'upper': None},
                                     dtype='str')

        constants = pd.DataFrame(index=tuple(variables.keys()),
                                 data=tuple(variables.values()),
                                 dtype='str')
        constants.index.name = start_date

        # Temporary; TOGO
        # PA has to be in DF, but it's not right now.
        constants.drop(index="PA", inplace=True)

        # Update transformation matrix with config.
        conversion_df.loc[constants.index] = constants
        conversion_df.fillna("None", inplace=True)

        # Evaluate math expressions in transformation matrix.
        evaluated_dataframe = conversion_df.map(evaluator_fn,
                                                na_action='ignore')

        print(evaluated_dataframe)
        # print(evaluated_dataframe.dtypes)
        # print(evaluated_dataframe.offset + evaluated_dataframe.offset)

    sys.exit(0)


if __name__ == '__main__':
    main()
