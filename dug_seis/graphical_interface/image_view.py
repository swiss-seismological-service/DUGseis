# DUGSeis
# Copyright (C) 2022 DUGSeis Authors
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

from PySide6 import QtGui, QtWidgets


class ImageView(QtWidgets.QDialog):
    def __init__(self, parent, image_data: bytes):
        super().__init__(parent)

        self.setWindowTitle("All Waveforms View")

        # Load as image.
        self.lb = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image_data)
        self.lb.setPixmap(pixmap)

        # Figure out a nice geometry for everything.
        g = QtWidgets.QWidget.screen(parent).availableGeometry()
        self.resize(pixmap.width() + 50, g.height() - 100)
        qr = self.frameGeometry()
        qr.moveCenter(g.center())
        self.move(qr.topLeft())

        # Display everything inside a scrollbar.
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.lb)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

        self.show()
