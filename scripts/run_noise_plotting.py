# flake8: noqa
"""
Example script demonstrating how a two stage processing would be run.

This is not a valid script but demonstrates the idea.
"""
from obspy.core import UTCDateTime

# Import from the DUGSeis library.
from dug_seis.project.project import DUGSeisProject
from dug_seis import util
from dug_seis.plotting.plotting import plot_time_waveform,\
                                        plot_time_characteristic_function,\
                                        plot_waveform_characteristic_function

# Load project.
project = DUGSeisProject(config="dug_seis_example_4_acquisition_systems.yaml")


# Loop over waveforms
intervals = util.compute_intervals(
    project=project, interval_length_in_seconds=5, interval_overlap_in_seconds=0.1
)

print("data between: {0} and {1}".format(UTCDateTime(intervals[0][0]), UTCDateTime(intervals[-1:][0][1])))

noise_start = UTCDateTime('2021-08-24T14:38:00.000000Z')
noise_interval = 0.002

# load stream data
# all channels: project.waveforms.channel_list
st_noise = project.waveforms.get_waveforms(
        channel_ids=[
            "XB.01.31.001",
            "XB.01.32.001",
            "XB.02.31.001",
            "XB.02.32.001",
            "XB.03.30.001",
            "XB.03.31.001",
            "XB.03.32.001",
            "XB.04.31.001",
            "XB.04.32.001"],
        start_time=noise_start,
        end_time=noise_start + noise_interval)


fig1 = plot_time_waveform(st_noise)
fig1.set_size_inches(8.27, 11.69)
fig1.show()
fig1.savefig('test_1.png')


fig2 = plot_time_characteristic_function(st_noise, 70, 700)
fig2.set_size_inches(8.27, 11.69)
fig2.show()
fig2.savefig('test_2.png')


fig3 = plot_waveform_characteristic_function(st_noise, 70, 700)
fig3.set_size_inches(11.69, 8.27)
fig3.show()
fig3.savefig('test_3.png')
