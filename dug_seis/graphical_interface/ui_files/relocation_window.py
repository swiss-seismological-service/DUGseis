# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'relocation_window.ui'
##
## Created by: Qt User Interface Compiler version 6.2.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

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
        self.verticalLayout_6 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.pick_table = QTableWidget(self.centralwidget)
        self.pick_table.setObjectName(u"pick_table")

        self.verticalLayout_6.addWidget(self.pick_table)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout_16 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
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

        self.p_velocity_spin_box = QDoubleSpinBox(self.groupBox)
        self.p_velocity_spin_box.setObjectName(u"p_velocity_spin_box")
        self.p_velocity_spin_box.setMaximum(10000.000000000000000)
        self.p_velocity_spin_box.setSingleStep(100.000000000000000)

        self.horizontalLayout_5.addWidget(self.p_velocity_spin_box)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_9 = QLabel(self.groupBox)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_10.addWidget(self.label_9)

        self.s_velocity_spin_box = QDoubleSpinBox(self.groupBox)
        self.s_velocity_spin_box.setObjectName(u"s_velocity_spin_box")
        self.s_velocity_spin_box.setMaximum(10000.000000000000000)
        self.s_velocity_spin_box.setSingleStep(100.000000000000000)

        self.horizontalLayout_10.addWidget(self.s_velocity_spin_box)


        self.verticalLayout_2.addLayout(self.horizontalLayout_10)

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


        self.horizontalLayout_16.addLayout(self.verticalLayout_2)

        self.groupBox_2 = QGroupBox(self.groupBox)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.use_anisotropy_check_box = QCheckBox(self.groupBox_2)
        self.use_anisotropy_check_box.setObjectName(u"use_anisotropy_check_box")

        self.verticalLayout_5.addWidget(self.use_anisotropy_check_box)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.groupBox_3 = QGroupBox(self.groupBox_2)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout = QVBoxLayout(self.groupBox_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.groupBox_3)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.p_inc_spin_box = QDoubleSpinBox(self.groupBox_3)
        self.p_inc_spin_box.setObjectName(u"p_inc_spin_box")
        self.p_inc_spin_box.setMinimum(-180.000000000000000)
        self.p_inc_spin_box.setMaximum(180.000000000000000)

        self.horizontalLayout_4.addWidget(self.p_inc_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_3.addWidget(self.label_4)

        self.p_azi_spin_box = QDoubleSpinBox(self.groupBox_3)
        self.p_azi_spin_box.setObjectName(u"p_azi_spin_box")
        self.p_azi_spin_box.setMinimum(-360.000000000000000)
        self.p_azi_spin_box.setMaximum(360.000000000000000)

        self.horizontalLayout_3.addWidget(self.p_azi_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_5 = QLabel(self.groupBox_3)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_2.addWidget(self.label_5)

        self.p_delta_spin_box = QDoubleSpinBox(self.groupBox_3)
        self.p_delta_spin_box.setObjectName(u"p_delta_spin_box")
        self.p_delta_spin_box.setMinimum(-10.000000000000000)
        self.p_delta_spin_box.setMaximum(10.000000000000000)

        self.horizontalLayout_2.addWidget(self.p_delta_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_6 = QLabel(self.groupBox_3)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout.addWidget(self.label_6)

        self.p_epsilon_spin_box = QDoubleSpinBox(self.groupBox_3)
        self.p_epsilon_spin_box.setObjectName(u"p_epsilon_spin_box")
        self.p_epsilon_spin_box.setMinimum(-10.000000000000000)
        self.p_epsilon_spin_box.setMaximum(10.000000000000000)

        self.horizontalLayout.addWidget(self.p_epsilon_spin_box)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.horizontalLayout_15.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.groupBox_2)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_10 = QLabel(self.groupBox_4)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_11.addWidget(self.label_10)

        self.s_inc_spin_box = QDoubleSpinBox(self.groupBox_4)
        self.s_inc_spin_box.setObjectName(u"s_inc_spin_box")
        self.s_inc_spin_box.setMinimum(-180.000000000000000)
        self.s_inc_spin_box.setMaximum(180.000000000000000)

        self.horizontalLayout_11.addWidget(self.s_inc_spin_box)


        self.verticalLayout_4.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_11 = QLabel(self.groupBox_4)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_12.addWidget(self.label_11)

        self.s_azi_spin_box = QDoubleSpinBox(self.groupBox_4)
        self.s_azi_spin_box.setObjectName(u"s_azi_spin_box")
        self.s_azi_spin_box.setMinimum(-360.000000000000000)
        self.s_azi_spin_box.setMaximum(360.000000000000000)

        self.horizontalLayout_12.addWidget(self.s_azi_spin_box)


        self.verticalLayout_4.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_12 = QLabel(self.groupBox_4)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_13.addWidget(self.label_12)

        self.s_delta_spin_box = QDoubleSpinBox(self.groupBox_4)
        self.s_delta_spin_box.setObjectName(u"s_delta_spin_box")
        self.s_delta_spin_box.setMinimum(-10.000000000000000)
        self.s_delta_spin_box.setMaximum(10.000000000000000)

        self.horizontalLayout_13.addWidget(self.s_delta_spin_box)


        self.verticalLayout_4.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_13 = QLabel(self.groupBox_4)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_14.addWidget(self.label_13)

        self.s_epsilon_spin_box = QDoubleSpinBox(self.groupBox_4)
        self.s_epsilon_spin_box.setObjectName(u"s_epsilon_spin_box")
        self.s_epsilon_spin_box.setMinimum(-10.000000000000000)
        self.s_epsilon_spin_box.setMaximum(10.000000000000000)

        self.horizontalLayout_14.addWidget(self.s_epsilon_spin_box)


        self.verticalLayout_4.addLayout(self.horizontalLayout_14)


        self.horizontalLayout_15.addWidget(self.groupBox_4)


        self.verticalLayout_5.addLayout(self.horizontalLayout_15)


        self.horizontalLayout_16.addWidget(self.groupBox_2)


        self.horizontalLayout_17.addWidget(self.groupBox)

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


        self.horizontalLayout_17.addLayout(self.verticalLayout_3)


        self.verticalLayout_6.addLayout(self.horizontalLayout_17)

        self.verticalLayout_6.setStretch(0, 2)
        RelocationWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(RelocationWindow)

        QMetaObject.connectSlotsByName(RelocationWindow)
    # setupUi

    def retranslateUi(self, RelocationWindow):
        RelocationWindow.setWindowTitle(QCoreApplication.translate("RelocationWindow", u"Relocate Event", None))
        self.groupBox.setTitle(QCoreApplication.translate("RelocationWindow", u"Location Algorithm Settings", None))
        self.label.setText(QCoreApplication.translate("RelocationWindow", u"P Velocity [m/s]", None))
        self.label_9.setText(QCoreApplication.translate("RelocationWindow", u"S Velocity [m/s]", None))
        self.label_2.setText(QCoreApplication.translate("RelocationWindow", u"Damping", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("RelocationWindow", u"Anisotropy", None))
        self.use_anisotropy_check_box.setText(QCoreApplication.translate("RelocationWindow", u"Use Anisotropy", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("RelocationWindow", u"P Anisotropy", None))
        self.label_3.setText(QCoreApplication.translate("RelocationWindow", u"Inc", None))
        self.label_4.setText(QCoreApplication.translate("RelocationWindow", u"Azi", None))
        self.label_5.setText(QCoreApplication.translate("RelocationWindow", u"Delta", None))
        self.label_6.setText(QCoreApplication.translate("RelocationWindow", u"Epsilon", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("RelocationWindow", u"S Anisotropy", None))
        self.label_10.setText(QCoreApplication.translate("RelocationWindow", u"Inc", None))
        self.label_11.setText(QCoreApplication.translate("RelocationWindow", u"Azi", None))
        self.label_12.setText(QCoreApplication.translate("RelocationWindow", u"Delta", None))
        self.label_13.setText(QCoreApplication.translate("RelocationWindow", u"Epsilon", None))
        self.label_7.setText(QCoreApplication.translate("RelocationWindow", u"RMS origin time error [ms]: ", None))
        self.rms_time_error_label.setText(QCoreApplication.translate("RelocationWindow", u"--", None))
        self.relocate_push_button.setText(QCoreApplication.translate("RelocationWindow", u"Relocate", None))
        self.save_new_origin_push_button.setText(QCoreApplication.translate("RelocationWindow", u"Save new Origin", None))
    # retranslateUi

