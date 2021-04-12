# Load waveform data for processing
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import numpy as np
import pyasdf
from obspy import Stream


def get_waveforms_dugseis(param, load_file, trig_time, logger):
    '''Call (somewhat) generic function get_waveforms using the DUG-Seis parameters'''
    return get_waveforms(
        load_file=[param['General']['asdf_folder'] + '/' + f for f in load_file],
        start_time=trig_time - param['Trigger']['starttime'],
        end_time=trig_time + param['Trigger']['endtime'],
        network_id=param['General']['stats']['network'],
        sensor_count=param['General']['sensor_count'],
        input_range_source=param['Trigger']['input_range_source'],
        input_range=param['Acquisition']['hardware_settings']['input_range'],
        logger=logger,
    )

def get_waveforms(load_file, start_time, end_time, network_id,
                  sensor_count, input_range_source, input_range, logger):
    '''Read a waveform snippet form one file or two files.'''
    channel_range = range(sensor_count)

    def ds_get_waveforms(ds, starttime, endtime):
        # network_id is in the scope of this function.
        stream = Stream()
        for ch_idx in channel_range:
            stream += ds.get_waveforms(network=network_id,
                                    station=str(int(ch_idx + 1)).zfill(3),
                                    location='00',
                                    channel='001',
                                    starttime=starttime,
                                    endtime=endtime,
                                    tag='raw_recording'
            )
        return stream

    def set_input_range(stream):
        if input_range_source == 'YAML':
            for ch_idx in channel_range:
                stream.traces[ch_idx].data = stream.traces[ch_idx].data / 32768 * \
                    input_range[ch_idx]
            if logger:
                logger.info('Input range event retrieved from YAML file')


    # To create the waveform, load 2 data snippets if event in overlap otherwise load 1
    if len(load_file) == 1:
        ds = pyasdf.ASDFDataSet(load_file[0], mode='r')
        wf_stream = ds_get_waveforms(
            ds=ds,
            starttime=start_time,
            endtime=end_time
        )
        set_input_range(wf_stream)

    else:
        # In this case the waveform will be loaded in from 2 data snippets.
        ds1 = pyasdf.ASDFDataSet(load_file[0], mode='r')
        ds2 = pyasdf.ASDFDataSet(load_file[1], mode='r')

        if end_time > ds2.waveforms[network_id + '_001'].raw_recording.traces[0].stats['starttime']:
            # end_time is in second file
            stream1 = ds_get_waveforms(
                ds=ds1,
                starttime=start_time,
                endtime=ds1.waveforms[network_id + '_001'
                    ].raw_recording.traces[0].stats['endtime']
            )
            stream2 = ds_get_waveforms(
                ds=ds2,
                starttime=ds2.waveforms[network_id + '_001'
                    ].raw_recording.traces[0].stats['starttime'],
                endtime=end_time
            )
            wf_stream = stream1 + stream2
            wf_stream.merge(method=1, interpolation_samples=0)
            set_input_range(wf_stream)

        else:
            # end_time is NOT in second file, meaning there must be a gap
            # between the two files
            wf_stream = Stream()
            end_time = min(end_time, ds1.waveforms[network_id + '_001'
                ].raw_recording.traces[0].stats['endtime'])
            wf_stream = ds_get_waveforms(
                ds=ds1,
                starttime=start_time,
                endtime=end_time
            )
            set_input_range(wf_stream)

    return wf_stream

