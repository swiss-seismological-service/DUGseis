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
Test suite for the DUGSeis project class.
"""
import pathlib

import obspy

from dug_seis.project.project import DUGSeisProject


def test_config_validation(tmp_path):
    d = tmp_path / "subfolder"

    # These two must exist.
    (d / "asdf_folder").mkdir(parents=True)
    (d / "stationxml_folder").mkdir(parents=True)
    (d / "cache_folder").mkdir(parents=True)

    config = {
        "version": 14,
        "meta": {
            "project_name": "Example",
            "project_location": "Hello",
        },
        "local_coordinate_system": {
            "epsg_code": 2091,
            "translation_vector": [1.0, 2.0, 3.0],
        },
        "paths": {
            "asdf_folders": [str(d / "asdf_folder")],
            "stationxml_folders": [str(d / "stationxml_folder")],
            "database": "sqlite://:memory:",
            "cache_folder": str(d / "cache_folder"),
        },
        "temporal_range": {
            "start_time": "2021-04-19T12:05:23.658960Z",
            "end_time": "2021-04-19T12:09:23.658960Z",
        },
        "graphical_interface": {
            "classifications": ["passive", "active", "random"],
            "pick_types": ["P", "S"],
            "uncertainties_in_ms": [0.1, 0.2],
        },
        "filters": [
            {
                "filter_id": "smi:local/some_filter",
                "filter_settings": {
                    "filter_type": "butterworth_bandpass",
                    "highpass_frequency_in_hz": 10.0,
                    "lowpass_frequency_in_hz": 15.0,
                    "filter_corners": 3,
                    "zerophase": False,
                },
            }
        ],
    }

    p = DUGSeisProject(config=config)

    # Should be pathlib objects.
    assert len(p.config["paths"]["asdf_folders"]) == 1
    assert isinstance(p.config["paths"]["asdf_folders"][0], pathlib.Path)
    assert isinstance(p.config["paths"]["stationxml_folders"][0], pathlib.Path)

    # Time should have been converted to ObsPy UTCDateTimes.
    assert isinstance(p.config["temporal_range"]["start_time"], obspy.UTCDateTime)
    assert p.config["temporal_range"]["start_time"] == obspy.UTCDateTime(
        "2021-04-19T12:05:23.658960Z"
    )
    assert isinstance(p.config["temporal_range"]["end_time"], obspy.UTCDateTime)
