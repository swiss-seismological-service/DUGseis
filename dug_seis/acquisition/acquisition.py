'''
Acquisition module of DUG-Seis


# Copyright (c) 2018 by SCCER-SoE and SED at ETHZ

Version 0.0, 23.10.2018, Joseph Doetsch (doetschj)
             23.10.2018, Thomas Haag (thaag)

'''


import datetime
import logging
import os
import oyaml as yaml
import sys

# import dug_seis.gui.gui_util as gui_util
import dug_seis.acquisition.card_manager as card_manager

logger = None


def acquisition_(param):
    return
    global logger
    logger = gui_util.setup_ac_logging(param['General']['acquisition_folder'])
    logger.info('Acquisition script started')
    logger.info('==========================')
    # print('logger name: ' + logger.name);
    # print('logger level: ' + logging.getLevelName(logger.level));

    # should be False, or no real data is recorded when True!
    param['Acquisition']['simulation_mode'] = False
    # 32 * 1024 * 1024   # in bytes (amount of data processed per python call)
    param['Acquisition']['bytes_per_transfer'] = 33554432
    # 128 * 1024 * 1024 # in bytes (computer memory reserved for data)
    param['Acquisition']['hardware_settings']['ram_buffer_size'] = 134217728
    # ms, when during this time not transfer_size data is available -> timeout
    param['Acquisition']['hardware_settings']['timeout'] = 8000
    # store Data as 16 or 32 bit in the ASDF file
    param['Acquisition']['hardware_settings']['use_16_bit_mode'] = False
    # amount of generated data for simulation: 0...4
    # 0 = fastest, only zeroes used, will lead to high compression rate
    #   -> small files, low load
    # 4 = slow, all channels with sine, sawtooth and random data filled
#   -> "worst cast data"
    param['Acquisition']['simulation_amount'] = 1

    _check_if_hardware_needs_to_be_simulated(param)
    _write_used_param_to_log_recursive(param, 'Acquisition')
    card_manager.run(param)


def _check_if_hardware_needs_to_be_simulated(param):
    if param['Acquisition']['simulation_mode']:
        logger.warning(
            'param["Acquisition"]["simulation_mode"] = True, this is for'
            ' testing purposes only. This setting should never be pushed to'
            ' Git, the real system does only record simulated data this way.'
            ' A computer without the acquisition hardware will detect the missing'
            ' hardware and ask to change to the simulation mode automatically.'
        )
        input('...')
    else:
        if _check_if_hardware_driver_can_be_loaded():
            logger.info('Hardware driver found, running on real hardware')
        else:
            # user_input = input('\nCould not load hardware driver,'
            #     + ' to simulate hardware press: enter or (y)es?')
            # if (user_input == 'y' or user_input == 'Y'
            #     or user_input == 'yes' or user_input == ''):
            if True:
                param['Acquisition']['simulation_mode'] = True
                logger.info('Could not load hardware driver,'
                            'user requested simulation of hardware.')
            else:
                logger.info('Could not load hardware driver, user abort.')
                return


def _check_if_hardware_driver_can_be_loaded():
    if os.path.isfile('c:\\windows\\system32\\spcm_win64.dll') or os.path.isfile(
            'c:\\windows\\system32\\spcm_win32.dll'):
        return True
    else:
        return False


def _write_used_param_to_log_recursive(param_dict, sub_group):
    for key, value in param_dict.items():
        if key == sub_group or sub_group == '':
            if type(value) == dict:
                # print('next call, key:{}, value:{}'.format(key, value))
                _write_used_param_to_log_recursive(value, '')
            else:
                # print('{}: {}'.format(key, value))
                logger.info('{}: {}'.format(key, value))


if __name__ == '__main__':
    # This module is meant to be called exclusively by gui.py
    # therefore no validation is needed here.
    with open(sys.argv[1]) as file_handle:
        param = yaml.load(file_handle, Loader=yaml.FullLoader)

    os.chdir(param['General']['acquisition_folder'])
    acquisition_(param)
