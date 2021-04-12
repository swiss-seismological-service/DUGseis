'''
Comparison of the events picked by DUG-Seis
with the reference manually picked by Linus Villiger.

An event is declared the same as one in the reference if the time difference
of the average of the pick times of channels 16, 17, 18, 19, 20, 21, 22
is less than a max_diff.


'missed'         events in reference that have no triggered partner
'as electronic'  triggered events classified as 'electronic'
'false'          triggered events classified as 'passive' not in reference


Output files

details<…>.json
    array of details
        detail:
            i               serial number of events, either only reference
                            or only dug-seis or both
            ref_id          id in reference
            ref_time        average of pick times in reference
            dug_avrg        average of pick times in dug-seis
            match           'OK'|'false'|'missed'
            time_diff       dug_evt['average'] - ref_evt['average']
            picks           object
                OK          number of matching picks
                missed      number of picks only in reference
                false       number of picks only in dug-seis
                diffs       array
                    ch      channel number
                    diff    (time pick dug-seis) - (time pick reference)

statistic<…>.json
    max_diff                    time difference in seconds of average pick times of events
                                for events to be considered equal
    OK                          number of matching events
    missed                      number of events only in reference
    false                       number of events only in dug-seis
    diffs                       object
        keys:                   channel IDs
        values:                 array of time differences of matching individual pick times

    ok_percentage               # OK / # events in reference * 100
    sum_picks                   total number of matching individual picks
    picks_in_aim                number of picks with absolute difference to reference < 0.1ms
    picks_in_aim_percentage     %

'''

import os
import re
import json

import pandas as pd
from obspy import core
from obspy.core import utcdatetime
from obspy.core.utcdatetime import UTCDateTime


channels_compare = [4, 5, 6,   16, 17, 18, 19, 20, 21, 22, 23,   25, 26, 27]
channels_for_avrg = [16, 17, 18, 19, 20, 21, 22]


def utf_to_sec_relative(utc):
    return utc.__float__() - 1486646660 + 20

def utf_average(event):
    # minutes and seconds to float, relative to 2017-02-09T13-24-00
    sum = 0
    # if only_range:
    #     utc_list = [v for k,v in event['picks'].items() if k in channels_for_avrg]
    # else:
    #     utc_list = list(event['picks'].values())
    utc_list = [v for k,v in event['picks'].items() if k in channels_for_avrg]

    for t in utc_list:
        sum += t.__float__()
    # t = 0 is 2017-02-09T13-24-00
    return sum / len(utc_list) - 1486646660 + 20


def load_data(cfg):
    # select reference file depending on number of source files
    # src_file = (cfg['tools'] + f'p_picker_reference--{cfg["num_src_files"]}.csv')
    # src_file = (cfg['tools'] + f'{cfg["picker"]}/{cfg["picker"]}_reference--{cfg["num_src_files"]}.csv')
    src_file = (f'{cfg["tools"]}reference--{cfg["num_src_files"]}.csv')

    df_src = pd.read_csv(src_file, sep='\t', index_col=False, header=None)

    ref = []
    event = {}

    for row in [df_src.iloc[i] for i in range(0, len(df_src))]:
        if row[1] != 'P':
            ref.append(event)
            event = {
                'time' : UTCDateTime(row[1]),
                # 'x'    : row[2],
                # 'y'    : row[3],
                # 'z'    : row[4],
                # 'mag'  : row[5],
                'id'   : row[6].replace('smi:local/event/', ''),
                'picks': {},
                }
        else:
            event['picks'][int(row[4].replace('R', ''))] = UTCDateTime(row[2])

    ref.append(event)

    # delete empty first element
    ref = ref[1:]

    for i in range(0, len(ref)):
        ref[i]['average'] = utf_average(ref[i])


    with open(cfg['results'] + 'picks.csv', 'r') as f:
        txt = f.read()

    src = re.sub(r'\n$', '', txt).split('\n')

    dugseis = []
    for row in [src[i] for i in range(0, len(src))]:
        tmp = row.split(',')
        event = {
            'id'   : int(tmp[0]),
            'picks':  {},
        }
        for pair in list(zip(tmp[1::2], tmp[2::2])):
            event['picks'][int(pair[0])] = UTCDateTime(pair[1])

        if (len(event['picks']) == 0 or 
            len([k for k in event['picks'].keys() if k in channels_for_avrg]) == 0):
            continue

        event['average'] = utf_average(event)
        dugseis.append(event)

    return [ref, dugseis]


