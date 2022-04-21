from dug_seis.project.project import DUGSeisProject
from obspy.core import UTCDateTime


# folder = "/home/user/mrosskopf/Projects/CODES/"
# project = DUGSeisProject(config=folder + "DUGseis_example.yaml")
project = DUGSeisProject(
    config="/Users/mameier/programs/seismo/projects/bedretto/DUGseis/"
    "scripts/mam/yaml/DUGseis_example.yaml"
)
database = project.db


interval_start = UTCDateTime("2022-02-03T21:30:00")
interval_end = UTCDateTime("2022-02-03T21:30:05")

# channel_ids=["XB.02.01.001"]
# channel_ids='all_channels'
channel_ids = sorted(project.channels.keys())

print(interval_end)
# breakpoint()
st_event = project.waveforms.get_waveforms(
    channel_ids=channel_ids,
    start_time=interval_start,
    end_time=interval_end,
)

print(st_event)
