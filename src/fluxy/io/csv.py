import pandas as pd
from ..utils.config import get_config


def load_timeseries(csv_path: str) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    config = get_config()
    return pd.read_csv(csv_path, **config['read_csv_opts'])# .asfreq('30min')
