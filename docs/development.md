# Development

This software package is for the processing, data management, and visualization
of micro-seismic data.

It is an evolution of the code found here:
[https://gitlab.seismo.ethz.ch/doetschj/DUG-Seis](https://gitlab.seismo.ethz.ch/doetschj/DUG-Seis)

The acquisition companion code can be found here: [https://github.com/swiss-seismological-service/DUGseis-acquisition](https://github.com/swiss-seismological-service/DUGseis-acquisition)

## Directory Structure

As of Juni 2021 the directory structure is approximately as follows:

```
.
├── README.md
├── docs
│   └── ...
├── dug_seis
│   ├── __init__.py
│   ├── cmd_line.py
│   ├── coordinate_transforms.py
│   ├── db
│   ├── event_processing
│   ├── graphical_interface
│   ├── project
│   ├── pytest.ini
│   ├── tests
│   ├── util.py
│   └── waveform_handler
├── scripts
│   └── ...
├── ...
└── setup.py
```

* `README.md`: Root level readme file.
* `docs`: Sphinx based documentation.
* `dug_seis`: Source code for the actual `DUGSeis` package.
* `dug_seis/cmd_line.py`: Code for the command line interface.
* `dug_seis/coordinate_transforms.py`: Coordinate transformations.
* `dug_seis/db`: Submodule implementing the SeisComP compatible database
  interface.
* `dug_seis/event_processing`: Submodule containing all detectors, pickers, ...
* `dug_seis/graphical_interface`: Submodule for the graphical Qt interface.
* `dug_seis/project`: Submodule implementing the `DUGSeisProject` class.
* `dug_seis/pytest.ini`: Configuration file for the unit tests.
* `dug_seis/tests`: Unit tests for the `DUGSeis` package.
* `dug_seis/util.py`: Utility functions useful across `DUGSeis`.
* `dug_seis/waveform_handler`: Low-level implementation of the waveform data
  access.
* `scripts`: A collection of useful scripts and examples.
* `setup.py`: Setup script teaching Python how to install `DUGSeis`.

## Testing

Unit tests are written in the [pytest](https://pytest.org) framework.

To execute them make sure `pytest` is installed (`pip install pytest`) an run

```bash
py.test
```

in the `DUGSeis` code directory. The tests are not comprehensive but they do
test a decent chunk of the complicated part of it and thus should always work.

## Linting

To adhere to the style guide and avoid silly errors always make sure `black` and
`flake8` pass (`pip install flake8 black`).

Just run the following in the `DUGSeis` source code directory:

```bash
black .
flake8 .
```

Both tools are configured in the `pyproject.toml` and the `.flake8` files in the
root source directory, respectively.

## Documentation Building

The documentation resides in the `docs` directory. It depends on the following packages:

* `sphinx`
* `sphinx-book-theme`
* `myst-parser`

Once these are installed, just change to the docs directory and execute

```bash
make html
```

or (on Windows)

```bash
./make.bat html
```

and the HTML documentation will be saved to `docs/_build/html`.


## Graphical Interface

The `.ui` files in `dug_seis/graphical_interface/ui_files` can be graphically
edited with the [Qt Creator](https://www.qt.io/product/development-tools).

Once the UI files have been edited they can be converted to Python files like this:

```bash
pyside6-uic .\main_window.ui -o main_window.py
```

It works the same for the other UI files.


## Misc

### Possible database migration path

The SQLite database ORM is well tested in the sense that it can reliably
round-trip data to and from QuakeML. It has seen little external validation for
full compatibility with other tools able to work with SeisComP compatible
databases.

If changes to the database implementation are necessary it should be possible
to first export everything to QuakeML files and reimport these into the new
database.

Dump whole archive to QuakeML by using the current DUGSeis version:

```python
project.db.dump_as_quakeml_files(folder="/path/to/archive")
```

Then update the DUGSeis version and do:

```python
for filename in pathlib.Path("/path/to/archive").glob(".xml"):
    for event in obspy.read_events(str(filename)):
        project.db.add_object(event)
```