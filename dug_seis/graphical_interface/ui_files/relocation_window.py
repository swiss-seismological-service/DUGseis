# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'relocation_window.ui'
##
## Created by: Qt User Interface Compiler version 6.1.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_RelocationWindow(object):
    def setupUi(self, RelocationWindow):
        if not RelocationWindow.objectName():
            RelocationWindow.setObjectName(u"RelocationWindow")
        RelocationWindow.resize(1100, 800)
        RelocationWindow.setMinimumSize(QSize(1100, 800))
        RelocationWindow.setMaximumSize(QSize(1100, 800))
        self.centralwidget = QWidget(RelocationWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setMinimumSize(QSize(1100, 800))
        self.centralwidget.setMaximumSize(QSize(1100, 800))
        self.verticalLayout_4 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pick_table = QTableWidget(self.centralwidget)
        self.pick_table.setObjectName(u"pick_table")

        self.verticalLayout_4.addWidget(self.pick_table)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout_7 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_5.addWidget(self.label)

        self.velocity_spin_box = QDoubleSpinBox(self.groupBox)
        self.velocity_spin_box.setObjectName(u"velocity_spin_box")
        self.velocity_spin_box.setMaximum(10000.000000000000000)
        self.velocity_spin_box.setSingleStep(100.000000000000000)

        self.horizontalLayout_5.addWidget(self.velocity_spin_box)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_6.addWidget(self.label_2)

        self.damping_spin_box = QDoubleSpinBox(self.groupBox)
        self.damping_spin_box.setObjectName(u"damping_spin_box")
        self.damping_spin_box.setDecimals(3)
        self.damping_spin_box.setMaximum(100.000000000000000)
        self.damping_spin_box.setSingleStep(0.001000000000000)

        self.horizontalLayout_6.addWidget(self.damping_spin_box)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout_7.addLayout(self.verticalLayout_2)

        self.groupBox_2 = QGroupBox(self.groupBox)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.use_anisotropy_check_box = QCheckBox(self.groupBox_2)
        self.use_anisotropy_check_box.setObjectName(u"use_anisotropy_check_box")

        self.verticalLayout.addWidget(self.use_anisotropy_check_box)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.inc_spin_box = QDoubleSpinBox(self.groupBox_2)
        self.inc_spin_box.setObjectName(u"inc_spin_box")
        self.inc_spin_box.setMinimum(-180.000000000000000)
        self.inc_spin_box.setMaximum(180.000000000000000)

        self.horizontalLayout_4.addWidget(self.inc_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_3.addWidget(self.label_4)

        self.azi_spin_box = QDoubleSpinBox(self.groupBox_2)
        self.azi_spin_box.setObjectName(u"azi_spin_box")
        self.azi_spin_box.setMinimum(-360.000000000000000)
        self.azi_spin_box.setMaximum(360.000000000000000)

        self.horizontalLayout_3.addWidget(self.azi_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_2.addWidget(self.label_5)

        self.delta_spin_box = QDoubleSpinBox(self.groupBox_2)
        self.delta_spin_box.setObjectName(u"delta_spin_box")
        self.delta_spin_box.setMinimum(-10.000000000000000)
        self.delta_spin_box.setMaximum(10.000000000000000)

        self.horizontalLayout_2.addWidget(self.delta_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout.addWidget(self.label_6)

        self.epsilon_spin_box = QDoubleSpinBox(self.groupBox_2)
        self.epsilon_spin_box.setObjectName(u"epsilon_spin_box")
        self.epsilon_spin_box.setMinimum(-10.000000000000000)
        self.epsilon_spin_box.setMaximum(10.000000000000000)

        self.horizontalLayout.addWidget(self.epsilon_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.horizontalLayout_7.addWidget(self.groupBox_2)


        self.horizontalLayout_10.addWidget(self.groupBox)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_7 = QLabel(self.centralwidget)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_8.addWidget(self.label_7)

        self.rms_time_error_label = QLabel(self.centralwidget)
        self.rms_time_error_label.setObjectName(u"rms_time_error_label")

        self.horizontalLayout_8.addWidget(self.rms_time_error_label)


        self.verticalLayout_3.addLayout(self.horizontalLayout_8)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_3)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.relocate_push_button = QPushButton(self.centralwidget)
        self.relocate_push_button.setObjectName(u"relocate_push_button")

        self.horizontalLayout_9.addWidget(self.relocate_push_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer)

        self.save_new_origin_push_button = QPushButton(self.centralwidget)
        self.save_new_origin_push_button.setObjectName(u"save_new_origin_push_button")

        self.horizontalLayout_9.addWidget(self.save_new_origin_push_button)


        self.verticalLayout_3.addLayout(self.horizontalLayout_9)


        self.horizontalLayout_10.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_10)

        self.verticalLayout_4.setStretch(0, 2)
        RelocationWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(RelocationWindow)

        QMetaObject.connectSlotsByName(RelocationWindow)
    # setupUi

    def retranslateUi(self, RelocationWindow):
        RelocationWindow.setWindowTitle(QCoreApplication.translate("RelocationWindow", u"Relocate Event", None))
        self.groupBox.setTitle(QCoreApplication.translate("RelocationWindow", u"Location Algorithm Settings", None))
        self.label.setText(QCoreApplication.translate("RelocationWindow", u"Velocity [m/s]", None))
        self.label_2.setText(QCoreApplication.translate("RelocationWindow", u"Damping", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("RelocationWindow", u"Anisotropy", None))
        self.use_anisotropy_check_box.setText(QCoreApplication.translate("RelocationWindow", u"Use Anisotropy", None))
        self.label_3.setText(QCoreApplication.translate("RelocationWindow", u"Inc", None))
        self.label_4.setText(QCoreApplication.translate("RelocationWindow", u"Azi", None))
        self.label_5.setText(QCoreApplication.translate("RelocationWindow", u"Delta", None))
        self.label_6.setText(QCoreApplication.translate("RelocationWindow", u"Epsilon", None))
        self.label_7.setText(QCoreApplication.translate("RelocationWindow", u"RMS origin time error [ms]: ", None))
        self.rms_time_error_label.setText(QCoreApplication.translate("RelocationWindow", u"--", None))
        self.relocate_push_button.setText(QCoreApplication.translate("RelocationWindow", u"Relocate", None))
        self.save_new_origin_push_button.setText(QCoreApplication.translate("RelocationWindow", u"Save new Origin", None))
    # retranslateUi

