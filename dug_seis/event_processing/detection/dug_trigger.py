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
Central triggering routine within DUGSeis.
"""

import obspy
import typing

from .coincidence_trigger import coincidence_trigger


def dug_trigger(
    st: obspy.Stream,
    active_triggering_channel: typing.Optional[str],
    minimum_time_between_events_in_seconds: float,
    max_spread_electronic_interference_in_seconds: float,
    conincidence_trigger_opts: typing.Dict,
):
    """
    DUGSeis triggering routine.

    This is largely a wrapper around the coincidence trigger with a few more QA
    steps and some classification heuristics.

    Args:
        st: ObsPy Stream objects with the waveform data.
        active_triggering_channel: Id of the active triggering channel. If
            this channel was amongst the triggering ones, the event will be
            classified as active.
        minimum_time_between_events_in_seconds: Don't allow two events too close
            in time.
        max_spread_electronic_interference_in_seconds: The maximum time between
            the first and the last moment of triggering at different stations
            for which this event is classified as electronic interference.
            Usually set to 0.25e-2.
        coincidence_trigger_opts: Keyword arguments passed on to the coincidence
            trigger.
    """
    triggers = coincidence_trigger(stream=st, **conincidence_trigger_opts)

    events = []
    for trig in triggers:
        event = {"time": min(trig["time"]), "triggered_channels": trig["trace_ids"]}
        # Too close to previous event.
        if (
            events
            and abs(events[-1]["time"] - event["time"])
            < minimum_time_between_events_in_seconds
        ):
            continue

        # Classification.
        # Triggered on active triggering channel == active
        if active_triggering_channel and active_triggering_channel in trig["trace_ids"]:
            classification = "active"
        # Single input trace == passive
        elif len(st) == 1:
            classification = "passive"
        # Spread too small == electronic noise.
        elif (
            max(trig["time"]) - min(trig["time"])
        ) < max_spread_electronic_interference_in_seconds:
            classification = "electronic"
        # Otherwise just treat is as passive.
        else:
            classification = "passive"

        event["classification"] = classification
        events.append(event)

    return events
