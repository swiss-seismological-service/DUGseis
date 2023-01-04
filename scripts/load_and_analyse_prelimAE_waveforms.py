"""
Example processing script for loading and analysing AE waveform data from the prelimAE array of the FEAR project
"""
import logging
from obspy import UTCDateTime

import obspy
import tqdm
import numpy as np

# Import from the DUGSeis library.
from dug_seis.project.project import DUGSeisProject
from dug_seis import util

from dug_seis.plotting.plotting import (
    get_time_vector,
    plot_time_waveform,
    plot_waveform_characteristic_function_magnitude,
    plot_waveform_characteristic_function,
)

# Load the DUGSeis project.
project = DUGSeisProject(config="load_and_analyse_prelimAE_waveforms.yaml")


# Helper function to compute intervals over the project.
intervals = util.compute_intervals(
    project=project, interval_length_in_seconds=60, interval_overlap_in_seconds=0.1
)

st_triggering = project.waveforms.get_waveforms(
    channel_ids=["XB.01.03.001", "XB.01.04.001"],
    start_time=interval_start,
    end_time=interval_end,
)
""" for interval_start, interval_end in tqdm.tqdm(intervals):
    # Run the trigger only on a few waveforms.
    st_triggering = project.waveforms.get_waveforms(
        channel_ids=["XB.01.03.001", "XB.01.04.001"],
        start_time=interval_start,
        end_time=interval_end,
    )

#st_triggering.plot()

# Single out a trace
#tr = st_triggering[0]

# Trim to shorter duration
#dt = tr.stats.starttime
#tr.trim(dt, dt + 0.01)

#tr.plot()
#tr.spectrogram()

t = get_time_vector(st_triggering)
print(t)
plot_time_waveform(st_triggering)


"""


# Customise spectrogram

# Plot amplitude spectrum

