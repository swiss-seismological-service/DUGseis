# DUG-Seis picker
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

# flake8: noqa

from obspy.core import UTCDateTime
from obspy import Stream
import os
import time
import pyasdf
import numpy as np
import scipy
from obspy import read, Trace
from .Statelevels import statelevel

# from matplotlib import pyplot as plt


def pphasepicker(input, Tn, xi):
    dt = 1 / input.stats.sampling_rate

    # x_d = input.detrend(type='simple')
    x_d = input

    # # Construct a fixed-base viscously damped SDF oscillator
    omegan = 2 * np.pi / Tn
    # natural frequency in radian/second
    C = 2 * xi * omegan  # viscous damping term
    K = omegan ** 2  # stiffness term
    # y(:,1) = [0;0]             # response vector
    y = np.array([[0, 0]])

    # % Solve second-order ordinary differential equation of motion
    A = np.array([[0, 1], [-K, -C]])
    Ae = scipy.linalg.expm(A * dt)
    koek = (Ae - np.eye(2)) * np.array([0, 1])
    equal = (Ae - np.eye(2)) * np.array([0, 1])
    b = equal[:, 1]

    num_vars = A.shape[1]
    rank = np.linalg.matrix_rank(A)
    if rank == num_vars:
        AeB = np.linalg.lstsq(A, b)[0]  # not under-determined
    else:
        for nz in combinations(range(num_vars), rank):  # the variables not set to zero
            try:
                AeB = np.zeros((num_vars, 1))
                AeB[nz, :] = np.asarray(np.linalg.solve(A[:, nz], b))

            except np.linalg.LinAlgError:
                pass

    # ind_peak = np.where(abs(x_d.data) == max(abs(x_d.data)))
    # tot = np.asscalar(ind_peak[0])
    xnew = Stream()
    xnew_trace = Trace(x_d.data)
    xnew.append(xnew_trace)

    for k in range(1, len(xnew.traces[0].data)):
        y = np.concatenate(
            (y, [np.matmul(Ae, y[k - 1]) + AeB * xnew.traces[0].data[k]])
        )  # check

    veloc = y[:, 1]  # relative velocity of mass
    Edi = 2 * xi * omegan * veloc ** 2
    # integrand of viscous damping energy

    # appy histogram method
    nbins = int(np.ceil(2 / dt))
    levels, histograms = statelevel(Edi, int(nbins))
    R = levels

    locs = [x for (x, val) in enumerate(Edi) if val > R[0]]  # find(Edi > R(1));

    indx_1 = (
        xnew.traces[0].data[0 : int(locs[0]) - 1]
        * xnew.traces[0].data[1 : int(locs[0])]
    )
    indx = [x for (x, val) in enumerate(indx_1) if val < 0]
    if indx:
        loc = indx[-1] * dt
    else:
        loc = "nopick"

    return loc
