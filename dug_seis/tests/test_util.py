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

import numpy as np
import obspy

from dug_seis.util import filter_settings_to_function


def test_filter_settings_function_generation_bandpass():
    filter_settings = {
        "filter_type": "butterworth_bandpass",
        "highpass_frequency_in_hz": 2.0,
        "lowpass_frequency_in_hz": 4.0,
        "filter_corners": 3,
        "zerophase": False,
    }

    # Use the filter function.
    f = filter_settings_to_function(filter_settings)
    tr = obspy.read()[0]
    tr = f(tr)

    # Apply manually.
    tr2 = obspy.read()[0]
    tr2.filter("bandpass", freqmin=2.0, freqmax=4.0, corners=3, zerophase=False)

    # Should be identical.
    np.testing.assert_allclose(tr.data, tr2.data)

    filter_settings = {
        "filter_type": "butterworth_bandpass",
        "highpass_frequency_in_hz": 1.0,
        "lowpass_frequency_in_hz": 5.0,
        "filter_corners": 5,
        "zerophase": True,
    }

    # Use the filter function.
    f = filter_settings_to_function(filter_settings)
    tr = obspy.read()[0]
    tr = f(tr)

    # Apply manually.
    tr2 = obspy.read()[0]
    tr2.filter("bandpass", freqmin=1.0, freqmax=5.0, corners=5, zerophase=True)

    # Should be identical.
    np.testing.assert_allclose(tr.data, tr2.data)


def test_filter_settings_function_generation_lowpass():
    filter_settings = {
        "filter_type": "butterworth_lowpass",
        "frequency_in_hz": 2.0,
        "filter_corners": 3,
        "zerophase": False,
    }

    # Use the filter function.
    f = filter_settings_to_function(filter_settings)
    tr = obspy.read()[0]
    tr = f(tr)

    # Apply manually.
    tr2 = obspy.read()[0]
    tr2.filter("lowpass", freq=2.0, corners=3, zerophase=False)

    # Should be identical.
    np.testing.assert_allclose(tr.data, tr2.data)

    filter_settings = {
        "filter_type": "butterworth_lowpass",
        "frequency_in_hz": 5.0,
        "filter_corners": 6,
        "zerophase": True,
    }

    # Use the filter function.
    f = filter_settings_to_function(filter_settings)
    tr = obspy.read()[0]
    tr = f(tr)

    # Apply manually.
    tr2 = obspy.read()[0]
    tr2.filter("lowpass", freq=5.0, corners=6, zerophase=True)

    # Should be identical.
    np.testing.assert_allclose(tr.data, tr2.data)


def test_filter_settings_function_generation_highpass():
    filter_settings = {
        "filter_type": "butterworth_highpass",
        "frequency_in_hz": 2.0,
        "filter_corners": 3,
        "zerophase": False,
    }

    # Use the filter function.
    f = filter_settings_to_function(filter_settings)
    tr = obspy.read()[0]
    tr = f(tr)

    # Apply manually.
    tr2 = obspy.read()[0]
    tr2.filter("highpass", freq=2.0, corners=3, zerophase=False)

    # Should be identical.
    np.testing.assert_allclose(tr.data, tr2.data)

    filter_settings = {
        "filter_type": "butterworth_highpass",
        "frequency_in_hz": 5.0,
        "filter_corners": 6,
        "zerophase": True,
    }

    # Use the filter function.
    f = filter_settings_to_function(filter_settings)
    tr = obspy.read()[0]
    tr = f(tr)

    # Apply manually.
    tr2 = obspy.read()[0]
    tr2.filter("highpass", freq=5.0, corners=6, zerophase=True)

    # Should be identical.
    np.testing.assert_allclose(tr.data, tr2.data)
