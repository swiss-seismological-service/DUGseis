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
Base DB interface.

Just a thin wrapper around the underlying implementations.
"""

import pathlib
import typing

import obspy

from .sqlite_db_backend import _SQLiteBackend

_PROTOCOL_BACKEND_MAP = {"sqlite": _SQLiteBackend}


class DB:
    def __init__(self, url: str):
        """
        ORM between ObsPy event objects and a Seiscomp database.

        Args:
            url: Connection URL inspired by SQLAlchemy. Must be in the form
                `PROTOCOL://CONNECTION`. `PROTOCOL` is currently limited to
                `sqlite`.
        """
        try:
            protocol, connection = url.split("://", 1)
        except ValueError:
            raise ValueError(f"Invalid database URL: {url}")

        if protocol not in _PROTOCOL_BACKEND_MAP:
            raise ValueError(
                f"Unsupported database protocol '{protocol}'. "
                f"Supported protocols: {list(_PROTOCOL_BACKEND_MAP.keys())}"
            )

        self._backend = _PROTOCOL_BACKEND_MAP[protocol](connection=connection)

    def add_object(
        self, obj: typing.Any, parent_object_id: typing.Optional[int] = None
    ):
        self._backend.add_object(obj=obj, parent_object_id=parent_object_id)

    def __iadd__(self, obj: typing.Any):
        self.add_object(obj=obj)
        return self

    def get_objects(
        self,
        object_type: str,
        where: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ):
        return self._backend.get_objects(object_type=object_type, where=where)

    def dump_as_quakeml_files(self, folder: pathlib.Path):
        folder = pathlib.Path(folder)
        folder.mkdir(exist_ok=True, parents=True)
        events = self.get_objects(object_type="Event")
        for i, event in enumerate(events):
            filename = folder / f"event_{i}.xml"
            event.write(str(filename), format="quakeml")

    def count(self, object_type: str) -> int:
        """
        Return the count of objects of a certain type in the database.

        Args:
            object_type: The type of object to count.
        """
        return self._backend.count(object_type=object_type)

    def get_event_summary(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Get a short summary of all events, sorted by earliest origin.

        The returned latitude/longitude/depth belong to the earliest origin of
        each event.
        """
        return self._backend.get_event_summary()

    def get_event_by_resource_id(
        self, resource_id: typing.Union[str, obspy.core.event.ResourceIdentifier]
    ) -> obspy.core.event.Event:
        """
        Helper method retrieving and event by resource id.

        Args:
            resource_id: The resource id to query.
        """
        events = self.get_objects(
            object_type="Event", where={"publicID__eq": str(resource_id)}
        )
        if len(events) == 0:
            raise ValueError("Could not find the given event.")
        elif len(events) > 1:  # pragma: no cover
            raise RuntimeError("Should not happen.")
        return events[0]

    def get_unassociated_picks(self) -> obspy.core.event.Pick:
        """
        Get all picks currently not associated with any event.
        """
        return self._backend.get_unassociated_picks()

    def delete_objects(self, objects=typing.List[typing.Any]):
        """
        Delete the passed objects from the database.
        """
        if not isinstance(objects, list):
            raise ValueError("Must pass a list of objects.")
        if len(objects) == 0:
            raise ValueError("Must pass something to delete.")
        return self._backend.delete_objects(objects=objects)

    def update_event(self, event: obspy.core.event.Event):
        """
        Updates an event. The event in the database will be identified via its
        resources id. All dependent objects will be deleted and fresh new event
        will be added to the database.
        """
        old_event = self.get_event_by_resource_id(resource_id=event.resource_id)
        self.delete_objects([old_event])
        self.add_object(event)

    def update_event_comments(self, event: obspy.core.event.Event):
        """
        Specialized update command that only updates an event's comments.

        Mainly useful for the GUI or other mass comment changes.

        Args:
            event: The event whose comments should be updated. Will use the
                its resource id, delete all old comments and add the new
                comments.
        """
        self._backend.update_event_comments(event=event)
