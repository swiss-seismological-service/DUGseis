# DUG-Seis Statelevel picker
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import pandas as pd
from obspy.core import UTCDateTime
from obspy import Stream
import os
import time
import pyasdf
import numpy as np
import scipy
from obspy import read, Trace

def statelevel(y, n):

    ymax=max(y)
    ymin=min(y)-np.finfo(float).eps

    idx = np.ceil(n * (y - ymin) / (ymax - ymin))

    idx= [x for x in idx if 1 <= x <= n-1]


    histogram = np.zeros(n)
    for i in range(0,len(idx)):
        histogram[int(idx[i])]=histogram[int(idx[i])] + 1

    # Compute Center of Each Bin
    ymin = min(y)
    Ry = ymax - ymin
    dy = Ry / n

    verm=[x-0.5 for x in range(1, n + 1)]
    bins = ymin + [x * dy for x in verm]

    # compute statelevels
    iLowerRegion = next(x[0] for x in enumerate(histogram) if x[1] > 0) #find(histogram > 0, 1, 'first');
    histogram2=histogram[::-1]
    iUpperRegion = len(histogram2) - next(x[0] for x in enumerate(histogram2) if x[1] > 0) - 1  #find(histogram > 0, 1, 'last');

    iLow = iLowerRegion #iLowerRegion[0]
    iHigh = iUpperRegion #iUpperRegion[0]

    lLow  = int(iLow)
    lHigh = int(iLow + np.floor((iHigh - iLow)/2))
    uLow  = int(iLow + np.floor((iHigh - iLow)/2))
    uHigh = int(iHigh)

    # Upper and lower histograms
    lHist = histogram[lLow:lHigh]
    uHist = histogram[uLow:uHigh]

    levels = np.zeros(2)
    iMax = max(lHist[1:])
    iMin = max(uHist)
    levels[0] = ymin + dy * (lLow + iMax - 1.5)
    levels[1] = ymin + dy * (uLow + iMin - 1.5)




    return(levels,histogram)

