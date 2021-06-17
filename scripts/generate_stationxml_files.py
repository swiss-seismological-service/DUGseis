# DUGSeis
# Copyright (C) 2021 DUGSeis Authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
    PolesZerosResponseStage,
)

from dug_seis.coordinate_transforms import local_to_global

# XML Namespace inside the StationXML files for non-standard attribute like the
# cartesian coordinates.
DUG_SEIS_NAMESPACE_TAG = "DUG_SEIS"
# XXX: Change at one point.
DUG_SEIS_NAMESPACE = "https://gitlab.seismo.ethz.ch/doetschj/DUG-Seis"

# Output folder for the produces StationXML files.
OUTPUT_FOLDER = "StationXML"

# Simplistic global instrument definition. I have no idea if this is correct
# but this seems to be what is currently done. Could of course be expanded to
# be per channel and a lot more sophisticated.
INSTRUMENT_SENSITIVITY = 10 ** ((20 + 10) / 10)
INSTRUMENT_FREQUENCY = 5000
INSTRUMENT_INPUT_UNITS = "M/S"
INSTRUMENT_OUTPUT_UNITS = "V"

# Channel coordinates are given in local coordinates here but will be converted
# to WGS84 before being written to the StationXML files.
CHANNELS = {
    "GRM.001.001.001": {"coordinates": [0, 0, 0]},
    "GRM.002.001.001": {"coordinates": [8.652, 84.869, 32.87]},
    "GRM.003.001.001": {"coordinates": [16.187, 98.37, 32.841]},
    "GRM.004.001.001": {"coordinates": [23.103, 110.886, 32.747]},
    "GRM.005.001.001": {"coordinates": [30.7, 125.024, 32.546]},
    "GRM.006.001.001": {"coordinates": [42.158, 135.681, 33.575]},
    "GRM.007.001.001": {"coordinates": [71.148, 135.037, 32.476]},
    "GRM.008.001.001": {"coordinates": [71.169, 125.102, 32.192]},
    "GRM.009.001.001": {"coordinates": [70.764, 114.158, 32.429]},
    "GRM.010.001.001": {"coordinates": [70.569, 104.196, 32.495]},
    "GRM.011.001.001": {"coordinates": [67.306, 93.02, 33.403]},
    "GRM.012.001.001": {"coordinates": [71.162, 122.331, 46.367]},
    "GRM.013.001.001": {"coordinates": [70.716, 104.681, 46.15]},
    "GRM.014.001.001": {"coordinates": [67.236, 91.771, 46.019]},
    "GRM.015.001.001": {"coordinates": [70.069, 77.752, 46.315]},
    "GRM.016.001.001": {"coordinates": [57.243, 96.098, 17.46]},
    "GRM.017.001.001": {"coordinates": [50.51, 96.166, 10.067]},
    "GRM.018.001.001": {"coordinates": [54.122, 96.053, 21.287]},
    "GRM.019.001.001": {"coordinates": [37.572, 96.071, 10.057]},
    "GRM.020.001.001": {"coordinates": [57.542, 111.943, 17.619]},
    "GRM.021.001.001": {"coordinates": [50.805, 111.951, 10.229]},
    "GRM.022.001.001": {"coordinates": [49.339, 111.944, 17.995]},
    "GRM.023.001.001": {"coordinates": [37.743, 111.972, 10.151]},
    "GRM.024.001.001": {"coordinates": [68.6, 107.81, 34.081]},
    "GRM.025.001.001": {"coordinates": [68.565, 105.806, 34.115]},
    "GRM.026.001.001": {"coordinates": [68.53, 103.807, 34.15]},
    "GRM.027.001.001": {"coordinates": [68.496, 101.807, 34.184]},
    "GRM.028.001.001": {"coordinates": [22.974, 110.826, 32.791]},
    "GRM.029.001.001": {"coordinates": [42.048, 135.768, 33.571]},
    "GRM.030.001.001": {"coordinates": [71.237, 134.959, 32.515]},
    "GRM.031.001.001": {"coordinates": [70.852, 114.095, 32.48]},
    "GRM.032.001.001": {"coordinates": [67.279, 92.885, 33.421]},
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
            # Code for the coordinate conversion will have to change if this is
            # no longer satisfied.
            assert len(channel_list) == 1

            # XXX: The elevation is a bit shady here.
            latitude, longitude, vertical = local_to_global(
                local_crs="CH1903",
                global_crs="WGS84",
                translation_vector=[
                    579300.0,  # ch1903 easting origin of local coordinate system
                    247500.0,  # ch1903 northing origin of local coordinate system
                    500.0,  # elevation of origin of local coordinate system
                ],
                point=channels[channel_list[0]]["coordinates"],
            )

            station_inv = Inventory(
                networks=[
                    Network(
                        code=network_code,
                        stations=[
                            Station(
                                code=station_code,
                                latitude=latitude,
                                longitude=longitude,
                                elevation=0.0,
                            )
                        ],
                    )
                ]
            )

            sta = station_inv[0][0]
            # Now add each channel. We'll add the cartesian coordinates at the
            # channel level for now.
            for c in channel_list:
                channel_latitude = latitude
                channel_longitude = longitude
                channel_elevation = 0.0
                channel_depth = -vertical

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
                # a good guess here.
                instrument_sensitivity = InstrumentSensitivity(
                    value=INSTRUMENT_SENSITIVITY,
                    frequency=INSTRUMENT_FREQUENCY,
                    input_units=INSTRUMENT_INPUT_UNITS,
                    output_units=INSTRUMENT_OUTPUT_UNITS,
                )
                channel.response = Response(
                    instrument_sensitivity=instrument_sensitivity,
                    response_stages=[
                        # Empty PAZ stage so tr.remove_response() works.
                        PolesZerosResponseStage(
                            stage_sequence_number=1,
                            stage_gain=INSTRUMENT_SENSITIVITY,
                            stage_gain_frequency=INSTRUMENT_FREQUENCY,
                            input_units=INSTRUMENT_INPUT_UNITS,
                            output_units=INSTRUMENT_OUTPUT_UNITS,
                            pz_transfer_function_type="LAPLACE (HERTZ)",
                            normalization_frequency=INSTRUMENT_FREQUENCY,
                            zeros=[],
                            poles=[],
                        )
                    ],
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
