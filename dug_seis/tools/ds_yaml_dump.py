'''
Print a YAML dump
'''

import sys
import yaml

fh = open(sys.argv[1])
param = yaml.load(fh, Loader=yaml.FullLoader)
fh.close()

if len(sys.argv) == 3:
    print(f'only "{sys.argv[2]}"\n')
    print(yaml.dump(param[sys.argv[2]]))
else:
    print(yaml.dump(param))
