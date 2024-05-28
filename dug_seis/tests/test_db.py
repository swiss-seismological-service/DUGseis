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

import io
import pathlib

import obspy
import pytest

from dug_seis.db.db import DB

DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_basic_db(tmp_path):
    url = f"sqlite://{tmp_path / 'db.sqlite'}"
    db = DB(url=url)
    assert db._backend._default_parent_id == 1
    del db

    # Reopen.
    db2 = DB(url=url)
    assert db2._backend._default_parent_id == 1

    # Memory files should also work.
    db3 = DB(url="sqlite://:memory:")
    assert db3._backend._default_parent_id == 1


def test_pick_file_db(tmp_path):
    """
    Same as test_pick() but for an actual file.
    """
    url = f"sqlite://{tmp_path / 'db.sqlite'}"
    db = DB(url=url)

    pick = obspy.core.event.Pick(
        time=obspy.UTCDateTime(2021, 1, 1),
        waveform_id=obspy.core.event.WaveformStreamID(
            network_code="BW", station_code="FUR", location_code="", channel_code="EHZ"
        ),
        method_id="smi:/random/method",
        phase_hint="P",
    )

    # Let's see if the single pick object survives round-tripping.
    db += pick
    picks = db.get_objects(object_type="Pick")
    assert pick == picks[0]


def test_pick():
    db = DB(url="sqlite://:memory:")

    pick = obspy.core.event.Pick(
        time=obspy.UTCDateTime(2021, 1, 1),
        waveform_id=obspy.core.event.WaveformStreamID(
            network_code="BW", station_code="FUR", location_code="", channel_code="EHZ"
        ),
        method_id="smi:/random/method",
        phase_hint="P",
    )

    # Let's see if the single pick object survives round-tripping.
    db += pick
    picks = db.get_objects(object_type="Pick")
    assert pick == picks[0]


def test_reading_and_writing_full_pick():
    event = obspy.read_events(str(DATA_DIR / "event_with_full_pick.xml"))[0]
    pick = event.picks[0]

    db = DB(url="sqlite://:memory:")

    # Make sure the pick survives a full round trip.
    db += pick
    picks = db.get_objects(object_type="Pick")
    assert pick == picks[0]

    # There is a second pick - make sure this also works.
    db += event.picks[1]
    picks = db.get_objects(object_type="Pick")
    assert pick == picks[0]


def test_retrieving_pick_by_resource_id():
    db = DB(url="sqlite://:memory:")

    event = obspy.read_events(str(DATA_DIR / "event_with_full_pick.xml"))[0]
    for p in event.picks:
        db += p

    assert db.get_objects(
        object_type="Pick",
        where={"publicID__eq": event.picks[0].resource_id.resource_id},
    ) == [event.picks[0]]
    assert db.get_objects(
        object_type="Pick",
        where={"publicID__eq": event.picks[1].resource_id.resource_id},
    ) == [event.picks[1]]


def test_parent_object_id_logic():
    comment = obspy.core.event.Comment(text="hallo", force_resource_id=False)

    db = DB(url="sqlite://:memory:")
    db.add_object(comment)
    # Parent object id should be one, e.g. the default
    assert db._backend.cursor.execute(
        "SELECT (_parent_oid) from Comment"
    ).fetchall() == [(1,)]
    del db

    # Manually set a different one.
    db = DB(url="sqlite://:memory:")
    db.add_object(comment, parent_object_id=33)
    assert db._backend.cursor.execute(
        "SELECT (_parent_oid) from Comment"
    ).fetchall() == [(33,)]
    del db


