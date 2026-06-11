import pandas as pd

from ..io.csv import load_timeseries
from ..utils.config import SiteConfig
from ..utils.config import get_config
from ..utils.conversions import project_analog_values_to_meteo_units


def process_site_meteo(site: str):
    """Generalization of the meteorological processing scripts
    per location.

    This pipeline processes the merged 30min timeline.

    ## For consideration:
    1. Should this pipeline be able to process individual time
    periods independently?
    """
    config: SiteConfig = get_config()[site]

    # Load data.
    data = load_timeseries(config['file'], config)

    # PA injection. We need atmospheric pressure
    # measurements from the flux sensors.
    data = data

    # Convert volts. Add all variables prior to this.
    data = project_analog_values_to_meteo_units(data, config)

    print(data)
    # Convert volts to meteorological units.
    # For distinct periods in config.yaml
    
    # Fill small linear gaps after conversion.
    # Median filter.


    return 0


def process_site_flux(site: str):
    return 0
