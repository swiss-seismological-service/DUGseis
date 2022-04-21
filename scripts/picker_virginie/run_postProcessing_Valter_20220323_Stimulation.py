
import copy
import logging
import pathlib
import re
import time

import obspy
import obspy.realtime

import tqdm
import yaml

# Import from the DUGSeis library.
from dug_seis.project.project import DUGSeisProject
from dug_seis.waveform_handler.waveform_handler import FILENAME_REGEX
from dug_seis import util

from aurem.aurem import REC

import numpy as np

from dug_seis.event_processing.detection.dug_trigger import dug_trigger
from dug_seis.event_processing.picking.dug_picker import dug_picker
from dug_seis.event_processing.location.locate_homogeneous import (
    locate_in_homogeneous_background_medium,
)

from dug_seis.event_processing.magnitudes.amplitude_based_magnitudes import amplitude_based_relative_magnitude
from obspy.core.event import Magnitude

import copy
import math
from matplotlib import mlab
from matplotlib.collections import LineCollection
import matplotlib.transforms as transforms
from scipy.stats import kurtosis
from scipy import signal
from obspy.signal.filter import bandpass
from obspy.signal.invsim import cosine_taper
from obspy.core.event import WaveformStreamID, Pick







###############################################

def nans(shape, dtype=float):  # shape : [lignes,colonnes]
    "creer une matrice de NaN"
    a = np.empty(shape, dtype)
    a.fill(np.nan)
    return a


def inc_zeros(small_v, n, i):
    if len(small_v) > n:
        big_v = small_v
    else:
        b = len(small_v)
        if i < 1:
            big_v = np.concatenate((small_v, np.zeros(n - (b + i))), axis=0)
        else:
            big_v = np.concatenate((np.zeros(i - 1), small_v, np.zeros(n - (b + i) + 1)), axis=0)
    return big_v


def KurtoF(data, window_sample, n_bands):
    kt = []
    Nwin = window_sample
    if window_sample == 1:  # Function doesn't work with window sample<2
        print("window sample=1 doesn't work. Put to 2")
        window_sample = 2.0
    # start0 = time.time()
    for j in range(n_bands):
        # start1 = time.time()
        # changelength of trace
        v = data[j]
        idx = np.array(np.nonzero(np.isnan(v) == 0))
        a = idx[0, 0]  # first element != NaN
        b = idx[0, -1]  # last element != NaN
        inp = v[a:b + 1]
        # Compute Kurtosis
        average = signal.lfilter(np.ones([Nwin]) / Nwin, 1, inp)
        # end1 = time.time()
        # print(f"Runtime of average {end1 - start1}")
        # start1 = time.time()
        m_2 = signal.lfilter(np.ones([Nwin]) / Nwin, 1, ((inp - average) ** 2))
        m_4 = signal.lfilter(np.ones([Nwin]) / Nwin, 1, ((inp - average) ** 4))
        # end1 = time.time()
        # print(f"Runtime of m2, m4 {end1 - start1}")
        # start1 = time.time()
        out = m_4 / (m_2 ** 2)
        # end1 = time.time()
        # print(f"Runtime of kurtosis {end1 - start1}")
        # start1=time.time()
        out = inc_zeros(out[Nwin - 1:], len(inp), Nwin + (a + 1) - 1)
        kt.append(out)
    #     end1 = time.time()
    #     print(f"Runtime of out {end1 - start1}")
    # end0 = time.time()
    # print(f"Runtime of all freqbands {end0 - start0}")

    return kt


def Kurto(tr, t_win, delta, npts, sampling_rate):
    data = tr.data
    t = np.arange(0, delta * npts, delta)
    m = len(data)
    Nsta = int(t_win * sampling_rate)

    # create zeros 2D array for BF
    kt = np.zeros(m, dtype="float64")
    pad_kt = np.zeros(Nsta)
    # Tricky: Construct a big window of length len(a)-nsta. Now move this
    # window nsta points, i.e. the window "sees" every point in a at least
    # once.
    # Changed xrange to range as it is compatible in both python 2 & 3
    for i in range(m):  # window size to smooth over
        kt[i] = abs(kurtosis(data[i - Nsta: i]))

        kt[0:Nsta] = 0

    return kt


def N_bands(tr, freqmin):
    """
    Determine number of band n_bands in term of sampling rate.
    freqmin     : the center frequency of first octave filtering band"""
    df = tr.stats.sampling_rate
    Nyquist = df / 2.0
    n_bands = int(np.log2(Nyquist / 1.5 / freqmin)) + 1
    return n_bands


