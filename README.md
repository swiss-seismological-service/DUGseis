![](./docs/static/dug_seis_logo.svg)

# Software for processing and visualization of micro-seismic data

The DUGSeis software package was developed to manage, process and visualize continuous, high-frequency seismic data. It can be used to create earthquake catalogs in real-time,
as well as in post-processing and directly visualize the event waveforms and event locations in a graphical user interface. The software is Python-based therefore, users can easily
add their own processing routines.

Detailed information can be found in the [Documentation](https://dugseis.readthedocs.io/).

## Installation

The `conda` Python distribution is recommended, but you can use any Python distribution you see fit.

### Installing `conda`

1. Install `miniconda` for your operating system: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
2. Create a new environment:

```bash
conda create -n dug_seis python=3.11
conda activate dug_seis
```

**Make sure the `dug_seis` environment is active when using `DUGSeis` and for
all the following steps on this page!**

### Install DUGSeis

Clone DUGSeis

```bash
git clone https://github.com/swiss-seismological-service/DUGseis.git
```


```bash
cd DUGseis
conda activate dug_seis
pip install -e .
```

% add example dataset on zenodo

## Example
An example dataset to test the software can be accessed with the [Zenodo DOI](https://doi.org/10.5281/zenodo.10598393).\
The dataset consists of a python run-file and its associated configuration file and the needed waveform and station xml files. 