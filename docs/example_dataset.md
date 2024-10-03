# Example dataset

An example dataset consisting of waveform data, station information, processing and config file can be found here:
[Zenodo - DUGSeis Example Dataset](https://doi.org/10.5281/zenodo.10598392)



## Usage
After downloading the zip file, extract the content in the zip folder. The folder `BedrettoExampleData` contains the following folders:
* `WAVEFORMS`: containing the waveform files in asdf format
* `STATIONXMLS`: containing the station information files in xml format
* `cache`: the folder where the cache files will be saved (empty until first run of graphical user interface or post-processing script)

Additionally, the folder contains the following files:
* `GUIExample_PaperExample.yaml`: the config file for quickly opening the graphical user interface
* `VALTERStimu_PaperDatabase.sqlite`: the database file containing the results of the processing displayed in the graphical user interface
* `post_processing_PaperExample.yaml`: the config file for the post-processing script
* `run_postProcessing_PaperExample.py`: Python script to run the post-processing

To open the graphical interface, run the following command in the terminal:
```bash
dug-seis gui --operator="Your Name" --config=GUIExample_PaperExample.yaml
```

To run the post-processing, run the following command in the terminal:
```bash
python3 run_postProcessing_PaperExample.py
```



