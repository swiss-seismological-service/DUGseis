# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

import os
import pyasdf
from scipy.io import savemat
# from obspy.core import read

file_list = []
for file in os.listdir("c:/20190206_sw_test"):
    if file.endswith(".h5"):
        file_list.append(os.path.join("/20190206_sw_test", file))
        # print(os.path.join("/20181107_sw_test", file))
file_list.sort(reverse=True)
load_file = file_list[0]
print("loading latest file: {}".format(load_file))

ds = pyasdf.ASDFDataSet(load_file)
print(ds.events)
print(ds.waveforms.list())

several_channels = ds.waveforms["XM.001"].raw_recording
several_channels += ds.waveforms["XM.001"].raw_recording
several_channels += ds.waveforms["XM.001"].raw_recording


dt = ds.waveforms["XM.001"].raw_recording[0].stats.starttime
several_channels.plot(size=(800, 600))
# three_channels.plot(size=(800, 600), starttime=dt, endtime=dt+0.02)

# gap at 5.2429 sec? 32 Mb buffer
# several_channels.plot(size=(800, 600), starttime=dt + 5.241, endtime=dt + 5.245)

several_channels.plot(size=(800, 600), starttime=dt + 4, endtime=dt + 5.42)

for i, tr in enumerate(several_channels):
    # for i, tr in enumerate(ds.waveforms["XG.001"].raw_recording):
    mdict = {k: str(v) for k, v in tr.stats.items()}
    mdict['data'] = tr.data
    folder = 'matlab'
    if not os.path.isdir(folder):
        os.makedirs(folder)
        print("creating folder: {}".format(folder))
    savemat(folder + "/" + "data-%d.mat" % i, mdict)

"""
# direct:
# ds.waveforms["XG.003"].raw_recording.plot()

print(ds.events)
print(ds.waveforms.list())

station = ds.waveforms["XG.003"]
print(station)
print(station.get_waveform_tags())

stream = station.raw_recording
print(stream)

stream.plot()

dt = stream[0].stats.starttime
stream.plot(starttime=dt, endtime=dt+0.01)

three_channels = ds.waveforms["XG.000"].raw_recording
three_channels += ds.waveforms["XG.001"].raw_recording
three_channels += ds.waveforms["XG.002"].raw_recording
three_channels += ds.waveforms["XG.003"].raw_recording
three_channels.plot(size=(800, 600))
"""
