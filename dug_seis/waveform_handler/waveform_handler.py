# DUGSeis
# Copyright (C) 2021 DUGSeis Authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Object used to orchestrate, cache, and facilitate waveform access within
DUGSeis.
"""

import functools
import hashlib
import logging
import re
import pathlib
import typing

import numpy as np
import obspy
import pyasdf
import tqdm

from ..util import pretty_filesize
from .indexing import index_trace, combine_caches, _interweave_arrays
from .utils import compute_sha256_hash_for_file

logger = logging.getLogger(__name__)

FILENAME_REGEX = re.compile(
    r"""
^                                                              # Beginning of string
(\d{4})_(\d{2})_(\d{2})T(\d{2})_(\d{2})_(\d{2})[_\.](\d{6})Z?  # Start time as capture groups
__                                                             #
(\d{4})_(\d{2})_(\d{2})T(\d{2})_(\d{2})_(\d{2})[_\.](\d{6})Z?  # End time as capture groups
__
.*                                                             # Rest of name
$                                                              # End of string.
""",
    re.VERBOSE,
)


@functools.lru_cache(maxsize=20)
def _get_open_asdf_file(filename: pathlib.Path) -> pyasdf.ASDFDataSet:
    """
    Get an open ASDF file.

    Use a LRU cache to get fast repeated file accesses.
    """
    return pyasdf.ASDFDataSet(filename=str(filename), mode="r")


@functools.lru_cache(maxsize=200)
def _get_channel_from_file(filename: pathlib.Path, channel_id: str) -> obspy.Trace:
    """
    Get an open ASDF file.

    Use a LRU cache to get fast repeated file accesses.
    """
    # Get files - already cached.
    ds = _get_open_asdf_file(filename)

    sta = ds.waveforms[".".join(channel_id.split(".")[:2])]
    items = [i for i in sta.list() if i.startswith(channel_id)]
    if not len(items):
        raise ValueError(f"Could not find data for channel '{channel_id}'")
    assert len(items) == 1, f"{items}"
    st = sta[items[0]]

    return st[0]


class WaveformHandler:
    """
    Central class handling waveform access for DUGseis.

    Args:
        waveform_folders: Folders containing the waveforms as ASDF files.
        cache_folder: Some information about the files must be cached. Store
            that information here.
        index_sampling_rate_in_hz: The desired sampling rate of the waveform
            index.
        start_time: Limit temporal range.
        end_time: Limit temporal range.
        existing_caches: List of already read caches.
    """

    def __init__(
        self,
        waveform_folders: typing.List[pathlib.Path],
        cache_folder: pathlib.Path,
        index_sampling_rate_in_hz: int,
        start_time: obspy.UTCDateTime,
        end_time: obspy.UTCDateTime,
        existing_caches: typing.Optional[typing.Dict] = None,
    ):
        self._start_time = start_time
        self._end_time = end_time
        self._index_sampling_rate_in_hz = index_sampling_rate_in_hz
        self._waveform_folders = [pathlib.Path(i) for i in waveform_folders]
        self._cache_folder = pathlib.Path(cache_folder)
        self._open_folder()
        self._build_cache(existing_caches=existing_caches)

    @property
    def starttime(self) -> obspy.UTCDateTime:
        """
        Time of the first sample.
        """
        return min(t[0] for t in self._time_ranges)

    @property
    def endtime(self) -> obspy.UTCDateTime:
        """
        Time of the last sample.
        """
        return max(t[1] for t in self._time_ranges)

    @property
    def receivers(self) -> typing.List[str]:
        """
        List of all receivers.
        """
        return self._cache["receivers"]

    @property
    def channel_list(self) -> typing.List[str]:
        """
        Get a list of all channels.
        """
        return self._cache["receivers"]

    def _get_index_for_channel(self, channel_id: str) -> int:
        """
        Get the cache index for the channel id.

        Args:
            channel_id: Channel to use.
        """
        return self.receivers.index(channel_id)

    @property
    def sampling_rate(self) -> float:
        """
        Sampling rate in Hz.
        """
        return self._cache["data_sampling_rate_in_hz"]

    @property
    def dt(self) -> float:
        """
        Sample spacing in seconds.
        """
        return 1.0 / self.sampling_rate

    @property
    def _cache_start_timestamp_ns(self) -> int:
        """
        Time of the first sample in the cache as a nanosecond timestamp.
        """
        return self._cache["start_time_stamp_in_ns"]

    @property
    def _cache_end_timestamp_ns(self) -> int:
        """
        Time of the last sample in the cache as a nanosecond timestamp.
        """
        return (
            self._cache_start_timestamp_ns + (self._cache_npts - 1) * self._cache_dt_ns
        )

    @property
    def _cache_npts(self) -> int:
        """
        Number of time samples in the binned cache.
        """
        return self._cache["data"].shape[-1]

    @property
    def _cache_dt_ns(self) -> int:
        """
        Sample spacing of the the cache in nanoseconds.
        """
        return self._cache["cache_dt_ns"]

    def _build_cache(self, existing_caches: typing.Optional[typing.Dict] = None):
        self._cache_folder.mkdir(parents=True, exist_ok=True)

        caches = {}

        filename_receivers_map = {}

        for name, info in tqdm.tqdm(
            self._files.items(), desc="Creating/updating cache"
        ):
            # Reuse existing caches if necessary.
            if existing_caches is None or name not in existing_caches:
                single_file_cache = self._cache_single_file(filename=name, info=info)
            else:
                single_file_cache = existing_caches[name]

            caches[name] = single_file_cache
            filename_receivers_map[name] = set(single_file_cache["receivers"])

        # Combine everything into a single cache.
        self._individual_caches = caches
        self._cache = combine_caches(caches=list(caches.values()))

        # Keep track of which file stores which receivers.
        self._filename_receivers_map = filename_receivers_map

    def _cache_single_file(self, filename: pathlib.Path, info: typing.Dict):
        filename = filename.absolute()

        # hash the filename
        file_hash = hashlib.sha256()
        file_hash.update(str(filename).encode())
        file_hash_hex = file_hash.hexdigest()

        cache_file = self._cache_folder / f"{filename.stem}__{file_hash_hex}.npz"

        waveform_file = filename
        assert waveform_file.exists()

        stat = waveform_file.stat()

        expected_keys = {
            "start_time_stamp_in_ns",
            "index_sampling_rate_in_hz",
            "data_sampling_rate_in_hz",
            "receivers",
            "data",
            "mtime",
            "filesize",
            "filehash",
        }

        if cache_file.exists():
            # Keep track if we want to keep analyzing the cache file or
            # recompute it.
            cache_file_valid = True

            # Try loading it - if it fails delete it so it can be recomputed.
            try:
                d = np.load(cache_file)
            except Exception as e:
                logger.warning(
                    f"Failed to open cache file '{cache_file}' due to: {str(e)}. "
                    "Will recompute cache file."
                )
                cache_file.unlink()
                cache_file_valid = False

            # If the cache file can be opened check the contents.
            if cache_file_valid:
                keys = set(d.keys())
                # First check if all available keys exist.
                if keys != expected_keys:
                    logger.warning(
                        f"Cache file '{cache_file}' might be outdated. Has keys: {keys}. "
                        f"Expected keys: {expected_keys}. "
                        "Will recompute cache file."
                    )
                    cache_file_valid = False
                # Then make sure the file has not been modified.
                elif d["mtime"] != stat.st_mtime or d["filesize"] != stat.st_size:
                    logger.warning(
                        f"Cache file '{cache_file}' might be outdated. mtime or size changed. "
                        "Will recompute cache file."
                    )
                    cache_file_valid = False
                # The index sampling rate might not match.
                elif (
                    int(d["index_sampling_rate_in_hz"])
                    != self._index_sampling_rate_in_hz
                ):
                    idx_sr = int(d["index_sampling_rate_in_hz"])
                    logger.warning(
                        f"Cache file '{cache_file}' has an index sampling rate of {idx_sr}. "
                        "Cache should have an index sampling rate of "
                        f"{self._index_sampling_rate_in_hz}. Will recompute cache file."
                    )
                    cache_file_valid = False

                if not cache_file_valid:
                    d.close()
                    del d
                    cache_file.unlink()

            if cache_file_valid:
                return {
                    "start_time_stamp_in_ns": int(d["start_time_stamp_in_ns"]),
                    "data_sampling_rate_in_hz": float(d["data_sampling_rate_in_hz"]),
                    "index_sampling_rate_in_hz": float(d["index_sampling_rate_in_hz"]),
                    "receivers": [str(i) for i in d["receivers"]],
                    "data": d["data"],
                }

        file_hash = compute_sha256_hash_for_file(filename=waveform_file)

        cache = {}
        # Open file and index each trace.
        with pyasdf.ASDFDataSet(waveform_file, mode="r") as ds:
            for station in ds.waveforms:
                tags = station.get_waveform_tags()
                assert len(tags) == 1
                tag = tags[0]
                st = station[tag]
                for tr in st:
                    cache[tr.id] = index_trace(
                        trace=tr,
                        index_sampling_rate_in_hz=self._index_sampling_rate_in_hz,
                    )

        # Some sanity checks to make sure every trace is idencial.
        sr = set(i["index_sampling_rate_in_hz"] for i in cache.values())
        sr_d = set(i["data_sampling_rate_in_hz"] for i in cache.values())
        st = set(i["start_time_stamp_in_ns"] for i in cache.values())
        assert len(sr) == 1
        assert len(st) == 1

        index_sampling_rate_in_hz = list(sr)[0]
        data_sampling_rate_in_hz = list(sr_d)[0]
        start_time_stamp_in_ns = list(st)[0]

        # Also every trace in the file must have the same length.
        assert len(set(len(i["min_values"]) for i in cache.values())) == 1
        assert len(set(len(i["max_values"]) for i in cache.values())) == 1

        # Assemble into large dataset.
        receivers = sorted(cache.keys())
        data = np.empty(
            (len(cache), 2, cache[receivers[0]]["min_values"].shape[0]),
            # Make sure the dtype is the same as the data.
            dtype=cache[receivers[0]]["min_values"].dtype,
        )
        for _i, r in enumerate(receivers):
            data[_i, 0, :] = cache[r]["min_values"]
            data[_i, 1, :] = cache[r]["max_values"]

        # Store everything in a simple npz file for now.
        np.savez(
            cache_file,
            start_time_stamp_in_ns=start_time_stamp_in_ns,
            index_sampling_rate_in_hz=index_sampling_rate_in_hz,
            data_sampling_rate_in_hz=data_sampling_rate_in_hz,
            receivers=np.array(receivers),
            data=data,
            mtime=stat.st_mtime,
            filesize=stat.st_size,
            filehash=file_hash,
        )

        return {
            "start_time_stamp_in_ns": start_time_stamp_in_ns,
            "index_sampling_rate_in_hz": index_sampling_rate_in_hz,
            "data_sampling_rate_in_hz": data_sampling_rate_in_hz,
            "receivers": receivers,
            "data": data,
        }

    def _open_folder(self):
        logger.info(f"Opening waveform {len(self._waveform_folders)} folder(s) ...")
        self._files = {}

        # Loop over all files and store some basic information.
        files = []
        for folder in self._waveform_folders:
            files.extend([i for i in folder.glob("*__*__*.h5") if i.is_file()])
        total_size = 0
        for f in files:
            m = re.match(FILENAME_REGEX, f.stem)
            if not m:
                continue
            g = m.groups()

            # Filter the times.
            starttime = obspy.UTCDateTime(*[int(i) for i in g[:7]])
            endtime = obspy.UTCDateTime(*[int(i) for i in g[7:]])
            if starttime > self._end_time or endtime < self._start_time:
                continue

            s = f.stat()
            self._files[f] = {
                "starttime": starttime,
                "endtime": endtime,
                "mtime": s.st_mtime,
                "size": s.st_size,
            }
            total_size += s.st_size

        if not self._files:
            raise ValueError("Could not find any waveform data files.")

        self._total_size = total_size
        self._pretty_total_size = pretty_filesize(total_size)

        logger.info(
            f"Found {len(self._files)} waveform files [{self._pretty_total_size} in total]."
        )

        self._figure_out_times()

    def _figure_out_times(self):
        """
        A bit of analysis to determine if there are any gaps in the data and what not.
        """
        durations = np.array(
            [i["endtime"] - i["starttime"] for i in self._files.values()],
            dtype=np.float64,
        )
        mean_duration = durations.mean()
        if np.any(np.abs(durations - mean_duration) > 0.01 * durations.mean()):
            # XXX: Better error handling/messages required.
            raise ValueError(
                "The durations of the individual files are not equal enough."
            )

        # Again likely overkill but better safe than sorry.
        #
        # Fraction of the duration that can be missing.
        threshold = 0.01
        time_ranges = []
        for t in sorted(self._files.values(), key=lambda x: x["starttime"]):
            # First time in the loop.
            if not time_ranges:
                time_ranges.append([t["starttime"], t["endtime"]])
                continue

            # Latest time range.
            lr = time_ranges[-1]

            # New time range.
            if t["starttime"] > (lr[1] + threshold * mean_duration):
                time_ranges.append([t["starttime"], t["endtime"]])
                continue

            if t["endtime"] > lr[1]:
                lr[1] = t["endtime"]

        # Cannot really happen.
        assert time_ranges
        logger.info(f"Found {len(time_ranges)} time range(s) with waveform data.")
        for t in time_ranges:
            logger.info(
                f"Time range: {t[0]}-{t[1]} [Duration: {t[1] - t[0]:.1f} seconds]"
            )

        # For now only a single time range is supported!
        if len(time_ranges) != 1:
            raise NotImplementedError(
                "Currently only supports a single continuous time range."
            )

        self._time_ranges = time_ranges

    def _get_timestamps_for_binned_index(self) -> np.ndarray:
        if not hasattr(self, "_timestamp_cache"):
            t = np.linspace(
                self._cache_start_timestamp_ns / 1e9,
                self._cache_end_timestamp_ns / 1e9,
                self._cache_npts,
            )
            times = _interweave_arrays(t, t)
            self._timestamp_cache = times

        return self._timestamp_cache

    def get_binned_index_data(
        self, channel_id: str
    ) -> typing.Tuple[np.ndarray, np.ndarray]:
        """
        Get the min-max binned data for a certain index.

        Return timestamps, bins ready for plotting.

        Args:
            channel_id: Id of the channel to get.
        """
        index = self._get_index_for_channel(channel_id=channel_id)
        min_values = self._cache["data"][index, 0, :]
        max_values = self._cache["data"][index, 1, :]
        return self._get_timestamps_for_binned_index(), _interweave_arrays(
            min_values, max_values
        )

    def get_waveforms(
        self,
        channel_ids: typing.List[str],
        start_time: obspy.UTCDateTime,
        end_time: obspy.UTCDateTime,
    ) -> obspy.Stream:
        """
        Retrieve waveforms as an ObsPy Stream objects.

        Args:
            channel_ids: List of channel ids.
            start_time: The start time of the requested data.
            end_time: The end time of the requested data.
        """
        st = obspy.Stream()
        for channel_id in channel_ids:
            st.append(
                self.get_waveform_data(
                    channel_id=channel_id,
                    start_time=start_time,
                    end_time=end_time,
                    npts=10000000000000,
                    return_trace=True,
                )
            )
        return st

    def get_waveform_data(
        self,
        channel_id: str,
        start_time: obspy.UTCDateTime,
        end_time: obspy.UTCDateTime,
        npts: int,
        return_trace: bool = False,
    ):
        """
        Lower level waveform access. Please use the ``.get_waveforms()`` method
        instead.
        """
        # Get all the files that contain part of that trace.
        files = {
            key: value
            for key, value in self._files.items()
            if value["starttime"] <= end_time
            and value["endtime"] > start_time
            and channel_id in self._filename_receivers_map[key]
        }

        if not files:
            raise ValueError("Could not find data.")

        st = obspy.Stream(
            traces=[
                _get_channel_from_file(filename=f, channel_id=channel_id).copy()
                for f in files.keys()
            ]
        )
        st.trim(obspy.UTCDateTime(start_time), obspy.UTCDateTime(end_time))
        deltas = {tr.stats.delta for tr in st}
        if len(deltas) != 1:
            breakpoint()
        for tr in st:
            tr.stats.delta = list(deltas)[0]
        st.merge()
        assert len(st) == 1, "Merging failed somehow."
        tr = st[0]

        if return_trace:
            return tr

        # If it has too many samples, bin the data.
        if tr.stats.npts > npts * 2:
            factor = int(tr.stats.npts // npts)
            for _ in range(10):
                if tr.stats.npts / factor < npts:
                    factor *= 2
                    continue
                break
            else:
                raise ValueError(
                    "Something went wrong with the decimation factor " "computation."
                )
            if factor > 1:
                size = tr.stats.npts // factor
                array_size = size
                if tr.stats.npts % factor:
                    array_size += 1
                data = np.empty((array_size, 2))
                d = tr.data[: size * factor].reshape((size, factor))
                data[:size, 0] = d.min(axis=1)
                data[:size, 1] = d.max(axis=1)

                # Fill the last sample that does not exactly fit.
                if size != array_size:
                    d = tr.data[size * factor :]  # noqa
                    data[-1, 0] = d.min()
                    data[-1, 1] = d.max()

                # The end time is off by a bit if it is not an even division.
                # More than likely does not matter for anything so should be
                # fine.
                new_dt = tr.stats.delta * factor
                new_start_time = tr.stats.starttime.timestamp + new_dt * 0.5
                new_end_time = new_start_time + (data.shape[0] - 1) * new_dt
                times = np.linspace(new_start_time, new_end_time, data.shape[0])

                return {
                    "data": _interweave_arrays(data[:, 0], data[:, 1]),
                    "times": _interweave_arrays(times, times),
                    "start_time": new_start_time,
                    "end_time": new_end_time,
                    "npts": data.shape[0],
                    "delta": new_dt,
                    "is_max_resolution": False,
                }

        return {
            "data": tr.data,
            "times": tr.times() + tr.stats.starttime.timestamp,
            "start_time": tr.stats.starttime.timestamp,
            "end_time": tr.stats.endtime.timestamp,
            "npts": tr.stats.npts,
            "delta": tr.stats.delta,
            "is_max_resolution": True,
        }
