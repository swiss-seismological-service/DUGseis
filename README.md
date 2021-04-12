# DUG Seis

Software for acquisition and processing of micro-seismic data

## Status

This software currently has alpha/beta status.

Furthermore it is currently in a transition status between two version of the
code so some things are a bit awkward.

## Usage

This version currently supports two things:

Automatic processing of data:

```bash
$ dug-seis --cfg=./path/to/config.yaml processing
```

Manual classification of picking of processed data:

```bash
$ dug-seis --cfg=./path/to/config.yaml gui
```

## Installation

1. Install miniconda: https://docs.conda.io/en/latest/miniconda.html
2. Create new environment:

```bash
conda create -n dug_seis python=3.9
conda activate dug_seis
```

(On Windows please use 3.8 for now because ObsPy does not yet build 3.9 binaries).

3. Clone DUGSeis

```
git clone https://github.com/swiss-seismological-service/DUGseis.git
```

4. Install DugSeis and dependencies

```
cd DUGseis
conda activate dug_seis
pip install -e .
```

## License & Copyright

DUG Seis is licensed under the GNU Lesser General Public License, Version 3
    (https://www.gnu.org/copyleft/lesser.html).

The copyright is held by ETH Zurich, Switzerland.
Main Contributors for the first version developed until August 2019 are
- Joseph Doetsch
- Thomas Haag
- Sem Demir
- Linus Villiger
