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
Implementation of the coincidence trigger.

Based on ObsPy's coincidence trigger with a few adaptions for DUGSeis.
"""

import warnings

import numpy as np

from obspy import UTCDateTime
from obspy.signal.trigger import trigger_onset
from obspy.signal.cross_correlation import templates_max_similarity


def coincidence_trigger(
    trigger_type,
    thr_on,
    thr_off,
    stream,
    thr_coincidence_sum,
    active_channels,
    trace_ids=None,
    max_trigger_length=1e6,
    delete_long_trigger=False,
    trigger_off_extension=0,
    details=False,
    event_templates={},
    similarity_threshold=0.7,
    **options
):
    """
    Perform a network coincidence trigger.

    The routine works in the following steps:
      * take every single trace in the stream
      * apply specified triggering routine (can be skipped to work on
        precomputed custom characteristic functions)
      * evaluate all single station triggering results
      * compile chronological overall list of all single station triggers
      * find overlapping single station triggers
      * calculate coincidence sum of every individual overlapping trigger
      * add to coincidence trigger list if it exceeds the given threshold
      * optional: if master event templates are provided, also check single
        station triggers individually and include any single station trigger if
        it exceeds the specified similarity threshold even if no other stations
        coincide with the trigger
      * return list of network coincidence triggers

    .. note::
        An example can be found in the
        `Trigger/Picker Tutorial
        <https://tutorial.obspy.org/code_snippets/trigger_tutorial.html>`_.

    .. note::
        Setting `trigger_type=None` precomputed characteristic functions can
        be provided.

    :param trigger_type: String that specifies which trigger is applied (e.g.
        ``'recstalta'``). See e.g. :meth:`obspy.core.trace.Trace.trigger` for
        further details. If set to `None` no triggering routine is applied,
        i.e.  data in traces is supposed to be a precomputed characteristic
        function on which the trigger thresholds are evaluated.
    :type trigger_type: str or None
    :type thr_on: float
    :param thr_on: threshold for switching single station trigger on
    :type thr_off: float
    :param thr_off: threshold for switching single station trigger off
    :type stream: :class:`~obspy.core.stream.Stream`
    :param stream: Stream containing waveform data for all stations. These
        data are changed inplace, make a copy to keep the raw waveform data.
    :type thr_coincidence_sum: int or float
    :type active_channels: list of active channels
    :param thr_coincidence_sum: Threshold for coincidence sum. The network
        coincidence sum has to be at least equal to this value for a trigger to
        be included in the returned trigger list.
    :type trace_ids: list or dict, optional
    :param trace_ids: Trace IDs to be used in the network coincidence sum. A
        dictionary with trace IDs as keys and weights as values can
        be provided. If a list of trace IDs is provided, all
        weights are set to 1. The default of ``None`` uses all traces present
        in the provided stream. Waveform data with trace IDs not
        present in this list/dict are disregarded in the analysis.
    :type max_trigger_length: int or float
    :param max_trigger_length: Maximum single station trigger length (in
        seconds). ``delete_long_trigger`` controls what happens to single
        station triggers longer than this value.
    :type delete_long_trigger: bool, optional
    :param delete_long_trigger: If ``False`` (default), single station
        triggers are manually released at ``max_trigger_length``, although the
        characteristic function has not dropped below ``thr_off``. If set to
        ``True``, all single station triggers longer than
        ``max_trigger_length`` will be removed and are excluded from
        coincidence sum computation.
    :type trigger_off_extension: int or float, optional
    :param trigger_off_extension: Extends search window for next trigger
        on-time after last trigger off-time in coincidence sum computation.
    :type details: bool, optional
    :param details: If set to ``True`` the output coincidence triggers contain
        more detailed information: A list with the trace IDs (in addition to
        only the station names), as well as lists with single station
        characteristic function peak values and standard deviations in the
        triggering interval and mean values of both, relatively weighted like
        in the coincidence sum. These values can help to judge the reliability
        of the trigger.
    :param options: Necessary keyword arguments for the respective trigger
        that will be passed on. For example ``sta`` and ``lta`` for any STA/LTA
        variant (e.g. ``sta=3``, ``lta=10``).
        Arguments ``sta`` and ``lta`` (seconds) will be mapped to ``nsta``
        and ``nlta`` (samples) by multiplying with sampling rate of trace.
        (e.g. ``sta=3``, ``lta=10`` would call the trigger with 3 and 10
        seconds average, respectively)
    :param event_templates: Event templates to use in checking similarity of
        single station triggers against known events. Expected are streams with
        three traces for Z, N, E component. A dictionary is expected where for
        each station used in the trigger, a list of streams can be provided as
        the value to the network/station key (e.g. {"GR.FUR": [stream1,
        stream2]}). Templates are compared against the provided `stream`
        without the specified triggering routine (`trigger_type`) applied.
    :type event_templates: dict
    :param similarity_threshold: similarity threshold (0.0-1.0) at which a
        single station trigger gets included in the output network event
        trigger list. A common threshold can be set for all stations (float) or
        a dictionary mapping station names to float values for each station.
    :type similarity_threshold: float or dict
    :rtype: list
    :returns: List of event triggers sorted chronologically.
    """
    st = stream.copy()
    # if no trace ids are specified use all traces ids found in stream
    if trace_ids is None:
        trace_ids = [tr.id for tr in st]
    # we always work with a dictionary with trace ids and their weights later
    if isinstance(trace_ids, list) or isinstance(trace_ids, tuple):
        trace_ids = dict.fromkeys(trace_ids, 1)
    # set up similarity thresholds as a dictionary if necessary
    if not isinstance(similarity_threshold, dict):
        similarity_threshold = dict.fromkeys(
            [tr.stats.station for tr in st], similarity_threshold
        )

    # the single station triggering
    triggers = []
    # prepare kwargs for trigger_onset

    def util_val_of_scalar_or_list(elem, idx):
        if type(elem) is list:
            return elem[idx]
        return elem

    kwargs = {"max_len_delete": delete_long_trigger}
    for idx, tr in enumerate(st):
        if tr.id not in trace_ids:
            msg = (
                "At least one trace's ID was not found in the "
                + "trace ID list and was disregarded (%s)" % tr.id
            )
            warnings.warn(msg, UserWarning)
            continue
        if trigger_type is not None:
            # original ObsPy
            # tr.trigger(trigger_type, **options)
            # adjustments for DUG-Seis
            new_options = {}
            for key, val in options.items():
                new_options[key] = util_val_of_scalar_or_list(val, idx)
        if not any(x in tr.id for x in active_channels):
            # Linus inserted this on 15.03.2023, no cf performed on trigger channels
            tr.trigger(trigger_type, **new_options)
            # end of adjustments
        if any(x in tr.id for x in active_channels):
            x = 2

        kwargs["max_len"] = int(max_trigger_length * tr.stats.sampling_rate + 0.5)

        # original
        # tmp_triggers = trigger_onset(tr.data, thr_on, thr_off, **kwargs)
        # adjustments for DUG-Seis
        tmp_triggers = trigger_onset(
            tr.data,
            util_val_of_scalar_or_list(thr_on, idx),
            util_val_of_scalar_or_list(thr_off, idx),
            **kwargs
        )
        # end of adjustments
        for on, off in tmp_triggers:
            try:
                cft_peak = tr.data[on:off].max()
                cft_std = tr.data[on:off].std()
            except ValueError:
                cft_peak = tr.data[on]
                cft_std = 0
            on = tr.stats.starttime + float(on) / tr.stats.sampling_rate
            off = tr.stats.starttime + float(off) / tr.stats.sampling_rate
            triggers.append((on.timestamp, off.timestamp, tr.id, cft_peak, cft_std))
    triggers.sort()

    # the coincidence triggering and coincidence sum computation
    coincidence_triggers = []
    last_off_time = 0.0
    while triggers != []:
        # remove first trigger from list and look for overlaps
        on, off, tr_id, cft_peak, cft_std = triggers.pop(0)
        sta = tr_id.split(".")[1]
        event = {}
        event["time"] = [
            UTCDateTime(on)
        ]  # added square brackets, Linus 22.10.2018_____
        event["stations"] = [tr_id.split(".")[1]]
        event["trace_ids"] = [tr_id]
        event["coincidence_sum"] = float(trace_ids[tr_id])
        event["similarity"] = {}
        if details:
            event["cft_peaks"] = [cft_peak]
            event["cft_stds"] = [cft_std]
        # evaluate maximum similarity for station if event templates were
        # provided
        templates = event_templates.get(sta)
        if templates:
            event["similarity"][sta] = templates_max_similarity(
                stream, event["time"], templates
            )
        # compile the list of stations that overlap with the current trigger
        for trigger in triggers:
            tmp_on, tmp_off, tmp_tr_id, tmp_cft_peak, tmp_cft_std = trigger
            tmp_sta = tmp_tr_id.split(".")[1]
            # skip retriggering of already present station in current
            # coincidence trigger
            if tmp_tr_id in event["trace_ids"]:
                continue
            # check for overlapping trigger,
            # break if there is a gap in between the two triggers
            if tmp_on > off + trigger_off_extension:
                break
            event["stations"].append(tmp_sta)
            event["trace_ids"].append(tmp_tr_id)
            event["coincidence_sum"] += trace_ids[tmp_tr_id]
            if details:
                event["cft_peaks"].append(tmp_cft_peak)
                event["cft_stds"].append(tmp_cft_std)
                event["time"].append(
                    UTCDateTime(tmp_on)
                )  # inserted by Linus 22.10.2018_____
            # allow sets of triggers that overlap only on subsets of all
            # stations (e.g. A overlaps with B and B overlaps w/ C => ABC)
            off = max(off, tmp_off)
            # evaluate maximum similarity for station if event templates were
            # provided
            templates = event_templates.get(tmp_sta)
            if templates:
                event["similarity"][tmp_sta] = templates_max_similarity(
                    stream, event["time"], templates
                )
        # skip if both coincidence sum and similarity thresholds are not met
        if event["coincidence_sum"] < thr_coincidence_sum:
            if not event["similarity"]:
                continue
            elif not any(
                [
                    val > similarity_threshold[_s]
                    for _s, val in event["similarity"].items()
                ]
            ):
                continue
        # skip coincidence trigger if it is just a subset of the previous
        # (determined by a shared off-time, this is a bit sloppy)
        if off <= last_off_time:
            continue
        event["duration"] = off - on
        if details:
            weights = np.array([trace_ids[i] for i in event["trace_ids"]])
            weighted_values = np.array(event["cft_peaks"]) * weights
            event["cft_peak_wmean"] = weighted_values.sum() / weights.sum()
            weighted_values = np.array(event["cft_stds"]) * weights
            event["cft_std_wmean"] = (
                np.array(event["cft_stds"]) * weights
            ).sum() / weights.sum()
        coincidence_triggers.append(event)
        last_off_time = off
    return coincidence_triggers
