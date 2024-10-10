# Data Requirements

`DUGSeis` requires two pieces of data: waveforms and meta information about each
channel.

## Waveform data

Waveform data must use the [`ASDF`](https://seismic-data.org) file format. It
can deal with ASDF data from one or more acquisition systems and thus the files
can be stored in one or more folders.

`DUGSeis` searches the configured folders and finds all `*.h5` files.
Additionally the filenames have to satisfy the following regular expression:

```
^                                                              # Beginning of string
(\d{4})_(\d{2})_(\d{2})T(\d{2})_(\d{2})_(\d{2})[_\.](\d{6})Z?  # Start time as capture groups
__                                                             #
(\d{4})_(\d{2})_(\d{2})T(\d{2})_(\d{2})_(\d{2})[_\.](\d{6})Z?  # End time as capture groups
__
.*                                                             # Rest of name
$                                                              # End of string.
```

Valid examples include:

* `2017_02_09T13_24_15_000058__2017_02_09T13_24_25_000058__HS4.h5`
* `2021_05_05T17_31_30_000015Z__2021_05_05T17_32_00_000015Z__03.h5`
* `2021_05_05T17_59_30_000294Z__2021_05_05T17_59_51_352674Z__04.h5`

The times must be the time of the first and the time of the last sample in the
file in UTC. All traces in a file are expected to be continuous and have the
same length. Integer and floating point data are both supported. Furthermore
adjacent files are expected to match exactly timing wise.

`DUGSeis` assumes all timing information in the ASDF files to be correct.

## StationXML Meta Data

Metadata, e.g., location and instrument response information, must be available
for each channel. The channel identifiers must exactly match the channel
identifiers in the ASDF files.

We recommend to use one StationXML file per channel. The `scripts` subdirectory
in the `DUGSeis` repository contains a helper script to generate suitable
StationXML files.

The coordinates must be given in WGS84 and be stored on the channel level.
Please refer to the {mod}`dug_seis.coordinate_transforms` module for more
details.