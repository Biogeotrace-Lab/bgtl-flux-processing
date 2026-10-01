from unittest import TestCase
from fluxy.utils.timeseries import find_timezone_shift
from fluxy.utils.timeseries import fix_timezone_issue
from fluxy.utils.timeseries import potential_timezone_issue

import pandas as pd


class TestTimeshiftFix(TestCase):
    
    def test_1h_shift_identified(self):
        daterange = pd.date_range("2022-01-01", "2023-01-01", freq="30 min")
        df = pd.DataFrame(index=daterange)
        ...
    
    def test_2h_shift_identified(self):
        daterange = pd.date_range("2022-01-01", "2023-01-01", freq="30 min")
        df = pd.DataFrame(index=daterange)
        ...
    
    def test_3h_shift_identified(self):
        daterange = pd.date_range("2022-01-01", "2023-01-01", freq="30 min")
        df = pd.DataFrame(index=daterange)
        ...

    def test_2_5h_shift_failed(self):
        daterange = pd.date_range("2022-01-01", "2023-01-01", freq="30 min")
        df = pd.DataFrame(index=daterange)
        ...

    def test_shift_overlap_is_correct(self):
        ...
    
    def test_shift_gap_without_voids_is_correct(self):
        ...
    
    def test_shift_gap_with_voids_is_correct(self):
        ...

    def test_shift_without_voids_fixed_correctly(self):
        ...
    
    def test_shift_with_voids_fixed_correctly(self):
        ...
