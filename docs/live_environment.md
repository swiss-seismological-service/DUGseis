# Live Environment

`DUGSeis` can be used in a live environment. The assumption here is that some
other acquisition process will write waveform data files continuously. The
processing script will monitor the folders and process them as they come in.

The graphical interface can update with changing data - this either happens
manually or by monitoring the database and waveform directories. This can be
selected in the graphical interface.

Similar to the normal processing this is handled with a Python file. This can
tuned to each use case to be maximally useful. Please have a look at this
example:

```{literalinclude} ../scripts/mock_live_environment/run_mock_live_processing.py
   :language: py
```

A corresponding configuration file could look like this:

```{literalinclude} ../scripts/mock_live_environment/live_processing_example.yaml
   :language: yaml
```

Last but not least it is oftentimes useful to simulate a live environment. This
helper script here can aid with that:

```{literalinclude} ../scripts/mock_live_environment/fake_live_acquisition.py
   :language: py
```