def test_reading_and_writing_single_comment():
    # No resource id for now.
    db = DB(url="sqlite://:memory:")
    comment = obspy.core.event.Comment(text="hallo", force_resource_id=False)
    assert not comment.resource_id
    db += comment
    comments = db.get_objects(object_type="Comment")
    assert comment == comments[0]
    assert not comments[0].resource_id
    # Make sure the creationInfo_used flag is False here.
    assert db._backend.cursor.execute(
        "SELECT (creationInfo_used) from Comment"
    ).fetchall() == [(0,)]
    del db

    # With resource id for now.
    db = DB(url="sqlite://:memory:")
    comment = obspy.core.event.Comment(text="hallo", force_resource_id=True)
    assert comment.resource_id
    assert not comment.creation_info
    db += comment
    comments = db.get_objects(object_type="Comment")
    assert comment == comments[0]
    assert comments[0].resource_id
    assert not comments[0].creation_info
    # Make sure the creationInfo_used flag is False here.
    assert db._backend.cursor.execute(
        "SELECT (creationInfo_used) from Comment"
    ).fetchall() == [(0,)]
    del db

    # With creation info.
    db = DB(url="sqlite://:memory:")
    comment = obspy.core.event.Comment(
        text="hallo",
        force_resource_id=True,
        creation_info=obspy.core.event.CreationInfo(
            agency_id="Somewhere",
            agency_uri=obspy.core.event.ResourceIdentifier(),
            author="Me",
            author_uri=obspy.core.event.ResourceIdentifier(),
            creation_time=obspy.UTCDateTime(2021, 1, 2, 3, 4, 5, 6),
            version="0.1.2",
        ),
    )
    assert comment.resource_id
    assert comment.creation_info
    db += comment
    comments = db.get_objects(object_type="Comment")
    assert comment == comments[0]
    assert comments[0].resource_id
    assert comments[0].creation_info
    # Make sure the creationInfo_used flag is True here.
    assert db._backend.cursor.execute(
        "SELECT (creationInfo_used) from Comment"
    ).fetchall() == [(1,)]
    del db


def test_reading_and_writing_full_magnitude():
    event = obspy.read_events(str(DATA_DIR / "event_with_full_magnitude.xml"))[0]
    magnitude = event.magnitudes[0]

    db = DB(url="sqlite://:memory:")

    # Make sure the magnitude survives a full round trip.
    db += magnitude
    magnitudes = db.get_objects(object_type="Magnitude")
    assert magnitude == magnitudes[0]


def test_reading_and_writing_composite_time():
    # This event's origin has a composite time.
    event = obspy.read_events(str(DATA_DIR / "event_with_full_origin.xml"))[0]
    composite_time = event.origins[0].composite_times[0]

    db = DB(url="sqlite://:memory:")

    # Have it round-trip.
    db += composite_time
    composite_times = db.get_objects(object_type="CompositeTime")
    assert composite_time == composite_times[0]


def test_reading_and_writing_full_origin():
    event = obspy.read_events(str(DATA_DIR / "event_with_full_origin.xml"))[0]
    origin = event.origins[0]

    db = DB(url="sqlite://:memory:")

    # Make sure the origin survives a full round trip. The region origin
    # attribute is not supported by the Seiscomp database - thus an appropriate
    # warning should be emitted.
    with pytest.warns(UserWarning) as w:
        db += origin
    assert len(w) == 1
    assert w[0].message.args[0] == (
        "The region attribute in Origin objects is not supported by the Seiscomp "
        "database and will thus be ignored."
    )

    # Remove the region from the ground-truth object.
    origin.region = None

    origins = db.get_objects(object_type="Origin")
    assert origin == origins[0]


def test_reading_and_writing_arrival():
    event = obspy.read_events(str(DATA_DIR / "event_with_full_arrival.xml"))[0]
    arrival = event.origins[0].arrivals[0]

    db = DB(url="sqlite://:memory:")

    with pytest.warns(UserWarning) as w:
        db += arrival
    assert len(w) == 4
    assert w[0].message.args[0] == (
        "The Origin.takeoff_angle_errors attribute will be ignored because it "
        "cannot be stored in the Seiscomp compatible database."
    )
    assert w[1].message.args[0] == (
        "The Origin.time_weight attribute will be ignored because it "
        "cannot be stored in the Seiscomp compatible database."
    )
    assert w[2].message.args[0] == (
        "The Origin.horizontal_slowness_weight attribute will be ignored because it "
        "cannot be stored in the Seiscomp compatible database."
    )
    assert w[3].message.args[0] == (
        "The Origin.backazimuth_weight attribute will be ignored because it "
        "cannot be stored in the Seiscomp compatible database."
    )

    # Set these four to None and compare.
    arrival.takeoff_angle_errors = None
    arrival.time_weight = None
    arrival.horizontal_slowness_weight = None
    arrival.backazimuth_weight = None
    arrivals = db.get_objects(object_type="Arrival")
    assert arrival == arrivals[0]