def filter(tr, freqmin, cnr, perc_taper):
    """Filter data for each band."""
    n_bands = N_bands(tr, freqmin)
    LEN = tr.stats.npts
    df = tr.stats.sampling_rate

    # create zeros 2D array for BF
    BF = np.zeros(shape=(n_bands, LEN))
    fcenter = np.zeros(n_bands)

    for j in range(n_bands):
        octave_high = (freqmin + freqmin * 2.0) / 2.0 * (2 ** j)
        octave_low = octave_high / 2.0
        fcenter[j] = (octave_low + octave_high) / 2.0
        BF[j] = bandpass(
            tr.data,
            octave_low,
            octave_high,
            df,
            corners=cnr,
            zerophase=False,
        )
        BF[j] = cosine_taper(LEN, perc_taper) * BF[j]

    return BF, fcenter


def KurtoFreq(tr, freqmin, t_long, cnr, perc_taper):
    """Calculate statistics for each band."""
    n_bands = N_bands(tr, freqmin)
    LEN = tr.stats.npts
    delta = 1.0 / tr.stats.sampling_rate
    sampling_rate = tr.stats.sampling_rate
    dt = tr.stats.delta
    npts_t_long = int(t_long / dt) + 1

    # BF: band filtered data
    BF, fcenter = filter(tr, freqmin, cnr, perc_taper)

    # FC = KurtoF(BF, t_long, delta, LEN, sampling_rate, n_bands)
    # start = time.time()
    FC = KurtoF(BF, npts_t_long, n_bands)
    # end = time.time()
    # print(f"Runtime of Kurto {end - start}")

    return FC, BF, n_bands, fcenter


def rms(x, axis=None):
    """Function to calculate the root mean square value of an array."""
    return np.sqrt(np.mean(x ** 2, axis=axis))


def rolling_window(a, window):
    """Efficient rolling statistics with NumPy: This is applied to Picker._statistics() to calculate statistics
    and Summary.threshold() to calcuate threshold to trigger event
    Reference from:
    http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
    """
    # start=time.time()
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    # end=time.time()
    # print(f"Runtime of rollingWindow {end - start}")

    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

def threshold(tr, HOS, t_ma, nsigma):
    """
    Control the threshold level with nsigma.
    """
    dt = tr.stats.delta
    npts_Tma = int(round(t_ma / dt, 0))
    LEN = tr.stats.npts
    # print "npts_Tma: ",npts_Tma
    threshold = np.zeros(LEN)
    # threshold[0:npts_Tma] = 1
    # threshold[npts_Tma:LEN] = (
    #     rms(rolling_window(HOS[0 : LEN - 1], npts_Tma), -1)
    #     * nsigma
    # )
    threshold[npts_Tma:LEN] = (
            np.mean(rolling_window(HOS[0: LEN - 1], npts_Tma), -1)
            * nsigma
    )

    return threshold

###################################################

# The logging is optional, but useful.
util.setup_logging_to_file(
    # folder=".",
    # If folder is not specified it will not log to a file but only to stdout.
    folder=None,
    log_level="info",
)
logger = logging.getLogger(__name__)

NUMBER_OF_RECORDING_SYSTEMS = 3

# The logging is optional, but useful.
util.setup_logging_to_file(
    # folder=".",
    # If folder is not specified it will not log to a file but only to stdout.
    folder=None,
    log_level="info",
)
logger = logging.getLogger(__name__)

# Load the DUGSeis project.
project5P = DUGSeisProject(config="./post_processing_VALTERInt13_20220323_Stimulation.yaml")
project3P = DUGSeisProject(config="./post_processing_VALTERInt13_20220323_Stimulation_3Picks.yaml")


active_channels = ["XB.02.31.001", "XB.03.31.001", "XB.04.31.001"]
channels_toRm = ["XB.02.02.001", "XB.02.04.001", "XB.02.05.001", "XB.02.06.001",
                     "XB.02.11.001", "XB.02.13.001", "XB.02.14.001", "XB.02.15.001", "XB.02.16.001", "XB.02.17.001",
                     "XB.02.18.001", "XB.02.21.001", "XB.02.24.001", "XB.02.25.001", "XB.02.26.001", "XB.02.27.001", "XB.02.30.001",
                     "XB.04.01.001", "XB.04.03.001", "XB.04.04.001", "XB.04.05.001", "XB.04.12.001",
                     "XB.04.13.001", "XB.04.14.001", "XB.04.15.001",
                     "XB.04.20.001", "XB.04.21.001", "XB.04.22.001", "XB.04.23.001",
                     "XB.03.05.001", "XB.03.07.001"]#,
                     # "XB.02.31.001", "XB.03.31.001", "XB.04.31.001"]  # Remove accelerometers and channels with spikes
