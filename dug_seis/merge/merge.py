# DUG-Seis Merge module
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#



import logging
import numpy as np
from obspy import Stream
import pyasdf
import glob
import os


def merge(param):
    tparam = param['Trigger']
    gparam = param['General']
    logging.info('Starting merge module')

    # create folders for processing
    if not os.path.exists(param['Processing']['Folders']['quakeml_folder']):
        os.makedirs(param['Processing']['Folders']['quakeml_folder'])

    # Initialisation
    asdf_folder = tparam['asdf_folder']  # 'raw'  # Location of .h5 file
    merge_folder = param['Merge']['merge_folder']
    last_merge = 0

    # load list of ASDF snippets in folder
    new_files = sorted([f for f in os.listdir(asdf_folder) if f.endswith('.h5')])  # generates a list of the .asdf files in asdf_folder

    filenumber = round(param['Merge']['merge_time_sec'] / param['Acquisition']['asdf_settings']['file_length_sec'])

    while last_merge+filenumber<=len(new_files) and filenumber>0:
        logging.info('Merging files ' + str(new_files[last_merge:last_merge + filenumber]))

        sta = Stream()
        ch_in = range(0, gparam['sensor_count'])

        for i in new_files[last_merge:last_merge + filenumber]:
            ds = pyasdf.ASDFDataSet(asdf_folder + '/' + i, mode='r')
            wf_list = ds.waveforms.list()

            for k in ch_in:
                sta += ds.waveforms[wf_list[k]].raw_recording

        for tr in sta:
            tr.stats.delta = sta[0].stats.delta

        sta.merge(method=1, interpolation_samples=0)
        start_time = sta.traces[0].stats["starttime"]

        name = merge_folder + '/' + gparam['project_name'] + str(start_time)
        name2 = name.replace('.', '-')
        name3 = name2.replace(':', '-')
        # sta.write(merge_folder + '/' + gparam['project_name'] + str(start_time) + ".mseed")

        sta.write(name3 + ".mseed")



        name = merge_folder + '/' + str(start_time) + '_' + gparam['project_name']
        name2 = name.replace('.', '-')
        name3 = name2.replace(':', '-')
        #merge_folder + '/' + str(start_time) + '_' + gparam['project_name'] + ".h5"

        new_file = pyasdf.ASDFDataSet(name3 + ".h5",
                                      compression="gzip-3")


        name = merge_folder + '/' + gparam['project_name'] + str(start_time)
        name2 = name.replace('.', '-')
        name3 = name2.replace(':', '-')
        #merge_folder + '/' + gparam['project_name'] + str(start_time) + ".mseed"

        files = glob.glob(name3 + ".mseed")
        for _i, filename in enumerate(files):
            ...
            print("Adding file %i of %i ..." % (_i + 1, len(files)))
            new_file.add_waveforms(filename, tag="raw_recording")

        name = merge_folder + '/' + gparam['project_name'] + str(start_time)
        name2 = name.replace('.', '-')
        name3 = name2.replace(':', '-')
        #merge_folder + '/' + gparam['project_name'] + str(start_time) + ".mseed"
        os.remove(name3 + ".mseed")

        last_merge += filenumber

        if last_merge+filenumber>len(new_files):
            filenumber = len(new_files) - last_merge

