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
Utilities to parse the SQLite definition of SeisComP.
"""

import re

import schema

# For sanity checks - this list has been manually verified.
EXPECTED_TABLES = set(
    [
        "Meta",
        "Object",
        "PublicObject",
        "EventDescription",
        "Comment",
        "DataUsed",
        "CompositeTime",
        "PickReference",
        "AmplitudeReference",
        "Reading",
        "MomentTensorComponentContribution",
        "MomentTensorStationContribution",
        "MomentTensorPhaseSetting",
        "MomentTensor",
        "FocalMechanism",
        "Amplitude",
        "StationMagnitudeContribution",
        "Magnitude",
        "StationMagnitude",
        "Pick",
        "OriginReference",
        "FocalMechanismReference",
        "Event",
        "Arrival",
        "Origin",
        "Parameter",
        "ParameterSet",
        "Setup",
        "ConfigStation",
        "ConfigModule",
        "QCLog",
        "WaveformQuality",
        "Outage",
        "StationReference",
        "StationGroup",
        "AuxSource",
        "AuxDevice",
        "SensorCalibration",
        "Sensor",
        "ResponsePAZ",
        "ResponsePolynomial",
        "ResponseFAP",
        "ResponseFIR",
        "ResponseIIR",
        "DataloggerCalibration",
        "Decimation",
        "Datalogger",
        "AuxStream",
        "Stream",
        "SensorLocation",
        "Station",
        "Network",
        "RouteArclink",
        "RouteSeedlink",
        "Route",
        "Access",
        "JournalEntry",
        "ArclinkUser",
        "ArclinkStatusLine",
        "ArclinkRequestLine",
        "ArclinkRequest",
        "DataSegment",
        "DataAttributeExtent",
        "DataExtent",
    ]
)


def parse_sqlite_definition(content: str):
    """
    Parse the tables from the SQLite3 to simplify the ORM generation from ObsPy
    Objects <-> Seiscomp DB.
    """
    table_strings = re.findall(
        r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);", content, re.MULTILINE | re.DOTALL
    )
    assert set(i[0] for i in table_strings) == EXPECTED_TABLES

    type_map = {
        re.compile(r"CHAR"): str,
        re.compile(r"VARCHAR"): str,
        re.compile(r"VARCHAR\(\d+\)"): str,
        re.compile(r"INTEGER"): int,
        re.compile(r"INTEGER\(\d+\)"): int,
        re.compile(r"INT"): int,
        re.compile(r"TINYINT"): int,
        re.compile(r"SMALLINT"): int,
        re.compile(r"DOUBLE"): float,
        re.compile(r"TIMESTAMP"): int,
        re.compile(r"DATETIME"): str,
        re.compile(r"BLOB"): bytes,
    }

    tables = {}
    for table_name, table_content in table_strings:
        # Parse each table to a schema.
        table_schema = {}
        content_lines = [i.strip() for i in table_content.strip().split(",")]

        for line in content_lines:
            # Skip a few lines.
            if (
                line.startswith("PRIMARY KEY")
                or line.startswith("FOREIGN KEY")
                or line.startswith("UNIQUE(")
            ):
                continue

            split_line = line.split()
            if len(split_line) <= 1:
                continue

            name = split_line[0]
            db_value_type = split_line[1]

            if (
                "NOT NULL" not in line
                or " DEFAULT " in line
                or "AUTOINCREMENT" in line
                # These two are optional in the sense that they can be
                # auto-created.
                or name == "_oid"
                or name == "_parent_oid"
            ):
                key = schema.Optional(name)
            else:
                key = name

            for db_type, python_type in type_map.items():
                if re.match(db_type, db_value_type):
                    table_schema[key] = python_type
                    break
            else:
                raise NotImplementedError(f"Unknown database type: {db_value_type}")

        # Convert to a schema.
        tables[table_name] = schema.Schema(table_schema)

    return tables
