"""
Example processing script for loading and analysing AE waveform data from the prelimAE array of the FEAR project
"""
from obspy import UTCDateTime
import obspy
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

st = project.waveforms.get_waveforms(
    channel_ids=["XB.01.03.001", "XB.01.04.001"],
    start_time=project.config['temporal_range']['start_time'],
    end_time=project.config['temporal_range']['end_time'],
)



# %% Visualise single trace
st_c = st.copy()
tr = st_c[0]

# Trim to shorter duration
ts = tr.stats.starttime
tr.trim(ts, ts + 0.1)
tr.plot()
tr.spectrogram()

# Filter out high frequencies and check effect on waveform and spectrogram
tr.plot()
tr.filter("lowpass", freq=20000, corners=2)
tr.spectrogram()




# %% Visualise multiple traces
fig = plot_time_waveform(st)
fig.show()

# Trim to shorter duration
st2 = st.copy()
st2.trim(ts, ts + 0.1)
fig = plot_time_waveform(st2)
fig.show()

# Filter out high frequencies and check effect on waveform and spectrogram
st2.filter("lowpass", freq=2000, corners=2)
fig = plot_time_waveform(st2)
fig.show()




# More interesting plots
# . Customise spectrograms
# . Plot amplitude and phase spectra
# . Plot amplitude spectra of multiple time segments in same plot
