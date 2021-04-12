"""
Script generating StationXML files for use in DUGSeis.
"""
import pathlib
import typing

from obspy.core.inventory import (
    Inventory,
    Network,
    Station,
    Channel,
    Response,
    InstrumentSensitivity,
)

# XML Namespace inside the StationXML files for non-standard attribute like the
# cartesian coordinates.
DUG_SEIS_NAMESPACE_TAG = "DUG_SEIS"
DUG_SEIS_NAMESPACE = "https://gitlab.seismo.ethz.ch/doetschj/DUG-Seis"

# Output folder for the produces StationXML files.
OUTPUT_FOLDER = "StationXML"

# Simplistic global instrument definition. I have no idea if this is correct
# but this seems to be what is currently done. Could of course be expanded to
# be per channel and a lot more sophisticated.
INSTRUMENT_SENSITIVITY = 10 ** ((20 + 10) / 10)
INSTRUMENT_FREQUENCY = 200000
INSTRUMENT_INPUT_UNITS = "M/S"
INSTRUMENT_OUTPUT_UNITS = "V"

CHANNELS = {
    "GRM.000.000.001": {"coordinates": [0, 0, 0]},
    "GRM.001.000.001": {"coordinates": [8.652, 84.869, 32.87]},
    "GRM.002.000.001": {"coordinates": [16.187, 98.37, 32.841]},
    "GRM.003.000.001": {"coordinates": [23.103, 110.886, 32.747]},
    "GRM.004.000.001": {"coordinates": [30.7, 125.024, 32.546]},
    "GRM.005.000.001": {"coordinates": [42.158, 135.681, 33.575]},
    "GRM.006.000.001": {"coordinates": [71.148, 135.037, 32.476]},
    "GRM.007.000.001": {"coordinates": [71.169, 125.102, 32.192]},
    "GRM.008.000.001": {"coordinates": [70.764, 114.158, 32.429]},
    "GRM.009.000.001": {"coordinates": [70.569, 104.196, 32.495]},
    "GRM.010.000.001": {"coordinates": [67.306, 93.02, 33.403]},
    "GRM.011.000.001": {"coordinates": [71.162, 122.331, 46.367]},
    "GRM.012.000.001": {"coordinates": [70.716, 104.681, 46.15]},
    "GRM.013.000.001": {"coordinates": [67.236, 91.771, 46.019]},
    "GRM.014.000.001": {"coordinates": [70.069, 77.752, 46.315]},
    "GRM.015.000.001": {"coordinates": [57.243, 96.098, 17.46]},
    "GRM.016.000.001": {"coordinates": [50.51, 96.166, 10.067]},
    "GRM.017.000.001": {"coordinates": [54.122, 96.053, 21.287]},
    "GRM.018.000.001": {"coordinates": [37.572, 96.071, 10.057]},
    "GRM.019.000.001": {"coordinates": [57.542, 111.943, 17.619]},
    "GRM.020.000.001": {"coordinates": [50.805, 111.951, 10.229]},
    "GRM.021.000.001": {"coordinates": [49.339, 111.944, 17.995]},
    "GRM.022.000.001": {"coordinates": [37.743, 111.972, 10.151]},
    "GRM.023.000.001": {"coordinates": [68.6, 107.81, 34.081]},
    "GRM.024.000.001": {"coordinates": [68.565, 105.806, 34.115]},
    "GRM.025.000.001": {"coordinates": [68.53, 103.807, 34.15]},
    "GRM.026.000.001": {"coordinates": [68.496, 101.807, 34.184]},
    "GRM.027.000.001": {"coordinates": [22.974, 110.826, 32.791]},
    "GRM.028.000.001": {"coordinates": [42.048, 135.768, 33.571]},
    "GRM.029.000.001": {"coordinates": [71.237, 134.959, 32.515]},
    "GRM.030.000.001": {"coordinates": [70.852, 114.095, 32.48]},
    "GRM.031.000.001": {"coordinates": [67.279, 92.885, 33.421]},
}


def create_stationxml_files(channels: typing.Dict):
    """
    Generate StationXML files for a given list of channels.

    Args:
        channels: Definition of the channels.
    """
    # Split into network + station to be able to create single files per
    # station. Might become important at one point.
    networks = {}
    for key in channels.keys():
        net_code, sta_code, *_ = key.split(".")
        if net_code not in networks:
            networks[net_code] = {}
        if sta_code not in networks[net_code]:
            networks[net_code][sta_code] = []
        networks[net_code][sta_code].append(key)

    for network_code, station_dict in networks.items():
        for station_code, channel_list in station_dict.items():
            # XXX: Latitude/longitude/elevation right now are just set to
            # 0/0/0. They must be set in StationXML - if you have a proper way
            # to get these numbers it might be worthwhile to fill them.
            latitude = 0.0
            longitude = 0.0
            elevation = 0.0

            station_inv = Inventory(
                networks=[
                    Network(
                        code=network_code,
                        stations=[
                            Station(
                                code=station_code,
                                latitude=latitude,
                                longitude=longitude,
                                elevation=elevation,
                            )
                        ],
                    )
                ]
            )

            sta = station_inv[0][0]
            # Now add each channel. We'll add the cartesian coordinates at the
            # channel level for now.
            for c in channel_list:
                # XXX: Latitude/longitude/elevation/depth right now are just
                # set to 0/0/0/0. They must be set in StationXML - if you have
                # a proper way to get these numbers it might be worthwhile to
                # fill them.
                channel_latitude = 0.0
                channel_longitude = 0.0
                channel_elevation = 0.0
                channel_depth = 0.0

                *_, location_code, channel_code = c.split(".")
                channel = Channel(
                    code=channel_code,
                    location_code=location_code,
                    latitude=channel_latitude,
                    longitude=channel_longitude,
                    elevation=channel_elevation,
                    depth=channel_depth,
                )

                extra = {
                    "cartesian_coordinates": {
                        "value": channels[c]["coordinates"],
                        "namespace": DUG_SEIS_NAMESPACE,
                    }
                }
                channel.extra = extra
                sta.channels.append(channel)

                # XXX: I don't really know enough about the instruments to make
                # a goog guess here.
                instrument_sensitivity = InstrumentSensitivity(
                    value=INSTRUMENT_SENSITIVITY,
                    frequency=INSTRUMENT_FREQUENCY,
                    input_units=INSTRUMENT_INPUT_UNITS,
                    output_units=INSTRUMENT_OUTPUT_UNITS,
                )
                channel.response = Response(
                    instrument_sensitivity=instrument_sensitivity,
                    response_stages=[]
                )

            output_folder = pathlib.Path(OUTPUT_FOLDER)
            output_folder.mkdir(exist_ok=True, parents=True)

            station_inv.write(
                str(output_folder / f"{network_code}.{station_code}.xml"),
                format="stationxml",
                validate=True,
                nsmap={DUG_SEIS_NAMESPACE_TAG: DUG_SEIS_NAMESPACE},
            )


if __name__ == "__main__":
    create_stationxml_files(channels=CHANNELS)
