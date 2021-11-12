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
from obspy.core.event.magnitude import Amplitude, StationMagnitude, StationMagnitudeContribution
from obspy.core.event.base import TimeWindow, WaveformStreamID
import uuid


def amplitude_based_relative_magnitude(st_event, event):
    # main parameters for magnitude processing
    s_wave_velocity = 3100  # [m/s]
    filter_freq_min = 3e3  # [Hz]
    filter_freq_max = 12e3  # [Hz]
    filter_corners = 4
    filter_zerophase = 'false'
    signal_copy = st_event.copy()
    noise_copy = st_event.copy()
    conversion_factor_counts_mV = 0.003125  # assuming 64'000 (not 2**16 = 65536) counts
    # resolution per +/-10V (direct communication by GMuG) as well as 30dB pre-amplification
    # and 10 dB amplification from the supply/filter unit
    p_amp = []
    n_amp = []
    t_window = []
    distances = []
    count = 0
    for index, pick in enumerate(event.picks):
        dist = event.origins[0].arrivals[index].distance  # get distances
        s_arrival = event.preferred_origin().time + (dist/s_wave_velocity)  # calc. theoretical s-wave arrival
        delta_p_s = s_arrival - pick.time  # time between s-arrival and p-pick
        if delta_p_s < 0:
            continue
        distances.append(dist)  # only the distances for which an amplitude can be estimated
        t_window.append(TimeWindow(begin=0.0, end=delta_p_s * 2, reference=pick.time - delta_p_s))  # prepare
        # "Amplitude" class TimeWindow

        # get signal window
        signal = signal_copy.select(id=pick.waveform_id.id)[0]
        signal = signal.trim(starttime=pick.time - delta_p_s, endtime=pick.time + delta_p_s)
        signal = signal.detrend('constant')
        signal.taper(max_percentage=0.05, type="hann")
        signal = signal.filter('bandpass', freqmin=filter_freq_min, freqmax=filter_freq_max,
                               corners=filter_corners, zerophase=filter_zerophase)
        p_amp.append(np.amax(np.abs(signal.data)) * conversion_factor_counts_mV)  # get p-wave amplitude

        # get noise window
        noise = noise_copy.select(id=pick.waveform_id.id)[0]
        noise = noise.trim(starttime=pick.time - 2*delta_p_s, endtime=pick.time)
        noise = noise.detrend('constant')
        noise.taper(max_percentage=0.05, type="hann")
        noise = noise.filter('bandpass', freqmin=filter_freq_min, freqmax=filter_freq_max,
                             corners=filter_corners, zerophase=filter_zerophase)
        noise_95pers = np.percentile(np.abs(noise.data), 95)  # take 95 % percentile to omit outliers
        n_amp.append(noise_95pers * conversion_factor_counts_mV)

    # And add amplitude to the respective event
    for index, pick in enumerate(event.picks):
        event.amplitudes.append(
            Amplitude(resource_id=f"amplitude/p_wave/{uuid.uuid4()}",
                      generic_amplitude=p_amp[count],
                      type='AMB',
                      unit='other',
                      snr=p_amp[count] / n_amp[count],
                      waveform_id=WaveformStreamID(network_code=st_event[index].stats.network,
                                                   station_code=st_event[index].stats.station,
                                                   location_code=st_event[index].stats.location,
                                                   channel_code=st_event[index].stats.channel),
                      time_window=TimeWindow(begin=t_window[count].begin, end=t_window[count].end,
                                             reference=t_window[count].reference)))
        count += 1

    # Magnitude determination per station
    f_0 = (filter_freq_max - filter_freq_min) / 2 + filter_freq_min  # dominant frequency [Hz]
    Q = 76.0  # Quality factor [] introduced by Hansruedi Maurer (Email 29.07.2021)
    V_P = 5400.0  # P-wave velocity [m/s]
    r_0 = 10.0  # reference distance [m]
    Grimsel_factor = 4.0  # determined Grimsel factor

    s_m = []
    Mr_station = []
    for index, amplitudes in enumerate(event.amplitudes):
        # distance source receiver
        dist = distances[index]
        # correction for attenuation
        corr_fac_1 = np.exp(np.pi*(dist-r_0)*f_0/(Q*V_P))
        # correction for geometrical spreading
        corr_fac_2 = dist/r_0
        # station magnitude computation
        Mr_station.append(np.log10(amplitudes.generic_amplitude * corr_fac_2 * corr_fac_1))
        # append station magnitude to event
        event.station_magnitudes.append(
            StationMagnitude(resource_id=f"station_magnitude/p_wave_magnitude/relative/{uuid.uuid4()}",
                             origin_id=event.preferred_origin_id.id,
                             mag=Mr_station[index] - Grimsel_factor,
                             station_magnitude_type='Mb',
                             amplitude_id=event.amplitudes[index].resource_id))
        # store station magnitude contribution
        s_m.append(
            StationMagnitudeContribution(station_magnitude_id="smi:local/" + event.station_magnitudes[index].resource_id.id,
                                         weight=1/len(event.amplitudes)))
    Mr_station = np.array(Mr_station)
    Mr_network = np.log10(np.sqrt(np.sum((10**Mr_station)**2) / len(Mr_station)))  # network magnitude
    MA_network = Mr_network - Grimsel_factor  # correction with Grimsel adjustment factor

    # Create network magnitude and add station magnitude contribution
    m = Magnitude(resource_id=f"magnitude/p_wave_magnitude/relative/{uuid.uuid4()}",
                  mag=MA_network,
                  magnitude_type='Mb',
                  method_id="method/magnitude/amplitude_based",
                  station_count=len(Mr_station),
                  station_magnitude_contributions=s_m)

    # append magnitude
    event.magnitudes.append(m)

    return event
