# DUG-Seis ASDF converter
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

from obspy import Stream
import pyasdf
import yaml
import numpy as np
from obspy import read


#name of ASDF file and to be generated GMUG files
name="event1"
n=4096

################
sta = Stream()
sta =read(name+'.h5')

f = open('dug-seis.yaml')
param = yaml.load(f)
stations = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]


hr=sta.traces[0].stats["starttime"].hour
minute=sta.traces[0].stats["starttime"].minute
sec=sta.traces[0].stats["starttime"].second
mil=int(sta.traces[0].stats["starttime"].microsecond/1000)
year=sta.traces[0].stats["starttime"].year
month=sta.traces[0].stats["starttime"].month
day=sta.traces[0].stats["starttime"].day


#print(sta.traces[0].stats["delta"])
data = []
inpl=[]
for i in range(0,len(stations)):
    data.append(sta.traces[i].data[0:n])
    inpl.append(param['Acquisition']['hardware_settings']['input_range'][i])

nsamp=n #len(data[0])
nchan=32
nrec=1
sra=sta.traces[0].stats["delta"] * 1e6

inpl=str(inpl)
inpl = inpl.replace(',', '')
inpl = inpl.replace('[', '')
inpl = inpl.replace(']', '')


triglevel=[40,400,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000] #set to 1000?
triglevel=str(triglevel)
triglevel = triglevel.replace(',', '')
triglevel = triglevel.replace('[', '')
triglevel = triglevel.replace(']', '')

digitmultiplier=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1] #set to 1? #[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] #[
digitmultiplier=str(digitmultiplier)
digitmultiplier = digitmultiplier.replace(',', '')
digitmultiplier = digitmultiplier.replace('[', '')
digitmultiplier = digitmultiplier.replace(']', '')



data = np.asarray(data)
data.astype('int16').tofile(name+'.dat')

newfile=open(name+".txt","w")
with open(name+".txt", 'a') as file:
    file.write("rate[µs], number of records, number of samples, number of channels\n")
    file.write("pre trigger [%], AD resolution [bit]\n")
    file.write("input range [+/- MilliVolts], all channels\n")
    file.write("trigger level [1/1000], all channels\n")
    file.write(str(sra)+"\n") #1.0 or from asdf?
    file.write(str(nrec) + "\n")
    file.write(str(nsamp) + "\n")
    file.write(str(nchan) + "\n")
    file.write(str(30) + "\n") #keep 30%?
    file.write(str(16) + "\n")
    file.write(str(inpl) + "\n")
    file.write(str(triglevel) + "\n")
    file.write("Trans-Channel: 2;  nStack: 1\n")
    file.write("digit multiplier\n")
    file.write(str(digitmultiplier) + "\n")
    file.write("Reserve\n")
    file.write("Reserve\n")
    file.write("     No.      Hour    Minute Second Millis. Year     Month    Day\n")
    file.write("       "+str(1)+"      "+str(hr)+"      "+str(minute)+"      "+str(sec)+"     "+str(mil)+"    "+str(year)+"       "+str(month)+"      "+str(day)+ "\n")




