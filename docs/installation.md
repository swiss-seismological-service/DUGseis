# Installation

## Dependencies

`DUGSeis` is a Python package and has the following dependencies:

* `Python >= 3.9`
* `click`
* `joblib`
* `numba`
* `numpy`
* `obspy`
* `pyasdf`
* `pyopengl`
* `pyproj>=3`
* `pyqtgraph`
* `pyside6`
* `pyyaml`
* `schema`
* `scipy`
* `tqdm`

Furthermore `git` is required to get the `DUGSeis` code.

## Installation Instructions

The `conda` Python distribution is recommended, but you can use any Python
distribution you see fit.

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

### Update DUGSeis

To update `DUGSeis` please change to the `DUGSeis` directory and run

```bash
git pull
```

If that does not work for some reason (e.g. the `DUGSeis` repository has been
force pushed to, local changes, ...) please do the following (**All your local
changes will be deleted!**):

```bash
git fetch origin main
git reset --hard origin/main
```

If the `DUGSeis` dependencies changed, just run

```bash
pip install -e .
```

again. Make sure the correct `conda` environment is active.
