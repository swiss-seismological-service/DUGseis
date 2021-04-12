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

import obspy

from obspy.core.inventory import (
    Inventory, Network, Station, Channel, Site, Response,
    InstrumentSensitivity, PolesZerosResponseStage, Longitude, Latitude)


def get_flat_response_inventory(
        sensitivity_value: float, sensitivity_frequency: float,
        input_units: str, output_units: str,
        sampling_rate: float,
        creation_date: obspy.UTCDateTime,
        network_code: str, station_code: str,
        location_code: str, channel_code: str,
        latitude: Latitude, longitude: Longitude, elevation: float, depth: float,
        azimuth: float, dip: float,
        site_name: str = "site",
        source_str: str = "self"):
    _inv = Inventory(
        networks=[],
        source=source_str)

    net = Network(
        code=network_code,
        stations=[])

    sta = Station(
        code=station_code,
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        site=Site(name=site_name),
        creation_date=creation_date)

    cha = Channel(
        code=channel_code,
        location_code=location_code,
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        depth=depth,
        azimuth=azimuth,
        dip=dip,
        sample_rate=sampling_rate)

    response = Response(
        instrument_sensitivity=InstrumentSensitivity(
            value=sensitivity_value, frequency=sensitivity_frequency,
            input_units=input_units, output_units=output_units),
        response_stages=[PolesZerosResponseStage(
            stage_sequence_number=1, stage_gain=sensitivity_value,
            stage_gain_frequency=sensitivity_frequency,
            input_units=input_units, output_units=output_units,
            pz_transfer_function_type="LAPLACE (RADIANS/SECOND)",
            normalization_frequency=sensitivity_frequency,
            zeros=[], poles=[]
        )])

    # Now tie it all together.
    cha.response = response
    sta.channels.append(cha)
    net.stations.append(sta)
    _inv.networks.append(net)

    return _inv
