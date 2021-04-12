# Event class of DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import copy
import json
import math
import os
import re
import sys

import numpy as np
import pyproj
import pandas as pd
import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from obspy import UTCDateTime, Stream
from obspy.core.event import WaveformStreamID, Pick, Origin, Arrival, Magnitude
from obspy.core.event.event import Event as ObsPyEvent
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

from dug_seis import util
from dug_seis.processing.Pickers.PhasePApy_Austin_Holland import fbpicker
from dug_seis.processing.Pickers.PhasePApy_Austin_Holland import aicdpicker
from dug_seis.processing.Pickers.PhasePApy_Austin_Holland import ktpicker
from dug_seis.processing.Pickers.P_Phase_Picker_USGS.pphasepicker import pphasepicker

# necessary for picker
sys.path.append("../")


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


# TODO  Development code, testing s-wave picker
# def indigo_log_single_picks(evt, picks, version='p-picks'):
#     # Append all pick station_ids and times to picks.csv
#     station_ids = [str(p['indigo-station']) for p in picks]
#     times = [p.time.isoformat() for p in picks]
#     tmp = []
#     for item in zip(station_ids, times):
#         tmp.append(f'{item[0]},{item[1]}')
#         # tmp.append(item[1])

#     txt = (';').join(tmp) + '\n'
#     filename = 'picks' if version == 'p-picks' else 'picks_s'
#     fh = open(f'./{filename}.csv', 'a')
#     fh.write(txt)
#     fh.close()


def sta_lta(
    event, stream, param, p_picks=[], gap=0, interval_length=0, version="p-picks"
):
    """Apply the STA LTA picker

    When the argument p_picks is set, it is a search for S-waves.
    In this case the time interval is set after the P-pick time
    according to the parameters "gap" and "length".
    """
    sampling_rate = stream[0].stats.sampling_rate

    if "bandpass_f_min" in param:
        stream.filter(
            "bandpass", freqmin=param["bandpass_f_min"], freqmax=param["bandpass_f_max"]
        )

    picks = []

    if len(p_picks):
        # TODO  Prüfen, ob das mit der neuen station_id/station_code noch stimmt
        trace_range = [p["indigo-station"] for p in p_picks]
    else:
        trace_range = range(len(stream))

    for idx, station_idx in enumerate(trace_range):
        if len(p_picks):
            # select trace
            trace = [tr for tr in stream.traces if tr.stats.station == station_idx][0]
            # setup time interval to be processed
            trace = trace.trim(
                p_picks[idx].time + gap,
                p_picks[idx].time + gap + interval_length,
            )
        else:
            trace = stream[station_idx]

        # create characteristic function
        cft = recursive_sta_lta(trace, param["st_window"], param["lt_window"])

        # do picking
        trig = trigger_onset(cft, param["threshold_on"], param["threshold_off"])

        if len(trig):
            # The picked value is the sample, where the STA/LTA value
            # is greater than the threshold.

            # If a pick is done on a trace, convert it to seconds
            # and add the start time of the snippet.

            # unadjusted version
            # t_pick_UTC = (event.wf_stream[0].stats['starttime']
            #     + trig[0][0] / sampling_rate)

            # t_pick_UTC = (event.wf_stream[0].stats['starttime']
            t_pick_UTC = (
                event.wf_stream[0].stats["starttime"]
                + adjust_pick_time(trig[0][0], cft) / sampling_rate
            )

            # station_id = station_idx +  1
            station_id = trace.stats.station
            picks.append(
                Pick(
                    time=t_pick_UTC,
                    resource_id="%s/picks/%d"
                    % (event.resource_id.id, len(event.picks) + 1),
                    waveform_id=WaveformStreamID(
                        network_code=trace.stats.network,
                        station_code=trace.stats.station,
                        location_code=trace.stats.location,
                        channel_code=trace.stats.channel,
                    ),
                    method_id="recursive_sta_lta",
                )
            )
            # picks[-1]['indigo-samples'] = trig[0][0]
            picks[-1]["indigo-station"] = station_id

    # TODO  Development code, testing s-wave picker
    #       Append all pick station_ids and times to picks.csv
    # indigo_log_single_picks(event, picks, version)

    return picks


