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
import logging
logger = logging.getLogger(__name__)



def is_time_between(begin_time, end_time, check_time):
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time <= end_time


def amplitude_based_relative_magnitude(st_event, event):
    # main parameters for magnitude processing
    s_wave_velocity = 3100  # [m/s]
    filter_freq_min = 3e3  # [Hz]
    filter_freq_max = 12e3  # [Hz]
    filter_corners = 4
    filter_zerophase = 'false'
    signal_copy = st_event.copy()
    noise_copy = st_event.copy()
    gainLogAE = 100  # 10dB + 30dB
    gainAE = 1. / gainLogAE
    Count2VoltAE = 10. / 32000  # 10V on 32000 samples
    conversion_factor_counts_mV = gainAE * Count2VoltAE  # assuming 64'000 (not 2**16 = 65536) counts
    # resolution per +/-10V (direct communication by GMuG) as well as 30dB pre-amplification
    # and 10 dB amplification from the supply/filter unit
    # Magnitude determination per station
    f_0 = (filter_freq_max - filter_freq_min) / 2 + filter_freq_min  # dominant frequency [Hz]
    Q = 76.0  # Quality factor [] introduced by Hansruedi Maurer (Email 29.07.2021)
    V_P = 5100.0  # P-wave velocity [m/s]
    r_0 = 10.0  # reference distance [m]
    ### For amplitude
    p_amp = []
    n_amp = []
    t_window = []
    distances = []
    ### For magnitude
    s_m = []
    Mr_station = []

    count = 0
    tmpPicks = event.picks
    if len(tmpPicks)>len(event.preferred_origin().arrivals):
        idx = [i for i,x in enumerate(tmpPicks) if x.evaluation_mode=='manual']
        PicksManual = [tmpPicks[x].waveform_id for x in idx]
        idx2 = [i for i,x in enumerate(tmpPicks) if x.waveform_id in PicksManual and x.evaluation_mode=='automatic']
        PickDouble = [tmpPicks[x].waveform_id for x in idx2]
        Picks = [x for x in tmpPicks if x.waveform_id not in PickDouble or x.evaluation_mode=='manual']
    else:
        Picks = tmpPicks

    for index, pick in enumerate(Picks):
        dist = event.preferred_origin().arrivals[index].distance  # get distances
        s_arrival = event.preferred_origin().time + (dist / s_wave_velocity)  # calc. theoretical s-wave arrival
        delta_p_s = s_arrival - pick.time  # time between s-arrival and p-pick
        signal_window_start_time = pick.time - delta_p_s
        signal_window_end_time = pick.time + delta_p_s
        noise_window_start_time = pick.time - 2*delta_p_s
        noise_window_end_time = pick.time

        # magnitude computation is omitted when delta_p_s or signal/noise windows are not within the st_event time
        # interval
        if ((delta_p_s < 0)
                or not is_time_between(signal_copy[0].stats.starttime, signal_copy[0].stats.endtime, signal_window_start_time)
                or not is_time_between(signal_copy[0].stats.starttime, signal_copy[0].stats.endtime, signal_window_end_time)
                or not is_time_between(noise_copy[0].stats.starttime, noise_copy[0].stats.endtime, noise_window_start_time)
                or not is_time_between(noise_copy[0].stats.starttime, noise_copy[0].stats.endtime, noise_window_end_time)):

            continue

        distances.append(dist)  # only the distances for which an amplitude can be estimated
        t_window.append(TimeWindow(begin=0.0, end=delta_p_s * 2, reference=pick.time - delta_p_s))  # prepare
        # "Amplitude" class TimeWindow

        # get signal window
        signal = signal_copy.select(id=pick.waveform_id.id)[0]
        signal = signal.trim(starttime=signal_window_start_time, endtime=signal_window_end_time)
        signal = signal.detrend('constant')
        signal.taper(max_percentage=0.05, type="hann")
        signal = signal.filter('bandpass', freqmin=filter_freq_min, freqmax=filter_freq_max,
                               corners=filter_corners, zerophase=filter_zerophase)
        p_amp.append(np.amax(np.abs(signal.data)) * conversion_factor_counts_mV)  # get p-wave amplitude

        # get noise window
        noise = noise_copy.select(id=pick.waveform_id.id)[0]
        noise = noise.slice(starttime=noise_window_start_time, endtime=noise_window_end_time)
        noise = noise.detrend('constant')
        noise.taper(max_percentage=0.05, type="hann")
        noise = noise.filter('bandpass', freqmin=filter_freq_min, freqmax=filter_freq_max,
                             corners=filter_corners, zerophase=filter_zerophase)
        noise_95pers = np.percentile(np.abs(noise.data), 95)  # take 95 % percentile to omit outliers
        n_amp.append(noise_95pers * conversion_factor_counts_mV)

        event.amplitudes.append(
            Amplitude(resource_id=f"amplitude/p_wave/{uuid.uuid4()}",
                      generic_amplitude=p_amp[count],
                      type='AMB',
                      unit='other',
                      snr=p_amp[count] / n_amp[count],
                      waveform_id=WaveformStreamID(network_code=pick.waveform_id.network_code,
                                                   station_code=pick.waveform_id.station_code,
                                                   location_code=pick.waveform_id.location_code,
                                                   channel_code=pick.waveform_id.channel_code),
                      time_window=TimeWindow(begin=t_window[count].begin, end=t_window[count].end,
                                             reference=t_window[count].reference)))

        print(len(event.amplitudes))
        print(index)
        if not event.amplitudes[index]:
            continue

        corr_fac_1 = np.exp(np.pi * (dist - r_0) * f_0 / (Q * V_P))
        # correction for geometrical spreading
        corr_fac_2 = dist / r_0
        # station magnitude computation
        tmpMrSta = np.log10(p_amp[count] * corr_fac_2 * corr_fac_1)
        Mr_station.append(tmpMrSta)
        # append station magnitude to event
        event.station_magnitudes.append(
            StationMagnitude(resource_id=f"station_magnitude/p_wave_magnitude/relative/{uuid.uuid4()}",
                             origin_id=event.preferred_origin_id.id,
                             mag=0.52 * tmpMrSta - 4.46,
                             station_magnitude_type='Mb',
                             amplitude_id=event.amplitudes[index].resource_id))
        # store station magnitude contribution
        s_m.append(
            StationMagnitudeContribution(
                station_magnitude_id="smi:local/" + event.station_magnitudes[index].resource_id.id,
                weight=1 / len(event.amplitudes)))

        count+=1

    if not event.amplitudes:  # if no amplitudes are assigned return from the definition
        delattr(event, 'amplitudes')
        return event


    Mr_station = np.array(Mr_station)
    # Mr_network = np.log10(np.sqrt(np.sum((10**Mr_station)**2) / len(Mr_station)))  # network magnitude
    Mr_network = np.sum(Mr_station) / len(Mr_station) # network magnitude
    MA_network = 0.52*Mr_network-4.46  # temporary relation deduced from VALTER Stimulaiton1, using individual stations estimations

    # Create network magnitude and add station magnitude contribution
    m = Magnitude(resource_id=f"magnitude/p_wave_magnitude/relative/{uuid.uuid4()}",
                  mag=MA_network,
                  magnitude_type='Mb',
                  method_id="method/magnitude/amplitude_based",
                  station_count=len(Mr_station),
                  station_magnitude_contributions=s_m)

    # append magnitude
    event.magnitudes.append(m)
    logger.info(
        f"MA_net successfully computed: {MA_network:.2f}")
    # f"Network magnitude successfully computed: MA{MA_network:.2f}")

    return event