def test_read_and_write_origin_without_fixed_epicenter():
    origin = obspy.read_events(str(DATA_DIR / "simple_quakeml_file.xml"))[0].origins[0]

    db = DB(url="sqlite://:memory:")

    db += origin
    origins = db.get_objects(object_type="Origin")

    assert origin == origins[0]


def test_read_and_write_whole_event():
    event = obspy.read_events(str(DATA_DIR / "simple_quakeml_file.xml"))[0]

    db = DB(url="sqlite://:memory:")

    db += event
    events = db.get_objects(object_type="Event")

    assert event == events[0]


def test_read_and_write_event_description():
    db = DB(url="sqlite://:memory:")

    ed = obspy.core.event.EventDescription(text="something", type="felt report")

    db += ed
    event_descriptions = db.get_objects(object_type="EventDescription")
    assert ed == event_descriptions[0]


def test_read_and_write_moment_tensor():
    mt = (
        obspy.read_events(str(DATA_DIR / "event_with_full_focal_mechanism.xml"))[0]
        .focal_mechanisms[0]
        .moment_tensor
    )

    db = DB(url="sqlite://:memory:")

    db += mt

    moment_tensors = db.get_objects(object_type="MomentTensor")
    assert mt == moment_tensors[0]


def test_read_and_write_focal_mechanism():
    foc_mec = obspy.read_events(str(DATA_DIR / "event_with_full_focal_mechanism.xml"))[
        0
    ].focal_mechanisms[0]

    db = DB(url="sqlite://:memory:")

    with pytest.warns(UserWarning) as w:
        db += foc_mec
    assert len(w) == 1
    assert w[0].message.args[0] == (
        "The FocalMechanism.waveform_id attribute will be ignored because it "
        "cannot be stored in the Seiscomp compatible database."
    )
    # Delete them because they cannot be represented in the DB.
    foc_mec.waveform_id = []

    foc_mecs = db.get_objects(object_type="FocalMechanism")
    assert foc_mec == foc_mecs[0]


def test_read_and_write_amplitude():
    amplitude = obspy.read_events(str(DATA_DIR / "qml-example-1.2-RC3.xml"))[
        0
    ].amplitudes[0]

    db = DB(url="sqlite://:memory:")

    with pytest.warns(UserWarning) as w:
        db += amplitude
    assert len(w) == 1
    assert w[0].message.args[0] == (
        "The Amplitude.category attribute will be ignored because it "
        "cannot be stored in the Seiscomp compatible database."
    )

    amplitude.category = None

    amplitudes = db.get_objects(object_type="Amplitude")
    assert amplitude == amplitudes[0]


def test_read_and_write_data_used():
    data_used = (
        obspy.read_events(str(DATA_DIR / "event_with_data_used.xml"))[0]
        .focal_mechanisms[0]
        .moment_tensor.data_used[0]
    )

    db = DB(url="sqlite://:memory:")
    db += data_used

    data_used_objects = db.get_objects(object_type="DataUsed")
    assert data_used == data_used_objects[0]


def test_read_and_write_station_magnitude():
    sm = obspy.read_events(str(DATA_DIR / "event_with_station_magnitude.xml"))[
        0
    ].station_magnitudes[0]

    db = DB(url="sqlite://:memory:")
    db += sm

    station_magnitudes = db.get_objects(object_type="StationMagnitude")
    assert sm == station_magnitudes[0]


def test_read_and_write_station_magnitude_contribution():
    smc = (
        obspy.read_events(
            str(DATA_DIR / "event_with_station_magnitude_contribution.xml")
        )[0]
        .magnitudes[0]
        .station_magnitude_contributions[0]
    )

    db = DB(url="sqlite://:memory:")
    db += smc

    station_magnitude_contributions = db.get_objects(
        object_type="StationMagnitudeContribution"
    )
    assert smc == station_magnitude_contributions[0]


