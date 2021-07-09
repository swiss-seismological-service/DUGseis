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
Low level indexing functionality.

Performance critical things are done using numba.
"""

import typing

import numba
import numpy as np
import obspy


def index_trace(trace: obspy.Trace, index_sampling_rate_in_hz: int):
    # Must be an integer because it internally bins and the bins are per
    # second.
    assert isinstance(index_sampling_rate_in_hz, int)
    start_time_in_ns, min_values, max_values = _internal_index_trace(
        data=trace.data,
        starttime_in_ns=trace.stats.starttime.ns,
        sampling_rate_in_hz=trace.stats.sampling_rate,
        index_sampling_rate_in_hz=index_sampling_rate_in_hz,
    )

    return {
        "start_time_stamp_in_ns": start_time_in_ns,
        "data_sampling_rate_in_hz": trace.stats.sampling_rate,
        "index_sampling_rate_in_hz": index_sampling_rate_in_hz,
        "min_values": min_values,
        "max_values": max_values,
    }


@numba.jit(nopython=True, cache=True)
def _internal_index_trace(
    data: np.ndarray,
    starttime_in_ns: int,
    sampling_rate_in_hz: float,
    index_sampling_rate_in_hz: float,
):
    # Sample spacing in nanoseconds for the actual time array and the desired
    # indexing.
    dt_ns = int(round((1.0 / sampling_rate_in_hz) * 1e9))
    index_dt_ns = int(round(1.0 / index_sampling_rate_in_hz * 1e9))

    # Always start at the full second.
    full_second = int(starttime_in_ns / 1_000_000_000) * 1_000_000_000

    # Find the largest increment of full_second + n * index_dt_ns that is still
    # smaller or equal than the data starttime.
    current_start_time = (
        full_second + int((starttime_in_ns - full_second) / index_dt_ns) * index_dt_ns
    )

    # Times for the first interval.
    start_time_in_ns = current_start_time
    current_end_time = current_start_time + index_dt_ns

    # Figure out the number of samples we'll have.
    time_of_last_sample_in_ns = starttime_in_ns + (data.shape[0] - 1) * dt_ns

    size = int(np.ceil((time_of_last_sample_in_ns - start_time_in_ns) / index_dt_ns))

    min_values = np.empty(size, dtype=data.dtype)
    max_values = np.empty(size, dtype=data.dtype)

    current_min_value = data[0]
    current_max_value = data[0]

    idx = 0
    current_sample_time = starttime_in_ns
    for t in data:
        # Add to lists and continue.
        if current_sample_time > current_end_time:
            min_values[idx] = current_min_value
            max_values[idx] = current_max_value

            current_start_time += index_dt_ns
            current_end_time = current_start_time + index_dt_ns
            current_min_value = t
            current_max_value = t
            idx += 1

        if t > current_max_value:
            current_max_value = t
        elif t < current_min_value:
            current_min_value = t

        # Increment the time of the current array sample.
        current_sample_time += dt_ns

    min_values[idx] = current_min_value
    max_values[idx] = current_max_value

    return (start_time_in_ns, min_values, max_values)


def _compute_times(cache: typing.Dict):
    starttime = cache["start_time_stamp_in_ns"]
    # Do integer maths here to not accumulate rounding errors.
    # At some earlier stage we made sure it divides nicely.
    dt_ns = int(round(1.0 / cache["index_sampling_rate_in_hz"] * 1e9))
    endtime = starttime + (cache["data"].shape[-1] - 1) * dt_ns
    return starttime, endtime, dt_ns


def combine_caches(caches: typing.List[typing.Dict]):
    # Sort by time.
    caches = sorted(caches, key=lambda x: x["start_time_stamp_in_ns"])

    receivers = set()

    # First loop to get all as well as the smallest start and largest endtime.
    starttime, endtime, dt_ns = _compute_times(caches[0])
    for c in caches:
        s, e, dt = _compute_times(c)
        if s < starttime:
            starttime = s
        if e > endtime:
            endtime = e
        receivers = receivers.union(set(c["receivers"]))
        assert dt_ns == dt

    receiver_list = sorted(receivers)
    npts = int(round((endtime - starttime) / dt_ns)) + 1

    data = np.zeros((len(receiver_list), 2, npts), dtype=caches[0]["data"].dtype)
    has_data_mask = np.zeros(npts, dtype=np.bool)

    for _i, cache in enumerate(caches):
        # Map to the receiver indices.
        indices = np.array(
            [receiver_list.index(i) for i in cache["receivers"]], dtype=np.int32
        )
        _add_to_combined_data(
            dt_ns=dt_ns,
            start_time_in_ns=starttime,
            indices=indices,
            data=data,
            has_data_mask=has_data_mask,
            start_time_in_ns_chunk=cache["start_time_stamp_in_ns"],
            data_chunk=cache["data"],
        )

    return {
        "receivers": receiver_list,
        "data": data,
        "start_time_stamp_in_ns": starttime,
        "cache_dt_ns": dt_ns,
        "data_sampling_rate_in_hz": caches[0]["data_sampling_rate_in_hz"],
    }


@numba.jit(nopython=True, cache=True)
def _add_to_combined_data(
    dt_ns: int,
    start_time_in_ns: int,
    indices: np.ndarray,
    data: np.ndarray,
    has_data_mask: np.ndarray,
    start_time_in_ns_chunk: int,
    data_chunk: np.ndarray,
):
    idx = int(round((start_time_in_ns_chunk - start_time_in_ns) / dt_ns))

    for _i in range(data_chunk.shape[-1]):
        if has_data_mask[idx] is False:
            for _j in range(data_chunk.shape[0]):
                data[indices[_j], :, idx] = data_chunk[_j, :, _i]
                has_data_mask[idx] = True
        else:
            for _j in range(data_chunk.shape[0]):
                min_value = data_chunk[_j, 0, _i]
                max_value = data_chunk[_j, 1, _i]

                if min_value < data[indices[_j], 0, idx]:
                    data[indices[_j], 0, idx] = min_value

                if max_value > data[indices[_j], 1, idx]:
                    data[indices[_j], 1, idx] = max_value
        idx += 1


def _interweave_arrays(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Helper function interweaving two arrays, e.g.

    ```
    a = [0, 1, 2]
    b = [4, 5, 6]
    _interweave_arrays(a, b) == [0, 4, 1, 5, 2, 6]
    ```

    Args:
        a: First array.
        b: Second array.
    """
    values = np.empty(2 * a.shape[0], dtype=a.dtype)
    values[0::2] = a
    values[1::2] = b
    return values
