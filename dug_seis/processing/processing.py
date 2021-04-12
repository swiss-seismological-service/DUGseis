# Trigger and processing module of DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import logging
import os
import re
import pathlib
import sys
import time
import traceback

import pyasdf
import obspy
from obspy import Stream, UTCDateTime
from dug_seis import util
from dug_seis.processing.dug_trigger import dug_trigger
from dug_seis.processing.event_processing import event_processing

from dug_seis.waveform_handler.waveform_handler import FILENAME_REGEX


class Get_files:
    """
    Iterator for files in asdf_folder.

    Special method: prev, to get the previous file.
    Example for filename: 2017-02-09T13-24-50-225998Z_Grimsel.h5

    Args:
        asdf_folder (str): path of folder with ASDF files
        start_time (str): start_time, arbitrary separators e. g. 2019-05/22T15:09
        logger (logger): logger
        wait_for_new_data (bool, optional): if truthy, processing never ends
    """

    def __init__(
        self, asdf_folder, start_time, logger, wait_for_new_data=True, end_time=None
    ):
        self.asdf_folder = asdf_folder
        self.files = []

        self.start_time = start_time
        self.end_time = end_time
        self.wait_for_new_data = wait_for_new_data
        self.logger = logger
        self.index = -1

        self.files += self.find_new_files()

    def __iter__(self):
        return self

    def find_new_files(self):
        all_files = [
            f
            for f in sorted(os.listdir(self.asdf_folder))
            if f.endswith(".h5") and f not in self.files
        ]
        new_files = []

        # Filter by dates.
        for f in all_files:
            m = re.match(FILENAME_REGEX, pathlib.Path(f).stem)
            if not m:
                continue
            g = m.groups()

            # Filter the times.
            starttime = obspy.UTCDateTime(*[int(i) for i in g[:7]])
            endtime = obspy.UTCDateTime(*[int(i) for i in g[7:]])
            if starttime > self.end_time or endtime < self.start_time:
                continue
            new_files.append(f)

        return new_files

    def __next__(self):
        self.index += 1
        if self.index >= len(self.files):
            if self.wait_for_new_data:
                while 1:
                    self.logger.info("Waiting for new files.")
                    time.sleep(0.5)
                    new_files = self.find_new_files()
                    if len(new_files):
                        self.files += new_files
                        return self.files[self.index]

            self.logger.info("No new files. Processing finished.")
            raise StopIteration

        return self.files[self.index]

    def prev(self):
        return self.files[self.index - 1]


def create_folders(param):
    for folder in ["quakeml", "json"]:
        if not os.path.exists(folder):
            os.makedirs(folder)


def stream_from_file(file, channels):
    stream = Stream()
    with pyasdf.ASDFDataSet(file, mode="r") as ds:
        wf_list = ds.waveforms.list()
        for idx0 in range(len(wf_list)):
            if idx0 not in channels:
                continue
            stream += ds.waveforms[wf_list[idx0]].raw_recording
    return stream


def get_snippet(stream, trig_time, param):
    """
    Create an ObsPy Stream object to be processed by the class Event

    In these snippets the data values are divided by the
    factors preamplifier gain and internal gain.
    """
    starttime = trig_time + param["Trigger"]["offset"]
    endtime = starttime + param["Trigger"]["interval_length"]
    hw_param = param["Acquisition"]["hardware_settings"]

    # If picking of p and s waves is performed, use bigger snippet.
    if param["Picking"]["s_picking"]:
        pick_param = param["Picking"][param["Picking"]["algorithm"]]
        endtime += pick_param["s_wave"]["gap"] + pick_param["s_wave"]["length"]

    new_stream = util.stream_copy(stream).trim(
        # starttime,
        # endtime,
        # TODO  Adding one sample at start and end respectively mimicks the
        #       behavior of pyasdf.ASDFDataSet.get_waveforms.
        #       This may be not necessary or even wrong.
        starttime - 1 / param["Acquisition"]["hardware_settings"]["sampling_frequency"],
        endtime + 1 / param["Acquisition"]["hardware_settings"]["sampling_frequency"],
    )

    # apply gain factors
    for idx, tr in enumerate(new_stream.traces):
        factor = 10 ** (
            (hw_param["preamp_gain"][idx] + hw_param["internal_gain"][idx]) / 20
        )
        tr.data = tr.data / factor

    return new_stream


