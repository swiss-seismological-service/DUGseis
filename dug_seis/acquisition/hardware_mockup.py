# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

import logging

import time
from unittest.mock import MagicMock
from math import floor

from dug_seis.acquisition.generate_simulated_data import generate_data_for_pv_buffer

logger = logging.getLogger('dug-seis')

class SimulatedHardware:
    def __init__(self, param):
        self.bytes_available = 0

        self._bytes_per_transfer = param['Acquisition']['bytes_per_transfer']
        self._ram_buffer_size = param['Acquisition']['hardware_settings']['ram_buffer_size']
        self._sampling_frequency = param['Acquisition']['hardware_settings']['sampling_frequency']
        self._use_16_bit_mode = param['Acquisition']['hardware_settings']['use_16_bit_mode']

        self._pv_buffer = generate_data_for_pv_buffer(self._ram_buffer_size, param['Acquisition']['simulation_amount'])
        self._l_pc_pos = 0
        self._timestamp_last_call = time.time()
        # nr of channels & 16 bit = 2 bytes
        self._nr_of_datapoints = floor(param['Acquisition']['bytes_per_transfer'] / 16 / 2)

    def _simulated_nr_of_bytes_available(self):
        # add data, might be more than a transfer can handle
        # self.bytes_available += random.randrange(0, int(self._bytes_per_transfer*1.5))

        # 16 channels, 16 bit = 2 bytes, per sample
        self.bytes_available += int((time.time() - self._timestamp_last_call) * self._sampling_frequency * 16 * 2)
        self._timestamp_last_call = time.time()

        # print("SimulatedHardware, bytes_available: {}".format(self.bytes_available))
        return self.bytes_available

    def _simulated_read_buffer_position(self):
        return self._l_pc_pos

    def _simulated_data_has_been_read(self):
        self.bytes_available -= self._bytes_per_transfer
        self._l_pc_pos += self._bytes_per_transfer
        if self._l_pc_pos == self._ram_buffer_size:
            self._l_pc_pos = 0
        if self._l_pc_pos > self._ram_buffer_size:
            logger.error("Something is wrong, ram_buffer_size should be dividable by bytes_per_transfer")

    def _simulated_init_card(self, param):
        self._timestamp_last_call = time.time()

    def mock_card(self, card):
        card.init_card = self._simulated_init_card
        card.read_status = MagicMock(return_value=None)
        card.nr_of_bytes_available = self._simulated_nr_of_bytes_available
        card._pv_buffer = self._pv_buffer
        card.read_buffer_position = self._simulated_read_buffer_position
        card.data_has_been_read = self._simulated_data_has_been_read

    def mock_starhub(self, hub):
        hub.init_star_hub = MagicMock(return_value=None)
        hub.start = MagicMock(return_value=None)
