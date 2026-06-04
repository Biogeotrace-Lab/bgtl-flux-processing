import pandas as pd
from ..utils.config import ConfigDict


def load_timeseries(csv_path: str, config: ConfigDict) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    for opts in config["read_csv_opts"]:
        try:
            return pd.read_csv(csv_path, **opts)
        except:
            ...

    raise RuntimeError("Couldn't load timeseries.")

