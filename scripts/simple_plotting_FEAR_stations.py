"""
Example processing script.
"""
from obspy import UTCDateTime

# Import from the DUGSeis library.
from dug_seis.project.project import DUGSeisProject
import dug_seis.plotting.plotting as ds_plt

import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('Qt5Agg')

# Load the DUGSeis project.
project = DUGSeisProject(config="run_processing_FEAR_stations.yaml")

# adjust start and end times of data snipped you'd like to load (need to be within the range set in the project .yaml)
project.config['temporal_range']['start_time'] = UTCDateTime('2022-11-20T10:50:00.000000Z')
project.config['temporal_range']['end_time'] = UTCDateTime('2022-11-20T10:50:30.000000Z')

# load data
st_data = project.waveforms.get_waveforms(
        channel_ids=[
            "XB.01.01.001",
            "XB.01.02.001",
            "XB.01.03.001",
            "XB.01.04.001",
            "XB.01.05.001",
            "XB.01.06.001",
            "XB.01.07.001",
            "XB.01.08.001",
        ],
        start_time=project.config['temporal_range']['start_time'],
        end_time=project.config['temporal_range']['end_time'],
    )

# plot data
st_data.plot()

fig1 = ds_plt.plot_time_waveform(st_data, markers="no")
fig1.set_size_inches(ds_plt.cm_to_inch(21), ds_plt.cm_to_inch(29.7))
fig1.show()

fig2 = ds_plt.plot_waveform_characteristic_function(st_data, 70, 700)
fig2.set_size_inches(ds_plt.cm_to_inch(21), ds_plt.cm_to_inch(29.7))
fig2.show()
