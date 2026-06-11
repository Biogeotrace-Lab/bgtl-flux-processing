import pandas as pd
from ..utils.config import DefaultOpts
from ..utils.config import SiteConfig
from ..utils.config import ReadCsvOpts
from ..utils.config import get_default_config
from typing import cast


_default_config = get_default_config()['default']


def load_timeseries(csv_path: str,
                    config: DefaultOpts | SiteConfig = _default_config,
                    **kwargs) -> pd.DataFrame:
    """Load CSV into a DataFrame with preconfigured options in `config.yaml`
    """
    read_csv_opts = config['read_csv_opts']
    error = "Undefined."
    for opts in read_csv_opts:
        opts = cast(dict, opts)
        opts.update(kwargs)
        try:
            return pd.read_csv(csv_path, **opts)
        except Exception as e:
            error = e

    raise RuntimeError(f"Couldn't load timeseries {csv_path} with error\n {error}")

