# DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
# example from lion HowTo generate a StationXML file
#
# ObsPy StationXML:             https://docs.obspy.org/tutorial/code_snippets/stationxml_file_from_scratch.html
# pyasdf adding StationXML:     http://seismicdata.github.io/pyasdf/tutorial.html#adding-station-information
# pyasdf reading StationXML:    http://seismicdata.github.io/pyasdf/tutorial.html#reading-waveforms-and-stationxml

import io
import obspy

from obspy.core.inventory import (Longitude, Latitude)
from dug_seis.acquisition.flat_response_stationxml import get_flat_response_inventory

tr = obspy.read()[0]

inv = get_flat_response_inventory(
    sensitivity_value=200.0,
    sensitivity_frequency=1.0,
    input_units="M/S",
    output_units="Counts",
    creation_date=obspy.UTCDateTime(2012, 1, 1),
    network_code=tr.stats.network,
    station_code=tr.stats.station,
    location_code=tr.stats.location,
    channel_code=tr.stats.channel,
    sampling_rate=tr.stats.sampling_rate,
    latitude=Latitude(0.0),
    longitude=Longitude(0.0),
    depth=0.0,
    elevation=0.0,
    azimuth=0.0,
    dip=0.0)

# Test if the response makes up a valid StationXML file.
with io.BytesIO() as buf:
    inv.write(buf, format="stationxml", validate=True)

inv.plot_response(0.001)

# Now plot the trace once before and once after
# removing the response.
tr.plot()
tr.remove_response(inventory=inv)
tr.plot()

# end lion
# test file generation

import pyasdf

ds = pyasdf.ASDFDataSet("test_file.h5", compression="gzip-3")
print(ds)
ds.add_waveforms(tr, tag="raw_recording")
print(ds)
ds.add_stationxml(inv)

print(ds.waveforms.BW_RJOB)
print(ds.waveforms.BW_RJOB.raw_recording)
print(ds.waveforms.BW_RJOB.StationXML)

# ds.waveforms.XB_001.StationXML.plot_response(1)