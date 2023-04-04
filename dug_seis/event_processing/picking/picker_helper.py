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
Script that contains various helper functions for picker.
"""
import numpy as np
from dug_seis.event_processing.magnitudes.amplitude_based_magnitudes import is_time_between
from aurem.pickers import AIC
from obspy.core.event import Pick, WaveformStreamID

def mask_list_indices(lst, indices):
    """
    Function that masks list depending on indices.
    """
    return [lst[i] for i in indices]


def time_delta_between_picks(picks, thr_time_deltas):
    """
    Function that calculates time deltas between picks and removes picks which are within set time threshold.
    Input:
    - Obspy picks in list
    - threshold of time-delta
    Output:
    - Obspy picks in list which where not within set time-delta threshold
    - nr of picks within set delta-time threshold
    - nr of picks which do not fall into delta-time interval
    """
    # time deltas between all arrivals
    time_deltas = np.ones(shape=(len(picks), len(picks)))
    for i in range(0, len(picks)):
        for j in range(i, len(picks)):
            time_deltas[i, j] = np.abs(picks[i].time - picks[j].time)
    np.fill_diagonal(time_deltas, 1.0)

    # find time deltas below threshold
    ind_low_time_delta = np.unique(np.where(time_deltas <= thr_time_deltas))
    nr_low_time_deltas = len(ind_low_time_delta)
    ind_high_time_delta = np.setdiff1d(np.arange(0, len(time_deltas), 1, dtype=int), ind_low_time_delta)
    nr_high_time_deltas = len(ind_high_time_delta)
    picks_masked = mask_list_indices(picks, ind_high_time_delta)
    return picks_masked, nr_low_time_deltas, nr_high_time_deltas


def AIC_picker_wrapper(stream, picks, pick_refine_window=0.004):
    pick_list = []
    for pick in picks:  # get waveform id from all picks
        pick_list.append(pick.waveform_id.id)

    for idx, tr in enumerate(stream):
        if tr.id in pick_list:
            idx_pick_pick_list = pick_list.index(tr.id)
            pick_starttime = picks[idx_pick_pick_list].time - pick_refine_window / 2
            pick_endtime = picks[idx_pick_pick_list].time + pick_refine_window / 2

            if not is_time_between(  # check if pick refinement trim window is in st_event window
                    tr.stats.starttime,
                    tr.stats.endtime,
                    pick_starttime) \
                    and \
                    is_time_between(
                        tr.stats.starttime,
                        tr.stats.endtime,
                        pick_starttime):
                stream.remove(tr)
            else:
                tr.trim(pick_starttime, pick_endtime)
                aicobj = AIC(stream, id=tr.id)
                aicobj.work()
                aic_pick_time = aicobj.get_pick()
                # if no pick, just go with previous
                if not aic_pick_time:
                    continue
                # aicobj.plot()
                # only take refined pick when delta below 0.8 * pick_window STA/LTA pick
                if np.abs(picks[idx_pick_pick_list].time - aic_pick_time) <= 0.8 * pick_refine_window:
                    picks[idx_pick_pick_list] = Pick(
                        time=aic_pick_time,
                        waveform_id=WaveformStreamID(
                            network_code=tr.stats.network,
                            station_code=tr.stats.station,
                            location_code=tr.stats.location,
                            channel_code=tr.stats.channel,
                        ),
                        method_id="aic",
                        phase_hint="P",
                        evaluation_mode="automatic",
                    )
                else:
                    continue
        else:  # remove trace if not picked
            stream.remove(tr)
    return picks