def draw_vertical_line(ax, x, **kwargs):
    ax.plot(
        (x, x),
        (ax.get_ylim()[0], ax.get_ylim()[1]),
        linewidth=1.0,
        **kwargs,
    )


class PannableAxes(matplotlib.axes.Axes):
    """Confine dragging to x axis."""

    name = "PannableAxes"

    def drag_pan(self, button, key, x, y):
        matplotlib.axes.Axes.drag_pan(self, button, "x", x, y)  # pretend key=='x'


class Event(ObsPyEvent):
    """Main class for processing the waveform of the snippet.

    This class contains the bandpass, picker, localization,
    magnitude, and visualization to be applied the waveform snippet.
    """

    class Pseudo_pick:
        def __init__(self, time, station_code):
            self.time = time
            self.waveform_id = {"station_code": station_code}

    # Switch off warning when custom properties are set.
    warn_on_non_default_key = False

    def __init__(
        self,
        param,
        wf_stream,
        event_id,
        classification,
        logger,
        file_path=None,
    ):

        self.param = param
        self.wf_stream = wf_stream
        self.logger = logger
        self.param_proc = param["Processing"]
        self.param_pick = param["Picking"]

        super().__init__(
            resource_id="smi:%s/event/%d"
            % (re.sub(" ", "_", param["General"]["project_name"]), event_id)
        )

        if file_path is not None:
            self.read_json(file_path)
            return

        self.event_id = event_id
        self.classification = classification
        self.t0 = []
        self.dist = []
        self.tcalc = []
        self.loc_ind = []
        self.s_picks = []
        self.locations = {}
        self.extra = {}
        self.start_time = self.wf_stream.traces[0].stats["starttime"]
        self.trigger_time = self.start_time - param["Trigger"]["offset"]
        text = str(self.start_time)[11:-1] + ", processing started."
        if self.classification != "noise":
            self.logger.info("Event " + str(self.event_id) + ": Time " + text)
        else:
            self.logger.info("Noise Visualisation at " + text)

    def pick(self):
        """Apply a picker algorithm on all traces to pick first arrivals.

        Depending on the value of the parameter Processing.Picking.algorithm
        picks are appended to the instance parameter "pick".
        Possible values of "algorithm":
            "fb"            FB picker
            "kt"            Kurtosis picker
            "aicd"          AICD
            "sta_lta"       STA/LTA picker
            "pphase"        P Phase picker

        Args:
            none

        Returns:
            no value
        """
        algo_param = self.param_pick[self.param_pick["algorithm"]]
        sampling_rate = self.wf_stream[0].stats.sampling_rate
        self.picks = []

        # apply the fb picker.
        if self.param_pick["algorithm"] == "fb":
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
            picker = fbpicker.FBPicker(
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

            # do picking for each trace in snippet
            for j in range(len(self.wf_stream)):
                tr = self.wf_stream[j]
                # Perform a linear detrend on the data
                tr.detrend("linear")

                scnl, picks, polarity, snr, uncert = picker.picks(tr)

                if len(picks):
                    # if a pick is done on a trace, convert it to seconds
                    # t_picks=trig[0][0] / sampling_rate
                    # and add the start time of the snippet
                    # self.wf_stream[0].stats['starttime'] + t_picks
                    t_pick_UTC = picks[0]
                    station_id = j + 1
                    self.picks.append(
                        Pick(
                            time=t_pick_UTC,
                            resource_id="%s/picks/%d"
                            % (self.resource_id.id, len(self.picks) + 1),
                            waveform_id=WaveformStreamID(
                                network_code=tr.stats.network,
                                station_code=tr.stats.station,
                                channel_code=tr.stats.channel,
                                location_code=tr.stats.location,
                            ),
                            method_id="AICD",
                        )
                    )

        # apply the kt (kurtosis) picker.
        if self.param_pick["algorithm"] == "kt":
            t_win = 1 / 2000
            t_ma = 10 / 2000
            nsigma = 6 / 100
            t_up = 0.78 / 100
            nr_len = 2
            nr_coeff = 2
            pol_len = 10
            pol_coeff = 10
            uncert_coeff = 3
            chenPicker = ktpicker.KTPicker(
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

            # do picking for each trace in snippet
            for j in range(len(self.wf_stream)):
                tr = self.wf_stream[j]

                # Perform a linear detrend on the data
                tr.detrend("linear")
                scnl, picks, polarity, snr, uncert = chenPicker.picks(tr)

                if len(picks):
                    t_pick_UTC = picks[0]
                    station_id = j + 1
                    self.picks.append(
                        Pick(
                            time=t_pick_UTC,
                            resource_id="%s/picks/%d"
                            % (self.resource_id.id, len(self.picks) + 1),
                            waveform_id=WaveformStreamID(
                                network_code=tr.stats.network,
                                station_code=tr.stats.station,
                                location_code=tr.stats.location,
                                channel_code=tr.stats.channel,
                            ),
                            method_id="AICD",
                        )
                    )

        # apply the AICD picker.
        if self.param_pick["algorithm"] == "aicd":
            # t_ma         = 3 / 1000
            # nsigma       = 8
            # t_up         = 0.78 / 1000
            # nr_len       = 2
            # nr_coeff     = 2
            # pol_len      = 10
            # pol_coeff    = 10
            # uncert_coeff = 3
            self.wf_stream.filter(
                "bandpass",
                freqmin=algo_param["bandpass_f_min"],
                freqmax=algo_param["bandpass_f_max"],
            )
            chenPicker = aicdpicker.AICDPicker(
                t_ma=algo_param["t_ma"] / 1000,
                nsigma=algo_param["nsigma"],
                t_up=algo_param["t_up"] / 1000,
                nr_len=algo_param["nr_len"],
                nr_coeff=algo_param["nr_coeff"],
                pol_len=algo_param["pol_len"],
                pol_coeff=algo_param["pol_coeff"],
                uncert_coeff=algo_param["uncert_coeff"],
            )

            picksav = []

            # do picking for each trace in snippet
            for j in range(len(self.wf_stream)):
                tr = self.wf_stream[j]

                # Perform a linear detrend on the data
                tr.detrend("linear")

                scnl, picks, polarity, snr, uncert = chenPicker.picks(tr)

                if len(picks):
                    t_pick_UTC = picks[0]
                    station_id = j + 1
                    picksav.append(t_pick_UTC - self.wf_stream[0].stats["starttime"])
                    self.picks.append(
                        Pick(
                            time=t_pick_UTC,
                            resource_id="%s/picks/%d"
                            % (self.resource_id.id, len(self.picks) + 1),
                            waveform_id=WaveformStreamID(
                                network_code=tr.stats.network,
                                station_code=tr.stats.station,
                                location_code=tr.stats.location,
                                channel_code=tr.stats.channel,
                            ),
                            method_id="AICD",
                        )
                    )
            pickaverage = np.mean(picksav) * 1000

        # apply the STA LTA picker.
        if self.param_pick["algorithm"] == "sta_lta":
            # p picks
            stream = util.stream_copy(self.wf_stream)
            stream.trim(
                stream[0].stats["starttime"],
                stream[0].stats["starttime"] + self.param["Trigger"]["interval_length"],
            )
            p_picks = sta_lta(self, stream, algo_param["p_wave"])
            self.picks += p_picks

            # s picks
            stream = util.stream_copy(self.wf_stream)
            stream.trim(
                stream[0].stats["starttime"],
                stream[0].stats["starttime"] + self.param["Trigger"]["interval_length"],
            )
            if self.param_pick["s_picking"]:
                s_picks = sta_lta(
                    self,
                    self.wf_stream.copy(),
                    algo_param["s_wave"],
                    p_picks,
                    gap=algo_param["s_wave"]["gap"],
                    interval_length=algo_param["s_wave"]["length"],
                    version="s-picks",
                )
                self.s_picks += s_picks

        # apply the P Phase picker.
        if self.param_pick["algorithm"] == "pphase":
            Tn = 0.01
            xi = 0.6

            # do picking for each trace in snippet
            for j in range(len(self.wf_stream)):

                loc = pphasepicker(self.wf_stream[j], Tn, xi)
                if loc != "nopick":
                    t_picks = loc

                    # and add the start time of the snippet
                    t_pick_UTC = self.wf_stream[0].stats["starttime"] + t_picks
                    station_id = j + 1
                    # XXX: Need to fix the ids here!
                    raise NotImplementedError("Ids missing")
                    self.picks.append(
                        Pick(
                            time=t_pick_UTC,
                            resource_id="%s/picks/%d"
                            % (self.resource_id.id, len(self.picks) + 1),
                            waveform_id=WaveformStreamID(
                                network_code="GR",
                                station_code="%03i" % station_id,
                                channel_code="001",
                                location_code="00",
                            ),
                            method_id="recursive_sta_lta",
                        )
                    )

        self.logger.info(f"Event {self.event_id}: {len(self.picks)} picks.")

    def locate(self):
        """Apply a localization algorithm that makes use of the picks
        done by the picker module."""
        lparam = self.param["Loc_Mag"]["Locate"]
        if lparam["algorithm"] == "hom_aniso":
            aparam = lparam["hom_aniso"]

        # apply localization if there is a minimum number of picks
        # done for the event.
        if len(self.picks) < lparam["min_picks"]:
            return

        channel_idxs = []
        # time relative to startime of snippets, in milliseconds.
        t_relative = []
        for pick in self.picks:
            coords = self.param["General"]["sensor_coords"][
                int(pick.waveform_id["station_code"]) - 1, :
            ]
            # Filtering out stations where all coordinates are 0.
            # TODO  Is that necessary? And HERE?
            #       Is it meant only to filter out the first station?
            if np.max(np.abs(coords)) and np.all(np.isfinite(coords)):
                channel_idxs.append(int(pick.waveform_id["station_code"]) - 1)
                t_relative.append(
                    (pick.time - self.wf_stream.traces[0].stats["starttime"]) * 1000
                )
        npicks = len(t_relative)
        sensor_coords = self.param["General"]["sensor_coords"][channel_idxs, :]
        vp = self.param["General"]["vp"] * np.ones([npicks]) / 1000.0

        if lparam["algorithm"] == "hom_iso" or lparam["algorithm"] == "hom_aniso":
            loc = sensor_coords[t_relative.index(min(t_relative)), :] + 0.1
            t0 = min(t_relative)
            nit = 0
            jacobian = np.zeros([npicks, 4])
            dm = 1.0 * np.ones(4)

            while nit < 100 and np.linalg.norm(dm) > 0.00001:
                nit = nit + 1

                # calculate anisotropic velocities
                if lparam["algorithm"] == "hom_aniso":
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
                            * np.cos(aparam["inc"])
                            * np.cos(aparam["azi"])
                            + np.cos(inc)
                            * np.sin(azi)
                            * np.cos(aparam["inc"])
                            * np.sin(aparam["azi"])
                            + np.sin(inc) * np.sin(aparam["inc"])
                        )
                        vp[i] = (
                            aparam["vp_min"]
                            / 1000.0
                            * (
                                1.0
                                + aparam["delta"]
                                * np.sin(theta) ** 2
                                * np.cos(theta) ** 2
                                + aparam["epsilon"] * np.sin(theta) ** 4
                            )
                        )

                dist = [
                    np.linalg.norm(loc - sensor_coords[i, :]) for i in range(npicks)
                ]
                tcalc = [dist[i] / vp[i] + t0 for i in range(npicks)]

                res = [t_relative[i] - tcalc[i] for i in range(npicks)]
                rms = np.linalg.norm(res) / npicks
                for j in range(3):
                    for i in range(npicks):
                        jacobian[i, j] = -(sensor_coords[i, j] - loc[j]) / (
                            vp[i] * dist[i]
                        )
                jacobian[:, 3] = np.ones(npicks)

                dm = np.matmul(
                    np.matmul(
                        np.linalg.inv(
                            np.matmul(np.transpose(jacobian), jacobian)
                            + pow(lparam["damping"], 2) * np.eye(4)
                        ),
                        np.transpose(jacobian),
                    ),
                    res,
                )
                loc = loc + dm[0:3]
                t0 = t0 + dm[3]
        else:
            self.logger.warning(
                "Location algorithm not implemented." + "Location not estimated."
            )

        x = loc[0] + self.param["General"]["origin_ch1903_east"]
        y = loc[1] + self.param["General"]["origin_ch1903_north"]
        z = loc[2] + self.param["General"]["origin_elev"]
        t0 = self.wf_stream.traces[0].stats["starttime"] + t0 / 1000.0

        # CH1903 coordinates
        self.loc_CH1903 = {
            "matplotlib_date": t0.matplotlib_date,
            "x": x,
            "y": y,
            "z": z,
        }

        # convert coordinates to WGS84
        proj_ch1903 = pyproj.Proj(init="epsg:21781")
        proj_wgs84 = pyproj.Proj(init="epsg:4326")
        lon, lat = pyproj.transform(proj_ch1903, proj_wgs84, x, y)

        # create origin object and append to event
        o = Origin(
            time=t0,
            longitude=lon,
            latitude=lat,
            depth=z,
            resource_id="%s/origin/%d" % (self.resource_id.id, len(self.origins) + 1),
            depthType="elevation",
            methodID=lparam["algorithm"],
        )
        for i in self.picks:
            if self.param["General"]["sensor_coords"][
                int(i.waveform_id["station_code"]) - 1, 0
            ]:
                o.arrivals.append(
                    Arrival(
                        pick_id=i.resource_id,
                        time_residual=res[len(o.arrivals)] / 1000,
                        phase="p",
                        resource_id="%s/origin/%d/arrival/%d"
                        % (self.resource_id.id, len(self.origins) + 1, len(o.arrivals)),
                    )
                )
        o.time_errors = rms / 1000
        self.origins.append(o)
        self.preferredOriginID = o.resource_id
        self.extra = {
            "x": {
                "value": loc[0],
                "namespace": "http://sccer-soe.ch/local_coordinates/1.0",
            },
            "y": {
                "value": loc[1],
                "namespace": "http://sccer-soe.ch/local_coordinates/1.0",
            },
            "z": {
                "value": loc[2],
                "namespace": "http://sccer-soe.ch/local_coordinates/1.0",
            },
        }
        self.t0.append(t0)
        self.dist.append(dist)
        self.tcalc.append(tcalc)
        self.loc_ind.append(channel_idxs)
        self.locations = {
            str(channel_idxs[i] + 1).rjust(3, "0"): tcalc[i]
            for i in range(len(channel_idxs))
        }
        self.logger.info(
            "Event "
            + str(self.event_id)
            + ": Location %3.2f %3.2f %3.2f; %i iterations, rms %4.3f ms"
            % (loc[0], loc[1], loc[2], nit, rms)
        )

    def est_magnitude(self, origin_number=np.inf):
        """Apply a magnitude estimation that makes use of the picks to
        find the maximum amplitude of arrivals."""
        emparam = self.param["Loc_Mag"]["Magnitude"]
        if origin_number > len(self.origins):
            origin_number = len(self.origins)
        elif origin_number < 1:
            self.logger.warning("Origin number does not exist.")
        origin_number = origin_number - 1

        trig_ch = []
        for i in self.picks:
            if self.param["General"]["sensor_coords"][
                int(i.waveform_id["station_code"]) - 1, 0
            ]:
                trig_ch.append(int(i.waveform_id["station_code"]))
        ch_in = [int(i.stats["station"]) for i in self.wf_stream.traces]
        ind_trig = np.where(np.isin(ch_in, trig_ch))  # Finds correct axis

        if not len(self.origins):
            return

        self.ts_approx = []
        # t0 for use in magnitude estimation
        t0_orig = self.t0[origin_number] - self.wf_stream.traces[0].stats["starttime"]
        righthand = []
        for i in range(len(self.dist[origin_number])):

            # time of s wave arrival/end of the segment (time)
            self.ts_approx.append(
                (self.dist[origin_number][i] / self.param["General"]["vs"] + t0_orig)
                * 1000
            )
            righthand.append(
                (
                    self.dist[origin_number][i] / self.param["General"]["vs"]
                    - self.dist[origin_number][i] / self.param["General"]["vp"]
                )
                * 1000
            )
            # TODO  This code looks extremely dubious.
            # original version
            # if self.ts_approx[i] > (self.param['Trigger']['endtime']
            #         + self.param['Trigger']['endtime']) * 1000:
            #     self.ts_approx[i] = (self.param['Trigger']['endtime']
            #         + self.param['Trigger']['endtime']) * 1000
            # version with changend parameters
            self.ts_approx[i] = min(
                self.ts_approx[i],
                (
                    self.param["Trigger"]["interval_length"]
                    + self.param["Trigger"]["offset"]
                )
                * 2000,
            )
            self.ts_approx_dict[
                self.picks[i].waveform_id["station_code"]
            ] = self.ts_approx[i]

        relstartwindow = []

        # we create a time window with a begin and end time around the expected
        # maximum amplitude of the arrival of the event at each trace.
        # this time window is based on the pick from the localization module(ts_approx)
        for i in range(len(self.ts_approx)):

            # begin of the segment (in time)
            relstartwindow.append(self.ts_approx[i] - 2 * righthand[i])
            if relstartwindow[i] < 0:
                relstartwindow[i] = 0

        # beginning of segment (in samples)
        sample_start = [
            int(round(i / 1000 * self.wf_stream.traces[0].stats.sampling_rate))
            for i in relstartwindow
        ]
        # end of segment (in samples)
        sample_end = [
            int(round(i / 1000 * self.wf_stream.traces[0].stats.sampling_rate))
            for i in self.ts_approx
        ]

        maxamp = []

        for k in range(len(ind_trig[0])):

            # find maximum amplitude in segment which will
            # impact the magnitude estimation.
            maxamp.append(
                max(
                    abs(
                        self.wf_stream[ind_trig[0][k]].data[
                            sample_start[k] : sample_end[k]
                        ]
                    )
                )
            )

        corr_fac = []
        mag_exp = []
        for i in range(len(self.dist[origin_number])):

            corr_fac.append(
                np.exp(
                    np.pi
                    * (self.dist[origin_number][i] - emparam["r0"])
                    * emparam["f0"]
                    / (emparam["q"] * self.param["General"]["vp"])
                )
            )
            mag_exp.append(
                maxamp[i] * self.dist[origin_number][i] / emparam["r0"] * corr_fac[i]
            )
            # calculate relative magnitude for each receiver/event recording

        average_magnitude = np.log10(np.mean(mag_exp))

        self.logger.info(
            "Event "
            + str(self.event_id)
            + ": Relative magnitude %4.2f." % average_magnitude
        )
        if average_magnitude < np.inf:
            self.magnitudes.append(
                Magnitude(
                    mag=average_magnitude,
                    resource_id="%s/magnitude/%d"
                    % (self.resource_id.id, len(self.magnitudes) + 1),
                    origin_id=self.origins[origin_number].resource_id,
                    type="relative_amplitude",
                )
            )
            self.preferredMagnitudeID = self.magnitudes[-1].resource_id

    def event_plot(
        self,
        communication,
        title="",
        freqmin=None,
        freqmax=None,
        png_path=None,
        spectro_show=False,
        spectro_logx=False,
        spectro_start_pick=False,
    ):
        """Generates a visualization of all traces of the waveform snippet
        and the picks done by the picker module as well as the picks
        resulting from visualization."""

        if communication["single_event"]["display_pick_channels"]:
            display_stations_ids = [p.waveform_id["station_code"] for p in self.picks]
        else:
            display_stations_ids = [
                str(i + 1).rjust(3, "0")
                for i in communication["single_event"]["display_channels"]
            ]

        plot_stream = Stream()
        for trace in self.wf_stream.traces:
            if trace.stats.station in display_stations_ids:
                plot_stream.traces.append(trace)

        if freqmin is not None and freqmax is not None:
            plot_stream.filter("bandpass", freqmin=freqmin, freqmax=freqmax)
        elif freqmin is None and freqmax is not None:
            plot_stream.filter("lowpass", freq=freqmax)
        elif freqmin is not None and freqmax is None:
            plot_stream.filter("highpass", freq=freqmin)

        sampRate = plot_stream.traces[0].stats.sampling_rate
        time_values = (
            np.arange(0, plot_stream[0].data.shape[0], 1) * 1 / sampRate * 1000
        )
        a_max = []
        for k in range(len(plot_stream)):
            a_max.append(format(np.amax(np.absolute(plot_stream[k].data)), ".1f"))

        fig = communication["fig"]
        fig.clear()

        # Keys of axs are the station ID strings like "009".
        axs = {}
        matplotlib.projections.register_projection(PannableAxes)

        for i in range(len(plot_stream)):
            station = plot_stream.traces[i].stats["station"]
            if i == 0:
                ax = fig.add_subplot(len(plot_stream), 1, i + 1)
                ax0 = ax
            else:
                # sharex is needed for synchronous zooming with mouse wheel
                ax = fig.add_subplot(
                    len(plot_stream), 1, i + 1, sharex=ax0, projection="PannableAxes"
                )

            axs[station] = ax
            # ----------  data  ----------------------------
            # pick time
            picks_of_station = [
                p for p in self.picks if p.waveform_id["station_code"] == station
            ]
            if len(picks_of_station):
                pick_time = (
                    picks_of_station[0].time - plot_stream.traces[0].stats["starttime"]
                ) * 1000

            if spectro_show:
                if len(picks_of_station) and spectro_start_pick:
                    # select samples starting with pick time
                    start_sample = math.ceil(pick_time * sampRate / 1000)
                    sample_selection = plot_stream[i].data[
                        start_sample : (start_sample + 2048)
                    ]
                else:
                    sample_selection = plot_stream[i].data[:2048]

                ax.magnitude_spectrum(
                    sample_selection, Fs=float(sampRate), scale="dB", color="C1"
                )
                ax.set_xlim([1, sampRate / 2])
                if spectro_logx:
                    ax.set_xscale("log")

            else:
                ax.plot(time_values, plot_stream[i].data)
                # mark special x values
                if len(picks_of_station):
                    draw_vertical_line(ax, pick_time, color="r", linestyle="-")

                s_picks_of_station = [
                    p for p in self.s_picks if p.waveform_id["station_code"] == station
                ]
                if len(s_picks_of_station):
                    pick_time = (
                        s_picks_of_station[0].time
                        - plot_stream.traces[0].stats["starttime"]
                    ) * 1000
                    draw_vertical_line(ax, pick_time, color="#00cfd9", linestyle="-.")

                if station in self.locations.keys():
                    draw_vertical_line(
                        ax, self.locations[station], color="g", linestyle="--"
                    )
                if len(self.magnitudes):
                    draw_vertical_line(
                        ax, self.ts_approx_dict[station], color="y", linestyle="--"
                    )
                ax.set_xlim([0, (len(time_values) / sampRate) * 1000])

            # ----------  axes, ticks, grid  ---------------
            ax.xaxis.grid(True)
            ax.set_yticklabels([])

            asterisk = " "
            if spectro_show and spectro_start_pick and not len(picks_of_station):
                asterisk = "*"

            ax.set_ylabel(
                plot_stream.traces[i].stats["station"] + asterisk + " ", rotation=0
            )
            ax.spines["top"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.axhline(y=0, color="k")

            ax2 = ax.twinx()
            ax2.set_yticklabels([])
            ax2.set_ylabel(
                str(a_max[i]),
                rotation=None,
                labelpad=0,
                color="g",
                horizontalalignment="left",
            )
            ax2.spines["top"].set_visible(False)
            ax2.spines["bottom"].set_visible(False)

            #  Hide x ticklabel in all axes but the last.
            if i < len(plot_stream) - 1:
                ax.tick_params(labelbottom=False)

        # ----------  captions  ----------------------------
        fig.suptitle(title, fontsize=15)
        if not spectro_show:
            fig.text(0.5, 0.015, "time [ms]", ha="center", fontsize=12)
            fig.text(
                0.98,
                0.5,
                "peak amplitude [mV]",
                va="center",
                rotation=90,
                fontsize=12,
                color="g",
            )
        else:
            # fig.text(0.5, 0.015, 'Freqency [Hz]', ha='center', fontsize=12)
            fig.text(
                0.98, 0.5, "[mV/Hz]", va="center", rotation=90, fontsize=12, color="g"
            )
        fig.subplots_adjust(
            hspace=0, wspace=0, left=0.05, right=0.93, top=0.95, bottom=0.05
        )

        communication["app"].axs = axs
        communication["app"].axs_lims = {
            key: {
                "x": axs[key].get_xlim(),
                "y": axs[key].get_ylim(),
            }
            for key in axs.keys()
        }
        communication["app"].canvas.draw()
        communication["app"].canvas.repaint()

        if png_path:
            fig.savefig(png_path, dpi=100)

    def write_json(self, dir="./json"):
        """
        Write JSON file with all data necessary for a plot except the stream.
        """

        # IMPORTANT NOTICE
        # Dict attributes of this class are actually AttributeDicts. To be
        # written in the JSON file they have to be converted to python dicts.

        # necessary for plot
        obj = {}
        obj["classification"] = self.classification
        obj["event_id"] = self.event_id
        obj["sensor_count"] = self.param["General"]["sensor_count"]
        obj["picks"] = [
            {
                "time": str(p.time),
                "wfid_stcode": p.waveform_id["station_code"],
            }
            for p in self.picks
        ]

        obj["s_picks"] = [
            {
                "time": str(p.time),
                "wfid_stcode": p.waveform_id["station_code"],
            }
            for p in self.s_picks
        ]

        obj["tcalc"] = [[float(repr(fl64)) for fl64 in li] for li in self.tcalc]

        obj["origins"] = [0 for i in range(0, len(self.origins))]
        obj["loc_ind"] = copy.deepcopy(self.loc_ind)
        obj["locations"] = {k: v for k, v in self.locations.items()}

        # not used yet
        # obj['magnitudes'] = self.magnitudes
        # obj['ts_approx'] = self.ts_approx

        obj["trigger_time"] = str(self.trigger_time)
        obj["start_time"] = str(self.start_time)

        # not necessary for plot
        if len(self.t0):
            obj["t0"] = str(self.t0[-1])
            obj["extra"] = copy.deepcopy(self.extra)
            obj["loc_CH1903"] = {k: v for k, v in self.loc_CH1903.items()}

        try:
            filename = util.utc_format(self.start_time, "filename") + ".json"
            with open(os.path.join(dir, filename), "w") as write_file:
                json.dump(obj, write_file)
        except Exception as e:
            return "Error: " + str(e)

    def read_json(self, path):
        with open(path, "r") as read_file:
            data = json.load(read_file)

        self.classification = data["classification"]
        self.event_id = data["event_id"]

        self.picks = [
            Event.Pseudo_pick(UTCDateTime(p["time"]), p["wfid_stcode"])
            for p in data["picks"]
        ]

        self.s_picks = []
        try:
            self.s_picks = [
                Event.Pseudo_pick(UTCDateTime(p["time"]), p["wfid_stcode"])
                for p in data["s_picks"]
            ]
        except:
            pass

        self.tcalc = [[np.float64(fl64) for fl64 in li] for li in data["tcalc"]]

        self.origins = data["origins"]
        self.loc_ind = data["loc_ind"]
        self.locations = data["locations"]

        # not used yet
        # TODO  implement!
        # self.magnitudes = data['magnitudes']
        # self.ts_approx = data['ts_approx']

        self.trigger_time = UTCDateTime(data["trigger_time"])
        self.start_time = UTCDateTime(data["start_time"])

        # not necessary for plot
        if "t0" in data:
            self.t0 = data["t0"]
            self.extra = data["extra"]
        else:
            self.t0 = None
            self.extra = {}

    def save_csv(self, filename="events.csv"):
        """Write CSV file with CH1903 coordinates."""
        cols = pd.Index(
            [
                "Event_id",
                "Trigger_time",
                "Date&Time",
                "x",
                "y",
                "z",
                "Mag",
                "loc_rms",
                "npicks",
            ],
            name="cols",
        )
        if len(self.t0):
            t0 = self.t0[-1]
            x = self.extra["x"]["value"]
            y = self.extra["y"]["value"]
            z = self.extra["z"]["value"]
            rms = self.origins[-1].time_errors["uncertainty"]
        else:
            t0 = "                 "
            x, y, z, rms = 0, 0, 0, 0
        if len(self.magnitudes):
            Mag = self.magnitudes[-1]["mag"]
        else:
            Mag = -99
        npicks = len(self.picks)
        outdata = (
            [self.event_id]
            + [self.trigger_time]
            + [t0]
            + [np.round(x, 3)]
            + [np.round(y, 3)]
            + [np.round(z, 3)]
            + [np.round(Mag, 2)]
            + [np.round(rms, 5)]
            + [npicks]
        )

        df = pd.DataFrame(data=[outdata], columns=cols)
        df.to_csv(filename, mode="a", header=False, index=False)
        self.logger.info(f"Event {self.event_id}: Info saved to {filename}.")
