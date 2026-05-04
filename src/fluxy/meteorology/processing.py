import pandas as pd
from ..io.csv import load_timeseries


def process_meteorological_data(argv):
    data = load_timeseries(argv.met_path)
    
    return 0