@pytest.mark.parametrize(
    "filename",
    [
        "iris_events.xml",
        "neries_events.xml",
        "usgs_event.xml",
        "event_with_preferred_ids.xml",
        "qml-example-1.2-RC3.xml",
        "quakeml_1.2_event.xml",
        "event_with_station_magnitude.xml",
        "event_with_station_magnitude_contribution.xml",
    ],
)
def test_round_trip_whole_files(filename):
    """
    Test round-tripping full events. Makes it easy to test a larger variety of
    events.
    """
    cat = obspy.read_events(str(DATA_DIR / filename))
    assert len(cat.events)

    db = DB(url="sqlite://:memory:")

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    events = db.get_objects(object_type="Event")

    # Sort both.
    cat.events = sorted(cat.events, key=lambda x: x.resource_id.resource_id)
    events = sorted(cat.events, key=lambda x: x.resource_id.resource_id)

    assert len(events) == len(cat.events)
    assert cat.events == events


def test_save_as_quakeml(tmp_path):
    cat = obspy.read_events(str(DATA_DIR / "neries_events.xml"))
    assert len(cat.events)
    db = DB(url="sqlite://:memory:")

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    db.dump_as_quakeml_files(folder=tmp_path / "quakeml")


def test_count():
    cat = obspy.read_events(str(DATA_DIR / "neries_events.xml"))
    assert len(cat.events) == 3
    db = DB(url="sqlite://:memory:")

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    assert db.count("Event") == 3
    assert db.count("Origin") == 3
    assert db.count("Magnitude") == 3


def test_round_trip_whole_event_to_disc(tmp_path):
    """
    Make sure a whole event can be serialized to a database on disc and be read
    again.
    """
    cat = obspy.read_events(str(DATA_DIR / "iris_events.xml"))
    assert len(cat.events)

    db_path = tmp_path / "db.sqlite"

    db = DB(url=f"sqlite://{db_path}")

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    # Close and reopen to retrieve.
    del db
    db2 = DB(url=f"sqlite://{db_path}")
    events = db2.get_objects(object_type="Event")

    # Sort both.
    cat.events = sorted(cat.events, key=lambda x: x.resource_id.resource_id)
    events = sorted(cat.events, key=lambda x: x.resource_id.resource_id)

    assert len(events) == len(cat.events)
    assert cat.events == events


def test_get_event_summary_real():
    cat = obspy.read_events(str(DATA_DIR / "neries_events.xml"))
    assert len(cat.events) == 3

    db = DB(url="sqlite://:memory:")

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    cat.events = sorted(cat.events, key=lambda e: e.origins[0].time)

    summary = db.get_event_summary()
    assert summary == [
        {
            "event_resource_id": event.resource_id.resource_id,
            "latitude": event.origins[0].latitude,
            "longitude": event.origins[0].longitude,
            "depth": event.origins[0].depth,
            "origin_time": event.origins[0].time,
            "origin_count": 1,
        }
        for event in cat.events
    ]


def test_get_event_summary_constructed():
    event1 = obspy.core.event.Event()
    event1.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(0), latitude=7.0, longitude=8.0, depth=9.0
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(20),
            latitude=31.034,
            longitude=12.0,
            depth=10020.0,
        ),
    ]

    event2 = obspy.core.event.Event()
    event2.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(-20),
            latitude=1.0,
            longitude=2.0,
            depth=3.0,
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(40),
            latitude=31.034,
            longitude=12.0,
            depth=10020.0,
        ),
    ]

    event3 = obspy.core.event.Event()
    event3.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(70),
            latitude=32.034,
            longitude=12.0,
            depth=10020.0,
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(-10),
            latitude=4.0,
            longitude=5.0,
            depth=6.0,
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(100),
            latitude=44.0,
            longitude=5.0,
            depth=6.0,
        ),
    ]

    db = DB(url="sqlite://:memory:")
    db += event1
    db += event2
    db += event3

    event_summary = db.get_event_summary()

    # Make sure the order is correct.
    assert event_summary == [
        {
            "event_resource_id": event2.resource_id.resource_id,
            "latitude": 1.0,
            "longitude": 2.0,
            "depth": 3.0,
            "origin_time": obspy.UTCDateTime(-20),
            "origin_count": 2,
        },
        {
            "event_resource_id": event3.resource_id.resource_id,
            "latitude": 4.0,
            "longitude": 5.0,
            "depth": 6.0,
            "origin_time": obspy.UTCDateTime(-10),
            "origin_count": 3,
        },
        {
            "event_resource_id": event1.resource_id.resource_id,
            "latitude": 7.0,
            "longitude": 8.0,
            "depth": 9.0,
            "origin_time": obspy.UTCDateTime(0),
            "origin_count": 2,
        },
    ]


