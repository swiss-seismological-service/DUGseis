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

from setuptools import setup, find_packages


_authors = [
    "Joseph Doetsch",
    "Linus Villiger",
    "Thomas Haag",
    "Sem Demir",
    "DUGSeis Authors",
]
_authors_email = ["linus.villiger@sed.ethz.ch", "joseph.doetsch@erdw.ethz.ch"]

_install_requires = [
    "click",
    "numba",
    "numpy",
    "obspy",
    "pyasdf",
    "pyopengl",
    "pyproj>=3",
    "pyqtgraph",
    "pyside6",
    "pyyaml",
    "schema",
    "scipy",
    "tqdm",
]

setup(
    name="DUG-Seis",
    version="0.1",
    author=" (SCCER-SoE, SED, ETHZ),".join(_authors),
    author_email=", ".join(_authors_email),
    description=(
        "Processing, data management, and visualization of " "micro-seismic data."
    ),
    license="LGPL",
    keywords=["induced seismicity", "seismology"],
    url="https://github.com/swiss-seismological-service/DUGseis",
    classifiers=[
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Science/Research",
        (
            "License :: OSI Approved :: GNU Lesser "
            "General Public License v3 or later (LGPLv3+)"
        ),
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering",
    ],
    platforms=["Linux", "MAC", "Windows"],
    install_requires=_install_requires,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["dug-seis=dug_seis.cmd_line:cli"]},
)
