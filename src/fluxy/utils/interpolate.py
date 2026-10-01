import pandas as pd



def interpolate_dataframe_columns(dataframe: pd.DataFrame, columns: pd.Index,
                                  limit: int) -> pd.DataFrame:
    dataframe[columns] = dataframe[columns].interpolate(method='linear',
                                                        limit=limit)
    return dataframe