def test_get_event_summary_returns_preferred_origin():
    # Event 1 - the preferred origin is the second.
    event1 = obspy.core.event.Event(resource_id="event1")
    event1.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(0), latitude=7.0, longitude=8.0, depth=9.0
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(20),
            latitude=31.034,
            longitude=12.0,
            depth=10020.0,
        ),
    ]
    event1.preferred_origin_id = event1.origins[1].resource_id

    # Event 2 - the preferred origin is the first.
    event2 = obspy.core.event.Event(resource_id="event2")
    event2.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(-20),
            latitude=1.0,
            longitude=2.0,
            depth=3.0,
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(40),
            latitude=31.034,
            longitude=12.0,
            depth=10020.0,
        ),
    ]
    event2.preferred_origin_id = event2.origins[0].resource_id

    # Event 3 - no preferred origin - Should pick the second one with the
    # earlier origin time.
    event3 = obspy.core.event.Event(resource_id="event3")
    event3.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(70),
            latitude=32.034,
            longitude=12.0,
            depth=10020.0,
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(-10),
            latitude=4.0,
            longitude=5.0,
            depth=6.0,
        ),
    ]

    db = DB(url="sqlite://:memory:")
    db += event1
    db += event2
    db += event3

    event_summary = db.get_event_summary()
    assert event_summary == [
        {
            "event_resource_id": "event2",
            "latitude": 1.0,
            "longitude": 2.0,
            "depth": 3.0,
            "origin_time": obspy.UTCDateTime(1969, 12, 31, 23, 59, 40),
            "origin_count": 2,
        },
        {
            "event_resource_id": "event3",
            "latitude": 4.0,
            "longitude": 5.0,
            "depth": 6.0,
            "origin_time": obspy.UTCDateTime(1969, 12, 31, 23, 59, 50),
            "origin_count": 2,
        },
        {
            "event_resource_id": "event1",
            "latitude": 31.034,
            "longitude": 12.0,
            "depth": 10020.0,
            "origin_time": obspy.UTCDateTime(1970, 1, 1, 0, 0, 20),
            "origin_count": 2,
        },
    ]


def test_get_event_by_resource_id():
    cat = obspy.read_events(str(DATA_DIR / "neries_events.xml"))
    assert len(cat.events) == 3

    db = DB(url="sqlite://:memory:")

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    assert (
        db.get_event_by_resource_id(resource_id=cat.events[2].resource_id)
        == cat.events[2]
    )
    assert (
        db.get_event_by_resource_id(resource_id=str(cat.events[0].resource_id))
        == cat.events[0]
    )


def test_write_origin_and_check_internal_structure():
    event = obspy.core.event.Event()
    event.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(), latitude=32.034, longitude=12.0, depth=10020.0
        )
    ]
    # Make sure the QuakeML file would be valid.
    with io.BytesIO() as buf:
        event.write(buf, format="quakeml", validate=True)

    assert len(event.origins) == 1

    db = DB(url="sqlite://:memory:")
    db += event

    assert db.count("Event") == 1
    assert db.count("Origin") == 1
    assert db.count("OriginReference") == 1

    # Now look at the internal structure.
    o_ref_oid, o_ref_p_oid, o_ref_origin_id = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid, originID from OriginReference"
    ).fetchall()[0]

    assert o_ref_origin_id == event.origins[0].resource_id.resource_id

    event_oid, event_p_oid = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid from Event"
    ).fetchall()[0]

    origin_oid, origin_p_oid = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid from Origin"
    ).fetchall()[0]

    # Should all be unique.
    assert event_oid > 1
    assert origin_oid > 1
    assert o_ref_oid > 1
    assert len({event_oid, origin_oid, o_ref_oid}) == 3

    # Origin parent id should be the event.
    assert o_ref_p_oid == event_oid

    # Event and origin should have the root EventParameters objects as the
    # parent.
    assert event_p_oid == 1
    assert origin_p_oid == 1

    # Can of course still be retrieved.
    events = db.get_objects(object_type="Event")
    assert len(events) == 1
    new_event = events[0]
    assert len(new_event.origins) == 1

    assert event == new_event


