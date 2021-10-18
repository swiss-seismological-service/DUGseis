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
Event location routines.
"""

import copy
import numpy as np
import typing
import uuid

from obspy.core.event import (
    Origin,
    Arrival,
    Pick,
    Event,
    QuantityError,
    ResourceIdentifier,
)


def locate_in_homogeneous_background_medium(
    picks: typing.List[Pick],
    coordinates: typing.Dict[str, np.array],
    velocity: float,
    damping: float,
    local_to_global_coordinates: typing.Callable,
    anisotropic_params: typing.Optional[typing.Dict[str, float]] = None,
    verbose: bool = False,
) -> Event:
    """
    Locate an event in a homogeneous background medium from a list of picks
    using travel times.

    This version will only consider P phase picks and ignores all other picks.

    Args:
        picks: List of pick objects to use.
        coordinates: Dictionary mapping channel ids to cartesian coordinates.
        velocity: P wave velocity or the minimum velocity in the anisotropic case.
        damping: Damping.
        local_to_global_coordinates: Function to convert the cartesian local
            coordinates to latitude/longitude/depth.
        anisotropic_params: If given, an anisotropic model will be used to
            compute the travel times.
        verbose: Print a short summary when an event is found.

    Returns:
        A complete event with a location origin. Will be returned regardless of
        how well the location works so a subsequent QC check is advisable.
    """
    # QC on the anisotropic parameters if given.
    if anisotropic_params and set(anisotropic_params.keys()) != {
        "inc",
        "azi",
        "delta",
        "epsilon",
    }:
        raise ValueError(
            "The 'anisotropic_params' dictionary, if given, must contain "
            "these keys: inc, azi, delta, epsilon. It contains: "
            f"{list(anisotropic_params.keys())}"
        )

    # Filter to only use P-phase picks.
    event_picks = []
    for pick in picks:
        pick = copy.deepcopy(pick)
        if pick.phase_hint and pick.phase_hint.lower() != "p":
            continue
        event_picks.append(pick)

    if len(event_picks) < 3:
        raise ValueError("At least 3 P phase picks are required for an event location.")

    starttime = min([p.time for p in event_picks])

    # time relative to startime of snippets, in milliseconds.
    t_relative = []
    for pick in event_picks:
        t_relative.append((pick.time - starttime) * 1000)

    npicks = len(t_relative)

    # Assemble sensor coordinate array for the actually used picks.
    sensor_coords = np.zeros((npicks, 3), dtype=np.float64)
    for i, p in enumerate(event_picks):
        sensor_coords[i, :] = coordinates[p.waveform_id.id]

    vp = velocity * np.ones([npicks]) / 1000.0

    loc = sensor_coords[t_relative.index(min(t_relative)), :] + 0.1
    t0 = min(t_relative)
    nit = 0
    jacobian = np.zeros([npicks, 4])
    dm = 1.0 * np.ones(4)

    # Actual optimization.
    while nit < 100 and np.linalg.norm(dm) > 0.00001:
        nit = nit + 1

        # calculate anisotropic velocities
        if anisotropic_params:
            for i in range(npicks):
                azi = np.arctan2(
                    sensor_coords[i, 0] - loc[0], sensor_coords[i, 1] - loc[1]
                )
                inc = np.arctan2(
                    sensor_coords[i, 2] - loc[2],
                    np.linalg.norm(sensor_coords[i, range(2)] - loc[range(2)]),
                )
                theta = np.arccos(
                    np.cos(inc)
                    * np.cos(azi)
                    * np.cos(anisotropic_params["inc"])
                    * np.cos(anisotropic_params["azi"])
                    + np.cos(inc)
                    * np.sin(azi)
                    * np.cos(anisotropic_params["inc"])
                    * np.sin(anisotropic_params["azi"])
                    + np.sin(inc) * np.sin(anisotropic_params["inc"])
                )
                vp[i] = (
                    velocity
                    / 1000.0
                    * (
                        1.0
                        + anisotropic_params["delta"]
                        * np.sin(theta) ** 2
                        * np.cos(theta) ** 2
                        + anisotropic_params["epsilon"] * np.sin(theta) ** 4
                    )
                )

        dist = [np.linalg.norm(loc - sensor_coords[i, :]) for i in range(npicks)]
        tcalc = [dist[i] / vp[i] + t0 for i in range(npicks)]

        res = [t_relative[i] - tcalc[i] for i in range(npicks)]
        rms = np.linalg.norm(res) / npicks
        for j in range(3):
            for i in range(npicks):
                jacobian[i, j] = -(sensor_coords[i, j] - loc[j]) / (vp[i] * dist[i])
        jacobian[:, 3] = np.ones(npicks)

        dm = np.matmul(
            np.matmul(
                np.linalg.inv(
                    np.matmul(np.transpose(jacobian), jacobian)
                    + pow(damping, 2) * np.eye(4)
                ),
                np.transpose(jacobian),
            ),
            res,
        )
        loc = loc + dm[0:3]
        t0 = t0 + dm[3]

    if verbose:
        print(
            "Event found: "
            "Location %3.2f %3.2f %3.2f; %i iterations, rms %4.3f ms"
            % (loc[0], loc[1], loc[2], nit, rms)
        )

    # Finally create the event object with the used picks and arrivals.
    # Try to specify as many details as possible.
    origin_time = starttime + t0 / 1000.0

    event = Event(resource_id=f"event/{uuid.uuid4()}")
    event.picks = event_picks

    # calculate distances source - sensors
    dists = np.linalg.norm(sensor_coords - np.tile(loc, (len(sensor_coords), 1)), axis=1)

    # Convert local coordinates to WGS84.
    latitude, longitude, depth = local_to_global_coordinates(loc)

    # Create descriptive ids.
    if anisotropic_params is None:
        s = "isotropic"
    else:
        s = "anisotropic"
    earth_model_id = ResourceIdentifier(
        id=f"earth_model/homogeneous/{s}/velocity={int(round(velocity))}"
    )
    method_id = "method/p_wave_travel_time/homogeneous_model"

    # Create origin.
    o = Origin(
        resource_id=f"origin/p_wave_travel_time/homogeneous_model/{uuid.uuid4()}",
        time=origin_time,
        longitude=longitude,
        latitude=latitude,
        depth=depth,
        depth_type="from location",
        time_fixed=False,
        epicenter_fixed=False,
        method_id=method_id,
        earth_model_id=earth_model_id,
    )

    # And fill with arrivals.
    for _i, pick in enumerate(event_picks):
        o.arrivals.append(
            Arrival(
                resource_id=f"arrival/{_i}/{o.resource_id.id}",
                pick_id=pick.resource_id,
                time_residual=res[_i] / 1000,
                phase="P",
                earth_model_id=earth_model_id,
                distance=dists[_i]
            )
        )

    o.time_errors = QuantityError(uncertainty=rms / 1000)

    event.origins.append(o)
    event.preferred_origin_id = o.resource_id

    return event
