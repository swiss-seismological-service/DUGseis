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

import numpy as np
import pytest

from dug_seis.coordinate_transforms import local_to_global, global_to_local


def test_local_to_global():
    x = 50.20269333
    y = 103.41166864
    z = 14.6968101034

    expected_longitude = 7.165186744904836
    expected_latitude = 47.3789374387355
    expected_negative_depth = 514.6968101033539

    np.testing.assert_allclose(
        local_to_global(
            local_crs="CH1903",
            global_crs="WGS84",
            translation_vector=[
                579300.0,  # ch1903 easting origin of local coordinate system
                247500.0,  # ch1903 northing origin of local coordinate system
                500.0,  # elevation of origin of local coordinate system
            ],
            point=[x, y, z],
        ),
        (expected_latitude, expected_longitude, expected_negative_depth),
    )


@pytest.mark.parametrize(
    "x, y, z",
    [(0.0, 0.0, 0.0), (1.0, 3.0, 100.0), (2.0, 40.0, -20.0), (30.0, 5.0, 40.0)],
)
def test_local_to_global_roundtripping(x, y, z):
    global_coords = local_to_global(
        local_crs="CH1903",
        global_crs="WGS84",
        translation_vector=[
            579300.0,  # ch1903 easting origin of local coordinate system
            247500.0,  # ch1903 northing origin of local coordinate system
            500.0,  # elevation of origin of local coordinate system
        ],
        point=[x, y, z],
    )

    local_coords = global_to_local(
        local_crs="CH1903",
        global_crs="WGS84",
        translation_vector=[
            579300.0,  # ch1903 easting origin of local coordinate system
            247500.0,  # ch1903 northing origin of local coordinate system
            500.0,  # elevation of origin of local coordinate system
        ],
        point=global_coords,
    )

    np.testing.assert_allclose([x, y, z], local_coords, atol=1.5e-3)


def test_error_for_repeated_roundtripping_not_too_large():
    """
    Repeated roundtripping increases the error. Make sure this is still okay.
    """
    point = [111.0, 222.0, -333.0]

    # Roundtrip 10 times.
    for _ in range(10):
        global_coords = local_to_global(
            local_crs="CH1903",
            global_crs="WGS84",
            translation_vector=[
                579300.0,  # ch1903 easting origin of local coordinate system
                247500.0,  # ch1903 northing origin of local coordinate system
                500.0,  # elevation of origin of local coordinate system
            ],
            point=point,
        )

        point = global_to_local(
            local_crs="CH1903",
            global_crs="WGS84",
            translation_vector=[
                579300.0,  # ch1903 easting origin of local coordinate system
                247500.0,  # ch1903 northing origin of local coordinate system
                500.0,  # elevation of origin of local coordinate system
            ],
            point=global_coords,
        )

    # Still within 1.5 cm after roundtripping 10 times.
    np.testing.assert_allclose([111.0, 222.0, -333.0], point, atol=0.015)
