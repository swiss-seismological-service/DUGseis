# Database

`DUGSeis` internally stores all its event information in a [SeisComP compatible
database](https://geofon.gfz-potsdam.de/_uml/).

It can be programmatically accessed via an active
{class}`~dug_seis.project.project.DUGSeisProject` object:

```python
from dug_seis.project.project import DUGSeisProject

project = DUGSeisProject(config="path/to/config.yaml")
db = project.db
```

Please refer to the documentation of the {class}`~dug_seis.db.db.DB` class for
detailed method references.

## Description

The database is a form of object relation mapping that can map QuakeML 1.2 in
the form of [ObsPy event objects and child
objects](https://docs.obspy.org/packages/obspy.core.event.html) to and from it.

In the simplest form it can be used like this:

```python
# Store in DB.
db += obspy.read_events()

# Retrieve again.
events = db.get_objects(object_type="Event")
```

## Limitations

The data model between QuakeML and a SeisComP compatible database (DB in the
following) is unfortunately not exactly identical which results in a few
limitations:

* Picks in QuakeML are attached to an event. In the DB they are not. They are
  only linked to an event via an arrival object. Thus an event that has picks
  but no arrivals can be stored in the DB but a retrieved event will no longer
  have the picks associated with it if there are no arrival objects.
* The following QuakeML attributes cannot currently not be stored in the DB (an
  appropriate warning will be raised by the code):

  - `Origin.region`
  - `Arrival.takeoff_angle_errors`
  - `Arrival.time_weight`
  - `Arrival.horizontal_slowness_weight`
  - `Arrival.backazimuth_weight`
  - `MomentTensor.category`
  - `MomentTensor.inversion_type`
  - `FocalMechanism.waveform_id`
  - `Amplitude.evaluation_status`
  - `Amplitude.category`
  - `DataUsed.longest_period`

## Common Operations

### Convert whole database to a list of QuakeML files

Use the {meth}`~dug_seis.db.db.DB.dump_as_quakeml_files` method:

```python
db.dump_as_quakeml_files(folder="/path/to/output_folder")
```

### Get all unassociated picks

Use the {meth}`~dug_seis.db.db.DB.get_unassociated_picks` method:

```python
picks = db.get_unassociated_picks()
```

### Expert: Directly execute a SQLite query

There are cases when you might have to drop down to raw SQL. The
`._backend.cursor` attributes gives you an active {class}`sqlite3.Cursor`
object.

```python
r = db._backend.cursor.execute("SELECT COUNT(*) FROM Event").fetchall();
```