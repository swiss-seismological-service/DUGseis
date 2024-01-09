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
#from aurem.pickers import AIC
from obspy.core.event import Pick, WaveformStreamID
import numpy as np
from obspy.signal.trigger import recursive_sta_lta

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
    # pick_list = []
    # for pick in picks:  # get waveform id from all picks
    #     pick_list.append(pick.waveform_id.id)

    for idx, pick in enumerate(picks):
        # if tr.id in pick_list:
        # idx_pick_pick_list = pick_list.index(tr.id)
        pick_ref_starttime = pick.time - pick_refine_window / 2
        pick_ref_endtime = pick.time + pick_refine_window / 2

        if not (is_time_between(  # check if pick refinement slice window is in stream window
                stream.traces[0].stats.starttime,
                stream.traces[0].stats.endtime,
                pick_ref_starttime) \
                or \
                is_time_between(
                    stream.traces[0].stats.starttime,
                    stream.traces[0].stats.endtime,
                    pick_ref_endtime)):
            continue
        else:
            signal = stream.select(id=pick.waveform_id.id)
            signal = signal.slice(
                starttime=pick_ref_starttime, endtime=pick_ref_endtime
            )
            # tr.trim(pick_starttime, pick_endtime)
            aicobj = AIC(signal, id=pick.waveform_id.id)
            aicobj.work()
            aic_pick_time = aicobj.get_pick()
            # idx_aic = aicobj.get_pick_index()
            # aicobj.plot()

            # if no pick, just go with previous
            if not aic_pick_time:
                continue
            # only take refined pick when delta below 0.8 * pick_window STA/LTA pick
            elif np.abs(pick.time - aic_pick_time) <= 0.8 * pick_refine_window:

                # try to calculate snr
                # try:
                #     snr = max(abs(signal.traces[0].data[idx_aic + 10:idx_aic + 100])) / max(
                #         abs(signal.traces[0].data[idx_aic - 100:idx_aic - 10]))
                # except ValueError:
                #     continue

                picks[idx] = Pick(
                    time=aic_pick_time,
                    waveform_id=WaveformStreamID(
                        network_code=signal.traces[0].stats.network,
                        station_code=signal.traces[0].stats.station,
                        location_code=signal.traces[0].stats.location,
                        channel_code=signal.traces[0].stats.channel,
                    ),
                    method_id="aic",
                    phase_hint="P",
                    evaluation_mode="automatic",  # comments=[str(round(snr, 3))],
                )
            else:
                continue
    return picks


def get_noise_levels(stream, nsta, nlta, added):
    noise_levels = []
    noise_levels_95_percentile = []
    for idx, tr in enumerate(stream):
        data_cft = recursive_sta_lta(tr.data, nsta, nlta)
        noise_levels.append(round(np.max(data_cft), 1) + added)
        noise_levels_95_percentile.append(round(np.percentile(data_cft, 95), 1))

    return noise_levels, noise_levels_95_percentile