def compare_picks(picks_ref, picks_dugseis):
    # TODO  Indigo: richtigen Text schreiben
    '''Second level: compare picks of an event

        Args:
            max_diff (float): time difference in seconds for events
                              to be considered equal

        Returns:
            dict: max_diff, counts of 'OK', 'missed', 'false'

        Output:
            optionally write CSV file
            print sys
    '''

    # ref_set     = set([p['ch'] for p in picks_ref['picks']])
    # dugseis_set = set([p['ch'] for p in picks_dugseis['picks']])
    # ref_set     = set(picks_ref['picks']].keys())
    ref_set     = set([k for k in picks_ref.keys() if k in channels_compare])
    dugseis_set = set([k for k in picks_dugseis.keys() if k in channels_compare])

    result = {
        'OK':     len(ref_set.intersection(dugseis_set)),
        'missed': sorted(list(ref_set.difference(dugseis_set))),
        'false':  sorted(list(dugseis_set.difference(ref_set))),
        'diffs':  []
    }

    for ch in ref_set.intersection(dugseis_set):
        result['diffs'].append({
            'ch': ch,
            # 'ref_time': picks_ref[ch],
            'ref_time': utf_to_sec_relative(picks_ref[ch]),
            'diff': picks_dugseis[ch] - picks_ref[ch],
            })

    return result


def exec(max_diff, params, cfg):
    '''First level: compare events

        Args:
            max_diff (float): time difference in seconds for events
                              to be considered equal picks
        Output:
            write CSV files
    '''
    ref, dugseis = load_data(cfg)

    idx = 0
    idx_ref = 0
    idx_dugseis = 0

    # statistical data, sums
    statistic = {
        'max_diff': max_diff,
        'OK': 0,
        'missed': 0,
        'false': 0,
        'diffs': {
        }
    }
    for ch in channels_compare:
        statistic['diffs'][ch] = []

    # detailed data of every event
    details = []

    while idx_ref < len(ref) or idx_dugseis < len(dugseis):

        if idx_dugseis < len(dugseis):
            dug_evt = dugseis[idx_dugseis]
            diff = -1000

        if idx_ref < len(ref):
            ref_evt = ref[idx_ref]
            diff = 1000

        if idx_ref < len(ref) and idx_dugseis < len(dugseis):
            diff = dug_evt['average'] - ref_evt['average']


        if abs(diff) <= max_diff:
            # considered the same event
            comparision = compare_picks(ref_evt['picks'], dug_evt['picks'])
            for el in comparision['diffs']:
                statistic['diffs'][el['ch']].append(el['diff'])

            details.append({
                'i'        : idx,
                'ref_id'   : ref_evt['id'],
                'ref_time' : ref_evt['average'],
                'dug_id'   : dug_evt['id'],
                'dug_avrg' : dug_evt['average'],
                'match'    : 'OK',
                'time_diff': diff,
                'picks'    : comparision,
            })
            idx_ref += 1
            idx_dugseis += 1
            statistic['OK'] += 1

        elif diff < 0:
            # only dug-seis: false positive
            details.append({
                'i'        : idx,
                'ref_id'   : '–',
                'ref_time' : '–',
                'dug_id'   : dug_evt['id'],
                'dug_avrg' : dug_evt['average'],
                'match'    : 'false',
                'time_diff': '–',
            })
            statistic['false'] += 1

            idx_dugseis += 1

        elif diff > 0:
            # only reference: 'missed'
            details.append({
                'i':         idx,
                'ref_id':    ref_evt['id'],
                'ref_time':  ref_evt['average'],
                'dug_avrg':  '–',
                'match':     'missed',
                'time_diff': '–',
            })
            idx_ref += 1
            statistic['missed'] += 1

        idx += 1


    # global calculations
    statistic['ok_percentage'] = round(statistic['OK'] / len(ref) * 100, 1)
    statistic['sum_picks'] = sum([len(statistic['diffs'][ch])
        for ch in statistic['diffs'].keys()])

    statistic['picks_in_aim'] = {'sum': 0}
    for ch in statistic['diffs'].keys():
        statistic['picks_in_aim'][ch] = len([v for v
            in statistic['diffs'][ch] if abs(v) <= 0.0001])
        statistic['picks_in_aim']['sum'] += statistic['picks_in_aim'][ch]

    statistic['picks_in_aim_percentage'] = 0
    if statistic['sum_picks'] != 0:
        statistic['picks_in_aim_percentage'] = round(
            statistic['picks_in_aim']['sum'] / statistic['sum_picks'] * 100, 1)


    # write files
    with open(cfg['results']
            + f'statistic_{cfg["param_str"]}.json', 'w') as write_file:
        json.dump(statistic, write_file)

    with open(cfg['results']
            + f'details_{cfg["param_str"]}.json', 'w') as write_file:
        json.dump(details, write_file)


    print(f'OK:            {statistic["OK"]}')
    print(f'missed:        {statistic["missed"]}')
    print(f'false:         {statistic["false"]}')
    print(f'OK percentage: {statistic["ok_percentage"]}')

    return {
        'max_diff':      max_diff,
        'OK':            statistic['OK'],
        'missed':        statistic['missed'],
        'false':         statistic['false'],
        'OK percentage': statistic['ok_percentage'],
    }

