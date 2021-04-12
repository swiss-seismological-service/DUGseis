'''
1. Read a CSV file.
2. Select a set of trigger parameters.
3. Write a complete YAML file with these parameters.
'''

import sys


def write_yaml(params, cfg):

    # load YAML template
    fh = open(f'{cfg["tools"]}{cfg["picker"]}/dug_seis_{cfg["picker"]}_template.yaml', 'r')
    template = fh.read()
    fh.close()

    config_text = template.format(
        cfg['src'],
        *list(params.values())
        # params['threshold_on'],
        # params['threshold_off'],
        # params['st_window'],
        # params['lt_window'],
    )

    fh = open(cfg['calc'] + 'dug-seis.yaml', 'w')
    fh.write(config_text)
    fh.close()

