'''
Converting GMuG format files to ASDF

Reads the .txt and the .dat file.
If the GMuG data contains more than one event
separate files are created for each event.

Usage:
from GMUG_to_ASDF import gmug_to_asdf
gmug_to_asdf(src_file=…, dest_dir=…, filename_suffix=…)

src_file            absolute path of source file, endings .txt or .dat are optional
dest_dir            absolute path
filename_suffix     optional part before the ".h5" ending
'''


import re
import os
import sys
from operator import itemgetter

import numpy as np
import pyasdf
from obspy import Stream, Trace, UTCDateTime


def read_txt(src_file):
    with open(f'{src_file}.txt', 'r', encoding='iso-8859-15') as fh:
        lines = re.sub(r'\n+$', '', fh.read()).split('\n')

    times = lines[18:]
    times = [[int(el) for el in x] for x in [t.strip().split() for t in times]]
    times = [UTCDateTime(t[5], t[6], t[7], t[1], t[2], t[3], t[4] * 1000)
        for t in times]

    lines = itemgetter(*[i for i in range(4, 15) if i not in (12, 13)])(lines)
    keys = ('delta', 'records_count', 'samples_count', 'channels_count',
        'pre_trigger_precent', 'ad_resolution', 'input_range', 'trigger_level',
        'digit_multiplier')
    params = dict(zip(keys, [l.strip() for l in lines]))

    # type conversions
    params['delta'] = float(params['delta'])

    # to integer
    for key in ('delta', 'records_count', 'samples_count', 'channels_count',
        'pre_trigger_precent', 'ad_resolution'):
        params[key] = int(params[key])

    # to list of integers
    for key in ('input_range', 'trigger_level', 'digit_multiplier'):
        params[key] = [int(x) for x in params[key].split()]

    params['sampling_rate'] = 1 / (params['delta'] * 1e-6)

    return params, times


def read_dat(src_file, times):
    src_data = np.fromfile(f'{src_file}.dat', dtype='int16')
    print(len(src_data))
    events = np.split(src_data, len(times))
    return events


def gmug_to_asdf(src_file, dest_dir, filename_suffix=''):
    src_file = re.sub('(.txt|.dat)$', '', src_file)

    if not os.path.exists(src_file + '.txt'):
        print(f'file "{src_file}.txt" not existing')
        sys.exit()

    if not os.path.exists(src_file + '.dat'):
        print(f'file "{src_file}.dat" not existing')
        sys.exit()

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f'directory "{dest_dir}" created')

    params, times = read_txt(src_file)
    events = read_dat(src_file, times)

    for evt_idx in range(len(times)):
        channels = np.split(events[evt_idx], params['channels_count'])
        stream = Stream()

        for ch_idx in range(0, params['channels_count']):
            data = channels[ch_idx]
            stats = {
                'network'      : 'GM',
                'station'      : str(ch_idx + 1).zfill(3),
                'location'     : '00',
                'channel'      : '001',
                'sampling_rate': params['sampling_rate'],
                'starttime'    : times[evt_idx],
            }
            stream += Trace(data=data, header=stats)

        # Writing the .h5 file
        # file name example: 2015-03-25T00-14-494000<suffix>.h5
        filename = (times[evt_idx].strftime('%Y-%m-%dT%H-%M-%S%f')[:-2]
            + filename_suffix + '.h5')
        file_handle = pyasdf.ASDFDataSet(os.path.join(dest_dir, filename),
            compression=None)
        file_handle.add_waveforms(stream, tag='raw_recording')
        print(f'file {filename} written')