def test_write_focal_mechanism_and_check_internal_structure():
    event = obspy.core.event.Event()
    event.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(), latitude=32.034, longitude=12.0, depth=10020.0
        )
    ]
    event.focal_mechanisms = [
        obspy.core.event.source.FocalMechanism(
            misfit=2.0, triggering_origin_id=event.origins[0].resource_id
        )
    ]
    # Make sure the QuakeML file would be valid.
    with io.BytesIO() as buf:
        event.write(buf, format="quakeml", validate=True)

    assert len(event.focal_mechanisms) == 1
    assert len(event.origins) == 1

    db = DB(url="sqlite://:memory:")
    db += event

    assert db.count("Event") == 1
    assert db.count("FocalMechanism") == 1
    assert db.count("Origin") == 1
    assert db.count("OriginReference") == 1
    assert db.count("FocalMechanismReference") == 1

    # Now look at the internal structure.
    o_ref_oid, o_ref_p_oid, o_ref_origin_id = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid, originID from OriginReference"
    ).fetchall()[0]
    fm_ref_oid, fm_ref_p_oid, fm_ref_origin_id = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid, focalMechanismID from FocalMechanismReference"
    ).fetchall()[0]

    assert o_ref_origin_id == event.origins[0].resource_id.resource_id
    assert fm_ref_origin_id == event.focal_mechanisms[0].resource_id.resource_id

    event_oid, event_p_oid = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid from Event"
    ).fetchall()[0]

    origin_oid, origin_p_oid = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid from Origin"
    ).fetchall()[0]
    fm_oid, fm_p_oid = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid from FocalMechanism"
    ).fetchall()[0]

    # Should all be unique.
    assert event_oid > 1
    assert origin_oid > 1
    assert o_ref_oid > 1
    assert fm_ref_oid > 1
    assert fm_oid > 1
    assert len({event_oid, origin_oid, o_ref_oid, fm_ref_oid, fm_oid}) == 5

    # Origin parent id should be the event.
    assert o_ref_p_oid == event_oid
    # Same with the focal mechanisms.
    assert fm_ref_p_oid == event_oid

    # Event and origin should have the root EventParameters objects as the
    # parent.
    assert event_p_oid == 1
    assert origin_p_oid == 1
    assert fm_p_oid == 1

    # Can of course still be retrieved.
    events = db.get_objects(object_type="Event")
    assert len(events) == 1
    new_event = events[0]
    assert len(new_event.origins) == 1
    assert len(new_event.focal_mechanisms) == 1

    assert event == new_event


def test_write_picks_and_check_internal_structure():
    event = obspy.core.event.Event()
    event.picks = [
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "A"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "B"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "C"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime() + 10,
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "D"),
        ),
    ]

    # Make sure the QuakeML file would be valid.
    with io.BytesIO() as buf:
        event.write(buf, format="quakeml", validate=True)

    assert len(event.picks) == 4

    db = DB(url="sqlite://:memory:")
    db += event

    assert db.count("Event") == 1
    assert db.count("Pick") == 4

    # Now check the database structure.
    e_oid, e_parent_oid = db._backend.cursor.execute(
        "SELECT _oid, _parent_oid from Event"
    ).fetchall()[0]
    assert e_parent_oid == 1
    assert e_oid != 1

    p = db._backend.cursor.execute("SELECT _oid, _parent_oid from Pick").fetchall()

    pick_parent_ids = [i[1] for i in p]

    # The only parent they have is the root event parameter object.
    assert pick_parent_ids == [1, 1, 1, 1]

    events = db.get_objects("Event")
    assert len(events) == 1
    new_event = events[0]

    # Pick, without arrivals, can no longer be retrieved.
    assert len(new_event.picks) == 0

    # Add an arrival
    del db
    db2 = DB(url="sqlite://:memory:")

    event.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(), latitude=32.034, longitude=12.0, depth=10020.0
        )
    ]
    event.origins[0].arrivals = [
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[1].resource_id, phase="P"
        ),
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[2].resource_id, phase="P"
        ),
    ]

    # Again make sure that it is valid.
    with io.BytesIO() as buf:
        event.write(buf, format="quakeml", validate=True)

    db2 += event

    assert db2.count("Event") == 1
    assert db2.count("Pick") == 4
    assert db2.count("Origin") == 1
    assert db2.count("Arrival") == 2

    # Now the retrieved event should have one pick (because one has an arrival).
    events = db2.get_objects("Event")
    assert len(events) == 1
    new_event = events[0]

    assert len(new_event.picks) == 2
    event.picks = event.picks[1:-1]
    assert event == new_event


