#!/usr/bin/env python
# coding: utf-8

import json

import pandas as pd
import matplotlib.pyplot as plt
from obspy import core
from obspy.core import utcdatetime
from obspy.core.utcdatetime import UTCDateTime


channels_for_avrg = [16, 17, 18, 19, 20, 21, 22]

def utf_average(event):
    # minutes and seconds to float, relative to 2017-02-09T13-24-00
    sum = 0
    utc_list = [v for k,v in event['picks'].items() if k in channels_for_avrg]

    for t in utc_list:
        sum += t.__float__()
    # t = 0 is 2017-02-09T13-24-00
    return sum / len(utc_list) - 1486646660 + 20


def load_data(cfg):
    # select reference file depending on number of source files
    src_file = (cfg['tools'] + 'p_picker_reference.csv')

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
    return ref

def exec(params, cfg):
    # main_dir = '/home/1/dev/proj/dugseis/devel/processing/analysis/p_picker/'
    # file = 'output/12-sourcefiles/3.0_1.5_7_180/details_3.0_1.5_7_180.json'
    # file = 'output/58-sourcefiles/5.0_2.0_11_180/details_5.0_2.0_11_180.json'
    file = cfg['results'] + f'details_{cfg["param_str"]}.json'

    # with open(main_dir + file, 'r') as read_file:
    with open(file, 'r') as read_file:
        details = json.load(read_file)

    matchings = [d for d in details if d['match'] == 'OK']

    # basetime = UTCDateTime('2017-02-09T13-24-00')
    ch_primary = [16, 17, 18, 19, 20, 21, 22, 23]
    ch_secondary = [4, 5, 6,    25, 26, 27]
    # plt.rcParams.update({'figure.figsize':(18, 12), 'figure.dpi':60})

    # fig, ax = plt.subplots()
    plt.subplots()
    plt.grid(True)

    mat = matchings
    ref_times = [r['ref_time'] for m in mat for r in m['picks']['diffs'] if r['ch'] in ch_secondary]
    diffs     = [r['diff'] * 1000 for m in mat for r in m['picks']['diffs'] if r['ch'] in ch_secondary]
    #ref_times = [basetime + rt for rt in ref_times]
    ref_times[0:10]

    plt.plot(ref_times, diffs, 'o', color="#0000ff", markersize=0.5)
    ref_times = [r['ref_time'] for m in mat for r in m['picks']['diffs'] if r['ch'] in ch_primary]
    diffs     = [r['diff'] * 1000 for m in mat for r in m['picks']['diffs'] if r['ch'] in ch_primary]
    len(ref_times)
    #ref_times = [basetime + rt for rt in ref_times]
    plt.plot(ref_times, diffs, 'o', color="#b00000", markersize=0.5)

    plt.xlabel('Pick time rel. to 2017-02-09T13-24-00 [s]')
    plt.ylabel('Difference: (dug-seis − reference) [ms]')

    plotfile = cfg['results'] + 'picker_dot_plots.png'
    plt.savefig(plotfile, dpi=300)

    #plt.show()
