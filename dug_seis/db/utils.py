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
Database utils.
"""

import typing


def collect_resource_ids(obj: typing.Any) -> typing.List[str]:
    """
    Collect all resource ids in the given object.
    """
    r_ids = []
    if hasattr(obj, "resource_id") and obj.resource_id:
        r_ids.append(obj.resource_id.resource_id)
    for o in getattr(obj, "_containers", []):
        for inner_object in getattr(obj, o):
            r_ids.extend(collect_resource_ids(inner_object))
    return r_ids
