import pandas as pd

from .xema_client import XEMAClient, XEMARecord
from .variables import xema_namings

from typing import Any, Literal, Self
from typing import Generator
from datetime import date, datetime, timedelta
from tqdm import tqdm

import asyncio
import msgspec
import io


class XEMADataFrame(pd.DataFrame):
    """A XEMA dataframe definition that automatically
    extracts online data for specified periods.

    Object diminishes to regular DataFrame.

    :param index: The array containing the candidate datetimes for data
                filling.
    :type index: `pandas.DatetimeIndex`
    :param variables: The XEMA variable codes to be extracted.
    :type variables: `list[int]`
    """
    def __init__(self, index: pd.DatetimeIndex | list,
                 variables: list[int] = [32, 33, 34, 35, 36],
                 station: Literal["DL"] = "DL") -> None:
        index = pd.DatetimeIndex(index)
        index = index.sort_values()
        delta = timedelta(minutes=30)

        # Turn index endtime to query starttime.
        # Necessary for the request.
        index -= delta

        # Returns all collected and validated records.
        data = asyncio.run(self._collect_xema_data(index, station, variables))

        # Reassemble data into a dataframe.
        dataframe = pd.read_json(io.BytesIO(msgspec.json.encode(data)))

        dataframe = (dataframe
                        .drop_duplicates()
                        .astype({
                            'data_lectura': "datetime64[ns]",
                            'codi_variable': int
                            })
                        .set_index(["data_lectura", "codi_variable"])
                        .loc[:, "valor_lectura"]
                        .unstack()
                        .sort_index()
                        .resample("30 min")
                        .asfreq())
        dataframe.index.rename("TIMESTAMP", inplace=True)
        dataframe.rename(columns=xema_namings, inplace=True)

        # Scale Pressure down to kPa
        dataframe['P'] /= 10

        # Assuming Met30min is endtime logged, XEMA must be offset by
        # the monitoring interval as it is starttime logged.
        # It is verifiably start time because it includes a PEAK value
        # timestamp for the measurement that is always later than the
        # marked timestmap for the 30 minute measurement.
        dataframe.index += delta

        # Load only the specific shifted indices that we need.
        super().__init__(data=dataframe) # type: ignore

    async def _collect_xema_data(self, index: pd.DatetimeIndex,
                                 station: Literal["DL"],
                                 variables: list[int]) -> list[XEMARecord]:
        """Async environment for XEMA requests.
        """
        client = XEMAClient()

        select = "data_lectura,codi_variable,valor_lectura"
        station_filter = "codi_estacio eq '{}'".format(station)
        variable_filter = "codi_variable eq '{}'".format
        time_filter_start = "data_lectura ge '{}'".format
        time_filter_end = "data_lectura le '{}'".format

        timedelta_period = index[-1] - index[0]

        # Break it into 50-day periods. Minimum 2 is required for date_range.
        n_periods_split = max(timedelta_period.days // 50, 2)
        
        daterange = pd.date_range(index[0], index[-1], periods=n_periods_split)

        starts = daterange[:-1]
        ends = daterange[1:]

        total_records = int(timedelta_period.total_seconds()) // 1800
        total_records *= len(variables)

        # Build shared progress bar between tasks.
        pbar = tqdm(desc="Downloading XEMA data", total=total_records)

        # Instantiate common payload
        # collection container.
        payload = []

        async with asyncio.TaskGroup() as tg:
            # Awaits tasks on context manager exits.
            [
                tg.create_task(

                    client.query(
                        select,
                        (station_filter,
                        variable_filter(variable),
                        time_filter_start(start.isoformat()),
                        time_filter_end(end.isoformat())),
                        pbar=pbar,
                        payload_buffer=payload
                        )
                    )

                    for variable in variables
                    for start, end in zip(starts, ends, strict=True)
            ]
        return payload