def test_get_unassociated_picks():
    db = DB(url="sqlite://:memory:")

    event = obspy.core.event.Event()
    event.picks = [
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "A"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime() + 1,
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "B"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime() + 2,
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "C"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime() + 3,
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "D"),
        ),
    ]

    assert len(event.picks) == 4

    db += event
    assert db.get_unassociated_picks() == event.picks
    del db

    event.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(), latitude=32.034, longitude=12.0, depth=10020.0
        )
    ]
    event.origins[0].arrivals = [
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[1].resource_id, phase="P"
        ),
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[2].resource_id, phase="P"
        ),
    ]

    db2 = DB(url="sqlite://:memory:")
    db2 += event
    assert db2.get_unassociated_picks() == [event.picks[0], event.picks[3]]
    del db2

    event.origins[0].arrivals.extend(
        [
            obspy.core.event.Arrival(
                force_resource_id=True, pick_id=event.picks[0].resource_id, phase="P"
            ),
            obspy.core.event.Arrival(
                force_resource_id=True, pick_id=event.picks[3].resource_id, phase="P"
            ),
        ]
    )
    db3 = DB(url="sqlite://:memory:")
    db3 += event
    assert db3.get_unassociated_picks() == []


def test_delete_event():
    db = DB(url="sqlite://:memory:")
    # db = DB(url="sqlite://dude.sqlite")

    # Contains just the default database objects so far.
    assert db.count("PublicObject") == 8
    assert db.count("Object") == 8
    assert db.count("Event") == 0
    assert db.count("Comment") == 0

    event = obspy.core.event.Event()
    event.comments.append(
        obspy.core.event.Comment(text="hallo", force_resource_id=False)
    )
    db += event

    # One more public and one more private (comment) object.
    assert db.count("PublicObject") == 9
    assert db.count("Object") == 10
    assert db.count("Event") == 1
    assert db.count("Comment") == 1

    db.delete_objects(objects=[event])

    # Back to the status quo.
    assert db.count("PublicObject") == 8
    assert db.count("Object") == 8
    assert db.count("Event") == 0
    assert db.count("Comment") == 0


@pytest.mark.parametrize(
    "filename",
    [
        "iris_events.xml",
        "neries_events.xml",
        "usgs_event.xml",
        "event_with_preferred_ids.xml",
        "qml-example-1.2-RC3.xml",
        "quakeml_1.2_event.xml",
        "event_with_station_magnitude.xml",
        "event_with_station_magnitude_contribution.xml",
    ],
)
def test_round_trip_whole_files_and_delete_whole_files(filename):
    """
    Test round-tripping full events. Makes it easy to test a larger variety of
    events.
    """
    cat = obspy.read_events(str(DATA_DIR / filename))
    assert len(cat.events)

    db = DB(url="sqlite://:memory:")

    assert db.count("PublicObject") == 8
    assert db.count("Object") == 8
    assert db.count("Meta") == 2

    assert db._backend._count_all_rows_in_db() == 18

    for event in cat.events:
        # SeisComP cannot store amplitudes.
        for a in event.amplitudes:
            a.category = None
        db += event

    events = db.get_objects(object_type="Event")

    # Sort both.
    cat.events = sorted(cat.events, key=lambda x: x.resource_id.resource_id)
    events = sorted(cat.events, key=lambda x: x.resource_id.resource_id)

    assert len(events) == len(cat.events)
    assert cat.events == events

    # Delete everything.
    db.delete_objects(objects=cat.events)

    # Back to the status quo.
    assert db.count("PublicObject") == 8
    assert db.count("Object") == 8
    assert db.count("Meta") == 2
    assert db._backend._count_all_rows_in_db() == 18


