# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
"""
- removing a bunch of lines out of one_card.py to make it slimmer
- not sure if this is a clever idea, i guess we will see
"""
import logging
import dug_seis.acquisition.hardware_driver.regs as regs

from dug_seis.acquisition.hardware_driver.pyspcm import spcm_hOpen, spcm_dwGetParam_i32
from dug_seis.acquisition.hardware_driver.pyspcm import spcm_dwSetParam_i32, spcm_dwGetContBuf_i64
from dug_seis.acquisition.hardware_driver.pyspcm import spcm_dwDefTransfer_i64
from dug_seis.acquisition.hardware_driver.pyspcm import SPCM_BUF_DATA, SPCM_DIR_CARDTOPC

from ctypes import c_int32, c_uint64
from ctypes import create_string_buffer, byref, c_void_p

logger = logging.getLogger('dug-seis')

def sz_type_to_name(l_card_type):
    """sz_type_to_name: doing name translation."""

    l_version = (l_card_type & regs.TYP_VERSIONMASK)
    if (l_card_type & regs.TYP_SERIESMASK) == regs.TYP_M2ISERIES:
        s_name = 'M2i.%04x' % l_version
    elif (l_card_type & regs.TYP_SERIESMASK) == regs.TYP_M2IEXPSERIES:
        s_name = 'M2i.%04x-Exp' % l_version
    elif (l_card_type & regs.TYP_SERIESMASK) == regs.TYP_M3ISERIES:
        s_name = 'M3i.%04x' % l_version
    elif (l_card_type & regs.TYP_SERIESMASK) == regs.TYP_M3IEXPSERIES:
        s_name = 'M3i.%04x-Exp' % l_version
    elif (l_card_type & regs.TYP_SERIESMASK) == regs.TYP_M4IEXPSERIES:
        s_name = 'M4i.%04x-x8' % l_version
    elif (l_card_type & regs.TYP_SERIESMASK) == regs.TYP_M4XEXPSERIES:
        s_name = 'M4x.%04x-x4' % l_version
    else:
        s_name = 'unknown type'
    return s_name


def init_card(param, card_nr):
    """Initialise card. Setup card parameters. Reserve buffers for DMA data transfer."""
    logger.debug("Initializing card {} sdt_init...".format(card_nr))

    sampling_frequency = param['Acquisition']['hardware_settings']['sampling_frequency']
    qw_buffer_size = c_uint64(param['Acquisition']['hardware_settings']['ram_buffer_size'])
    l_notify_size = c_int32(param['Acquisition']['bytes_per_transfer'])
    timeout = param['Acquisition']['hardware_settings']['timeout']

    input_range = param['Acquisition']['hardware_settings']['input_range']

    """ open card """
    if card_nr == 0:
        h_card = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))
        input_range_this_card = input_range[0:16]
    else:
        h_card = spcm_hOpen(create_string_buffer(b'/dev/spcm1'))
        input_range_this_card = input_range[16:32]
    if h_card is None:
        logger.error("card {} not found...".format(card_nr))
        return -1
        # exit ()

    # read type, function and sn and check for A/D card
    l_card_type = c_int32(0)
    spcm_dwGetParam_i32(h_card, regs.SPC_PCITYP, byref(l_card_type))
    l_serial_number = c_int32(0)
    spcm_dwGetParam_i32(h_card, regs.SPC_PCISERIALNO, byref(l_serial_number))
    l_fnc_type = c_int32(0)
    spcm_dwGetParam_i32(h_card, regs.SPC_FNCTYPE, byref(l_fnc_type))

    s_card_name = sz_type_to_name(l_card_type.value)
    if l_fnc_type.value == regs.SPCM_TYPE_AI:
        logger.info("Found: {0} sn {1:05d}".format(s_card_name, l_serial_number.value))
    else:
        logger.error("Card: {0} sn {1:05d} not supported by example".format(s_card_name, l_serial_number.value))
        return -1

    """ do a simple FIFO setup """

    # all channels enabled (must be 1, 2, 4, 8, 16)
    spcm_dwSetParam_i32(h_card, regs.SPC_CHENABLE,       0xFFFF)

    # ? of pre-trigger data at start of FIFO mode (must be reduced with more channels, see manual for limits)
    spcm_dwSetParam_i32(h_card, regs.SPC_PRETRIGGER,     4)

    # single FIFO mode
    spcm_dwSetParam_i32(h_card, regs.SPC_CARDMODE,       regs.SPC_REC_FIFO_SINGLE)

    # timeout im ms (e.g. 8 sec)
    spcm_dwSetParam_i32(h_card, regs.SPC_TIMEOUT,        timeout)

    # trigger set to software, card will trigger immediately after start
    spcm_dwSetParam_i32(h_card, regs.SPC_TRIG_ORMASK,    regs.SPC_TMASK_SOFTWARE)
    spcm_dwSetParam_i32(h_card, regs.SPC_TRIG_ANDMASK,   0)

    # clock mode internal PLL
    spcm_dwSetParam_i32(h_card, regs.SPC_CLOCKMODE,      regs.SPC_CM_INTPLL)

    # set sample rate
    spcm_dwSetParam_i32(h_card, regs.SPC_SAMPLERATE, sampling_frequency)
    logger.info("using: {0} sps".format(sampling_frequency))

    # no clock output
    spcm_dwSetParam_i32(h_card, regs.SPC_CLOCKOUT, 0)

    # read available ranges
    range_min = c_int32(0)
    range_max = c_int32(0)
    l_number_of_ranges = c_int32(0)
    spcm_dwGetParam_i32(h_card, regs.SPC_READIRCOUNT, byref(l_number_of_ranges))
    logger.debug("card {}: nr of available ranges: {}".format(card_nr, l_number_of_ranges.value))

    for i in range(l_number_of_ranges.value):
        spcm_dwGetParam_i32(h_card, regs.SPC_READRANGEMIN0 + i, byref(range_min))
        spcm_dwGetParam_i32(h_card, regs.SPC_READRANGEMAX0 + i, byref(range_max))
        logger.debug("card {}, range nr {}: {}mV to {}mV".format(card_nr, i, range_min.value, range_max.value))

    # set input range 50, 100, 250, 500, 1000, 2000, 5000, 10000 mV
    selected_range = c_int32(0)
    for i in range(16):
        spcm_dwSetParam_i32(h_card, regs.SPC_AMP0 + i * 100, input_range_this_card[i])

        spcm_dwGetParam_i32(h_card, regs.SPC_AMP0 + i * 100, byref(selected_range))
        logger.info("card {}, channel {} selected range: {}mV".format(card_nr, i, selected_range.value))

    """ define the data buffer """
    # we try to use continuous memory if available and big enough
    pv_buffer = c_void_p()
    qw_cont_buf_len = c_uint64(0)
    spcm_dwGetContBuf_i64(h_card, SPCM_BUF_DATA, byref(pv_buffer),
                          byref(qw_cont_buf_len))
    logger.debug("ContBuf length: {0:d}".format(qw_cont_buf_len.value))

    if qw_cont_buf_len.value >= qw_buffer_size.value:
        logger.info("Using continuous buffer")
    else:
        pv_buffer = create_string_buffer(qw_buffer_size.value)
        logger.info("Using buffer allocated by user program")

    spcm_dwDefTransfer_i64(h_card, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, l_notify_size.value, pv_buffer, c_uint64(0),
                           qw_buffer_size)

    return h_card, pv_buffer
