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
    ind_high_time_delta = np.setdiff1d(
        np.arange(0, len(time_deltas), 1, dtype=int), ind_low_time_delta
    )
    nr_high_time_deltas = len(ind_high_time_delta)
    picks_masked = mask_list_indices(picks, ind_high_time_delta)
    return picks_masked, nr_low_time_deltas, nr_high_time_deltas
