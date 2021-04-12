# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
"""Manages the different hardware components. Calls the data transfer periodically.
- state machine
- restart
- help to hardware problems
- simulation of data
"""
import time
import logging

from dug_seis.util import redis_get_ac_continue
from dug_seis.acquisition.one_card import Card
from dug_seis.acquisition.star_hub import StarHub
from dug_seis.acquisition.data_to_asdf import DataToASDF

from dug_seis.acquisition.hardware_mockup import SimulatedHardware

logger = logging.getLogger('dug-seis')

def run(param):
    bytes_per_transfer = param['Acquisition']['bytes_per_transfer']
    simulation_mode = param['Acquisition']['simulation_mode']

    # make classes
    card1 = Card(param, 0)
    card2 = Card(param, 1)
    star_hub = StarHub()

    # simulate hardware if in simulation mode
    if simulation_mode:
        simulated_hardware1 = SimulatedHardware(param)
        simulated_hardware2 = SimulatedHardware(param)
        simulated_hardware1.mock_card(card1)
        simulated_hardware2.mock_card(card2)
        simulated_hardware1.mock_starhub(star_hub)

    # try close, in case the last run was aborted ...
    card1.close()
    card2.close()
    star_hub.close()

    # init setup
    card1.init_card(param)
    card2.init_card(param)
    star_hub.init_star_hub([card1, card2])

    # start
    star_hub.start()
    data_to_asdf = DataToASDF(param)    # this has to be close to start(), it will set the starttime in the asdf file

    # wait?
    # card1.wait_for_data()
    # card2.wait_for_data()

    # read status, no actions planned at the moment
    # the read status function will print() if there is a problem ...
    card1.read_status()
    card2.read_status()

    time_stamp_this_loop = time.time()
    while redis_get_ac_continue():
        # polling scheme here, might not be the best?

        if card1.nr_of_bytes_available() >= bytes_per_transfer:
            # print("card1 data ready to be read: {} bytes ready".format(card1.nr_of_bytes_available()))
            if card2.nr_of_bytes_available() >= bytes_per_transfer:
                # print("card 1 & 2 data ready to be read")
                # print("card2 data ready to be read: {} bytes ready".format(card2.nr_of_bytes_available()))

                timestamp_before_eval = time.time()
                data_to_asdf.data_to_asdf([card1.read_data(), card2.read_data()])
                card1.data_has_been_read()
                card2.data_has_been_read()
                logger.debug("loop took: {:.2f} sec, processing for: {:.2f} -> {}%"
                              .format(time.time()-time_stamp_this_loop, time.time()-timestamp_before_eval,
                              int((time.time() - timestamp_before_eval)/(time.time() - time_stamp_this_loop)*100.0)))
                time_stamp_this_loop = time.time()
            else:
                time.sleep(0.1)
                # print("had time to sleep here (inner loop)")
        else:
            time.sleep(0.1)
            # print("had time to sleep here {}, {}".format(card1.nr_of_bytes_available(), bytes_per_transfer))

    # shutdown (is this optional?)
    card1.stop_recording()
    card2.stop_recording()

    card1.close()
    card2.close()
    star_hub.close()
