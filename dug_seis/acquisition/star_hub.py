# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
"""Interface to the Star Hub hardware.
Translation between python and the spectrum hardware drive.
The Star Hub is a "wire" connecting every card to every card and can therefore be used to start,
stop and synchronise the cards.

- on "same level" as one_card.py
- initialise star hub
- start cards over star hub
- bundling of several calls to a "higher level one"
"""
import logging
import os.path
import dug_seis.acquisition.hardware_driver.regs as regs

from ctypes import create_string_buffer, byref

from ctypes import c_int32

if os.path.isfile("c:\\windows\\system32\\spcm_win64.dll") or os.path.isfile(
        "c:\\windows\\system32\\spcm_win32.dll"):
    from dug_seis.acquisition.hardware_driver.pyspcm import spcm_hOpen, spcm_dwSetParam_i32, spcm_dwGetParam_i32
    from dug_seis.acquisition.hardware_driver.pyspcm import spcm_dwGetErrorInfo_i32, spcm_vClose
else:
    pass
    # logging at import messes with the later logging settings, no logging needed here
    # logging.warning('star_hub.py: problems loading the hardware driver. simulation still available.')

logger = logging.getLogger('dug-seis')

class StarHub:
    def __init__(self):

        self.h_sync = None

    def init_star_hub(self, card_list):
        """Initialise the star hub."""
        logger.info("init star hub")

        # open handle for star-hub
        self.h_sync = spcm_hOpen(create_string_buffer(b'sync0'))

        logger.debug("star-hub handler:{0}".format(self.h_sync))

        if self.h_sync is None:
            logger.error("Could not open star-hub...")
            return -1

        # setup star-hub
        nr_of_cards = len(card_list)
        spcm_dwSetParam_i32(self.h_sync, regs.SPC_SYNC_ENABLEMASK, (1 << nr_of_cards) - 1)

        # find star-hub carrier card and set it as clock master
        i = 0
        for one_card in card_list:
            l_features = c_int32(0)
            spcm_dwGetParam_i32(one_card.h_card, regs.SPC_PCIFEATURES, byref(l_features))

            l_serial_number = c_int32(0)
            spcm_dwGetParam_i32(one_card.h_card, regs.SPC_PCISERIALNO, byref(l_serial_number))
            # print("card nr i: {0:d}, serial:{1}\n".format(i, l_serial_number.value))

            if l_features.value & (regs.SPCM_FEAT_STARHUB5 | regs.SPCM_FEAT_STARHUB16):
                logger.info("Star hub found on card nr:{}, serial:{}".format(i, l_serial_number.value))
                break
            i += 1

        spcm_dwSetParam_i32(self.h_sync, regs.SPC_SYNC_CLKMASK, (1 << i))

    def start(self):
        """Start all cards using the star-hub handle."""
        dw_error = spcm_dwSetParam_i32(self.h_sync, regs.SPC_M2CMD,
                                       regs.M2CMD_CARD_START | regs.M2CMD_CARD_ENABLETRIGGER | regs.M2CMD_DATA_STARTDMA)
        if dw_error != 0:  # != ERR_OK
            sz_error_text_buffer = create_string_buffer(regs.ERRORTEXTLEN)
            spcm_dwGetErrorInfo_i32(self.h_sync, None, None, sz_error_text_buffer)
            logger.error("sz_error_text_buffer.value: {0}".format(sz_error_text_buffer.value))
            return -1

    def close(self):
        """Close the star hub."""
        if self.h_sync is not None:
            spcm_vClose(self.h_sync)
            logger.info("Star hub closed.")
