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

import functools
import random

import numpy as np
import obspy
from obspy.core.event import Pick, WaveformStreamID
import pytest

from dug_seis.event_processing.location.locate_homogeneous import (
    locate_in_homogeneous_background_medium,
)


@pytest.mark.parametrize(
    [
        "noise_level",
        "location_tolerance",
        "origin_time_tolerance",
        "damping",
        "phase",
        "velocity",
        "anisotropic_params",
        "earth_model_string",
    ],
    [
        (0.0, 1e-3, 1e-6, 0.7, "P", 3500.0, None, "P_3500"),
        (0.0001, 7e-3, 5e-6, 0.7, "P", 3500.0, None, "P_3500"),
        (0.001, 7e-2, 5e-5, 0.7, "P", 3500.0, None, "P_3500"),
        (0.01, 0.2, 2e-4, 0.7, "P", 3500.0, None, "P_3500"),
        (0.02, 0.4, 4e-4, 0.7, "P", 3500.0, None, "P_3500"),
        # More damping => Less accurate result in this synthetic case.
        (0.02, 0.8, 4e-4, 2.0, "P", 3500.0, None, "P_3500"),
        # Model isotropy with the anisotropic approach. Thus very small error.
        (
            0.0,
            1e-3,
            1e-6,
            0.7,
            "P",
            3500.0,
            {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.0},
            "P_3500",
        ),
        # Add some actual anisotropy => larger error because the synthetic data
        # is modelled wrongly.
        (
            0.0,
            0.05,
            2e-4,
            0.7,
            "P",
            3500.0,
            {"inc": 0.0, "azi": 0.0, "delta": 0.01, "epsilon": 0.0},
            "P_3500",
        ),
        (
            0.0,
            0.1,
            3e-4,
            0.7,
            "P",
            3500.0,
            {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.01},
            "P_3500",
        ),
        # Repeat the last five but use velocity dictionaries.
        (0.02, 0.8, 4e-4, 2.0, "P", {"P": 3500.0}, None, "P_3500"),
        (
            0.0,
            1e-3,
            1e-6,
            0.7,
            "P",
            {"P": 3500.0},
            {"P": {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.0}},
            "P_3500",
        ),
        (
            0.0,
            0.05,
            2e-4,
            0.7,
            "P",
            {"P": 3500.0},
            {"P": {"inc": 0.0, "azi": 0.0, "delta": 0.01, "epsilon": 0.0}},
            "P_3500",
        ),
        (
            0.0,
            0.1,
            3e-4,
            0.7,
            "P",
            {"P": 3500.0},
            {"P": {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.01}},
            "P_3500",
        ),
        # Try S velocities.
        (0.02, 0.8, 4e-4, 2.0, "S", {"S": 3500.0}, None, "S_3500"),
        (
            0.0,
            1e-3,
            1e-6,
            0.7,
            "S",
            {"S": 2500.0},
            {"S": {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.0}},
            "S_2500",
        ),
        # Extra velocities and anisotropic parameters should be ignored.
        (
            0.0,
            1e-3,
            1e-6,
            0.7,
            "S",
            {"S": 2500.0, "P": 3500.0},
            {
                "S": {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.0},
                "P": {"inc": 0.0, "azi": 0.0, "delta": 0.0, "epsilon": 0.0},
            },
            "P_3500__S_2500",
        ),
    ],
)
def test_locate_in_homogeneous_isotropic_medium(
    noise_level,
    location_tolerance,
    origin_time_tolerance,
    damping,
    phase,
    velocity,
    anisotropic_params,
    earth_model_string,
):
    """
    Simple tests to make sure the algorithm does what is says on the tin.
    """
    random.seed(12345)
    # Made up origin time and source location.
    origin_time = obspy.UTCDateTime(2021, 1, 2, 3, 4, 5, 123456)
    src_location = np.array([3.0, -7.0, 2.3])

    if isinstance(velocity, float):
        vel = 3500.0
    else:
        vel = velocity[phase]

    # Pretty good distribution of receivers.
    receivers = {
        "GRM.001.002.001": [100.0, 100.0, 100.0],
        "GRM.001.003.001": [-100.0, -100.0, -100.0],
        "GRM.001.004.001": [-100.0, 100.0, -100.0],
        "GRM.001.005.001": [-100.0, -100.0, 100.0],
        "GRM.001.006.001": [100.0, -100.0, -100.0],
        "GRM.001.007.001": [-100.0, 100.0, 100.0],
        "GRM.001.018.001": [100.0, -100.0, 100.0],
        "GRM.001.019.001": [100.0, 100.0, -100.0],
    }

    # Fake the data.
    picks = []
    for channel_id, coordinates in receivers.items():
        distance = np.linalg.norm(src_location - np.array(coordinates))
        tt = distance / vel
        # Add some noise if necessary.
        if noise_level:
            tt += random.random() * (noise_level * tt)

        net, sta, loc, cha = channel_id.split(".")
        picks.append(
            Pick(
                time=origin_time + tt,
                waveform_id=WaveformStreamID(net, sta, loc, cha),
                phase_hint=phase,
            )
        )

    # Recover the event.
    event = locate_in_homogeneous_background_medium(
        picks=picks,
        coordinates=receivers,
        velocity=velocity,
        damping=damping,
        # Identity mapping - thus latitude/longitude/depth == x/y/z for testing
        # purposes.
        local_to_global_coordinates=lambda x: x,
        anisotropic_params=anisotropic_params,
    )

    assert event.resource_id.id.startswith("event/")

    assert len(event.origins) == 1
    o = event.origins[0]
    # Make sure the parameters are recovered.
    np.testing.assert_allclose(
        [o.latitude, o.longitude, o.depth],
        src_location,
        # Gets within a mm in this idealized case.
        atol=location_tolerance,
    )
    # And the time.
    assert abs(o.time - origin_time) < origin_time_tolerance

    assert o.time_fixed is False
    assert o.epicenter_fixed is False
    assert o.depth_type == "from location"
    assert o.method_id.id == "method/travel_time/homogeneous_model"
    assert o.resource_id.id.startswith("origin/travel_time/homogeneous_model/")

    assert len(event.picks) == 8
    assert len(o.arrivals) == 8

    iso = "anisotropic" if anisotropic_params else "isotropic"
    earth_model_id_str = f"earth_model/homogeneous/{iso}/velocity={earth_model_string}"

    for pick, arrival in zip(picks, o.arrivals):
        assert arrival.pick_id == pick.resource_id
        # Extremely unlikely with floating point math and bounded accuracy.
        assert arrival.time_residual != 0.0
        assert arrival.phase == phase
        assert arrival.earth_model_id.id == earth_model_id_str


