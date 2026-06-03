import pandas as pd

from .xema_client import XEMAClient
from .variables import xema_variables

from typing import Literal
from datetime import timedelta


class XEMADataFrame(pd.DataFrame):
    """A XEMA dataframe definition that automatically
    extracts online data for specified periods.

    Object diminishes to regular DataFrame.

    :param index: The array containing the candidate datetimes for data
                filling.
    :type index: `pandas.DatetimeIndex`
    """
    def __init__(self, index: pd.DatetimeIndex,
                 station: Literal["DL"] = "DL") -> None:
        index = pd.DatetimeIndex(index)
        index = index.sort_values()
        client = XEMAClient()
        delta = timedelta(minutes=30)
        
        where_query = """
        data_lectura between
        '{start}' and '{end}'
        {validated_only}
        and codi_estacio = '{station}'
        and data_lectura is not null
        """.format(start=(index[0] - delta).strftime("%Y-%m-%dT%H:%M:%S"),
                   end=(index[-1] + delta).strftime("%Y-%m-%dT%H:%M:%S"),
                   station=station,
                   validated_only="and codi_estat = 'V'")

        data = client.query(select="data_lectura, codi_variable, valor_lectura",
                            where=where_query)

        there_is_data = bool(data)

        if there_is_data:
            data = (pd.DataFrame(data).set_index(["data_lectura",
                                                  "codi_variable"])
                                      .loc[:, "valor_lectura"]
                                      .unstack())
            data.index.rename("TIMESTAMP", inplace=True)
            data.rename(columns=xema_variables, inplace=True)
            # Assuming Met30min is endtime logged, XEMA must be offset by
            # the monitoring interval as it is starttime logged.
            data.index += delta
        
        # data = data.resample('30 min').asfreq() # type: ignore
        # Load only the specific shifted indices that we need.
        super().__init__(data=data) # type: ignore
