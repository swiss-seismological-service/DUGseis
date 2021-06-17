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
Implementation of a SQLite3 SeisComP compatible database able to store and
retrieve a subset of QuakeML.

This is not tuned to be as efficient as possible but rather to be correct and
maintaineable.
"""

import copy
import pathlib
import sqlite3
import typing
import warnings

import obspy

from .sqlite_parser import parse_sqlite_definition
from . import utils as db_utils

with (pathlib.Path(__file__).parent / "sqlite3.sql").open(mode="r") as f:
    SQLITE_DB_DEFINITION = f.read()

SQLITE_TABLES = parse_sqlite_definition(SQLITE_DB_DEFINITION)


# Parse to a list of column names for each table.
SQLITE_TABLE_COLUMNS = {}
for k, v in SQLITE_TABLES.items():
    column = []
    for key in v.schema.keys():
        if isinstance(key, str):
            column.append(key)
        else:
            column.append(key._schema)
    SQLITE_TABLE_COLUMNS[k] = column


class _SQLiteBackend:
    def __init__(self, connection: str):
        self.__db_definition: typing.Optional[str] = None

        self._connection_string = connection
        self.connection = sqlite3.connect(self._connection_string)
        self.cursor = self.connection.cursor()

        # Important for the cascaded delete to work.
        self.cursor.execute("PRAGMA foreign_keys=ON")

        self._init_tables()

        # Determine the default parent object which is the id of the
        # EventParameters "object". This is set by the init SQLite script.
        event_params = self.cursor.execute(
            "SELECT (_oid) from PublicObject WHERE publicID='EventParameters'"
        ).fetchall()
        assert len(event_params) == 1
        self._default_parent_id = event_params[0][0]

    def _init_tables(self):
        # Get existing tables and check if something needs to be done.
        tables = set(
            [
                i[0]
                for i in self.cursor.execute(
                    'SELECT name from sqlite_master where type= "table"'
                ).fetchall()
            ]
        )

        # These tables should exist in the database.
        expected_tables = set(SQLITE_TABLES.keys()).union({"sqlite_sequence"})

        if tables and tables != expected_tables:
            raise ValueError(
                "Invalid seiscomp compatible SQLite database. "
                f"Expected tables: {expected_tables}\n"
                f"Actual tables: {tables}\n"
            )

        if not tables:
            self.cursor.executescript(SQLITE_DB_DEFINITION)

            new_tables = set(
                [
                    i[0]
                    for i in self.cursor.execute(
                        'SELECT name from sqlite_master where type= "table"'
                    ).fetchall()
                ]
            )
            # Safety measure - should really not happen.
            if new_tables != expected_tables:
                raise RuntimeError(
                    "Invalid seiscomp database for a fresh DB!\n"
                    f"Expected tables: {expected_tables}\n"
                    f"Actual tables: {new_tables}\n"
                )

    def __del__(self):
        self.connection.close()

    def get_objects(
        self,
        object_type: str,
        where: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ):
        if object_type not in SQLITE_TABLES:
            raise ValueError(
                f"Unknown object type: {object_type}. "
                f"Known types: {list(SQLITE_TABLES.keys())}"
            )
        column_names = (
            SQLITE_TABLE_COLUMNS[object_type] + SQLITE_TABLE_COLUMNS["PublicObject"]
        )

        # Get all objects and join on the public ids.
        sql = f"""
        SELECT * FROM {object_type}
        LEFT JOIN PublicObject ON {object_type}._oid = PublicObject._oid
        """

        def to_str(v):
            if isinstance(v, str):
                return f"'{v}'"
            else:
                return str(v)

        if where:
            for key, value in where.items():
                name, clause = key.split("__")
                if clause == "in":
                    assert isinstance(value, (list, tuple))
                    sql += f" WHERE {name} IN ({', '.join(to_str(i) for i in value)})"
                elif clause == "eq":
                    sql += f" WHERE {name}='{value}'"
                else:
                    raise NotImplementedError(f"where key: {key}")

        results = []

        for row in self.cursor.execute(sql).fetchall():
            result = {}
            for name, r in zip(column_names, row):
                if name in result:
                    if result[name] == r or r is None:
                        continue
                    elif result[name] is None:
                        result[name] = r
                    else:
                        raise NotImplementedError(f"{result[name]} - {name} - {r}")
                else:
                    result[name] = r
            results.append(result)

        # Convert results dictionary to a waveform stream id.
        def wf(x: typing.Dict) -> typing.Optional[obspy.core.event.WaveformStreamID]:
            values = [
                x["waveformID_networkCode"],
                x["waveformID_stationCode"],
                x["waveformID_locationCode"],
                x["waveformID_channelCode"],
                x["waveformID_resourceURI"],
            ]
            if set(values) == {None}:
                return None
            return obspy.core.event.WaveformStreamID(
                network_code=values[0],
                station_code=values[1],
                location_code=values[2],
                channel_code=values[3],
                resource_uri=values[4],
            )

        # Result dict to a creation info.
        def ci(x: typing.Dict) -> typing.Optional[obspy.core.event.CreationInfo]:
            if x["creationInfo_used"] == 0:
                return None
            return obspy.core.event.CreationInfo(
                agency_id=x["creationInfo_agencyID"],
                agency_uri=obspy.core.event.ResourceIdentifier(
                    x["creationInfo_agencyURI"]
                )
                if x["creationInfo_agencyURI"]
                else None,
                author=x["creationInfo_author"],
                author_uri=obspy.core.event.ResourceIdentifier(
                    x["creationInfo_authorURI"]
                )
                if x["creationInfo_authorURI"]
                else None,
                creation_time=obspy.UTCDateTime(x["creationInfo_creationTime"])
                if x["creationInfo_creationTime"]
                else None,
                version=x["creationInfo_version"],
            )

        # Result dict to a quantity error.
        def qe(
            x: typing.Dict, name: str
        ) -> typing.Optional[obspy.core.event.QuantityError]:
            keys = (
                f"{name}_uncertainty",
                f"{name}_lowerUncertainty",
                f"{name}_upperUncertainty",
                f"{name}_confidenceLevel",
            )
            values = [x[k] for k in keys]
            if set(values) == {None}:
                return None
            return obspy.core.event.QuantityError(
                uncertainty=values[0],
                lower_uncertainty=values[1],
                upper_uncertainty=values[2],
                confidence_level=values[3],
            )

        def nodal_planes(x: typing.Dict) -> obspy.core.event.source.NodalPlanes:
            def nodal_plane(
                d: typing.Dict, p: int
            ) -> obspy.core.event.source.NodalPlane:
                kwargs = {}
                pre = f"nodalPlanes_nodalPlane{p}"
                for param in ["strike", "dip", "rake"]:
                    kwargs[param] = x[f"{pre}_{param}_value"]
                    kwargs[f"{param}_errors"] = qe(x, f"{pre}_{param}")
                return obspy.core.event.source.NodalPlane(**kwargs)

            return obspy.core.event.source.NodalPlanes(
                nodal_plane_1=nodal_plane(x, 1)
                if x["nodalPlanes_nodalPlane1_used"]
                else None,
                nodal_plane_2=nodal_plane(x, 2)
                if x["nodalPlanes_nodalPlane2_used"]
                else None,
                preferred_plane=x["nodalPlanes_preferredPlane"],
            )

        def principal_axes(x: typing.Dict) -> obspy.core.event.source.PrincipalAxes:
            def axis(d: typing.Dict, a: str) -> obspy.core.event.Axis:
                pre = f"principalAxes_{a}Axis"
                kwargs = {}
                for param in ["azimuth", "plunge", "length"]:
                    name = f"{pre}_{param}"
                    kwargs[param] = x[f"{name}_value"]
                    kwargs[f"{param}_errors"] = qe(x, name)

                return obspy.core.event.Axis(**kwargs)

            return obspy.core.event.source.PrincipalAxes(
                t_axis=axis(x, "t"),
                p_axis=axis(x, "p"),
                # Setting the empty Axis() object is a bit an oddity but
                # we just follow what ObsPy does here.
                n_axis=axis(x, "n")
                if x["principalAxes_nAxis_used"]
                else obspy.core.event.source.Axis(),
            )

        def rid_or_none(r: typing.Optional[obspy.core.event.ResourceIdentifier]):
            return obspy.core.event.ResourceIdentifier(r) if r is not None else None

        def to_tensor(x: typing.Dict) -> obspy.core.event.source.Tensor:
            d = {}
            for c in ["rr", "tt", "pp", "rt", "rp", "tp"]:
                k = f"tensor_M{c}"
                d[f"m_{c}"] = x[f"{k}_value"]
                d[f"m_{c}_errors"] = qe(x, k)
            return obspy.core.event.source.Tensor(**d)

        type_map = {
            "Pick": lambda x: obspy.core.event.Pick(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                time=obspy.UTCDateTime(x["time_value"]),
                time_errors=qe(x, "time"),
                waveform_id=wf(x),
                filter_id=x["filterID"],
                method_id=x["methodID"],
                horizontal_slowness=x["horizontalSlowness_value"],
                horizontal_slowness_errors=qe(x, "horizontalSlowness"),
                backazimuth=x["backazimuth_value"],
                backazimuth_errors=qe(x, "backazimuth"),
                slowness_method_id=x["slownessMethodID"],
                onset=x["onset"],
                phase_hint=x["phaseHint_code"],
                polarity=x["polarity"],
                evaluation_mode=x["evaluationMode"],
                evaluation_status=x["evaluationStatus"],
                # XXX: We still need to deal with the comments.
                comments=[],
                creation_info=ci(x),
            ),
            "Comment": lambda x: obspy.core.event.Comment(
                resource_id=rid_or_none(x["publicID"]),
                force_resource_id=False,
                text=x["text"].decode(),
                creation_info=ci(x),
            ),
            "Magnitude": lambda x: obspy.core.event.Magnitude(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                mag=x["magnitude_value"],
                mag_errors=qe(x, "magnitude"),
                magnitude_type=x["type"],
                origin_id=rid_or_none(x["originID"]),
                method_id=rid_or_none(x["methodID"]),
                station_count=x["stationCount"],
                azimuthal_gap=x["azimuthalGap"],
                evaluation_status=x["evaluationStatus"],
                creation_info=ci(x),
            ),
            "CompositeTime": lambda x: obspy.core.event.CompositeTime(
                year=x["year_value"],
                year_errors=qe(x, "year"),
                #
                month=x["month_value"],
                month_errors=qe(x, "month"),
                #
                day=x["day_value"],
                day_errors=qe(x, "day"),
                #
                hour=x["hour_value"],
                hour_errors=qe(x, "hour"),
                #
                minute=x["minute_value"],
                minute_errors=qe(x, "minute"),
                #
                second=x["second_value"],
                second_errors=qe(x, "second"),
                #
            ),
            "Origin": lambda x: obspy.core.event.Origin(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                time=obspy.UTCDateTime(x["time_value"]),
                time_errors=qe(x, "time"),
                longitude=x["longitude_value"],
                longitude_errors=qe(x, "longitude"),
                latitude=x["latitude_value"],
                latitude_errors=qe(x, "latitude"),
                depth=x["depth_value"],
                depth_errors=qe(x, "depth"),
                depth_type=x["depthType"],
                time_fixed=bool(x["timeFixed"]) if x["timeFixed"] is not None else None,
                epicenter_fixed=bool(x["epicenterFixed"])
                if x["epicenterFixed"] is not None
                else None,
                reference_system_id=rid_or_none(x["referenceSystemID"]),
                method_id=rid_or_none(x["methodID"]),
                earth_model_id=rid_or_none(x["earthModelID"]),
                quality=obspy.core.event.OriginQuality(
                    associated_phase_count=x["quality_associatedPhaseCount"],
                    used_phase_count=x["quality_usedPhaseCount"],
                    associated_station_count=x["quality_associatedStationCount"],
                    used_station_count=x["quality_usedStationCount"],
                    depth_phase_count=x["quality_depthPhaseCount"],
                    standard_error=x["quality_standardError"],
                    azimuthal_gap=x["quality_azimuthalGap"],
                    secondary_azimuthal_gap=x["quality_secondaryAzimuthalGap"],
                    ground_truth_level=x["quality_groundTruthLevel"],
                    minimum_distance=x["quality_minimumDistance"],
                    maximum_distance=x["quality_maximumDistance"],
                    median_distance=x["quality_medianDistance"],
                )
                if x["quality_used"]
                else None,
                origin_type=x["type"],
                origin_uncertainty=obspy.core.event.OriginUncertainty(
                    horizontal_uncertainty=x["uncertainty_horizontalUncertainty"],
                    min_horizontal_uncertainty=x[
                        "uncertainty_minHorizontalUncertainty"
                    ],
                    max_horizontal_uncertainty=x[
                        "uncertainty_maxHorizontalUncertainty"
                    ],
                    azimuth_max_horizontal_uncertainty=x[
                        "uncertainty_azimuthMaxHorizontalUncertainty"
                    ],
                    confidence_ellipsoid=obspy.core.event.ConfidenceEllipsoid(
                        semi_major_axis_length=x[
                            "uncertainty_confidenceEllipsoid_semiMajorAxisLength"
                        ],
                        semi_minor_axis_length=x[
                            "uncertainty_confidenceEllipsoid_semiMinorAxisLength"
                        ],
                        semi_intermediate_axis_length=x[
                            "uncertainty_confidenceEllipsoid_semiIntermediateAxisLength"
                        ],
                        major_axis_plunge=x[
                            "uncertainty_confidenceEllipsoid_majorAxisPlunge"
                        ],
                        major_axis_azimuth=x[
                            "uncertainty_confidenceEllipsoid_majorAxisAzimuth"
                        ],
                        major_axis_rotation=x[
                            "uncertainty_confidenceEllipsoid_majorAxisRotation"
                        ],
                    )
                    if x["uncertainty_confidenceEllipsoid_used"]
                    else None,
                    preferred_description=x["uncertainty_preferredDescription"],
                )
                if x["quality_used"]
                else None,
                evaluation_mode=x["evaluationMode"],
                evaluation_status=x["evaluationStatus"],
                creation_info=ci(x),
            ),
            "Arrival": lambda x: obspy.core.event.Arrival(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                pick_id=obspy.core.event.ResourceIdentifier(x["pickID"]),
                phase=x["phase_code"],
                time_correction=x["timeCorrection"],
                azimuth=x["azimuth"],
                distance=x["distance"],
                takeoff_angle=x["takeOffAngle"],
                time_residual=x["timeResidual"],
                horizontal_slowness_residual=x["horizontalSlownessResidual"],
                backazimuth_residual=x["backazimuthResidual"],
                # XXX: We don't fill in these because they don't exist in the DB
                # schema.
                # takeoff_angle_errors=...,
                # time_weight=...,
                # horizontal_slowness_weight=...,
                # backazimuth_weight=...,
                earth_model_id=rid_or_none(x["earthModelID"]),
                creation_info=ci(x),
            ),
            "Event": lambda x: obspy.core.event.Event(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                preferred_origin_id=rid_or_none(x["preferredOriginID"]),
                preferred_magnitude_id=rid_or_none(x["preferredMagnitudeID"]),
                preferred_focal_mechanism_id=rid_or_none(
                    x["preferredFocalMechanismID"]
                ),
                event_type=x["type"],
                event_type_certainty=x["typeCertainty"],
                creation_info=ci(x),
            ),
            "EventDescription": lambda x: obspy.core.event.EventDescription(
                text=x["text"], type=x["type"]
            ),
            "MomentTensor": lambda x: obspy.core.event.MomentTensor(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                derived_origin_id=obspy.core.event.ResourceIdentifier(
                    x["derivedOriginID"]
                ),
                moment_magnitude_id=rid_or_none(x["momentMagnitudeID"]),
                scalar_moment=x["scalarMoment_value"],
                scalar_moment_errors=qe(x, "scalarMoment"),
                tensor=to_tensor(x) if x["tensor_used"] == 1 else None,
                variance=x["variance"],
                variance_reduction=x["varianceReduction"],
                double_couple=x["doubleCouple"],
                clvd=x["clvd"],
                iso=x["iso"],
                greens_function_id=rid_or_none(x["greensFunctionID"]),
                filter_id=rid_or_none(x["filterID"]),
                source_time_function=obspy.core.event.source.SourceTimeFunction()
                if x["sourceTimeFunction_used"] == 1
                else None,
                method_id=rid_or_none(x["methodID"]),
            ),
            "FocalMechanism": lambda x: obspy.core.event.FocalMechanism(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                triggering_origin_id=rid_or_none(x["triggeringOriginID"]),
                nodal_planes=nodal_planes(x) if x["nodalPlanes_used"] else None,
                principal_axes=principal_axes(x) if x["principalAxes_used"] else None,
                azimuthal_gap=x["azimuthalGap"],
                station_polarity_count=x["stationPolarityCount"],
                misfit=x["misfit"],
                station_distribution_ratio=x["stationDistributionRatio"],
                method_id=rid_or_none(x["methodID"]),
                evaluation_mode=x["evaluationMode"],
                evaluation_status=x["evaluationStatus"],
                creation_info=ci(x),
            ),
            "Amplitude": lambda x: obspy.core.event.magnitude.Amplitude(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                generic_amplitude=x["amplitude_value"],
                generic_amplitude_errors=qe(x, "amplitude"),
                type=x["type"],
                unit=x["unit"],
                method_id=rid_or_none(x["methodID"]),
                period=x["period_value"],
                period_errors=qe(x, "period"),
                snr=x["snr"],
                time_window=obspy.core.event.base.TimeWindow(
                    begin=x["timeWindow_begin"],
                    end=x["timeWindow_end"],
                    reference=x["timeWindow_reference"],
                )
                if x["timeWindow_used"]
                else None,
                pick_id=rid_or_none(x["pickID"]),
                waveform_id=wf(x),
                filter_id=rid_or_none(x["filterID"]),
                scaling_time=x["scalingTime_value"],
                scaling_time_errors=qe(x, "scalingTime"),
                magnitude_hint=x["magnitudeHint"],
                evaluation_mode=x["evaluationMode"],
                creation_info=ci(x),
            ),
            "DataUsed": lambda x: obspy.core.event.DataUsed(
                wave_type=x["waveType"],
                station_count=x["stationCount"],
                component_count=x["componentCount"],
                shortest_period=x["shortestPeriod"],
            ),
            "StationMagnitude": lambda x: obspy.core.event.magnitude.StationMagnitude(
                resource_id=obspy.core.event.ResourceIdentifier(x["publicID"]),
                origin_id=rid_or_none(x["originID"]),
                mag=x["magnitude_value"],
                mag_errors=qe(x, "magnitude"),
                station_magnitude_type=x["type"],
                amplitude_id=rid_or_none(x["amplitudeID"]),
                method_id=rid_or_none(x["methodID"]),
                waveform_id=wf(x),
                creation_info=ci(x),
            ),
            "StationMagnitudeContribution": lambda x: obspy.core.event.magnitude.StationMagnitudeContribution(
                station_magnitude_id=rid_or_none(x["stationMagnitudeID"]),
                residual=x["residual"],
                weight=x["weight"],
            ),
        }

        def to_object(o_type: str, r):
            obj = type_map[o_type](r)

            # Set the DB object id + parent object id at the objects.
            # Required for some of the following queries.
            object.__setattr__(obj, "_object_id", r["_oid"])
            object.__setattr__(obj, "_parent_object_id", r["_parent_oid"])

            return obj

        object_results = [to_object(o_type=object_type, r=r) for r in results]
        if not object_results:
            return []

        attribute_map = {
            "comments": "Comment",
            "composite_times": "CompositeTime",
            "arrivals": "Arrival",
            "station_magnitude_contributions": "StationMagnitudeContribution",
            "event_descriptions": "EventDescription",
            "picks": "Pick",
            "amplitudes": "Amplitude",
            "focal_mechanisms": "FocalMechanism",
            "origins": "Origin",
            "magnitudes": "Magnitude",
            "station_magnitudes": "StationMagnitude",
            "data_used": "DataUsed",
            "moment_tensor": "MomentTensor",
        }

        containers = copy.copy(object_results[0]._containers)
        # The focal mechanism is a bit different.
        if isinstance(object_results[0], obspy.core.event.source.FocalMechanism):
            containers = ["comments", "moment_tensor"]

        # Now we need to reconstruct any potential direct child objects. The
        # child objects themselves will take care to retrieve their own
        # children. In the ObsPy objects the direct children are collected in
        # the "_containers" attribute so we can just use that.
        for object_attribute_name in containers:
            object_type_name = attribute_map[object_attribute_name]
            # Find all child comments to be able to reconstruct the whole object.
            parent_ids = []

            # Some objects require special treatment.
            if object_type_name == "Origin":
                # Origins are stored via origin references.
                origin_refs = self.cursor.execute(
                    "SELECT _oid, _parent_oid, originID from OriginReference "
                    f"WHERE _parent_oid in ({','.join(['?'] * len(object_results))})",
                    [o._object_id for o in object_results],
                ).fetchall()
                if origin_refs:
                    # Get all these origins.
                    origins = self.get_objects(
                        object_type="Origin",
                        where={"publicID__in": [i[2] for i in origin_refs]},
                    )
                    assert len(origins) == len(origin_refs)
                    # Assign them all to the correct events.
                    for origin in origins:
                        rid = origin.resource_id.resource_id
                        ref = [r for r in origin_refs if r[2] == rid][0]
                        for o in object_results:
                            if o._object_id != ref[1]:
                                continue
                            o.origins.append(origin)
                            break
                        else:
                            raise NotImplementedError("Should not happen")

            elif object_type_name == "FocalMechanism":
                # Focal mechanisms are stored via focal mechanisms refs.
                fm_refs = self.cursor.execute(
                    "SELECT _oid, _parent_oid, focalMechanismID from FocalMechanismReference "
                    f"WHERE _parent_oid in ({','.join(['?'] * len(object_results))})",
                    [o._object_id for o in object_results],
                ).fetchall()
                if fm_refs:
                    # Get all these origins.
                    fms = self.get_objects(
                        object_type="FocalMechanism",
                        where={"publicID__in": [i[2] for i in fm_refs]},
                    )
                    assert len(fms) == len(fm_refs)
                    # Assign them all to the correct events.
                    for fm in fms:
                        rid = fm.resource_id.resource_id
                        ref = [r for r in fm_refs if r[2] == rid][0]
                        for o in object_results:
                            if o._object_id != ref[1]:
                                continue
                            o.focal_mechanisms.append(fm)
                            break
                        else:
                            raise NotImplementedError("Should not happen")

            elif object_type_name == "Pick" and object_type == "Event":
                # Picks can only be retrieved via arrivals and origins. So we
                # are having fun with queries now.
                sql = f"""
                SELECT OriginReference._parent_oid, Arrival.pickID, p_object._oid
                FROM OriginReference
                INNER JOIN PublicObject
                    ON PublicObject.publicID = OriginReference.originID
                INNER JOIN Origin
                    ON Origin._oid = PublicObject._oid
                INNER JOIN Arrival
                    ON Arrival._parent_oid = Origin._oid
                INNER JOIN PublicObject p_object
                    ON p_object.publicID = Arrival.pickID
                WHERE OriginReference._parent_oid in ({','.join(['?'] * len(object_results))})
                """
                r = self.cursor.execute(
                    sql,
                    [o._object_id for o in object_results],
                ).fetchall()
                if r:
                    pick_id_to_event_oid = {i[1]: i[0] for i in r}
                    pick_objects = self.get_objects(
                        object_type="Pick", where={"Pick._oid__in": [i[2] for i in r]}
                    )
                    # Now assign the pick objects to the events.
                    for pick in pick_objects:
                        event_oid = pick_id_to_event_oid[pick.resource_id.resource_id]
                        for o in object_results:
                            if o._object_id == event_oid:
                                o.picks.append(pick)
                                break
                        else:
                            raise NotImplementedError

            else:
                for o in object_results:
                    if hasattr(o, object_attribute_name):
                        parent_ids.append(o._object_id)

                if parent_ids:
                    # Get all child objects.
                    child_objects = self.get_objects(
                        object_type=object_type_name,
                        where={
                            "_parent_oid__in": [i._object_id for i in object_results]
                        },
                    )
                    # Got to find the correct object for it. This loop might need some
                    # speeding up but it might also be fine.
                    for child_object in child_objects:
                        for o in object_results:
                            if o._object_id == child_object._parent_object_id:
                                # The moment tensor object falls a bit out of line.
                                if object_attribute_name == "moment_tensor":
                                    o.moment_tensor = child_object
                                else:
                                    getattr(o, object_attribute_name).append(
                                        child_object
                                    )
                                break
                        else:
                            # Should, by construction of the query, not happen.
                            raise ValueError(
                                f"Could not find parent object with id {child_object._parent_object_id}."
                            )

        return object_results

    def add_object(
        self, obj, parent_object_id: typing.Optional[int] = None, commit: bool = True
    ) -> int:
        def _expand_errors(
            v: obspy.core.event.QuantityError, k: str
        ) -> typing.Dict[str, typing.Any]:
            """
            Helper function to expand quantity errors.
            """
            assert isinstance(v, obspy.core.event.QuantityError)
            assert k.endswith("_errors")
            k = k[:-7]

            d = {}

            if v.uncertainty is not None:
                d[f"{k}_uncertainty"] = v.uncertainty
            if v.lower_uncertainty is not None:
                d[f"{k}_lowerUncertainty"] = v.lower_uncertainty
            if v.upper_uncertainty is not None:
                d[f"{k}_upperUncertainty"] = v.upper_uncertainty
            if v.confidence_level is not None:
                d[f"{k}_confidenceLevel"] = v.confidence_level

            return d

        def common_transforms(d):
            d = _common_transforms(d)
            # Get rid of all None values.
            return {k: v for k, v in d.items() if v is not None}

        def _common_transforms(d):
            """
            Collection of transforms common to many database items.
            """
            new_d = {}
            for k, v in d.items():
                # Skip None's - will be set to NULL in the DB in any case.
                if v is None:
                    continue
                # Map waveform ids.
                if k == "waveformID":
                    new_d["waveformID_networkCode"] = v.network_code
                    new_d["waveformID_stationCode"] = v.station_code
                    if v.location_code is not None:
                        new_d["waveformID_locationCode"] = v.location_code
                    if v.channel_code is not None:
                        new_d["waveformID_channelCode"] = v.channel_code
                    if v.resource_uri is not None:
                        new_d["waveformID_resourceURI"] = v.resource_uri.resource_id
                # Times always have two entries.
                elif isinstance(v, obspy.UTCDateTime):
                    new_d[k] = str(v)
                    new_d[f"{k}_ms"] = v.ns // 1000000
                elif isinstance(v, obspy.core.event.ResourceIdentifier):
                    new_d[k] = v.resource_id
                elif isinstance(v, obspy.core.event.source.SourceTimeFunction):
                    breakpoint()
                    pass
                elif isinstance(v, obspy.core.event.source.NodalPlanes):
                    new_d["nodalPlanes_preferredPlane"] = v.preferred_plane
                    for i in [1, 2]:
                        plane = getattr(v, f"nodal_plane_{i}")
                        if plane is None:
                            new_d[f"nodalPlanes_nodalPlane{i}_used"] = 0
                        else:
                            new_d[f"nodalPlanes_nodalPlane{i}_used"] = 1
                            for p in ["strike", "dip", "rake"]:
                                new_d[f"nodalPlanes_nodalPlane{i}_{p}_value"] = getattr(
                                    plane, p
                                )
                                err = getattr(plane, f"{p}_errors")
                                if err is not None:
                                    new_d.update(
                                        _expand_errors(
                                            v=err,
                                            k=f"nodalPlanes_nodalPlane{i}_{p}_errors",
                                        )
                                    )
                elif isinstance(v, obspy.core.event.source.PrincipalAxes):
                    # This is the only optional axes.
                    new_d["principalAxes_nAxis_used"] = 1 if v.n_axis else 0
                    for letter in ["t", "p", "n"]:
                        axis = getattr(v, f"{letter}_axis")
                        pre = f"principalAxes_{letter}Axis"
                        for c in ["azimuth", "plunge", "length"]:
                            new_d[f"{pre}_{c}_value"] = getattr(axis, c)
                            err = getattr(axis, f"{c}_errors")
                            if err is not None:
                                new_d.update(
                                    _expand_errors(v=err, k=f"{pre}_{c}_errors")
                                )
                elif isinstance(v, obspy.core.event.source.Tensor):
                    for c in ["rr", "tt", "pp", "rt", "rp", "tp"]:
                        new_d[f"tensor_M{c}_value"] = getattr(v, f"m_{c}")
                        err_key = f"m_{c}_errors"
                        err = getattr(v, err_key)
                        if err is not None:
                            new_d.update(_expand_errors(v=err, k=err_key))
                elif isinstance(v, obspy.core.event.OriginQuality):
                    new_d["quality_associatedPhaseCount"] = v.associated_phase_count
                    new_d["quality_usedPhaseCount"] = v.used_phase_count
                    new_d["quality_associatedStationCount"] = v.associated_station_count
                    new_d["quality_usedStationCount"] = v.used_station_count
                    new_d["quality_depthPhaseCount"] = v.depth_phase_count
                    new_d["quality_standardError"] = v.standard_error
                    new_d["quality_azimuthalGap"] = v.azimuthal_gap
                    new_d["quality_secondaryAzimuthalGap"] = v.secondary_azimuthal_gap
                    new_d["quality_groundTruthLevel"] = v.ground_truth_level
                    new_d["quality_maximumDistance"] = v.maximum_distance
                    new_d["quality_minimumDistance"] = v.minimum_distance
                    new_d["quality_medianDistance"] = v.median_distance
                elif isinstance(v, obspy.core.event.OriginUncertainty):
                    # Might include a confidence ellipsoid.
                    if v.confidence_ellipsoid is not None:
                        e = v.confidence_ellipsoid
                        new_d["uncertainty_confidenceEllipsoid_used"] = 1
                        new_d[
                            "uncertainty_confidenceEllipsoid_semiMajorAxisLength"
                        ] = e.semi_major_axis_length
                        new_d[
                            "uncertainty_confidenceEllipsoid_semiMinorAxisLength"
                        ] = e.semi_minor_axis_length
                        new_d[
                            "uncertainty_confidenceEllipsoid_semiIntermediateAxisLength"
                        ] = e.semi_intermediate_axis_length
                        new_d[
                            "uncertainty_confidenceEllipsoid_majorAxisPlunge"
                        ] = e.major_axis_plunge
                        new_d[
                            "uncertainty_confidenceEllipsoid_majorAxisAzimuth"
                        ] = e.major_axis_azimuth
                        new_d[
                            "uncertainty_confidenceEllipsoid_majorAxisRotation"
                        ] = e.major_axis_rotation
                    else:
                        new_d["uncertainty_confidenceEllipsoid_used"] = 0

                    if v.confidence_level is not None:
                        warnings.warn(
                            "The confidence level attribute in OriginUncertainty objects is not "
                            "supported by the Seiscomp database."
                        )

                    new_d["uncertainty_preferredDescription"] = v.preferred_description
                    new_d[
                        "uncertainty_horizontalUncertainty"
                    ] = v.horizontal_uncertainty
                    new_d[
                        "uncertainty_minHorizontalUncertainty"
                    ] = v.min_horizontal_uncertainty
                    new_d[
                        "uncertainty_maxHorizontalUncertainty"
                    ] = v.max_horizontal_uncertainty
                    new_d[
                        "uncertainty_azimuthMaxHorizontalUncertainty"
                    ] = v.azimuth_max_horizontal_uncertainty

                # Creation info.
                elif k == "creationInfo":
                    assert isinstance(v, obspy.core.event.CreationInfo)
                    has_creation_info = False
                    if v.agency_id is not None:
                        new_d["creationInfo_agencyID"] = v.agency_id
                        has_creation_info = True
                    if v.agency_uri is not None:
                        new_d["creationInfo_agencyURI"] = v.agency_uri.resource_id
                        has_creation_info = True
                    if v.author is not None:
                        new_d["creationInfo_author"] = v.author
                        has_creation_info = True
                    if v.author_uri is not None:
                        new_d["creationInfo_authorURI"] = v.author_uri.resource_id
                        has_creation_info = True
                    if v.creation_time is not None:
                        new_d.update(
                            common_transforms(
                                {"creationInfo_creationTime": v.creation_time}
                            )
                        )
                        has_creation_info = True
                    if v.version is not None:
                        new_d["creationInfo_version"] = v.version
                        has_creation_info = True

                    if has_creation_info:
                        new_d["creationInfo_used"] = 1
                # Expand all errors.
                elif k.endswith("_errors"):
                    new_d.update(_expand_errors(v=v, k=k))
                elif v is not None:
                    new_d[k] = v
            return new_d

        def bool_or_none(v):
            if v is True:
                return 1
            elif v is False:
                return 0
            elif v is None:
                return None
            else:
                raise NotImplementedError(f"{type(v)} - {v}")

        # Define how ObsPy objects are mapped to their database representation.
        type_map = {
            obspy.core.event.Pick: (
                "Pick",
                lambda pick: {
                    "time_value": pick.time,
                    "time_errors": pick.time_errors if pick.time_errors else None,
                    "waveformID": pick.waveform_id,
                    "filterID": pick.filter_id,
                    "methodID": pick.method_id,
                    "phaseHint_code": pick.phase_hint,
                    "phaseHint_used": 1 if pick.phase_hint else 0,
                    "backazimuth_value": pick.backazimuth,
                    "backazimuth_errors": pick.backazimuth_errors
                    if pick.backazimuth_errors
                    else None,
                    "onset": pick.onset,
                    "polarity": pick.polarity,
                    "evaluationMode": pick.evaluation_mode,
                    "evaluationStatus": pick.evaluation_status,
                    "creationInfo": pick.creation_info,
                },
            ),
            obspy.core.event.Comment: (
                "Comment",
                lambda comment: {
                    "creationInfo": comment.creation_info,
                    "text": comment.text.encode(),
                    "id": comment.resource_id,
                },
            ),
            obspy.core.event.Magnitude: (
                "Magnitude",
                lambda magnitude: {
                    "magnitude_value": magnitude.mag,
                    "magnitude_errors": magnitude.mag_errors,
                    "type": magnitude.magnitude_type,
                    "originID": magnitude.origin_id,
                    "methodID": magnitude.method_id,
                    "stationCount": magnitude.station_count,
                    "evaluationStatus": magnitude.evaluation_status,
                    "azimuthalGap": magnitude.azimuthal_gap,
                    "creationInfo": magnitude.creation_info,
                },
            ),
            obspy.core.event.CompositeTime: (
                "CompositeTime",
                lambda ct: {
                    "year_value": ct.year,
                    "year_errors": ct.year_errors,
                    "year_used": 1 if ct.year is not None else 0,
                    #
                    "month_value": ct.month,
                    "month_errors": ct.month_errors,
                    "month_used": 1 if ct.month is not None else 0,
                    #
                    "day_value": ct.day,
                    "day_errors": ct.day_errors,
                    "day_used": 1 if ct.day is not None else 0,
                    #
                    "hour_value": ct.hour,
                    "hour_errors": ct.hour_errors,
                    "hour_used": 1 if ct.hour is not None else 0,
                    #
                    "minute_value": ct.minute,
                    "minute_errors": ct.minute_errors,
                    "minute_used": 1 if ct.minute is not None else 0,
                    #
                    "second_value": ct.second,
                    "second_errors": ct.second_errors,
                    "second_used": 1 if ct.second is not None else 0,
                },
            ),
            obspy.core.event.Origin: (
                "Origin",
                lambda origin: {
                    "time_value": origin.time,
                    "time_errors": origin.time_errors,
                    "latitude_value": origin.latitude,
                    "latitude_errors": origin.latitude_errors,
                    "longitude_value": origin.longitude,
                    "longitude_errors": origin.longitude_errors,
                    "depth_value": origin.depth,
                    "depth_errors": origin.depth_errors,
                    "depth_used": 1 if origin.depth is not None else 0,
                    "depthType": origin.depth_type,
                    "timeFixed": bool_or_none(origin.time_fixed),
                    "epicenterFixed": bool_or_none(origin.epicenter_fixed),
                    "referenceSystemID": origin.reference_system_id,
                    "methodID": origin.method_id,
                    "earthModelID": origin.earth_model_id,
                    "quality": origin.quality,
                    "quality_used": 1 if origin.quality is not None else 0,
                    "uncertainty": origin.origin_uncertainty,
                    "uncertainty_used": 1
                    if origin.origin_uncertainty is not None
                    else 0,
                    "type": origin.origin_type,
                    "evaluationMode": origin.evaluation_mode,
                    "evaluationStatus": origin.evaluation_status,
                    "creationInfo": origin.creation_info,
                },
            ),
            obspy.core.event.Arrival: (
                "Arrival",
                lambda arrival: {
                    "pickID": arrival.pick_id,
                    "phase_code": arrival.phase,
                    "timeCorrection": arrival.time_correction,
                    "azimuth": arrival.azimuth,
                    "distance": arrival.distance,
                    "takeOffAngle": arrival.takeoff_angle,
                    "timeResidual": arrival.time_residual,
                    "horizontalSlownessResidual": arrival.horizontal_slowness_residual,
                    "backazimuthResidual": arrival.backazimuth_residual,
                    # XXX: These three don't have a direct representation in
                    # QuakeML. For now they are interpreted like this.
                    "timeUsed": 1 if arrival.time_residual is not None else 0,
                    "horizontalSlownessUsed": 1
                    if arrival.horizontal_slowness_residual is not None
                    else 0,
                    "backazimuthUsed": 1
                    if arrival.backazimuth_residual is not None
                    else 0,
                    # XXX: We cannot fill the weight as QuakeML has individual
                    # weights for the times, the horizontal slowness, and the
                    # backazimuth.
                    # "weight": ...
                    "earthModelID": arrival.earth_model_id,
                    # QuakeML does not have this.
                    "preliminary": 0,
                    "creationInfo": arrival.creation_info,
                },
            ),
            obspy.core.event.Event: (
                "Event",
                lambda event: {
                    "preferredOriginID": event.preferred_origin_id,
                    "preferredMagnitudeID": event.preferred_magnitude_id,
                    "preferredFocalMechanismID": event.preferred_focal_mechanism_id,
                    "type": event.event_type,
                    "typeCertainty": event.event_type_certainty,
                    "creationInfo": event.creation_info,
                },
            ),
            obspy.core.event.EventDescription: (
                "EventDescription",
                lambda ed: {"text": ed.text, "type": ed.type},
            ),
            obspy.core.event.source.MomentTensor: (
                "MomentTensor",
                lambda mt: {
                    "derivedOriginID": mt.derived_origin_id,
                    "momentMagnitudeID": mt.moment_magnitude_id,
                    "scalarMoment_value": mt.scalar_moment,
                    "scalarMoment_errors": mt.scalar_moment_errors,
                    "scalarMoment_used": 1 if mt.scalar_moment is not None else 0,
                    # Dealt with in the common transforms.
                    "tensor": mt.tensor,
                    "tensor_used": 1 if mt.tensor is not None else 0,
                    "variance": mt.variance,
                    "varianceReduction": mt.variance_reduction,
                    "doubleCouple": mt.double_couple,
                    "clvd": mt.clvd,
                    "iso": mt.iso,
                    "greensFunctionID": mt.greens_function_id,
                    "filterID": mt.filter_id,
                    # Dealt with in the common transforms.
                    "sourceTimeFunction": mt.source_time_function,
                    "sourceTimeFunction_used": 1
                    if mt.source_time_function is not None
                    else 0,
                    "methodID": mt.method_id,
                    "creationInfo": mt.creation_info,
                },
            ),
            obspy.core.event.source.FocalMechanism: (
                "FocalMechanism",
                lambda fm: {
                    "triggeringOriginID": fm.triggering_origin_id,
                    # Will be expanded in the common transforms.
                    "nodalPlanes": fm.nodal_planes,
                    "nodalPlanes_used": 1 if fm.nodal_planes is not None else 0,
                    # Will also be expanded.
                    "principalAxes": fm.principal_axes,
                    "principalAxes_used": 1 if fm.principal_axes is not None else 0,
                    "azimuthalGap": fm.azimuthal_gap,
                    "stationPolarityCount": fm.station_polarity_count,
                    "misfit": fm.misfit,
                    "stationDistributionRatio": fm.station_distribution_ratio,
                    "methodID": fm.method_id,
                    "evaluationMode": fm.evaluation_mode,
                    "evaluationStatus": fm.evaluation_status,
                    "creationInfo": fm.creation_info,
                },
            ),
            obspy.core.event.magnitude.Amplitude: (
                "Amplitude",
                lambda a: {
                    "type": a.type,
                    "amplitude_value": a.generic_amplitude,
                    "amplitude_errors": a.generic_amplitude_errors,
                    "amplitude_used": 1 if a.generic_amplitude is not None else 0,
                    "timeWindow_reference": a.time_window.reference
                    if a.time_window
                    else None,
                    "timeWindow_begin": a.time_window.begin if a.time_window else None,
                    "timeWindow_end": a.time_window.end if a.time_window else None,
                    "timeWindow_used": 1 if a.time_window else 0,
                    "period_value": a.period,
                    "period_errors": a.period_errors,
                    "period_used": 1 if a.period is not None else 0,
                    "snr": a.snr,
                    "unit": a.unit,
                    "pickID": a.pick_id,
                    "waveformID": a.waveform_id,
                    "waveformID_used": 1 if a.waveform_id is not None else 0,
                    "filterID": a.filter_id,
                    "methodID": a.method_id,
                    "scalingTime_value": a.scaling_time,
                    "scalingTime_errors": a.scaling_time_errors,
                    "scalingTime_used": 1 if a.scaling_time is not None else 0,
                    "magnitudeHint": a.magnitude_hint,
                    "evaluation_mode": a.evaluation_mode,
                    "creationInfo": a.creation_info,
                },
            ),
            obspy.core.event.base.DataUsed: (
                "DataUsed",
                lambda du: {
                    "waveType": du.wave_type,
                    "stationCount": du.station_count,
                    "componentCount": du.component_count,
                    "shortestPeriod": du.shortest_period,
                },
            ),
            obspy.core.event.magnitude.StationMagnitude: (
                "StationMagnitude",
                lambda sm: {
                    "originID": sm.origin_id,
                    "magnitude_value": sm.mag,
                    "magnitude_errors": sm.mag_errors,
                    "type": sm.station_magnitude_type,
                    "amplitudeID": sm.amplitude_id,
                    "methodID": sm.method_id,
                    "waveformID": sm.waveform_id,
                    "creationInfo": sm.creation_info,
                },
            ),
            obspy.core.event.magnitude.StationMagnitudeContribution: (
                "StationMagnitudeContribution",
                lambda smc: {
                    "stationMagnitudeID": smc.station_magnitude_id,
                    "residual": smc.residual,
                    "weight": smc.weight,
                },
            ),
        }
        t = type_map[type(obj)]

        db_type = common_transforms(t[1](obj))

        # Collected warnings for incompatibilities between the QuakeML and the
        if isinstance(obj, obspy.core.event.Origin) and obj.region is not None:
            warnings.warn(
                "The region attribute in Origin objects is not supported by the "
                "Seiscomp database and will thus be ignored."
            )
        elif isinstance(obj, obspy.core.event.Arrival):
            keys = [
                "takeoff_angle_errors",
                "time_weight",
                "horizontal_slowness_weight",
                "backazimuth_weight",
            ]
            for k in keys:
                if getattr(obj, k):
                    warnings.warn(
                        f"The Origin.{k} attribute will be ignored because it "
                        "cannot be stored in the Seiscomp compatible database."
                    )
        elif isinstance(obj, obspy.core.event.source.MomentTensor):
            keys = [
                "category",
                "inversion_type",
            ]
            for k in keys:
                if getattr(obj, k) is not None:
                    warnings.warn(
                        f"The MomentTensor.{k} attribute will be ignored because it "
                        "cannot be stored in the Seiscomp compatible database."
                    )
        elif isinstance(obj, obspy.core.event.source.FocalMechanism):
            keys = [
                "waveform_id",
            ]
            for k in keys:
                if getattr(obj, k):
                    warnings.warn(
                        f"The FocalMechanism.{k} attribute will be ignored because it "
                        "cannot be stored in the Seiscomp compatible database."
                    )
        elif isinstance(obj, obspy.core.event.magnitude.Amplitude):
            keys = ["evaluation_status", "category"]
            for k in keys:
                if getattr(obj, k):
                    warnings.warn(
                        f"The Amplitude.{k} attribute will be ignored because it "
                        "cannot be stored in the Seiscomp compatible database."
                    )
        elif isinstance(obj, obspy.core.event.base.DataUsed):
            keys = ["longest_period"]
            for k in keys:
                if getattr(obj, k):
                    warnings.warn(
                        f"The DataUsed.{k} attribute will be ignored because it "
                        "cannot be stored in the Seiscomp compatible database."
                    )

        # Public objects have resource ids.
        if "_oid" in db_type:
            breakpoint()
            pass
        else:
            if hasattr(obj, "resource_id") and obj.resource_id:
                o_id = self._create_new_public_object(
                    public_id_string=obj.resource_id.resource_id
                )
            else:
                o_id = self._create_new_object()
            db_type["_oid"] = o_id

        if parent_object_id is not None:
            db_type["_parent_oid"] = parent_object_id
        else:
            # If no explicit parent object id is given, set it to the default
            # one which should be one.
            db_type["_parent_oid"] = self._default_parent_id

        params = SQLITE_TABLES[t[0]].validate(db_type)

        # Some objects require special treatment.
        if t[0] == "Origin":
            # Origins don't take the event as the parent but the root
            # EventParameters. They are linked to the event via a
            # OriginReference.
            event_oid = params["_parent_oid"]
            params["_parent_oid"] = self._default_parent_id

            origin_reference_params = {
                "_oid": self._create_new_object(),
                "_parent_oid": event_oid,
                "originID": obj.resource_id.resource_id,
            }
            self._insert_into_db(
                db_name="OriginReference", params=origin_reference_params
            )
        elif t[0] == "FocalMechanism":
            # FocalMechanisms don't take the event as the parent but the root
            # EventParameters. They are linked to the event via a
            # FocalMechanismReference.
            event_oid = params["_parent_oid"]
            params["_parent_oid"] = self._default_parent_id

            origin_reference_params = {
                "_oid": self._create_new_object(),
                "_parent_oid": event_oid,
                "focalMechanismID": obj.resource_id.resource_id,
            }
            self._insert_into_db(
                db_name="FocalMechanismReference", params=origin_reference_params
            )
        elif t[0] == "Pick":
            # They are not directly associated with event.
            params["_parent_oid"] = self._default_parent_id

        self._insert_into_db(db_name=t[0], params=params)

        # Add child objects. Reuse the '._containers' attribute of the ObsPy
        # objects.
        if not isinstance(obj, obspy.core.event.source.FocalMechanism):
            for container in obj._containers:
                for c_obj in getattr(obj, container, []):
                    self.add_object(
                        c_obj, parent_object_id=params["_oid"], commit=False
                    )
        # FocalMechanisms fall a bit outside the line.
        else:
            for c_obj in obj.comments:
                self.add_object(c_obj, parent_object_id=params["_oid"], commit=False)
            if obj.moment_tensor:
                self.add_object(
                    obj.moment_tensor, parent_object_id=params["_oid"], commit=False
                )

        if commit:
            self.connection.commit()

        return params["_oid"]

    def _insert_into_db(self, db_name: str, params: typing.Dict[str, typing.Any]):
        """
        Helper method inserting into the DB.
        """
        names = []
        values = []
        for k, v in params.items():
            names.append(k)
            values.append(v)

        sql = (
            f"INSERT INTO {db_name} ({', '.join(names)}) VALUES "
            f"({', '.join(['?'] * len(names))})"
        )

        self.cursor.execute(sql, values)

    def _create_new_public_object(self, public_id_string: str) -> int:
        """
        Create a new public object + object and return the object id.

        Args:
            public_id_string: String of the public id.
        """
        o_id = self._create_new_object()
        self.cursor.execute(
            "INSERT INTO PublicObject (_oid, publicID) VALUES (?, ?);",
            (o_id, public_id_string),
        )
        return o_id

    def _create_new_object(self) -> int:
        """
        Creates a new Object into the DB and return the object id.
        """
        self.cursor.execute("INSERT INTO Object VALUES (NULL, CURRENT_TIMESTAMP)")
        return self.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]

    def count(self, object_type: str) -> int:
        """
        Return the count of objects of a certain type in the database.

        Args:
            object_type: The type of object to count.
        """
        if object_type not in SQLITE_TABLES:
            raise ValueError(
                f"Unknown object type: {object_type}. "
                f"Known types: {list(SQLITE_TABLES.keys())}"
            )
        return self.cursor.execute(f"SELECT COUNT(*) FROM {object_type};").fetchone()[0]

    def get_event_summary(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Get a short summary of all events, sorted by earliest origin.

        The returned latitude/longitude/depth belong to the earliest origin of
        each event.
        """
        sql = """
        SELECT
            event_public_object.publicID,
            MIN(Origin.time_value_ms),
            Origin.latitude_value,
            Origin.longitude_value,
            Origin.depth_value

        -- Get all origin references.
        FROM OriginReference

        -- Find the events for every origin reference.
        JOIN Event
            ON Event._oid = OriginReference._parent_oid
        JOIN PublicObject event_public_object
            ON event_public_object._oid = Event._oid

        -- Find the actual origin.
        JOIN PublicObject public_origin_object
            ON public_origin_object.publicID = OriginReference.originID
        JOIN Origin
            ON Origin._oid = public_origin_object._oid

        -- Only a single event.
        GROUP BY Event._oid
        ORDER BY Origin.time_value_ms
        """
        results = self.cursor.execute(sql).fetchall()
        return [
            {
                "event_resource_id": i[0],
                "origin_time": obspy.UTCDateTime(i[1] / 1000.0),
                "latitude": i[2],
                "longitude": i[3],
                "depth": i[4],
            }
            for i in results
        ]

    def get_unassociated_picks(self) -> obspy.core.event.Pick:
        """
        Get all picks currently not associated with any event.
        """
        sql = """
        SELECT Pick._oid
        FROM Pick
        INNER JOIN PublicObject
            ON PublicObject._oid = Pick._oid
        LEFT JOIN Arrival
            ON Arrival.pickID = PublicObject.publicID
        WHERE
            Arrival.pickID IS NULL
        ORDER BY
            Pick.time_value_ms
        """
        r = self.cursor.execute(sql).fetchall()
        if not r:
            return []
        return self.get_objects(
            object_type="Pick", where={"Pick._oid__in": [i[0] for i in r]}
        )

    def delete_objects(self, objects=typing.List[typing.Any]):
        """
        Delete the passed objects from the database.
        """
        resource_ids = []
        for o in objects:
            resource_ids.extend(db_utils.collect_resource_ids(o))

        q = ",".join(["?"] * len(resource_ids))

        # First find all public objects that are to be deleted.
        sql = f"""
        SELECT PublicObject._oid
        FROM PublicObject
        WHERE PublicObject.publicID in ({q})
        """
        deleted_ids = [i[0] for i in self.cursor.execute(sql, resource_ids).fetchall()]

        # Delete them via public id.
        sql = f"""
        DELETE FROM Object
        WHERE ROWID IN (
            SELECT Object.ROWID FROM Object
            INNER JOIN PublicObject ON PublicObject._oid = Object._oid
            WHERE PublicObject.publicID IN ({q})
        )
        """
        self.cursor.execute(sql, resource_ids)

        d = ",".join(str(i) for i in deleted_ids)
        # Now delete all objects who's parents is one of the deleted ones.
        sql = f"""
        DELETE FROM Object
        WHERE ROWID IN (
            SELECT Object.ROWID FROM Object

            LEFT JOIN Comment ON Comment._oid = Object._oid
            LEFT JOIN EventDescription on EventDescription._oid = Object._oid
            LEFT JOIN DataUsed on DataUsed._oid = Object._oid
            LEFT JOIN CompositeTime on CompositeTime._oid = Object._oid
            LEFT JOIN PickReference on PickReference._oid = Object._oid
            LEFT JOIN AmplitudeReference on AmplitudeReference._oid = Object._oid
            LEFT JOIN OriginReference on OriginReference._oid = Object._oid
            LEFT JOIN FocalMechanismReference on FocalMechanismReference._oid = Object._oid
            LEFT JOIN MomentTensorComponentContribution on MomentTensorComponentContribution._oid = Object._oid
            LEFT JOIN MomentTensorStationContribution on MomentTensorStationContribution._oid = Object._oid
            LEFT JOIN MomentTensor on MomentTensor._oid = Object._oid
            LEFT JOIN StationMagnitudeContribution on StationMagnitudeContribution._oid = Object._oid

            WHERE
                Comment._parent_oid in ({d})
                OR EventDescription._parent_oid in ({d})
                OR DataUsed._parent_oid in ({d})
                OR CompositeTime._parent_oid in ({d})
                OR PickReference._parent_oid in ({d})
                OR AmplitudeReference._parent_oid in ({d})
                OR OriginReference._parent_oid in ({d})
                OR FocalMechanismReference._parent_oid in ({d})
                OR MomentTensorComponentContribution._parent_oid in ({d})
                OR MomentTensorStationContribution._parent_oid in ({d})
                OR MomentTensor._parent_oid in ({d})
                OR StationMagnitudeContribution._parent_oid in ({d})
        )
        """
        self.cursor.execute(sql)

        self.connection.commit()

    def _count_all_rows_in_db(self) -> int:
        """
        Counts all rows in the SQLite DB.

        Mostly useful for testing and debugging.
        """
        # Very inefficient but does not matter here.
        return sum(self.count(i) for i in SQLITE_TABLES.keys())

    def update_event_comments(self, event: obspy.core.event.Event):
        """
        Specialized update command that only updates an events comments.

        Mainly useful for the GUI or other mass comment changes.

        Args:
            event: The event whose comments should be updated. Will use the
                its resource id, delete all old comments and add the new
                comments.
        """
        db_event = self.get_objects(
            "Event", where={"publicId__eq": str(event.resource_id)}
        )[0]

        # Delete existing comments.
        sql = """
        DELETE FROM Object
        WHERE ROWID IN (
            SELECT Object.ROWID FROM Object
            INNER JOIN Comment ON Comment._oid = Object._oid
            WHERE Comment._parent_oid = ?
        )
        """
        self.cursor.execute(sql, [db_event._object_id])

        # Add new ones.
        for c in event.comments:
            self.add_object(obj=c, parent_object_id=db_event._object_id)