Tmp_all_channels = sorted(project5P.channels.keys())
all_channels = [x for x in Tmp_all_channels if x not in channels_toRm]

# all_channels = ["XB.02.24.001",
#                 "XB.04.09.001", "XB.04.10.001", "XB.04.11.001", "XB.04.17.001", "XB.04.23.001",
#                 "XB.04.25.001", "XB.04.27.001", "XB.04.28.001",
#                 "XB.03.03.001", "XB.03.04.001", "XB.03.09.001", "XB.03.10.001",
#                 "XB.03.17.001", "XB.03.18.001",
#                 "XB.03.19.001", "XB.03.20.001", "XB.03.21.001"
#                 ]
# Helper function to compute intervals over the project.
intervals = util.compute_intervals(
    project=project5P, interval_length_in_seconds=5, interval_overlap_in_seconds=0.1
)

max_spread_electronic = 2e-5
minimum_time_between_events_in_seconds = 0.0006
total_event_count = 0
picks1 = []

startT_all = time.time()
for interval_start, interval_end in tqdm.tqdm(intervals):
    startT_Det = time.time()
    # Run the trigger only on a few waveforms.
    st_triggering = project5P.waveforms.get_waveforms(
        channel_ids=[
            "XB.03.04.001",
            "XB.03.19.001",
            "XB.03.20.001",
            "XB.04.10.001",
            "XB.04.25.001",
            "XB.02.31.001"
        ],
        start_time=interval_start,
        end_time=interval_end,
    )

    # startT = time.time()
    # Standard DUGSeis trigger.
    detected_events = dug_trigger(
        st=st_triggering,
        # Helps with classification.
        active_triggering_channel="XB.02.31.001",
        minimum_time_between_events_in_seconds=0.0006,
        max_spread_electronic_interference_in_seconds=max_spread_electronic,
        # Passed on the coincidence trigger.
        conincidence_trigger_opts={
            "trigger_type": "recstalta",
            "thr_on": 8.0,
            "thr_off": 2.0,
            "thr_coincidence_sum": 2,
            # The time windows are given in seconds.
            "sta": 1.0 / 200000.0 * 50,
            "lta": 1.0 / 200000.0 * 700,
            "trigger_off_extension": 0.01,
            "details": True,
        },
    )

    logger.info(
        f"Found {len(detected_events)} event candidates in interval "
        f"{interval_start}-{interval_end}."
    )
    # endT = time.time()
    # logger.info(f"Detection Took {(endT - startT_Det) / 60.} minutes.")

    if not detected_events:
        continue

    # Now loop over the detected events.
    added_event_count = 0

    # startT_interval = time.time()
    for event_candidate in detected_events:
        if event_candidate['classification'] != 'electronic' and event_candidate['classification'] != 'active':
            interval_start = event_candidate["time"] - 15e-3
            interval_end = event_candidate["time"] + 20e-3
            dt = interval_end - interval_start
            t_win = 0.005
            freqmin = 2250
            cnr = 2
            perc_taper = 0.1
            nsigma = 3.4  # 4.5
            nsigmaderiv = 25  # 32.0
            t_ma = 0.008
            t_Tr = 0.01
            ncum0 = 1000
            ncum1 = 1000
            # Get the waveforms for the event processing. Note that this could
            # use the same channels as for the initial trigger or different ones.
            # This step is to remove all transmitter shots
            # startT = time.time()

            st_classif = project5P.waveforms.get_waveforms(
                # All but the first because that is the active triggering channel
                # here.
                channel_ids=active_channels,
                start_time=interval_start,
                end_time=interval_end
            )

            tr_active = 0
            for tr in st_classif:
                fTimePick = 0
                delta = 1.0 / tr.stats.sampling_rate
                npts = tr.stats.npts
                sampling_rate = tr.stats.sampling_rate

                # Characteristic function
                HOS, filtSig, n_bands, frequencies = KurtoFreq(tr, freqmin, t_win, cnr, perc_taper)
                HOS_max = np.amax(HOS, axis=0)

                dt = tr.stats.delta
                npts_Tma = int(round(t_ma / dt, 0) + 50)
                LEN = tr.stats.npts

                threshold_HOS_max = threshold(tr, HOS_max, t_ma, nsigma)

                cHOS = np.cumsum(HOS_max)
                cHOS_detrend = signal.detrend(cHOS)

                # trigger the earthquakes
                nptsTr = int(round(t_Tr / dt, 0))
                trigger_ptnl_index = np.where(
                    (HOS_max[nptsTr:LEN] > threshold_HOS_max[nptsTr:LEN])
                    & (cHOS_detrend[nptsTr:LEN] < 0))
                trigger_ptnl_index = trigger_ptnl_index + np.array(nptsTr)

                time_array = np.arange(tr.stats.npts) / tr.stats.sampling_rate
                if len(trigger_ptnl_index[0]) > 0:
                    if trigger_ptnl_index[0][0] > ncum0:
                        time_array_Pick = time_array[
                                          trigger_ptnl_index[0][0] - ncum0:trigger_ptnl_index[0][0] + ncum1]
                        HOSPick = HOS_max[trigger_ptnl_index[0][0] - ncum0:trigger_ptnl_index[0][
                                                                               0] + ncum1]  # portion of HOS to compute pick
                        cte = trigger_ptnl_index[0][0] - ncum0
                    else:
                        time_array_Pick = time_array[trigger_ptnl_index[0][0]:trigger_ptnl_index[0][0] + ncum1]
                        HOSPick = HOS_max[trigger_ptnl_index[0][0]:trigger_ptnl_index[0][
                                                                       0] + ncum1]  # portion of HOS to compute pick
                        cte = trigger_ptnl_index[0][0]

                    cHOSPick = np.cumsum(HOSPick)
                    cHOSPick_detrend = signal.detrend(cHOSPick)
                    fPick = np.argmin(cHOSPick_detrend) + trigger_ptnl_index[0][0] - ncum0
                    fTimePick = time_array[fPick]
                    if fTimePick != 0:
                        fTimeTransm = fTimePick
                        if fTimePick<event_candidate["time"]:
                            event_candidate['classification'] = "active"
                            break  # if picks are made after the transmitter signal, they are active shots

            if event_candidate['classification'] == "active":
                continue
            # if tr_active == 3:
            #     event_candidate['classification'] = "active"
            #     continue

            # Get the waveforms for the event processing. Note that this could
            # use the same channels as for the initial trigger or different ones.
            st_event = project5P.waveforms.get_waveforms(
                # All but the first because that is the active triggering channel
                # here.
                channel_ids=all_channels,
                start_time=interval_start,
                end_time=interval_end
            )

            picks2 = picks1
            picks1 = []
            # startT = time.time()
            for tr in st_event:
                time1 = []
                time2 = []
                time3 = []
                time_tot = []
                fTimePick = 0
                SNR = 0

                data = tr.data

                sensorXML = project5P.inventory.select('XB', tr.id[3:5], tr.id[6:8])

                delta = 1.0 / tr.stats.sampling_rate
                npts = tr.stats.npts
                sampling_rate = tr.stats.sampling_rate

                # Characteristic function
                HOS, filtSig, n_bands, frequencies = KurtoFreq(tr, freqmin, t_win, cnr, perc_taper)

                # Summary characteristic function
                HOS_max = np.amax(HOS, axis=0)

                dt = tr.stats.delta
                npts_Tma = int(round(t_ma / dt, 0) + 50)
                LEN = tr.stats.npts
                threshold_HOS_max = threshold(tr, HOS_max, t_ma, nsigma)
                # threshold_HOS_RMS = threshold(tr, HOS_RMS, t_ma, nsigma)
                # threshold_derivativeHOS_max = threshold(tr, derivative_HOS_max, t_ma, nsigmaderiv)
                # threshold_derivativeHOS_RMS = threshold(tr, derivative_HOS_RMS, t_ma, nsigmaderiv)
                # end = time.time()
                # print(f"Runtime of HOS threshold {end - start}")

                cHOS = np.cumsum(HOS_max)
                cHOS_detrend = signal.detrend(cHOS)

                # trigger the earthquakes
                t_Tr = 0.01
                nptsTr = int(round(t_Tr / dt, 0))
                trigger_ptnl_index = np.where(
                    (HOS_max[nptsTr:LEN] > threshold_HOS_max[nptsTr:LEN])
                    & (cHOS_detrend[nptsTr:LEN] < 0))
                trigger_ptnl_index = trigger_ptnl_index + np.array(nptsTr)

                time_array = np.arange(tr.stats.npts) / tr.stats.sampling_rate

                if len(trigger_ptnl_index[0]) > 0:
                    time1.append(time_array[trigger_ptnl_index[0]])
                    if trigger_ptnl_index[0][0] > ncum0:
                        time_array_Pick = time_array[
                                          trigger_ptnl_index[0][0] - ncum0:trigger_ptnl_index[0][0] + ncum1]
                        HOSPick = HOS_max[trigger_ptnl_index[0][0] - ncum0:trigger_ptnl_index[0][
                                                                               0] + ncum1]  # portion of HOS to compute pick
                        cte = trigger_ptnl_index[0][0] - ncum0
                    else:
                        time_array_Pick = time_array[trigger_ptnl_index[0][0]:trigger_ptnl_index[0][0] + ncum1]
                        HOSPick = HOS_max[trigger_ptnl_index[0][0]:trigger_ptnl_index[0][
                                                                       0] + ncum1]  # portion of HOS to compute pick
                        cte = trigger_ptnl_index[0][0]

                    cHOSPick = np.cumsum(HOSPick)
                    cHOSPick_detrend = signal.detrend(cHOSPick)
                    fPick = np.argmin(cHOSPick_detrend) + trigger_ptnl_index[0][0] - ncum0
                    fTimePick = time_array[fPick]

                if fTimePick != 0:
                    Noise0 = tr.stats.starttime + fTimePick - 0.01
                    Noise1 = tr.stats.starttime + fTimePick - 0.0005
                    Signal0 = tr.stats.starttime + fTimePick - 0.0004
                    Signal1 = tr.stats.starttime + fTimePick + 0.01
                    trNoise = tr.slice(starttime=Noise0, endtime=Noise1)
                    trSignal = tr.slice(starttime=Signal0, endtime=Signal1)

                    SNR = np.mean(abs(trSignal.data)) / np.mean(abs(trNoise.data))

                    if SNR >= 1.3:
                        t_pick_UTC = (
                                tr.stats.starttime
                                + fTimePick
                        )
                        picks1.append(
                            Pick(
                                time=t_pick_UTC,
                                waveform_id=WaveformStreamID(
                                    network_code=tr.stats.network,
                                    station_code=tr.stats.station,
                                    location_code=tr.stats.location,
                                    channel_code=tr.stats.channel,
                                ),
                                method_id="FBKT",
                                phase_hint="P",
                                evaluation_mode="automatic",
                            )
                        )
            # endT = time.time()
            # logger.info(f"Pick Took {(endT - startT) / 60.} minutes to pick 1 event.")

            # Optionally remove the instrument response if necessary.
            # Requires StationXML files where this is possible.
            # st_event.remove_response(inventory=project.inventory, output="VEL")

            if len(picks1) == 0:
                continue

            ### To check that it is a new event
            ### if average time difference between picks of new event and picks of
            ### previous event less than minimum_time_between_events_in_seconds,
            ### not a new event, continue
            # startT = time.time()
            dt_events = [y.time - x.time for (x, y) in zip(picks2, picks1)]
            if np.sum(dt_events) / len(dt_events) <= minimum_time_between_events_in_seconds:
                continue
            # endT = time.time()
            # logger.info(f"Took {(endT - startT) / 60.} minutes to remove double event.")

            picks = picks1

            # # startT = time.time()
            # # Remove duplicated picks (mainly when electronic noise)
            # picksTimestamp = np.asarray([x.time.timestamp for x in picks1])
            # TimeRound = picksTimestamp // 0.001 * 0.001  # to round on the 3rd decimal, always down
            # idxDupli0 = np.arange(len(TimeRound))
            # idxDupli1 = []
            # for tt in TimeRound:
            #     idx = [i for i, x in enumerate(TimeRound) if x == tt]  # indexes of duplicates
            #     if len(idx) > 2:
            #         idxDupli1.append(idx)
            #     if len(idxDupli1) > 0:  # if duplicates
            #         idxDupli2 = []
            #         [idxDupli2.append(x) for x in idxDupli1 if
            #          x not in idxDupli2]  # check if duplicates in the indexes of duplicates
            #         if len(idxDupli2) > 1:
            #             idxDupli3 = []
            #             for idxD in idxDupli2:  # if there is at least 1 good pick
            #                 idxDupli3 += idxD
            #         else:
            #             idxDupli3 = idxDupli2
            #         idxDupli4 = np.delete(idxDupli0, idxDupli3)
            #     else:
            #         idxDupli4 = idxDupli0
            #
            # if len(idxDupli4) > 0:
            #     ### To remove very close picks that were not removed by previous step
            #     picksTimestamp0 = np.asarray([picksTimestamp[x] for x in range(len(picksTimestamp)) if
            #                                   x in idxDupli4])
            #     picksTimestamp1 = np.sort(picksTimestamp0)
            #     last_num = picksTimestamp1[0]
            #     xDupli = [last_num]
            #
            #     for x in picksTimestamp1[1:]:
            #         if x - last_num >= 3e-4:
            #             xDupli.append(x)
            #             last_num = x
            #     idxDupli = [i for i, x in enumerate(picksTimestamp) if x in xDupli]
            #
            #     if len(idxDupli) > 0 and (max(picksTimestamp0) - min(picksTimestamp0)) > max_spread_electronic:
            #         picks = [picks1[x] for x in range(len(picks1)) if
            #                  x in idxDupli]  # only picks that are not occurring at the same time
            #         picksID = [
            #             x.waveform_id["network_code"] + '.' + x.waveform_id["station_code"] + '.' +
            #             x.waveform_id[
            #                 "location_code"] for x in picks]
            #
            #
            #     else:
            #         continue
            # else:
            #     continue

            # endT = time.time()
            # logger.info(f"Took {(endT - startT) / 60.} minutes to remove duplicate picks.")
            # logger.info(f"Pick Took {(endT - startT) / 60.} minutes.")

            # We want at least three picks, otherwise we don't designate it an event.
            if len(picks) < 3:
                # Optionally save the picks to the database as unassociated picks.
                if picks:
                    [project3P.db.add_object(P) for P in picks]
                continue

            # # refine recSTA/LTA picks here  (Linus function, needs to be on linus_dev branch in DUGSeis to use it)
            # st_event_copy = st_event.copy()
            # win_pre = 0.0025
            # win_post = 0.0025
            # for index, pick in enumerate(picks):
            #     trace_1 = st_event_copy.select(id=pick.waveform_id.id)[0]
            #     if pick.time - win_pre < trace_1.stats.starttime:
            #         continue
            #     trace_1 = trace_1.trim(starttime=pick.time - win_pre, endtime=pick.time + win_post)
            #
            #     recobj = REC(trace_1)
            #     recobj.work()
            #     idx_REC = recobj.get_pick_index()
            #     pt = recobj.get_pick()
            #     # only take refined pick when delta below 0.8 * window pre STA/LTA pick
            #     if np.abs(picks[index].time - pt) <= 0.8 * win_pre:
            #         picks[index].time = pt

            event = locate_in_homogeneous_background_medium(
                picks=picks,
                coordinates=project5P.cartesian_coordinates,
                velocity=5100.0,  # According to Hansruedi email
                damping=0.01,
                local_to_global_coordinates=project5P.local_to_global_coordinates,
            )


            # If there is a magnitude determination algorithm this could happen
            # here. Same with a moment tensor inversion. Anything really.
            event = amplitude_based_relative_magnitude(st_event, event)

            # Write the classification as a comment.
            if len(picks) < 5:
                event.comments = [
                        obspy.core.event.Comment(
                            text=f"Classification:{'smallpassive'}"
                        )
                ]
            elif len(picks) >=5 and len(picks)<=7:
                event.comments = [
                        obspy.core.event.Comment(
                            text=f"Classification:{'mediumpassive'}"
                        )
                ]
            else:
                event.comments = [
                    obspy.core.event.Comment(
                        text=f"Classification: {'passive'}"
                    )
                ]

            # Could optionally do a QA step here.
            # if event.origins[0].time_errors.uncertainty > 5e-4:
            #     logger.info(
            #         "Rejected event. Time error too large: "
            #         f"{event.origins[0].time_errors.uncertainty}"
            #     )
            #     continue

            # Add the event to the project.
            added_event_count += 1
            if len(picks)<5:
                project3P.db.add_object(event)
            else:
                project5P.db.add_object(event)

    logger.info(
        f"Successfully located {added_event_count} of "
        f"{len(detected_events)} event(s)."
    )
    endT = time.time()
    logger.info(f"Processing of interval Took {(endT - startT_Det) } seconds.")

    total_event_count += added_event_count

logger.info("DONE.")
logger.info(f"Found {total_event_count} events.")
endT = time.time()
logger.info(f"Total time {(endT - startT_all)} seconds.")

