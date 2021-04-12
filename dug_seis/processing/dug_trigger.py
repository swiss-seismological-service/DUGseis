# Trigger function used by Trigger module of DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import pandas as pd
from obspy.core import UTCDateTime

from dug_seis.processing.obs_trigger import coincidence_trigger


def dug_trigger(sta_total, tparam, event_nr, event_nr_s):
    sta_total.filter(
        'bandpass',
        freqmin=tparam['bandpass_f_min'],
        freqmax=tparam['bandpass_f_max']
    )

    # Triggering
    t = 1 / sta_total[0].stats.sampling_rate
    trig = coincidence_trigger(
        'recstalta',
        tparam['recstalta']['threshold_on'],
        tparam['recstalta']['threshold_off'],
        sta_total,
        tparam['coincidence'],
        sta=[w * t for w in tparam['recstalta']['st_window']],
        lta=[w * t for w in tparam['recstalta']['lt_window']],
        trigger_off_extension=0.01,
        details=True
    )

    time_s = []
    classification_s = []
    coincidence_s = []
    time_min_s = []
    for f in range(len(trig)):
        # update cummulative event_id
        event_nr += 1
        # create a list of event_ids
        event_nr_s = event_nr_s + [event_nr]

        # trigger time of earliest arrival of one event
        time_min = trig[f]['time'][0]
        # list of trigger time of earliest arrival of one event
        time_min_s = time_min_s + [trig[f]['time'][0]]
        # trigger time of latest arrival of one event
        time_max = max(trig[f]['time'])

        # difference between earliest and latest arrival of one event
        diff = time_max - time_min
        # find out trace ids of one event
        id_int = [int(i.split(".")[1]) for i in trig[f]["trace_ids"]]
        # sort the trace ids of one event
        id_int.sort()

        if len(sta_total.traces) == 1:
            cla_s = 'passive'
        else:
            if diff < float(tparam['classification']['spread_int']):
                # if the difference between earliest and latest arrival is too small,
                # set: classification = electronic interference
                cla_s = 'electronic'
            elif id_int[0] == 1:
                # if the event has an arrival on the first trace, classification=active
                cla_s = 'active'
            else:
                # if none of the above are true, classification=passive
                cla_s = 'passive'

        # make a list of classifications for each event
        classification_s.append(cla_s)
        # make a list of earliest arrival times for each event
        time_s.append(UTCDateTime(time_min.isoformat()))
        # make a list of coincidence for each event
        coincidence_s.append(int(trig[f]['coincidence_sum']))

    diff = []
    delete = []

    for i in range(1, len(trig)):
        diff = time_min_s[i] - time_min_s[i - 1]
        if diff < tparam['time_between_events']:
            delete = delete + [i]

    if len(delete):
        n_del = 0
        delete.reverse()
        for i in delete:
            del trig[i]
            del event_nr_s[i]
            event_nr_s[i:] = [x - 1 for x in event_nr_s[i:]]
            del time_min_s[i]
            del time_s[i]
            del classification_s[i]
            del coincidence_s[i]
            n_del = n_del + 1
        event_nr = event_nr - n_del

    for f in range(len(trig)):
        # write a log file
        data = [event_nr_s[f]] + [coincidence_s[f]] + [time_min_s[f].isoformat()] + [
            classification_s[f]]
        cols = pd.Index(['Event_id', 'Coincidence_sum', 'Time', 'Classification'], name='cols')
        df = pd.DataFrame(data=[data], columns=cols)
        log_file = 'trigger.csv'
        df.to_csv(log_file, mode='a', header=False, index=False)

    # set up data frame containing list of event ids, trigger times and classifications
    trigger_out = pd.DataFrame({
        'Event_id': event_nr_s,
        'Time': time_s,
        'Classification': classification_s
    })
    return trigger_out, event_nr