@pytest.mark.parametrize(
    [
        "noise_level",
        "location_tolerance",
        "origin_time_tolerance",
        "damping",
        "velocity",
        "anisotropic_params",
        "earth_model_string",
    ],
    [
        (0.0, 1e-3, 1e-6, 0.7, {"P": 3500.0, "S": 2500.0}, None, "P_3500__S_2500"),
        (0.00001, 7e-3, 7e-6, 0.7, {"P": 3500.0, "S": 2500.0}, None, "P_3500__S_2500"),
        (0.0001, 7e-2, 6e-5, 0.7, {"P": 3500.0, "S": 2500.0}, None, "P_3500__S_2500"),
        (0.001, 0.5, 6e-4, 0.7, {"P": 3500.0, "S": 2500.0}, None, "P_3500__S_2500"),
        (0.002, 1.0, 2e-3, 0.7, {"P": 3500.0, "S": 2500.0}, None, "P_3500__S_2500"),
    ],
)
def test_joint_P_S_locate_in_homogeneous_isotropic_medium(
    noise_level,
    location_tolerance,
    origin_time_tolerance,
    damping,
    velocity,
    anisotropic_params,
    earth_model_string,
):
    """
    Very similar to the other test but test joint P and S inversions.
    """
    random.seed(2348)
    # Made up origin time and source location.
    origin_time = obspy.UTCDateTime(2021, 1, 2, 3, 4, 5, 123456)
    src_location = np.array([3.0, -7.0, 2.3])

    assert isinstance(velocity, dict)
    assert set(velocity.keys()) == {"P", "S"}

    # Quite some receivers.
    receivers = {
        "GRM.001.002.001": [100.0, 100.0, 100.0],
        "GRM.001.003.001": [-100.0, -100.0, -100.0],
        "GRM.001.004.001": [-100.0, 100.0, -100.0],
        "GRM.001.005.001": [-100.0, -100.0, 100.0],
        "GRM.001.006.001": [100.0, -100.0, -100.0],
        "GRM.001.007.001": [-100.0, 100.0, 100.0],
        "GRM.001.018.001": [100.0, -100.0, 100.0],
        "GRM.001.019.001": [100.0, 100.0, -100.0],
        "GRM.002.002.001": [200.0, 200.0, 200.0],
        "GRM.002.003.001": [-200.0, -200.0, -200.0],
        "GRM.002.004.001": [-200.0, 200.0, -200.0],
        "GRM.002.005.001": [-200.0, -200.0, 200.0],
        "GRM.002.006.001": [200.0, -200.0, -200.0],
        "GRM.002.007.001": [-200.0, 200.0, 200.0],
        "GRM.002.018.001": [200.0, -200.0, 200.0],
        "GRM.002.019.001": [200.0, 200.0, -200.0],
    }

    # Fake the data.
    all_picks = []
    for phase in ["P", "S"]:
        for channel_id, coordinates in receivers.items():
            distance = np.linalg.norm(src_location - np.array(coordinates))
            tt = distance / velocity[phase]
            # Add some noise if necessary.
            if noise_level:
                tt += random.random() * noise_level

            net, sta, loc, cha = channel_id.split(".")
            all_picks.append(
                Pick(
                    time=origin_time + tt,
                    waveform_id=WaveformStreamID(net, sta, loc, cha),
                    phase_hint=phase,
                )
            )

    # Two phases per pick.
    assert len(all_picks) == len(receivers) * 2

    locate = functools.partial(
        locate_in_homogeneous_background_medium,
        coordinates=receivers,
        velocity=velocity,
        damping=damping,
        # Identity mapping - thus latitude/longitude/depth == x/y/z for testing
        # purposes.
        local_to_global_coordinates=lambda x: x,
        anisotropic_params=anisotropic_params,
    )

    # Use the partial function to recover for only P, only S, and jointly.
    event_p = locate(
        picks=[p for p in all_picks if p.phase_hint == "P"],
    )
    event_s = locate(
        picks=[p for p in all_picks if p.phase_hint == "S"],
    )
    event_p_s = locate(picks=all_picks)

    # This is kind of hard to evaluate but the time error should P > S > P and
    # S. S waves are slower and thus the final error should be smaller. P and S
    # just has more information so the error should also be smaller.
    assert (
        event_p.origins[0].time_errors.uncertainty
        > event_s.origins[0].time_errors.uncertainty
        > event_p_s.origins[0].time_errors.uncertainty
    )

    # The same holds true for the location.
    dist_error = lambda e: np.linalg.norm(
        np.array([e.origins[0].latitude, e.origins[0].longitude, e.origins[0].depth])
        - src_location
    )
    dist_p = dist_error(event_p)
    dist_s = dist_error(event_s)
    dist_p_s = dist_error(event_p_s)

    # Test separately that both individual inaccuracies are smaller than for
    # the joint inversion.
    assert dist_p > dist_p_s
    assert dist_s > dist_p_s

    assert len(event_p.picks) == 16
    assert len(event_s.picks) == 16
    assert len(event_p_s.picks) == 32

    for event in [event_p, event_s, event_p_s]:
        assert event.resource_id.id.startswith("event/")

        assert len(event.origins) == 1
        o = event.origins[0]
        # Make sure the parameters are recovered.
        np.testing.assert_allclose(
            [o.latitude, o.longitude, o.depth],
            src_location,
            # Gets within a mm in this idealized case.
            atol=location_tolerance,
        )
        # And the time.
        assert abs(o.time - origin_time) < origin_time_tolerance

        assert o.time_fixed is False
        assert o.epicenter_fixed is False
        assert o.depth_type == "from location"
        assert o.method_id.id == "method/travel_time/homogeneous_model"
        assert o.resource_id.id.startswith("origin/travel_time/homogeneous_model/")

        assert len(event.picks) == len(o.arrivals)

        iso = "anisotropic" if anisotropic_params else "isotropic"
        earth_model_id_str = (
            f"earth_model/homogeneous/{iso}/velocity={earth_model_string}"
        )

        for arrival in o.arrivals:
            # Extremely unlikely with floating point math and bounded accuracy.
            assert arrival.time_residual != 0.0
            assert arrival.earth_model_id.id == earth_model_id_str
