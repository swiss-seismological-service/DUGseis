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
Test suite for the waveform indexing.
"""
import numpy as np
import obspy
import pytest

from dug_seis.waveform_handler.indexing import index_trace


def test_index_trace():
    # Simplistic example.
    data = np.array([1.0, 2.0, 0.5, 0.5, 1.0, 3.0, 4.0], dtype=np.float32)
    tr = obspy.Trace(
        data=data, header={"sampling_rate": 4.0, "starttime": obspy.UTCDateTime(5.25)}
    )

    out = index_trace(trace=tr, index_sampling_rate_in_hz=2)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 2
    assert out["start_time_stamp_in_ns"] == 5_000_000_000

    np.testing.assert_allclose(out["max_values"], [2.0, 0.5, 3.0, 4.0])
    np.testing.assert_allclose(out["min_values"], [1.0, 0.5, 1.0, 4.0])

    out = index_trace(trace=tr, index_sampling_rate_in_hz=1)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 1.0
    assert out["start_time_stamp_in_ns"] == 5_000_000_000

    np.testing.assert_allclose(out["max_values"], [2.0, 4.0])
    np.testing.assert_allclose(out["min_values"], [0.5, 1.0])


def test_index_trace_first_one_on_boundary():
    """
    Usually an item directly on the boundary between two intervals will be
    counted towards the later interval.

    There is an exception here for the very first sample.
    """
    data = np.array([1.0, 2.0, 7.0, 0.5, 1.0, 3.0, 4.0], dtype=np.float32)
    tr = obspy.Trace(
        data=data, header={"sampling_rate": 4.0, "starttime": obspy.UTCDateTime(5)}
    )

    out = index_trace(trace=tr, index_sampling_rate_in_hz=2)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 2
    assert out["start_time_stamp_in_ns"] == 5_000_000_000

    np.testing.assert_allclose(out["max_values"], [7.0, 1.0, 4.0])
    np.testing.assert_allclose(out["min_values"], [1.0, 0.5, 3.0])

    out = index_trace(trace=tr, index_sampling_rate_in_hz=1)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 1.0
    assert out["start_time_stamp_in_ns"] == 5_000_000_000

    np.testing.assert_allclose(out["max_values"], [7.0, 4.0])
    np.testing.assert_allclose(out["min_values"], [0.5, 3.0])

    # Samples not on boundary.
    tr = obspy.Trace(
        data=data, header={"sampling_rate": 4.0, "starttime": obspy.UTCDateTime(5.15)}
    )

    out = index_trace(trace=tr, index_sampling_rate_in_hz=2)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 2
    assert out["start_time_stamp_in_ns"] == 5_000_000_000

    np.testing.assert_allclose(out["max_values"], [2.0, 7.0, 3.0, 4.0])
    np.testing.assert_allclose(out["min_values"], [1.0, 0.5, 1, 4.0])

    # Just one sample in the previous time step.
    tr = obspy.Trace(
        data=data, header={"sampling_rate": 4.0, "starttime": obspy.UTCDateTime(5.9)}
    )

    out = index_trace(trace=tr, index_sampling_rate_in_hz=2)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 2
    assert out["start_time_stamp_in_ns"] == 5_500_000_000

    np.testing.assert_allclose(out["max_values"], [1, 7, 1, 4])
    np.testing.assert_allclose(out["min_values"], [1, 2, 0.5, 3])


def test_index_trace_regression():
    data = np.linspace(0, 1e8, 2000001)
    tr = obspy.Trace(
        data=data,
        header={
            "sampling_rate": 200000.0,
            "starttime": obspy.UTCDateTime(ns=1486646534999997696),
        },
    )

    out = index_trace(trace=tr, index_sampling_rate_in_hz=100)
    assert out["start_time_stamp_in_ns"] == 1486646534990000000
    assert out["data_sampling_rate_in_hz"] == 200000.0
    assert out["index_sampling_rate_in_hz"] == 100
    assert out["min_values"].shape == (1001,)
    assert out["max_values"].shape == (1001,)


@pytest.mark.parametrize(
    "dtype", [np.float32, np.float64, np.int16, np.int32, np.int64]
)
def test_index_trace_dtypes_are_preserved(dtype):
    data = np.array([-1, 2, 0, 0, 1, 3, 40], dtype=dtype)
    tr = obspy.Trace(
        data=data, header={"sampling_rate": 4.0, "starttime": obspy.UTCDateTime(5.25)}
    )
    assert tr.data.dtype == dtype

    out = index_trace(trace=tr, index_sampling_rate_in_hz=2)
    assert sorted(out.keys()) == [
        "data_sampling_rate_in_hz",
        "index_sampling_rate_in_hz",
        "max_values",
        "min_values",
        "start_time_stamp_in_ns",
    ]
    assert out["index_sampling_rate_in_hz"] == 2
    assert out["start_time_stamp_in_ns"] == 5_000_000_000
    # Should preserve the dtype.
    assert out["max_values"].dtype == dtype
    assert out["min_values"].dtype == dtype

    np.testing.assert_allclose(out["max_values"], [2, 0, 3, 40])
    np.testing.assert_allclose(out["min_values"], [-1, 0, 1, 40])
