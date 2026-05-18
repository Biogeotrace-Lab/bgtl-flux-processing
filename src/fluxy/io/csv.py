import pandas as pd
from ..utils.config import ConfigDict


def load_timeseries(csv_path: str, config: ConfigDict) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    return pd.read_csv(csv_path, **config['read_csv_opts'])# .asfreq('30min')
