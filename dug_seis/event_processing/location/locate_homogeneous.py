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
    velocity: typing.Union[float, typing.Dict[str, float]],
    damping: float,
    local_to_global_coordinates: typing.Callable,
    anisotropic_params: typing.Optional[
        typing.Union[typing.Dict[str, float], typing.Dict[str, typing.Dict[str, float]]]
    ] = None,
    verbose: bool = False,
) -> Event:
    """
    Locate an event in a homogeneous background medium from a list of picks
    using travel times.

    This version will only consider P phase picks and ignores all other picks.

    Args:
        picks: List of pick objects to use. The all must either be the same
            phase, or a the velocity + anisotropic parameters must be given
            for each pick type.
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
    # Set of all phases available in the picks.
    all_phases = set()
    # Collect all picks.
    event_picks = []

    for i, pick in enumerate(picks):
        pick = copy.deepcopy(pick)
        # Phase hints are necessary.
        if not pick.phase_hint:
            raise ValueError(f"Pick with index {i} has no phase hint.")
        all_phases.add(pick.phase_hint)
        event_picks.append(pick)

    if len(event_picks) < 3:
        raise ValueError("At least 3 picks are required for an event location.")

    # If velocity is given as a single number but there is only one phase, convert
    # it to a dictionary.
    if isinstance(velocity, float) and len(all_phases) == 1:
        velocity = {list(all_phases)[0]: velocity}
    if (
        anisotropic_params
        and set(anisotropic_params.keys()) == {"inc", "azi", "delta", "epsilon"}
        and len(all_phases) == 1
    ):
        anisotropic_params = {list(all_phases)[0]: anisotropic_params}

    ##
    # Lots of sanity checks.
    ##
    # Raise an exception if multiple phases but only a single velocity.
    if not isinstance(velocity, dict):
        raise ValueError(
            f"Picks available for these phases: {all_phases}. Only a"
            "single velocity value has been specified. Please specify one "
            "velocity per phase."
        )

    velocity_phases = set(velocity.keys())
    if not all_phases.issubset(velocity_phases):
        raise ValueError(
            f"Must specify one velocity per phase. Phases available in picks: {all_phases}. "
            f"Velocities are defined for phases: {velocity_phases}"
        )
    if anisotropic_params:
        anisotropy_phases = set(anisotropic_params.keys())
        if not all_phases.issubset(anisotropy_phases):
            raise ValueError(
                "Must specify one set of anisotropic parameters per phase. Phases "
                f"available in picks: {all_phases}. "
                f"Anisotropy is defined for phases: {anisotropy_phases}"
            )

    # XXX: Add the same error handling to the anisotropic parameters.

    # QC on the anisotropic parameters if given.
    if anisotropic_params:
        for phase, values in anisotropic_params.items():
            if set(values.keys()) != {
                "inc",
                "azi",
                "delta",
                "epsilon",
            }:
                raise ValueError(
                    "The 'anisotropic_params' dictionary, if given, must contain "
                    f"these keys: inc, azi, delta, epsilon. For '{phase}' contains: "
                    f"{list(anisotropic_params.keys())}"
                )

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

    vel = np.array([velocity[p.phase_hint] for p in event_picks]) / 1000.0

    loc = sensor_coords[t_relative.index(min(t_relative)), :] + 0.1
    t0 = min(t_relative)
    nit = 0
    jacobian = np.zeros([npicks, 4])
    dm = 1.0 * np.ones(4)

    # Actual optimization.
    while nit < 100 and np.linalg.norm(dm) > 0.00001:
        nit = nit + 1

        # Calculate anisotropic velocities if necessary.
        if anisotropic_params:
            for i in range(npicks):
                param_ani = anisotropic_params[event_picks[i].phase_hint]
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
                    * np.cos(param_ani["inc"])
                    * np.cos(param_ani["azi"])
                    + np.cos(inc)
                    * np.sin(azi)
                    * np.cos(param_ani["inc"])
                    * np.sin(param_ani["azi"])
                    + np.sin(inc) * np.sin(param_ani["inc"])
                )
                vel[i] = (
                    velocity[event_picks[i].phase_hint]
                    / 1000.0
                    * (
                        1.0
                        + param_ani["delta"] * np.sin(theta) ** 2 * np.cos(theta) ** 2
                        + param_ani["epsilon"] * np.sin(theta) ** 4
                    )
                )

        dist = [np.linalg.norm(loc - sensor_coords[i, :]) for i in range(npicks)]
        tcalc = [dist[i] / vel[i] + t0 for i in range(npicks)]

        res = [t_relative[i] - tcalc[i] for i in range(npicks)]
        rms = np.linalg.norm(res) / npicks
        for j in range(3):
            for i in range(npicks):
                jacobian[i, j] = -(sensor_coords[i, j] - loc[j]) / (vel[i] * dist[i])
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
    dists = np.linalg.norm(
        sensor_coords - np.tile(loc, (len(sensor_coords), 1)), axis=1
    )

    # Convert local coordinates to WGS84.
    latitude, longitude, depth = local_to_global_coordinates(loc)

    # Create descriptive ids.
    if anisotropic_params is None:
        s = "isotropic"
    else:
        s = "anisotropic"

    # Assemble a velocity string for the earth model id.
    vel_str = "__".join(
        [
            f"{i[0]}_{int(round(i[1]))}"
            for i in sorted(velocity.items(), key=lambda x: x[0])
        ]
    )

    earth_model_id = ResourceIdentifier(
        id=f"earth_model/homogeneous/{s}/velocity={vel_str}"
    )
    method_id = "method/travel_time/homogeneous_model"

    # Create origin.
    o = Origin(
        resource_id=f"origin/travel_time/homogeneous_model/{uuid.uuid4()}",
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
                phase=pick.phase_hint,
                earth_model_id=earth_model_id,
                distance=dists[_i],
            )
        )

    o.time_errors = QuantityError(uncertainty=rms / 1000)

    event.origins.append(o)
    event.preferred_origin_id = o.resource_id

    return event
