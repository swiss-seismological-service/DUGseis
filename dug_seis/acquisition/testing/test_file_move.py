# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
"""Test how to move a file.
- Check if directory exists
- Move file"""


import os


folder = "test/"
folder_tmp = "test/tmp/"
filename = "file.foo"

if not os.path.isdir(folder):
    os.makedirs(folder)
    print("creating folder: {}".format(folder))

if not os.path.isdir(folder_tmp):
    os.makedirs(folder_tmp)
    print("creating folder_tmp: {}".format(folder_tmp))

os.rename(folder_tmp+filename, folder+filename)
# os.rename(folder+filename, folder_tmp+filename)
# os.rename("test/tmp/file.foo", "test/tmp2/file.foo")

