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
Coordinate transformations for use within ``DUGSeis``.

Input and output files for DUGSeis utilize coordinates in the WGS84 reference
frame also known as EPSG 4326.

Internally ``DUGSeis`` operates in a Cartesian x,y,z reference frame in meters.
The conversions between WGS84 and the local reference frame happen with the
functions defined in this module.

The global reference system for all functions in this module will thus usually
be ``"WGS84"``; the local one must a be Cartesian one. A translation vector
that is applied to the data in the Cartesian reference system concludes the
definition of the internally use ``DUGSeis`` reference system.

The vertical coordinate is the negative depth in the QuakeML and StationXML
files.

**Coordinates in QuakeML files**

The used coordinates are fully valid in QuakeML files with latitude and
longitude being specified with respect to the WGS84 reference system. The depth
is with respect to the nominal sea level given by the WGS84 ellipsoid.

**Coordinates in StationXML files**

Coordinates in StationXML files always have to be specified at the channel
level. Latitude and longitude values are according to the WGS84 reference
system. The elevation must be set to zero and the depth is thus with respect to
the nominal sea level given by the WGS84 ellipsoid. This is slightly different
from the usual convention in StationXML files to set the elevation to the
height of the local surface and the depth the burial beneath that.
"""
import functools
import typing

import numpy as np
import pyproj

# For convenience.
EPSG_CODES = {"WGS84": 4326, "CH1903": 21781}


@functools.lru_cache(maxsize=128)
def _get_transformer(
    source_epsg_code: int, target_epsg_code: int
) -> pyproj.Transformer:
    """
    Helper function returning a pyproj Transformer object. The function caches
    the transformer creation so repeated calls are cheap.

    Args:
        source_epsg_code: EPSG code for the source reference system.
        target_epsg_code: EPSG code for the target reference system.
    """
    return pyproj.Transformer.from_crs(source_epsg_code, target_epsg_code)


def local_to_global(
    *,
    local_crs: typing.Union[int, str],
    global_crs: typing.Union[int, str],
    translation_vector: typing.Optional[
        typing.Union[typing.Tuple[float, float, float], typing.List[float], np.ndarray]
    ] = None,
    point: typing.Union[
        typing.Tuple[float, float, float], typing.List[float], np.ndarray
    ],
) -> typing.Tuple[float, float, float]:
    """
    Convert local coordinates (plus an optional translation vector) to a global
    CRS system.

    This will perform ``transform_local_to_global(point + translation_vector)``.

    Args:
        local_crs: The local coordinate reference system either as a string or a
            EPSG code.
        global_crs: The local coordinate reference system either as a string or a
            EPSG code.
        translation_vector: The translation vector.
        point: The point to convert.
    """

    if not isinstance(local_crs, int):
        local_crs = EPSG_CODES[local_crs]

    if not isinstance(global_crs, int):
        global_crs = EPSG_CODES[global_crs]

    transformer = _get_transformer(
        source_epsg_code=local_crs, target_epsg_code=global_crs
    )

    if translation_vector is not None:
        v = np.array(point) + np.array(translation_vector)
    else:
        v = np.array(point)

    return transformer.transform(xx=v[0], yy=v[1], zz=v[2])


def global_to_local(
    *,
    local_crs: typing.Union[int, str],
    global_crs: typing.Union[int, str],
    translation_vector: typing.Optional[
        typing.Union[typing.Tuple[float, float, float], typing.List[float], np.ndarray]
    ] = None,
    point: typing.Union[
        typing.Tuple[float, float, float], typing.List[float], np.ndarray
    ],
) -> typing.Tuple[float, float, float]:
    """
    Convert global coordinates to a local CRS system and substract an optional
    translation vector.

    This will perform ``global_to_local(point) - translation_vector``.

    Args:
        local_crs: The local coordinate reference system either as a string or a
            EPSG code.
        global_crs: The local coordinate reference system either as a string or a
            EPSG code.
        translation_vector: The translation vector.
        point: The point to convert.
    """

    if not isinstance(local_crs, int):
        local_crs = EPSG_CODES[local_crs]

    if not isinstance(global_crs, int):
        global_crs = EPSG_CODES[global_crs]

    transformer = _get_transformer(
        source_epsg_code=global_crs, target_epsg_code=local_crs
    )

    new_p = transformer.transform(xx=point[0], yy=point[1], zz=point[2])

    if translation_vector is not None:
        return new_p - np.array(translation_vector)
    else:
        return new_p
