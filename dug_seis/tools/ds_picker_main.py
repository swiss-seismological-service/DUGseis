'''
1. Write a YAML file
2. Run DUG-Seis with this YAML file
3. Create synopsis file

USAGE
Examples
duse picker aicd 12 '_'  0.04  5  0.78
duse picker p_picker 03  _test   5.5 2.0 70 700


Positional parameters:
1   picker_name             also name of the folder containing YAML template and output folders
2   <number of input files .h5>
3   <working folder of dug_seis, subfolder of /mnt/da/tmp/dug-seis/analysis/>
4   <results_dir_suffix>    string to be appended to results folder

5   …                       parameters specific to the picker
6   …
    …

'''

import sys
import os
import shutil
import glob
import subprocess
from subprocess import call
import pprint

import ds_picker_write_yaml
import ds_picker_synopsis
import ds_picker_histogram
import ds_picker_dot_plots_picks

pp = pprint.PrettyPrinter(indent=2)

'''
sys.argv += ['5.5', '2.0', '8', '60', '12', 'picker4']
sys.argv += ['5.5', '2.0', '12', '60', '12', 'picker4']
sys.argv += ['p_picker', '58', 'picker4', '',    '5.5', '2.0', '70', '700']
sys.argv += ['p_picker', '03', 'picker_check_01', '',     '5.5', '2.0', '70', '700']
'''

print('sys.argv')
pprint.sorted = lambda x, key=None: x
pp.pprint(sys.argv)

args = {
    'picker'        : sys.argv[1],
    'num_src_files' : sys.argv[2],
    'results_suffix': sys.argv[3],
}

if args['picker'] == 'p_picker':
    if len(sys.argv) >= 5:
        params = {
            'threshold_on': sys.argv[4],
            'threshold_off': sys.argv[5],
            'st_window': sys.argv[6],
            'lt_window': sys.argv[7],
        }
    else:
        params = {
            'threshold_on': '5.5',
            'threshold_off': '2.0',
            'st_window': '15',
            'lt_window': '60',
        }
elif args['picker'] == 'aicd':
        params = {
            't_ma'  : sys.argv[4],
            'nsigma': sys.argv[5],
            't_up'  : sys.argv[6],
        }


picker = sys.argv[1]
param_str = ('_').join([str(v) for k, v in params.items()])

cfg = {
    'picker'        : args['picker'],
    'num_src_files' : args['num_src_files'],
    'tools'         : '/home/1/dev/proj/dugseis/devel/processing/analysis/',
    'src'           : f'/mnt/da/tmp/dug-seis/src/Grimsel--{args["num_src_files"]}/',
    # 'calc'          : f'/mnt/da/tmp/dug-seis/analysis/{args["calc_dir"]}/',
    'calc'          : f'/mnt/da/tmp/dug-seis/analysis/{picker}/{param_str}/',
    'param_str'     : param_str,
    'results'       : f'/home/1/dev/proj/dugseis/devel/processing/analysis/{picker}/output/' +
                    #   f'{args["num_src_files"]}-sourcefiles-sta-lta-v2/{param_str}/',
                    #   f'{args["num_src_files"]}-sourcefiles-v3/{param_str}/',
                    #   f'{args["num_src_files"]}-sourcefiles-v2/{param_str}/',
                      f'{args["num_src_files"]}-sourcefiles/{param_str}{args["results_suffix"]}/',
}

print('cfg')
print(repr(cfg))
pp.pprint(cfg)

print('params')
pp.pprint(params)

if os.path.isdir(cfg['results']):
    print(f'Der result-Ordner ist schon vorhanden: cfg["results"]')
    sys.exit()

# #######################################################################
# start calculation

# prepare working directory for DUG-Seis
if os.path.isdir(cfg['calc']):
    # delete files in calc directory
    for item in os.listdir(cfg['calc']):
        file = os.path.join(cfg['calc'], item)
        if os.path.isdir(file):
            shutil.rmtree(file)
        else:
            os.remove(file)
elif os.path.isdir(cfg['calc']):
    print(f'Das ist eine Datei: cfg["calc"]')
    sys.exit()
else:
    # create directory
    os.mkdir(cfg['calc'])


ds_picker_write_yaml.write_yaml(params=params, cfg=cfg)


call([
    'python',
    '/home/1/dev/proj/dugseis/devel/DUG-Seis/dug_seis/cmd_line_debug.py',
    cfg['calc'],
])

# create results directory, copy *.csv
os.mkdir(cfg['results'])
for file in glob.glob(cfg['calc'] + r'*csv'):
    shutil.copy(file, cfg['results'])

shutil.copy(cfg['calc'] + 'dug-seis.yaml', cfg['results'])


ds_picker_synopsis.exec(max_diff=0.01,
                          params=params,
                          cfg=cfg,
)

ds_picker_histogram.exec(params=params,
                           cfg=cfg,
                           radius=0.2,
                        #    radius=4,
                        #    only_summary=True,
)

ds_picker_dot_plots_picks.exec(params=params,
                           cfg=cfg,
)

