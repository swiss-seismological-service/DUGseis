#!/usr/bin/env python
# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

import yaml

with open("config/dug-seis.yaml", 'r') as stream:
    try:
        param = yaml.safe_load(stream)
        print(param)

    except yaml.YAMLError as exc:
        print(exc)