def test_update_event_comments():
    db = DB(url="sqlite://:memory:")

    events = [obspy.core.event.Event(), obspy.core.event.Event()]

    events[0].comments = [
        obspy.core.event.Comment(text="A"),
        obspy.core.event.Comment(text="B"),
    ]
    events[1].comments = [
        obspy.core.event.Comment(text="C"),
        obspy.core.event.Comment(text="D"),
    ]

    db += events[0]
    db += events[1]

    assert db.count("Event") == 2
    assert db.count("Comment") == 4

    new_events = db.get_objects("Event")
    assert new_events == events

    events[1].comments = [
        obspy.core.event.Comment(text="E"),
        obspy.core.event.Comment(text="D"),
        obspy.core.event.Comment(text="F"),
    ]
    db.update_event_comments(event=events[1])

    assert db.count("Event") == 2
    assert db.count("Comment") == 5

    new_events = db.get_objects("Event")
    assert new_events == events


def test_write_and_read_same_picks_used_in_multiple_arrivals():
    event = obspy.core.event.Event()
    event.picks = [
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "A"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "B"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime(),
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "C"),
        ),
        obspy.core.event.Pick(
            time=obspy.UTCDateTime() + 10,
            waveform_id=obspy.core.event.base.WaveformStreamID("GM", "A", "B", "D"),
        ),
    ]

    event.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(), latitude=32.034, longitude=12.0, depth=10020.0
        ),
        obspy.core.event.Origin(
            time=obspy.UTCDateTime() + 2, latitude=32.034, longitude=12.0, depth=10020.0
        ),
    ]
    event.origins[0].arrivals = [
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[1].resource_id, phase="P"
        ),
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[2].resource_id, phase="P"
        ),
    ]

    event.origins[1].arrivals = [
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[1].resource_id, phase="P"
        ),
        obspy.core.event.Arrival(
            force_resource_id=True, pick_id=event.picks[3].resource_id, phase="P"
        ),
    ]

    # Again make sure that it is valid.
    with io.BytesIO() as buf:
        event.write(buf, format="quakeml", validate=True)

    db = DB(url="sqlite://:memory:")
    db += event

    events = db.get_objects("Event")
    assert len(events) == 1

    # unused pick.
    del event.picks[0]

    event
    events[0]

    # Now they are the same.
    assert event == events[0]


def test_add_origin_to_event_and_change_preferred_origin():
    """
    Just to make sure this works as expected.
    """
    event = obspy.core.event.Event()
    event.origins = [
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(), latitude=32.034, longitude=12.0, depth=10020.0
        )
    ]
    pref_id = event.origins[0].resource_id
    event.preferred_origin_id = pref_id
    assert event.preferred_origin() == event.origins[0]

    # Make sure the QuakeML file would be valid.
    with io.BytesIO() as buf:
        event.write(buf, format="quakeml", validate=True)

    db = DB(url="sqlite://:memory:")
    db += event

    assert db.count("Event") == 1
    assert db.count("Origin") == 1
    assert db.count("OriginReference") == 1

    assert db.get_objects(object_type="Event")[0] == event

    # Add a new origin.
    event.origins.append(
        obspy.core.event.Origin(
            time=obspy.UTCDateTime(10.0), latitude=33.034, longitude=32.0, depth=12020.0
        )
    )
    # Did not change the preferred origin yet.
    assert event.preferred_origin() == event.origins[0]

    new_pref_id = event.origins[1].resource_id
    event.preferred_origin_id = new_pref_id
    # Did change it.
    assert event.preferred_origin() == event.origins[1]

    # No change yet in the database.
    assert db.get_objects(object_type="Event")[0].preferred_origin() == event.origins[0]

    # Adding to the database should change it.
    db.update_event(event=event)
    assert db.get_objects(object_type="Event")[0] == event
    assert db.get_objects(object_type="Event")[0].preferred_origin() == event.preferred_origin()

    assert db.count("Event") == 1
    assert db.count("Origin") == 2
    assert db.count("OriginReference") == 2
