# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
'''Read data from an array to a ASDF file.
Create a new file when needed.
'''
import time
import logging
import os
import io

from ctypes import c_int32

from math import floor
from obspy.core import Stream, Trace, UTCDateTime
from obspy.core.inventory import Longitude, Latitude

import pyasdf

from dug_seis.acquisition.flat_response_stationxml import get_flat_response_inventory

logger = logging.getLogger('dug-seis')

class DataToASDF:

    def __init__(self, param):
        self.folder = param['Acquisition']['asdf_settings']['data_folder']
        self.folder_tmp = param['Acquisition']['asdf_settings']['data_folder_tmp']
        if self.folder[len(self.folder)-1] is not '/':
            self.folder += '/'
        if self.folder_tmp[len(self.folder_tmp)-1] is not '/':
            self.folder_tmp += '/'
        self.filename = param['General']['project_name']
        self.compression = param['Acquisition']['asdf_settings']['compression']
        self.file_length_sec = param['Acquisition']['asdf_settings']['file_length_sec']
        self.station_naming = param['Acquisition']['asdf_settings']['station_naming']
        self.vertical_resolution = param['Acquisition']['hardware_settings']['vertical_resolution']
        self.l_notify_size = c_int32(param['Acquisition']['bytes_per_transfer'])

        self.stats = {
            'network': param['General']['stats']['network'],
            'station': '099',
            'location': '00',
            'channel': '001',
            'starttime': UTCDateTime().timestamp,
            'sampling_rate': param['Acquisition']['hardware_settings']['sampling_frequency'],
            'gain': '0'
        }

        self._sampling_rate = param['Acquisition']['hardware_settings']['sampling_frequency']
        self._input_range = param['Acquisition']['hardware_settings']['input_range']
        self._sensor_coords = param['General']['sensor_coords']
        self._sensor_count = param['General']['sensor_count']
        # nr of channels & 16 bit = 2 bytes
        self._nr_of_datapoints = floor(self.l_notify_size.value / 16 / 2)
        self._file_handle = None
        self._time_age_of_file = 0      # keeps track internally how old the file is
        self._last_used_file_name = None
        self._really_verbose_timing_output = False

    def _check_if_folders_exist_create_if_needed(self):
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder)
            logger.info('creating folder: {}'.format(self.folder))

        if not os.path.isdir(self.folder_tmp):
            os.makedirs(self.folder_tmp)
            logger.info('creating folder_tmp: {}'.format(self.folder_tmp))

    def _create_new_file(self):
        '''Creates a new file.
        With parameters of the DataToAsdf class. Sets the age of the file to time.time().'''

        file_name = '{0}_{1}.h5'.format(UTCDateTime(), self.filename)
        file_name = file_name.replace(':', '_')
        folder_file_name = '{0}{1}'.format(self.folder_tmp, file_name)
        # print('_create_new_file with folder_file_name = {0}'.format(folder_file_name))
        logger.info('_create_new_file with folder_file_name = {0}'.format(folder_file_name))

        self._time_age_of_file = time.time()
        # logger.info('self.compression = {}, type = {}'.format(
        #     self.compression, type(self.compression)))
        if self.compression == 'None':
            # logger.info('if self.compression = None: -> true')
            self._file_handle = pyasdf.ASDFDataSet(folder_file_name, compression=None)
        else:
            self._file_handle = pyasdf.ASDFDataSet(folder_file_name, compression=self.compression)

        if self._last_used_file_name is not None:
            os.rename(self.folder_tmp + self._last_used_file_name,
                      self.folder + self._last_used_file_name)
        self._last_used_file_name = file_name

        self._add_all_station_xml_s(self._file_handle)

    def _create_new_file_if_needed(self):
        # check if file_handle exists
        if self._file_handle is None:
            # logger.info('no file found creating new file.\n')
            self._check_if_folders_exist_create_if_needed()
            self._create_new_file()

        # check if file is too old
        if self._time_age_of_file + self.file_length_sec < time.time():
            # logger.info('file too old, creating new file.\n')
            self._create_new_file()

    def _add_all_station_xml_s(self, ds):
        for i in range(self._sensor_count):
            ds.add_stationxml(self._create_station_xml(i))

    def _create_station_xml(self, channel_nr):
        # print('channel_nr = {}, len(self._sensor_coords) = {}'.format(
        #     channel_nr, len(self._sensor_coords)))

        inv = get_flat_response_inventory(
            # conversion 16bit int to mV
            sensitivity_value=self._input_range[channel_nr] * 2 / (
                2 ** self.vertical_resolution),
            sensitivity_frequency=1.0,
            input_units='M/S',                                          # ?
            output_units='Counts',                                      # ?
            creation_date=UTCDateTime(self._time_age_of_file),
            network_code=self.stats['network'],
            station_code=self._get_station_name(channel_nr),
            location_code=self.stats['location'],
            channel_code=self.stats['channel'],
            sampling_rate=self.stats['sampling_rate'],
            latitude=Latitude(self._sensor_coords[channel_nr][1]),      # from here on ?
            longitude=Longitude(self._sensor_coords[channel_nr][0]),
            depth=self._sensor_coords[channel_nr][2],
            elevation=0.0,
            azimuth=0.0,
            dip=0.0)

        # Test if the response makes up a valid StationXML file.
        with io.BytesIO() as buf:
            inv.write(buf, format='stationxml', validate=True)

        return inv

    def _get_station_name(self, channel_nr):
        return str(self.station_naming[channel_nr]).zfill(3)

    def data_to_asdf(self, np_data_list):

        time_start_buffer_data_available = time.time()

        stream = Stream()

        card_nr = 0
        for np_data in np_data_list:
            time_tmp = time.time()

            for i in range(16):
                self.stats['station'] = self._get_station_name(i + 16 * card_nr)

                # without transpose np_data[:, i]
                stream += Trace(np_data[i], header=self.stats)
                # logger.info('{}, {}\n'.format(self.stats['station'], self.stats['starttime']))

            del np_data
            if self._really_verbose_timing_output:
                logger.debug('stream += Trace: {0:.3f} sec, '.format(time.time() - time_tmp))

            card_nr += 1

        time_tmp = time.time()
        self._create_new_file_if_needed()
        if self._really_verbose_timing_output:
            logger.debug('_create_new_file_if_needed(): {0:.3f} sec, '.format(
                         time.time() - time_tmp))
        time_tmp = time.time()

        self._file_handle.append_waveforms(stream, tag='raw_recording')
        if self._really_verbose_timing_output:
            logger.debug('append_waveforms: {0:.3f} sec'.format(time.time() - time_tmp))

        # starttime for next segment
        self.stats['starttime'] = UTCDateTime(self.stats['starttime']) +\
            self._nr_of_datapoints / self._sampling_rate
        # logger.info('self.stats[ starttime ] = {}'.format(self.stats['starttime']))

        del stream
        if self._really_verbose_timing_output:
            logger.debug('end of data_to_asdf.py cycle used time: {0:.3f} sec'
                          .format(time.time() - time_start_buffer_data_available))
