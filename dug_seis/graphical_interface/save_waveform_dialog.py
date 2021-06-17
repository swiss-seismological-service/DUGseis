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
Dialog box to save waveform data to disc.
"""

import datetime
import pathlib
import typing

import obspy
from PySide6 import QtCore, QtWidgets

from ..project.project import DUGSeisProject
from .ui_files.save_waveforms_dialog import Ui_SaveWaveformsDialog


class SaveWaveformsDialog(QtWidgets.QDialog):
    """
    Dialog box to save waveforms to disk.
    """

    def __init__(
        self,
        parent,
        starttime: obspy.UTCDateTime,
        endtime: obspy.UTCDateTime,
        channels: typing.List[str],
        project: DUGSeisProject,
    ):
        super().__init__(parent)
        self.ui = Ui_SaveWaveformsDialog()
        self.ui.setupUi(self)

        self.starttime = starttime
        self.endtime = endtime
        self.channels = channels
        self.project = project

        self.npts_per_channel = int(
            round((self.endtime - self.starttime) / self.project.waveforms.dt + 1)
        )

        self.ui.titel_label.setText(
            f"Saving waveform data from {len(self.channels)} channels."
        )
        self.ui.samples_label.setText(
            f"Will write about {self.npts_per_channel} samples per channel."
        )

        d = self.endtime - self.starttime
        self.ui.times_label.setText(f"{self.starttime} - {self.endtime}")
        self.ui.duration_label.setText(f"{d:.5g} seconds of data")
        self.filename = None
        self.ui.file_format_combo_box.insertItems(0, ["MSEED", "SAC"])

        suffix = self.ui.file_format_combo_box.currentText().lower()
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = pathlib.Path(f"waveforms_{now}.{suffix}").absolute()
        self.ui.filename_label.setText(str(self.filename))

    def setCentralWidget(self, *args, **kwargs):
        pass

    @QtCore.Slot()
    def on_file_format_combo_box_currentIndexChanged(self, *args, **kwargs):
        if not self.filename:
            return
        suffix = self.ui.file_format_combo_box.currentText().lower()
        self.filename = self.filename.parent / f"{self.filename.stem}.{suffix}"
        self.ui.filename_label.setText(str(self.filename))

    @QtCore.Slot()
    def on_change_destination_push_button_released(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            parent=self, caption="Choose output file", dir=str(self.filename.parent)
        )
        # Cancelled.
        if not filename[0]:
            return
        self.filename = pathlib.Path(filename[0]).absolute()
        self.ui.filename_label.setText(str(self.filename))

    @QtCore.Slot()
    def on_write_data_push_button_released(self):
        # Should not be possible so just a safety fuse.
        if self.npts_per_channel > 100e6:
            raise ValueError("Too many samples!")
        st = self.project.waveforms.get_waveforms(
            channel_ids=self.channels, start_time=self.starttime, end_time=self.endtime
        )
        st.write(
            filename=str(self.filename),
            format=self.ui.file_format_combo_box.currentText(),
        )
        self.done(0)
