import pandas as pd
from ..utils.config import ConfigDict
from ..utils.config import get_default_config


_default_config = get_default_config()['default']


def load_timeseries(csv_path: str, config: ConfigDict = _default_config, **kwargs) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    config = config['read_csv_opts']
    for opts in config:
        opts.update(kwargs)
        try:
            return pd.read_csv(csv_path, **opts)
        except Exception as e:
            error = e

    raise RuntimeError(f"Couldn't load timeseries {csv_path} with error\n {error}")

