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

"""
Script that creates a fake live acquisition environment for development
purposes.
"""
import pathlib
import random
import re
import shutil
import time

import obspy

from dug_seis.waveform_handler.waveform_handler import FILENAME_REGEX

###########################################################################
# Settings
DATA_FOLDER = pathlib.Path(
    r"C:\Users\lionk\Downloads\DUGSeis\DUGSeis\01_dummy_Grimsel\01_ASDF_data"
)
FAKE_ACQUISITION_FOLDER = pathlib.Path(r"fake_live_data\asdf")
INITIAL_DELAY_IN_SECONDS = 10.0
###########################################################################


assert not FAKE_ACQUISITION_FOLDER.exists(), str(FAKE_ACQUISITION_FOLDER)
FAKE_ACQUISITION_FOLDER.mkdir(parents=True)

data_files = [i for i in DATA_FOLDER.glob("*.h5") if i.is_file()]

# Parse all filenames.
available_files = []
for f in data_files:
    m = re.match(FILENAME_REGEX, f.stem)
    if not m:
        continue
    g = m.groups()
    s = f.stat()

    # Filter the times.
    starttime = obspy.UTCDateTime(*[int(i) for i in g[:7]])
    endtime = obspy.UTCDateTime(*[int(i) for i in g[7:]])

    available_files.append(
        {
            "filename": f,
            "starttime": starttime,
            "endtime": endtime,
        }
    )

# Sort by start time.
available_files = sorted(available_files, key=lambda x: x["starttime"])

script_start_time = time.time()
reference_time = available_files[0]["starttime"]

time.sleep(INITIAL_DELAY_IN_SECONDS)

while available_files:
    current_delay = time.time() - script_start_time
    file_delay = available_files[0]["endtime"] - reference_time
    print(current_delay, file_delay)
    if current_delay > file_delay:
        f = available_files.pop(0)
        target = FAKE_ACQUISITION_FOLDER / f["filename"].name
        print(f"Copying file to {target}")
        print(f"  Remaining files: {len(available_files)}")
        shutil.copyfile(f["filename"], target)

    # A bit scatter to introduce some artificial irregularities.
    time.sleep(random.random() * 1.0)
