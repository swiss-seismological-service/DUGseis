from dug_seis.project.project import DUGSeisProject
from obspy.core import UTCDateTime


#folder = "/home/user/mrosskopf/Projects/CODES/"
#project = DUGSeisProject(config=folder + "DUGseis_example.yaml")
project = DUGSeisProject(config="/Users/mameier/programs/seismo/projects/bedretto/DUGseis/scripts/mam/DUGseis_example.yaml")

interval_start = UTCDateTime(2022,2,3,21,30)
interval_end = UTCDateTime(2022,2,3,22)

st_event = project.waveforms.get_waveforms(
            channel_ids=all_channels,
            start_time=interval_start,
            end_time=interval_end,
        )
