# Example dataset

An example dataset consisting of waveform data, station information, processing and config file can be found here:
[Zenodo - DUGSeis Example Dataset](https://doi.org/10.5281/zenodo.10598393)

## Usage

After downloading all files, the easiest way to try out the example is to add the waveform files (.h5 files) to a seperate folder (e.g. WAVEFORMS) and the station information files (.xml files) to another seperate folder (e.g. STATIONXMLS).
If the processing file (run_postProcessing_PaperExample.py) and the config file (post_processing_PaperExample.yaml) are located in the same folder, nothing needs to be changed in the processing file.
In the config file the `paths` need to be updated:
* `asdf_folders`: Absolute path to the folder containing the waveform files
* `stationxml_folders`: Absolute path to the folder containing the station information files
* `database`: Absolute path to where the database file should be saved including the name of the database file
* `cache_folder`: Absolute path to the cache folder, which needs to be created before running the processing

After updating the paths in the config file, the processing can be started by running the following command in the terminal:
```bash
python3 run_postProcessing_PaperExample.py
```



