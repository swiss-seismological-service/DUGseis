# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'save_waveforms_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.0.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class Ui_SaveWaveformsDialog(object):
    def setupUi(self, SaveWaveformsDialog):
        if not SaveWaveformsDialog.objectName():
            SaveWaveformsDialog.setObjectName(u"SaveWaveformsDialog")
        SaveWaveformsDialog.setEnabled(True)
        SaveWaveformsDialog.resize(1000, 188)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SaveWaveformsDialog.sizePolicy().hasHeightForWidth())
        SaveWaveformsDialog.setSizePolicy(sizePolicy)
        SaveWaveformsDialog.setMinimumSize(QSize(1000, 188))
        SaveWaveformsDialog.setMaximumSize(QSize(1000, 188))
        self.centralwidget = QWidget(SaveWaveformsDialog)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QSize(1000, 188))
        self.centralwidget.setMaximumSize(QSize(1000, 188))
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.titel_label = QLabel(self.centralwidget)
        self.titel_label.setObjectName(u"titel_label")

        self.verticalLayout.addWidget(self.titel_label)

        self.times_label = QLabel(self.centralwidget)
        self.times_label.setObjectName(u"times_label")

        self.verticalLayout.addWidget(self.times_label)

        self.duration_label = QLabel(self.centralwidget)
        self.duration_label.setObjectName(u"duration_label")

        self.verticalLayout.addWidget(self.duration_label)

        self.samples_label = QLabel(self.centralwidget)
        self.samples_label.setObjectName(u"samples_label")

        self.verticalLayout.addWidget(self.samples_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.change_destination_push_button = QPushButton(self.centralwidget)
        self.change_destination_push_button.setObjectName(u"change_destination_push_button")

        self.horizontalLayout_2.addWidget(self.change_destination_push_button)

        self.filename_label = QLabel(self.centralwidget)
        self.filename_label.setObjectName(u"filename_label")

        self.horizontalLayout_2.addWidget(self.filename_label)

        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.file_format_label = QLabel(self.centralwidget)
        self.file_format_label.setObjectName(u"file_format_label")

        self.horizontalLayout.addWidget(self.file_format_label)

        self.file_format_combo_box = QComboBox(self.centralwidget)
        self.file_format_combo_box.setObjectName(u"file_format_combo_box")

        self.horizontalLayout.addWidget(self.file_format_combo_box)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.write_data_push_button = QPushButton(self.centralwidget)
        self.write_data_push_button.setObjectName(u"write_data_push_button")

        self.horizontalLayout.addWidget(self.write_data_push_button)


        self.verticalLayout.addLayout(self.horizontalLayout)

        SaveWaveformsDialog.setCentralWidget(self.centralwidget)

        self.retranslateUi(SaveWaveformsDialog)

        QMetaObject.connectSlotsByName(SaveWaveformsDialog)
    # setupUi

    def retranslateUi(self, SaveWaveformsDialog):
        SaveWaveformsDialog.setWindowTitle(QCoreApplication.translate("SaveWaveformsDialog", u"Save Visible Data Dialog", None))
        self.titel_label.setText(QCoreApplication.translate("SaveWaveformsDialog", u"You are about to save waveform data from ", None))
        self.times_label.setText(QCoreApplication.translate("SaveWaveformsDialog", u"Times", None))
        self.duration_label.setText(QCoreApplication.translate("SaveWaveformsDialog", u"Duration", None))
        self.samples_label.setText(QCoreApplication.translate("SaveWaveformsDialog", u"samples label", None))
        self.change_destination_push_button.setText(QCoreApplication.translate("SaveWaveformsDialog", u"Change destination", None))
        self.filename_label.setText(QCoreApplication.translate("SaveWaveformsDialog", u"Filename", None))
        self.file_format_label.setText(QCoreApplication.translate("SaveWaveformsDialog", u"File format:", None))
        self.write_data_push_button.setText(QCoreApplication.translate("SaveWaveformsDialog", u"Write Data", None))
    # retranslateUi

