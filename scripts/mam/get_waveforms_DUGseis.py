from dug_seis.project.project import DUGSeisProject
from obspy.core import UTCDateTime


#folder = "/home/user/mrosskopf/Projects/CODES/"
#project = DUGSeisProject(config=folder + "DUGseis_example.yaml")
project = DUGSeisProject(config="/Users/mameier/programs/seismo/projects/bedretto/DUGseis/scripts/mam/DUGseis_example.yaml")
database = project.db


interval_start = UTCDateTime('2022-02-03T21:30:00')
interval_end = UTCDateTime('2022-02-03T21:30:05')

#channel_ids=["XB.02.01.001"]
channel_ids='all_channels'

print(interval_end)

st_event = project.waveforms.get_waveforms(
            channel_ids=["XB.02.03.001","XB.03.01.001",],
            start_time=interval_start,
            end_time=interval_end,
        )
print('coucou!')