def setup_stream(stream, stream_prev, param, stations, logger):
    """Create an ObsPy Stream object of a whole file,
    if possible prepending a time interval of the previous stream.
    """
    # Apply input range to all traces in the stream.
    resolution_bits = (
        param["Acquisition"]["hardware_settings"]["vertical_resolution"] / 2
    )
    if param["Trigger"]["input_range_source"] == "YAML":
        for tr_idx in range(0, len(stream.traces)):
            stream.traces[tr_idx].data = (
                stream.traces[tr_idx].data
                / resolution_bits
                * param["Acquisition"]["hardware_settings"]["input_range"][tr_idx]
            )
            # TODO  Development code, testing s-wave picker
            #       Only for GMuG data
            # stream.traces[tr_idx].stats['network'] = 'GM'
        logger.info("Input range trigger retrieved from YAML file")

    if len(stream_prev):
        # Use only one stream, if more than 10 samples between the streams are missing.
        if (
            stream.traces[0].stats["starttime"] - stream_prev.traces[0].stats["endtime"]
            > 10.0 / param["Acquisition"]["hardware_settings"]["sampling_frequency"]
        ):
            logger.info("Gap in waveform data found.")
        else:
            # Prepend stream_prev, merge streams
            stream = stream_prev + stream
            for tr in stream:
                tr.stats.delta = stream[0].stats.delta
            stream.merge(method=1, interpolation_samples=0)
    return stream


def proc_single_event(param, communication, asdf_folder, logger):
    starttime = (
        communication["single_event"]["trigger_time"] + param["Trigger"]["offset"]
    )
    file = util.file_of_time(
        asdf_folder,
        starttime.isoformat(),
        param["Acquisition"]["asdf_settings"]["file_length_sec"],
    )
    if not file:
        communication["callback_signal"].emit(
            {
                "error": (
                    "No ASDF file found for time "
                    + str(communication["single_event"]["start_time"])
                    + "."
                ),
            }
        )
        return

    display_channels = communication["single_event"]["display_channels"]
    # for location all channels are needed
    if (
        communication["single_event"]["calc"]
        or communication["single_event"]["display_pick_channels"]
    ):
        display_channels = list(range(param["General"]["sensor_count"]))

    stream = stream_from_file(
        os.path.join(asdf_folder, file),
        display_channels,
    )
    snippet = get_snippet(
        stream,
        communication["single_event"]["trigger_time"],
        param,
    )
    event_processing(
        param,
        snippet,
        int(communication["single_event"]["id"]),
        "passive",
        logger,
        communication,
    )
    return


def processing(param):
    logger = logging.getLogger("dug-seis")
    tparam = param["Trigger"]

    # Initialization
    asdf_folder = param["General"]["asdf_folder"]
    active_trigger_channel = param["General"]["active_trigger_channel"]

    # only used for triggering
    stations = [i - 1 for i in tparam["channels"]]
    if len(tparam["channels"]) != 1:
        if active_trigger_channel and active_trigger_channel - 1 not in stations:
            stations.insert(0, active_trigger_channel - 1)
    stations.sort()
    event_nr = 0
    event_nr_s = []

    stream_prev = Stream()
    interval_length = tparam["interval_length"]

    start_time = obspy.UTCDateTime(param["General"]["start_time"])
    end_time = obspy.UTCDateTime(param["General"]["end_time"])

    # Initialize file name getter
    get_files = Get_files(
        asdf_folder=asdf_folder,
        start_time=start_time,
        end_time=end_time,
        logger=logger,
        wait_for_new_data=param["Processing"]["wait_for_new_data"],
    )

    for _i, current_file in enumerate(get_files):
        print(f"Processsing file {_i}: {current_file}")
        stream = stream_from_file(
            os.path.join(asdf_folder, current_file),
            [i for i in range(param["General"]["sensor_count"])],
        )
        # stream_prev is not set during the very first run of the loop,
        # otherwise it's set.
        stream = setup_stream(stream, stream_prev, param, stations, logger)

        # Send stream to the trigger script using only traces in list "stations".
        trigger_out, event_nr = dug_trigger(
            Stream().extend(
                [stream[idx].copy() for idx in range(len(stream)) if idx in stations]
            ),
            tparam,
            event_nr,
            event_nr_s,
        )

        t_end = stream.traces[0].stats["endtime"]
        stream_prev = util.stream_copy(stream).trim(t_end - interval_length, t_end)

        # Send data snippet containing the event,
        # the triggered time of the event, the event id and the
        # event classification to the event processing script.
        for _, trig in trigger_out[
            trigger_out["Time"] < t_end - interval_length
        ].iterrows():
            # Do not process times at the end of the interval because
            # the interval for them to be processed exeeds the loaded waveforms.
            # These times will be processed in the next loop.
            snippet = get_snippet(stream, trig["Time"], param)

            event_processing(
                param, snippet, trig["Event_id"], trig["Classification"], logger
            )
