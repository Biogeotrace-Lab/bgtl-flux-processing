import h5py
import pandas as pd


class Matlab73(h5py.File):
    """Weak wrapper around :class:`h5py.File` for reading `.mat` files of v7.3+
    """
    def __init__(self, name, mode='r', driver=None, libver=None,
                 userblock_size=None, swmr=False, rdcc_nslots=None,
                 rdcc_nbytes=None, rdcc_w0=None, track_order=None,
                 fs_strategy=None, fs_persist=False, fs_threshold=1,
                 fs_page_size=None, page_buf_size=None, min_meta_keep=0,
                 min_raw_keep=0, locking=None, alignment_threshold=1,
                 alignment_interval=1, meta_block_size=None, *,
                 track_times=False, **kwds):
        super().__init__(name, mode, driver, libver, userblock_size,
                         swmr, rdcc_nslots, rdcc_nbytes, rdcc_w0, track_order,
                         fs_strategy, fs_persist, fs_threshold, fs_page_size,
                         page_buf_size, min_meta_keep, min_raw_keep, locking,
                         alignment_threshold, alignment_interval,
                         meta_block_size, track_times=track_times, **kwds)

        # Can recursively add keys as attributes pandas-style, optionally.

    def __getitem__(self, name):
        att = super().__getitem__(name)
        return att

    def __del__(self):
        self.close()


class MatlabFluxDataFrame(pd.DataFrame):
    """Extract specific 1-d columns from a `.mat` file
    into a `pandas.DataFrame`.
    """
    def __init__(self, filepath: str, keys: list[str]) -> None:
        matfile = Matlab73(filepath)
        super().__init__({k: matfile['data'][k][:].flatten() for k in keys}) # type: ignore
