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
Magnitude determination routines.
"""
import numpy as np
from obspy.core.event import Magnitude
from obspy.core.event.magnitude import Amplitude
from obspy.core.event.base import TimeWindow


def amplitude_based_relative_magnitude(st_event, event):
    # main parameters for magnitude processing
    s_wave_velocity = 3100  # [m/s]
    filter_freq_min = 3e3  # [Hz]
    filter_freq_max = 12e3  # [Hz]
    filter_corners = 4
    filter_zerophase = 'false'

    p_amp = np.empty((0, len(event.picks)), int)
    n_amp = np.empty((0, len(event.picks)), int)
    t_window = []
    signal_copy = st_event.copy()
    noise_copy = st_event.copy()
    conversion_factor_counts_mV = 0.003125  # assuming 64'000 (not 2**16 = 65536) counts
    # resolution per +/-10V (direct communication by GMuG) as well as 30dB pre-amplification
    # and 10 dB amplification from the supply/filter unit

    for index, pick in enumerate(event.picks):
        dist = event.origins[0].arrivals[index].distance  # get distances
        s_arrival = event.preferred_origin().time + (dist/s_wave_velocity)  # calc. theoretical s-wave arrival
        delta_p_s = s_arrival - pick.time  # time between s-arrival and p-pick
        t_window.append(TimeWindow(begin=0.0, end=delta_p_s * 2, reference=pick.time - delta_p_s))  # prepare
        # "Amplitude" class TimeWindow

        # get signal window
        signal = signal_copy.select(id=pick.waveform_id.id)[0]
        signal = signal.trim(starttime=pick.time - delta_p_s, endtime=pick.time + delta_p_s)
        signal = signal.detrend('constant')
        signal.taper(max_percentage=0.05, type="hann")
        signal = signal.filter('bandpass', freqmin=filter_freq_min, freqmax=filter_freq_max,
                               corners=filter_corners, zerophase=filter_zerophase)
        p_amp = np.append(p_amp, np.amax(np.abs(signal.data)) * conversion_factor_counts_mV)  # get p-wave amplitude

        # get noise window
        noise = noise_copy.select(id=pick.waveform_id.id)[0]
        noise = noise.trim(starttime=pick.time - 2*delta_p_s, endtime=pick.time)
        noise = noise.detrend('constant')
        noise.taper(max_percentage=0.05, type="hann"  )
        noise = noise.filter('bandpass', freqmin=filter_freq_min, freqmax=filter_freq_max,
                             corners=filter_corners, zerophase=filter_zerophase)
        noise_95pers = np.percentile(np.abs(noise.data), 95)  # take 95 % percentile to omit outliers
        n_amp = np.append(n_amp, noise_95pers * conversion_factor_counts_mV)

    # And fill event with amplitudes.
    for index, pick in enumerate(event.picks):
        event.amplitudes.append(
            Amplitude(resource_id=f"amplitude/{index}/{event.origins[0].resource_id.id}",
                      generic_amplitude=p_amp[index],
                      type='AMB',
                      unit='other',
                      snr=p_amp[index] / n_amp[index],
                      waveform_id=st_event[index].id,
                      time_window=TimeWindow(begin=t_window[index].begin, end=t_window[index].end,
                                             reference=t_window[index].reference)))

    # Magnitude determination per station
    f_0 = (filter_freq_max - filter_freq_min) / 2 + filter_freq_min  # dominant frequency [Hz]
    Q = 76.0  # Quality factor [] introduced by Hansruedi Maurer (Email 29.07.2021)
    V_P = 5400.0  # P-wave velocity [m/s]
    r_0 = 10.0  # reference distance [m]
    Grimsel_factor = 4.0  # determined Grimsel factor

    Mr_station = np.empty((0, len(event.picks)), int)
    for ind, pick in enumerate(event.picks):
        dist = event.origins[0].arrivals[ind].distance
        corr_fac_1 = np.exp(np.pi*(dist-r_0)*f_0/(Q*V_P))
        corr_fac_2 = dist/r_0

        Mr_station = np.append(Mr_station, np.log10(p_amp[ind] * corr_fac_2 * corr_fac_1))
    Mr = np.log10(np.sqrt(np.sum((10**Mr_station)**2) / len(Mr_station)))  # network magnitude
    MA_station = Mr_station - Grimsel_factor  # correction with Grimsel adjustment factor
    MA = Mr - Grimsel_factor  # correction with Grimsel adjustment factor

    # Append magnitude to event
    event.magnitudes.append(
        Magnitude(origin_id=event.preferred_origin_id.id,
                  mag=MA,
                  magnitude_type='Mb',
                  method_id="method/magnitude/amplitude_based",
                  station_count=len(Mr_station),
                  station_magnitude_contributions=MA_station.tolist()))

    return event
