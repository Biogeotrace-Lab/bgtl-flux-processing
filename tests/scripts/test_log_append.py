
import unittest
import pandas as pd
import shutil
import tempfile


def setUpModule():
    global TEST_DIR
    TEST_DIR = tempfile.mkdtemp()
    date_range = pd.date_range("2022-01-01", "2023-01-01")


def tearDownModule():
    global TEST_DIR
    shutil.rmtree(TEST_DIR)


class TestExtensionRestrictions(unittest.TestCase):
    
    def test_extension_lacks_timestamp(self):
        ...

    def test_extension_index_not_sorted(self):
        ...
    
    def test_extension_not_extending(self):
        ...


class TestMasterfileIntegrity(unittest.TestCase):
    ...


class TestBackupAndRecovery(unittest.TestCase):
    ...

