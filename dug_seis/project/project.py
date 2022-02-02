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
Central DUGSeis project class.
"""

import functools
import logging
import pathlib
import typing

import matplotlib.pyplot as plt
import numpy as np
import obspy
import schema
import yaml

from ..coordinate_transforms import local_to_global, global_to_local
from ..waveform_handler.waveform_handler import WaveformHandler
from ..db.db import DB


def _is_valid_resource_id(r_id):
    r = obspy.core.event.ResourceIdentifier(r_id)
    uri_str = r.get_quakeml_uri_str()
    if uri_str != r_id:
        raise ValueError(
            f"'{r_id}' is not a valid resource identifier. "
            f"Something like '{uri_str}' would be valid."
        )
    return True


def _directory_exists(p):
    p = pathlib.Path(p)
    if not p.exists():
        raise ValueError(f"Directory '{p}' does not exist.")
    if not p.is_dir():
        raise ValueError(f"'{p}' is not a directory")
    return p


def _path(p):
    return pathlib.Path(p)


def _3c_float_array(a):
    a = np.array(a, dtype=np.float64)
    if a.shape != (3,):
        raise ValueError("Must contain 3 floating point numbers.")
    return a


def _4c_float_array(a):
    a = np.array(a, dtype=np.float64)
    if a.shape != (4,):
        raise ValueError("Must contain 4 floating point numbers.")
    return a


def _colormap_or_color(a):
    # Colormap.
    if isinstance(a, str):
        if a not in plt.colormaps():
            raise ValueError(
                f"'{a}' must either be a color as 4 floats or a valid "
                "matplotlib colormap."
            )
        return a
    # Or color.
    else:
        return _4c_float_array(a)


logger = logging.getLogger(__name__)


_CONFIG_FILE_SCHEMA = schema.Schema(
    {
        # Version number must be this.
        "version": 14,
        "meta": {
            "project_name": str,
            schema.Optional("project_location"): str,
            schema.Optional("project_description"): str,
        },
        "local_coordinate_system": {
            "epsg_code": int,
            "translation_vector": schema.Use(_3c_float_array),
        },
        "paths": {
            "asdf_folders": [schema.Use(_directory_exists)],
            "stationxml_folders": [schema.Use(_directory_exists)],
            "cache_folder": schema.Use(_directory_exists),
            "database": str,
        },
        "temporal_range": {
            # Any valid time string or number or what not should work.
            "start_time": schema.Use(obspy.UTCDateTime),
            "end_time": schema.Use(obspy.UTCDateTime),
        },
        "graphical_interface": {
            "classifications": [str],
            "pick_types": [str],
            "uncertainties_in_ms": [float],
            schema.Optional(
                "color_all_picks", default=np.array([1.0, 1.0, 0.0, 0.7])
            ): schema.Use(_4c_float_array),
            schema.Optional("data_monitoring_ping_interval", default=5.0): float,
            schema.Optional("number_of_closest_channels", default=4): int,
            schema.Optional(
                "3d_view",
                default={
                    "hide_channels": [],
                    "line_segments": [],
                    "line_segments_width": 3.0,
                    "line_segments_color": np.array([0.0, 0.0, 1.0, 0.5]),
                    "size_channels_in_pixel": 10,
                    "color_channels": np.array([1.0, 1.0, 1.0, 0.5]),
                    "size_events_in_pixel": 3,
                    "color_events": np.array([1.0, 0.0, 0.0, 0.5]),
                    "size_active_event_in_pixel": 25,
                    "color_active_event": np.array([1.0, 0.0, 0.0, 1.0]),
                    "size_active_channels_in_pixel": 15,
                    "color_active_channels": np.array([0.0, 1.0, 0.0, 1.0]),
                },
            ): {
                schema.Optional("hide_channels", default=[]): [str],
                schema.Optional("line_segments", default=[]): [
                    [schema.Use(_3c_float_array)]
                ],
                schema.Optional("line_segments_width", default=3.0): float,
                schema.Optional(
                    "line_segments_color", default=[0.0, 0.0, 1.0, 0.5]
                ): schema.Use(_4c_float_array),
                schema.Optional("size_channels_in_pixel", default=10): int,
                schema.Optional(
                    "color_channels", default=[1.0, 1.0, 1.0, 0.5]
                ): schema.Use(_4c_float_array),
                schema.Optional("size_events_in_pixel", default=3): int,
                schema.Optional(
                    "color_events", default=[1.0, 0.0, 0.0, 0.5]
                ): schema.Use(_colormap_or_color),
                schema.Optional("size_active_event_in_pixel", default=25): int,
                schema.Optional(
                    "color_active_event", default=[1.0, 0.0, 0.0, 1.0]
                ): schema.Use(_4c_float_array),
                schema.Optional("size_active_channels_in_pixel", default=15): int,
                schema.Optional(
                    "color_active_channels", default=[0.0, 1.0, 0.0, 1.0]
                ): schema.Use(_4c_float_array),
            },
            schema.Optional(
                "location_algorithm_default_args",
                # A bit awkward here with the triple defaults but seems to do the trick.
                # Would be much easier if this here is ever resolved:
                # https://github.com/keleshev/schema/issues/203
                default={
                    "velocity": {"P": 4866.0, "S": 3200.0},
                    "damping": 0.01,
                    "use_anisotropy": False,
                    "anisotropy_parameters": {
                        "P": {
                            "azi": 310.0,
                            "inc": 28.6,
                            "delta": 0.071,
                            "epsilon": 0.067,
                        },
                        "S": {
                            "azi": 310.0,
                            "inc": 28.6,
                            "delta": 0.071,
                            "epsilon": 0.067,
                        },
                    },
                },
            ): {
                schema.Optional("velocity", default={"P": 4866.0, "S": 3200.0}): {
                    schema.Optional("P", default=4866.0): float,
                    schema.Optional("S", default=3200.0): float,
                },
                schema.Optional("damping", default=0.01): float,
                schema.Optional("use_anisotropy", default=False): bool,
                schema.Optional(
                    "anisotropy_parameters",
                    default={
                        "P": {
                            "azi": 310.0,
                            "inc": 28.6,
                            "delta": 0.071,
                            "epsilon": 0.067,
                        },
                        "S": {
                            "azi": 310.0,
                            "inc": 28.6,
                            "delta": 0.071,
                            "epsilon": 0.067,
                        },
                    },
                ): {
                    schema.Optional(
                        "P",
                        default={
                            "azi": 310.0,
                            "inc": 28.6,
                            "delta": 0.071,
                            "epsilon": 0.067,
                        },
                    ): {
                        schema.Optional("azi", default=310.0): float,
                        schema.Optional("inc", default=28.6): float,
                        schema.Optional("delta", default=0.071): float,
                        schema.Optional("epsilon", default=0.067): float,
                    },
                    schema.Optional(
                        "S",
                        default={
                            "azi": 310.0,
                            "inc": 28.6,
                            "delta": 0.071,
                            "epsilon": 0.067,
                        },
                    ): {
                        schema.Optional("azi", default=310.0): float,
                        schema.Optional("inc", default=28.6): float,
                        schema.Optional("delta", default=0.071): float,
                        schema.Optional("epsilon", default=0.067): float,
                    },
                },
            },
        },
        "filters": [
            {
                "filter_id": schema.Const(_is_valid_resource_id),
                "filter_settings": schema.Or(
                    {
                        "filter_type": "butterworth_bandpass",
                        "highpass_frequency_in_hz": float,
                        "lowpass_frequency_in_hz": float,
                        "filter_corners": int,
                        "zerophase": bool,
                    },
                    {
                        "filter_type": "butterworth_highpass",
                        "frequency_in_hz": float,
                        "filter_corners": int,
                        "zerophase": bool,
                    },
                    {
                        "filter_type": "butterworth_lowpass",
                        "frequency_in_hz": float,
                        "filter_corners": int,
                        "zerophase": bool,
                    },
                ),
            }
        ],
    }
)


class DUGSeisProject:
    def __init__(self, config: typing.Union[pathlib.Path, str, typing.Dict]):
        """
        Central DUGSeis project.

        Args:
            config: The project configuration as a filename or a dictionary.
        """
        self._load_and_validate_config(config=config)
        # Load the StationXML files.
        self._load_stationxml_files()

        self.__waveform_handler: typing.Optional[WaveformHandler] = None
        self.__db: typing.Optional[DB] = None

    @property
    def waveforms(self) -> WaveformHandler:
        """
        Access the project's waveform handler.
        """
        # Lazily load it.
        if self.__waveform_handler is None:
            self._load_waveforms()
        return self.__waveform_handler

    @property
    def db(self) -> DB:
        """
        Access the project's database.
        """
        # Lazily load it.
        if self.__db is None:
            self._open_db()
        return self.__db

    @property
    def cartesian_coordinates(self) -> typing.Dict[str, np.ndarray]:
        """
        Cartesian coordinates for all channels in the project.
        """
        return {k: np.array(v["coordinates"]) for k, v in self.channels.items()}

    def _open_db(self):
        self.__db = DB(url=self.config["paths"]["database"])

    def _load_waveforms(self):
        # Reuse caches if possible.
        if self.__waveform_handler is not None:
            existing_caches = self.__waveform_handler._individual_caches
        else:
            existing_caches = None

        wh = WaveformHandler(
            waveform_folders=self.config["paths"]["asdf_folders"],
            cache_folder=self.config["paths"]["cache_folder"],
            index_sampling_rate_in_hz=100,
            start_time=self.config["temporal_range"]["start_time"],
            end_time=self.config["temporal_range"]["end_time"],
            existing_caches=existing_caches,
        )

        # Time to check that the data also corresponds to the StationXML
        # meta-data. Only do this the first time around to not clutter the
        # output.
        if existing_caches is None:
            channels_in_data = set(wh.receivers)
            channels_in_meta_data = set(self.channels.keys())

            in_asdf_files = "\n".join(f"* {i}" for i in sorted(channels_in_data))
            in_stationxml_files = "\n".join(
                f"  * {i}" for i in sorted(channels_in_meta_data)
            )
            msg = (
                "Channels in the ASDF data don't correspond to \n"
                "the channels in the StationXML files.\n\n"
                f"Channels in the ASDF files:\n{in_asdf_files}\n\n"
                f"Channels in the StationXML files:\n{in_stationxml_files}"
            )

            extra_channels_in_meta_data = channels_in_meta_data.difference(
                channels_in_data
            )
            extra_channels_in_data = channels_in_data.difference(channels_in_meta_data)

            if extra_channels_in_data:
                in_data = "\n".join(f"* {i}" for i in sorted(extra_channels_in_data))
                msg += f"\n\n\nAdditional channels in the data:\n{in_data}"
            if extra_channels_in_meta_data:
                in_meta = "\n".join(
                    f"* {i}" for i in sorted(extra_channels_in_meta_data)
                )
                msg += f"\n\n\nAdditional channels in the meta data:\n{in_meta}"

            # Raise for extra channels in the meta data. This is likely an error.
            if extra_channels_in_meta_data:
                raise ValueError(msg)
            # Otherwise only warn.
            elif extra_channels_in_data:
                logger.warn(msg)

        self.__waveform_handler = wh

    def _load_and_validate_config(
        self, config: typing.Union[pathlib.Path, str, typing.Dict]
    ):
        if not isinstance(config, dict):
            with open(config, "r") as fh:
                config = yaml.load(fh, Loader=yaml.SafeLoader)

        # Manually check the version number to be able to raise a more
        # descriptive error
        expected_version = _CONFIG_FILE_SCHEMA.schema["version"]
        actual_version = config.get("version", None)
        if expected_version != actual_version:
            raise ValueError(
                f"This DUGSeis requires a config file of version '{expected_version}'. "
                f"The given file has a version number of '{actual_version}'."
            )

        # First validate using the config schema.
        v_config = _CONFIG_FILE_SCHEMA.validate(config)

        # A few manual validation stages.
        if (
            v_config["temporal_range"]["start_time"]
            >= v_config["temporal_range"]["end_time"]
        ):
            raise ValueError("'start_time' must be smaller than 'end_time'.")

        for f in v_config["filters"]:
            if f["filter_settings"]["filter_type"] == "butterworth_bandpass" and (
                f["filter_settings"]["highpass_frequency_in_hz"]
                >= f["filter_settings"]["lowpass_frequency_in_hz"]
            ):
                raise ValueError(
                    "The high pass filter frequency must be smaller than "
                    "the lowpass filter frequency."
                )

        filters = [f["filter_id"] for f in v_config["filters"]]
        if len(filters) != len(set(filters)):
            raise ValueError("Filter ids must be unique.")

        # Setup the coordinate transforms. Use partial functions here to easy
        # subsequent applications.
        self._local_to_global_coordinate_transform = functools.partial(
            local_to_global,
            local_crs=v_config["local_coordinate_system"]["epsg_code"],
            global_crs="WGS84",
            translation_vector=v_config["local_coordinate_system"][
                "translation_vector"
            ],
        )
        self._global_to_local_coordinate_transform = functools.partial(
            global_to_local,
            local_crs=v_config["local_coordinate_system"]["epsg_code"],
            global_crs="WGS84",
            translation_vector=v_config["local_coordinate_system"][
                "translation_vector"
            ],
        )

        self.config = v_config

    def global_to_local_coordinates(
        self, latitude: float, longitude: float, depth: float
    ) -> np.ndarray:
        """
        Convert WGS84 coordinates to the project's local coordinate system.

        Args:
            latitude: The WGS84 latitude in degrees.
            longitude: The WGS84 longitude in degrees.
            depth: The depth beneath the WGS84 ellipsoid in meters Positive is
                down.
        """
        return self._global_to_local_coordinate_transform(
            point=[latitude, longitude, -depth]
        )

    def local_to_global_coordinates(
        self,
        point: typing.Union[
            typing.Tuple[float, float, float], typing.List[float], np.ndarray
        ],
    ) -> np.ndarray:
        """
        Convert a point in the project's local Cartesian reference frame to
        WGS84. Will return latitude, longitude, depth beneath the ellipsoid.

        Args:
            point: x, y, z of the point in the project's local reference frame.
                z points up.
        """
        p = list(self._local_to_global_coordinate_transform(point=point))
        p[-1] = -1.0 * p[-1]
        return tuple(p)

    def _load_stationxml_files(self):
        """
        Read all StationXML files.

        Does some sanity checks and also extras the Cartesian coordinates.
        """
        # First read all to a common inventory.
        inv = obspy.core.inventory.Inventory()
        for p in self.config["paths"]["stationxml_folders"]:
            for f in p.glob("*.xml"):
                inv += obspy.read_inventory(str(f))

        # Keep the inventory around.
        self.inventory = inv

        channels = {}
        # Now parse per channel but make sure each channel is there exactly
        # once.
        for network in inv.networks:
            for station in network.stations:
                for channel in station.channels:
                    identifier = (
                        f"{network.code}.{station.code}."
                        f"{channel.location_code}.{channel.code}"
                    )
                    # Only one per channel.
                    if identifier in channels:
                        raise ValueError(
                            f"Channel {identifier} exists multiple times in the "
                            "StationXML files."
                        )

                    # Must have channel level coordinates. These are invalid.
                    if channel.latitude == 0.0 and channel.longitude == 0.0:
                        raise ValueError(
                            f"Channel {identifier} does not have channel level "
                            "coordinates. These must be available."
                        )

                    if channel.elevation != 0.0:
                        raise ValueError(
                            f"Channel {identifier}: The channel level elevation "
                            "must be zero so the depth is with respect to the WGS84 "
                            "ellipsoid."
                        )

                    channels[identifier] = {
                        "coordinates": self.global_to_local_coordinates(
                            latitude=channel.latitude,
                            longitude=channel.longitude,
                            depth=channel.depth,
                        ),
                        "channel_objects": channel,
                    }

        self.channels = channels
