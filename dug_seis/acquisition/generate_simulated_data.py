# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

import random
import time
import logging

from math import sin
from ctypes import create_string_buffer

logger = logging.getLogger('dug-seis')

def generate_data_for_pv_buffer(size, amount):
    # amount can be 0...4
    pv_buffer = create_string_buffer(size)
    fill_percent = 2  # 100 fills up all buffer
    ts = time.time()

    if amount == 0:
        logger.info("pv_buffer with no data, all zero, will lead to high compression rate -> small files, low load")

    if amount > 2:
        logger.info("generating random data for all channels storing in RAM ringbuffer: pv_buffer")
        if amount > 3:
            fill_percent = 100
        logger.info("only filling up {}% of buffer, to speed things up".format(fill_percent))
        logger.info("the part which is not filled is 0 and leads to a high compression rate -> small files, low load")
        for i in range(int(len(pv_buffer) * fill_percent / 100)):
            pv_buffer[i] = random.randrange(0, 255)
            if time.time() > ts:
                logger.info("all channels random. i: {}, {}%".format(i, int(i / size * 100)))
                ts = time.time() + 2
    # return pv_buffer
    fill_percent = 100  # 100 fills up all buffer

    if amount > 0:
        # for j in range(0, 32, 2):
        #     channel_byte_offset = j
        channel_byte_offset = 0  # 0 is channel 0
        for i in range(0 + channel_byte_offset, int(len(pv_buffer) * fill_percent / 100) + channel_byte_offset, 32):
            value = int(sin(i / 1100000) * 20000)
            pv_buffer[i] = value & 0xff
            pv_buffer[i + 1] = (value >> 8) & 0xff
            if time.time() > ts:
                logger.info("channel 0 and 16 sine wave 20000 amplitude. i: {}, {}%".format(i, int(i / size * 100)))
                ts = time.time() + 2

    if amount > 1:
        channel_byte_offset = 2  # 2byte offset = next channel, reordering leads to channel 002
        value = 0
        for i in range(0 + channel_byte_offset, int(len(pv_buffer) * fill_percent / 100) + channel_byte_offset, 32):
            pv_buffer[i] = value & 0xff
            pv_buffer[i + 1] = (value >> 8) & 0xff
            value += 1
            if time.time() > ts:
                logger.info("channel 1 and 18 ramp upwards, +1 per time step.i:{}, {}%".format(i, int(i / size * 100)))
                ts = time.time() + 2

    if amount > 1:
        channel_byte_offset = 4
        for i in range(0 + channel_byte_offset, int(len(pv_buffer) * fill_percent / 100) + channel_byte_offset, 32):
            value = int(sin(i / 1100000 * 0.6) * 32768)
            pv_buffer[i] = value & 0xff
            pv_buffer[i + 1] = (value >> 8) & 0xff
            if time.time() > ts:
                logger.info("channel 4 and 20 sine wave 32768 amplitude. i: {}, {}%".format(i, int(i / size * 100)))
                ts = time.time() + 2

    logger.info("generation for this card finished")
    return pv_buffer
