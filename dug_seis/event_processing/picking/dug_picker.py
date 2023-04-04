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
Central picking routine in DUGSeis.
"""
import typing

import obspy
from obspy.core.event import WaveformStreamID, Pick
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

from .pickers.PhasePApy_Austin_Holland.fbpicker import FBPicker
from .pickers.PhasePApy_Austin_Holland.ktpicker import KTPicker
from .pickers.PhasePApy_Austin_Holland.aicdpicker import AICDPicker
from .pickers.P_Phase_Picker_USGS.pphasepicker import pphasepicker


def dug_picker(
    st: obspy.Stream,
    pick_algorithm: str,
    picker_opts: typing.Optional[typing.Dict[str, typing.Any]] = None,
):
    """
    Apply a picker algorithm on all traces to pick first arrivals.

    Args:
        st: The ObsPy Stream object.
        pick_algorithm: Name of the picking algorithm.
        picker_opts: Options passed to the picker.
    """
    # Make sure the sampling rates are similar enough.
    srs = set(round(tr.stats.sampling_rate, 3) for tr in st)
    if len(srs) != 1:
        raise ValueError(f"Varying sampling rates: {srs}")

    picks = []

    # apply the fb picker.
    if pick_algorithm == "fb":
        t_long = 5 / 1000
        freqmin = 1
        mode = "rms"
        t_ma = 20 / 1500
        nsigma = 8 / 100
        t_up = 0.4 / 100
        nr_len = 2
        nr_coeff = 2
        pol_len = 10
        pol_coeff = 10
        uncert_coeff = 3
        picker = FBPicker(
            t_long=t_long,
            freqmin=freqmin,
            mode=mode,
            t_ma=t_ma,
            nsigma=nsigma,
            t_up=t_up,
            nr_len=nr_len,
            nr_coeff=nr_coeff,
            pol_len=pol_len,
            pol_coeff=pol_coeff,
            uncert_coeff=uncert_coeff,
        )

        final_picks = []

        # do picking for each trace in snippet
        for tr in st:
            tr = tr.copy()
            # Perform a linear detrend on the data
            tr.detrend("linear")

            scnl, picks, polarity, snr, uncert = picker.picks(tr)

            if len(picks):
                # if a pick is done on a trace, convert it to seconds
                # t_picks=trig[0][0] / sampling_rate
                # and add the start time of the snippet
                # self.wf_stream[0].stats['starttime'] + t_picks
                t_pick_UTC = picks[0]
                final_picks.append(
                    Pick(
                        time=t_pick_UTC,
                        waveform_id=WaveformStreamID(
                            network_code=tr.stats.network,
                            station_code=tr.stats.station,
                            channel_code=tr.stats.channel,
                            location_code=tr.stats.location,
                        ),
                        method_id="AICD",
                        phase_hint="P",
                        evaluation_mode="automatic",
                    )
                )

        return final_picks

    # apply the kt (kurtosis) picker.
    elif pick_algorithm == "kt":

        t_win = 1 / 2000
        t_ma = 10 / 2000
        nsigma = 6 / 100
        t_up = 0.78 / 100
        nr_len = 2
        nr_coeff = 2
        pol_len = 10
        pol_coeff = 10
        uncert_coeff = 3
        chenPicker = KTPicker(
            t_win=t_win,
            t_ma=t_ma,
            nsigma=nsigma,
            t_up=t_up,
            nr_len=nr_len,
            nr_coeff=nr_coeff,
            pol_len=pol_len,
            pol_coeff=pol_coeff,
            uncert_coeff=uncert_coeff,
        )

        final_picks = []

        # do picking for each trace in snippet
        for tr in st:
            tr = tr.copy()

            # Perform a linear detrend on the data
            tr.detrend("linear")
            scnl, picks, polarity, snr, uncert = chenPicker.picks(tr)

            if len(picks):
                t_pick_UTC = picks[0]
                final_picks.append(
                    Pick(
                        time=t_pick_UTC,
                        waveform_id=WaveformStreamID(
                            network_code=tr.stats.network,
                            station_code=tr.stats.station,
                            location_code=tr.stats.location,
                            channel_code=tr.stats.channel,
                        ),
                        method_id="AICD",
                        phase_hint="P",
                        evaluation_mode="automatic",
                    )
                )
        return final_picks

    # apply the AICD picker - has to be fixed at a lower level.
    elif pick_algorithm == "aicd":
        st = st.copy().filter(
            "bandpass",
            freqmin=picker_opts["bandpass_f_min"],
            freqmax=picker_opts["bandpass_f_max"],
        )
        chenPicker = AICDPicker(
            t_ma=picker_opts["t_ma"] / 1000,
            nsigma=picker_opts["nsigma"],
            t_up=picker_opts["t_up"] / 1000,
            nr_len=picker_opts["nr_len"],
            nr_coeff=picker_opts["nr_coeff"],
            pol_len=picker_opts["pol_len"],
            pol_coeff=picker_opts["pol_coeff"],
            uncert_coeff=picker_opts["uncert_coeff"],
        )

        final_picks = []

        # do picking for each trace in snippet
        for tr in st:
            # Perform a linear detrend on the data
            tr.detrend("linear")

            scnl, picks, polarity, snr, uncert = chenPicker.picks(tr)

            if len(picks):
                t_pick_UTC = picks[0]
                final_picks.append(
                    Pick(
                        time=t_pick_UTC,
                        waveform_id=WaveformStreamID(
                            network_code=tr.stats.network,
                            station_code=tr.stats.station,
                            location_code=tr.stats.location,
                            channel_code=tr.stats.channel,
                        ),
                        method_id="AICD",
                        phase_hint="P",
                        evaluation_mode="automatic",
                    )
                )

        return final_picks

    # apply the STA LTA picker.
    elif pick_algorithm == "sta_lta":
        p_picks = sta_lta(st, **picker_opts)
        picks += p_picks

    # apply the P Phase picker.
    elif pick_algorithm == "pphase":
        Tn = 0.01
        xi = 0.6

        final_picks = []

        # do picking for each trace in snippet
        for tr in st:
            loc = pphasepicker(tr, Tn, xi)
            if loc != "nopick":
                t_picks = loc
                # and add the start time of the snippet
                t_pick_UTC = tr.stats.starttime + t_picks
                final_picks.append(
                    Pick(
                        time=t_pick_UTC,
                        waveform_id=WaveformStreamID(
                            network_code=tr.stats.network,
                            station_code=tr.stats.station,
                            location_code=tr.stats.location,
                            channel_code=tr.stats.channel,
                        ),
                        method_id="pphase",
                        phase_hint="P",
                        evaluation_mode="automatic",
                    )
                )
        return final_picks

    else:
        raise NotImplementedError

    return picks


def sta_lta(stream, st_window, lt_window, thresholds):
    """
    Apply the STA LTA picker
    """
    stream.detrend("constant")
    # stream.filter("bandpass", freqmin=1000.0, freqmax=20000.0)
    sampling_rate = stream[0].stats.sampling_rate

    picks = []

    for idx, trace in enumerate(stream):
        # create characteristic function
        cft = recursive_sta_lta(trace, st_window, lt_window)

        # do picking
        trig = trigger_onset(cft, thresholds[idx], thresholds[idx])

        if len(trig):
            t_pick_UTC = (
                trace.stats.starttime
                + adjust_pick_time(trig[0][0], cft) / sampling_rate
            )
            picks.append(
                Pick(
                    time=t_pick_UTC,
                    waveform_id=WaveformStreamID(
                        network_code=trace.stats.network,
                        station_code=trace.stats.station,
                        location_code=trace.stats.location,
                        channel_code=trace.stats.channel,
                    ),
                    method_id="recursive_sta_lta",
                    phase_hint="P",
                    evaluation_mode="automatic",
                )
            )

    return picks


def adjust_pick_time(sample_idx, cft):
    # Corrected time: use zero of the line defined by two samples
    # left and right of picked value (if available, else use original value)
    x1 = max(sample_idx - 2, 0)
    x2 = min(sample_idx + 2, len(cft) - 1)
    y1 = cft[x1]
    y2 = cft[x2]

    # no adjustment, when line is horizontal
    if y1 == y2:
        return sample_idx
    return (x2 * y1 - x1 * y2) / (y1 - y2)
