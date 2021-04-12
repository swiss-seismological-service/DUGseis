# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.0.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pyqtgraph import GraphicsLayoutWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(973, 685)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.overview_tab = QWidget()
        self.overview_tab.setObjectName(u"overview_tab")
        self.verticalLayout = QVBoxLayout(self.overview_tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget.addTab(self.overview_tab, "")
        self.waveform_tab = QWidget()
        self.waveform_tab.setObjectName(u"waveform_tab")
        self.verticalLayout_3 = QVBoxLayout(self.waveform_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.plotWidget = GraphicsLayoutWidget(self.waveform_tab)
        self.plotWidget.setObjectName(u"plotWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotWidget.sizePolicy().hasHeightForWidth())
        self.plotWidget.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.plotWidget)

        self.channel_list_widget = QListWidget(self.waveform_tab)
        self.channel_list_widget.setObjectName(u"channel_list_widget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.channel_list_widget.sizePolicy().hasHeightForWidth())
        self.channel_list_widget.setSizePolicy(sizePolicy1)
        self.channel_list_widget.setMinimumSize(QSize(120, 0))
        self.channel_list_widget.setMaximumSize(QSize(120, 16777215))
        self.channel_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.horizontalLayout_2.addWidget(self.channel_list_widget)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.events_group_box = QGroupBox(self.waveform_tab)
        self.events_group_box.setObjectName(u"events_group_box")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.events_group_box.sizePolicy().hasHeightForWidth())
        self.events_group_box.setSizePolicy(sizePolicy2)
        self.events_group_box.setMaximumSize(QSize(16777215, 200))
        self.horizontalLayout_6 = QHBoxLayout(self.events_group_box)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label = QLabel(self.events_group_box)
        self.label.setObjectName(u"label")

        self.horizontalLayout_3.addWidget(self.label)

        self.event_number_spin_box = QSpinBox(self.events_group_box)
        self.event_number_spin_box.setObjectName(u"event_number_spin_box")
        self.event_number_spin_box.setMinimumSize(QSize(80, 0))
        self.event_number_spin_box.setMinimum(1)

        self.horizontalLayout_3.addWidget(self.event_number_spin_box)

        self.load_event_button = QPushButton(self.events_group_box)
        self.load_event_button.setObjectName(u"load_event_button")

        self.horizontalLayout_3.addWidget(self.load_event_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.previous_event_button = QPushButton(self.events_group_box)
        self.previous_event_button.setObjectName(u"previous_event_button")

        self.horizontalLayout_4.addWidget(self.previous_event_button)

        self.next_event_button = QPushButton(self.events_group_box)
        self.next_event_button.setObjectName(u"next_event_button")

        self.horizontalLayout_4.addWidget(self.next_event_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.show_channels_with_picks_button = QPushButton(self.events_group_box)
        self.show_channels_with_picks_button.setObjectName(u"show_channels_with_picks_button")

        self.verticalLayout_2.addWidget(self.show_channels_with_picks_button)


        self.horizontalLayout_6.addLayout(self.verticalLayout_2)

        self.event_text_browser = QTextBrowser(self.events_group_box)
        self.event_text_browser.setObjectName(u"event_text_browser")
        self.event_text_browser.setMaximumSize(QSize(16777215, 200))

        self.horizontalLayout_6.addWidget(self.event_text_browser)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.classification_combo_box = QComboBox(self.events_group_box)
        self.classification_combo_box.setObjectName(u"classification_combo_box")

        self.verticalLayout_4.addWidget(self.classification_combo_box)

        self.save_classification_button = QPushButton(self.events_group_box)
        self.save_classification_button.setObjectName(u"save_classification_button")

        self.verticalLayout_4.addWidget(self.save_classification_button)

        self.relocate_push_button = QPushButton(self.events_group_box)
        self.relocate_push_button.setObjectName(u"relocate_push_button")

        self.verticalLayout_4.addWidget(self.relocate_push_button)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_2 = QLabel(self.events_group_box)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_5.addWidget(self.label_2)

        self.pick_type_combo_box = QComboBox(self.events_group_box)
        self.pick_type_combo_box.setObjectName(u"pick_type_combo_box")

        self.horizontalLayout_5.addWidget(self.pick_type_combo_box)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)


        self.verticalLayout_3.addWidget(self.events_group_box)

        self.tabWidget.addTab(self.waveform_tab, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 973, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"DUGSeis", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.overview_tab), QCoreApplication.translate("MainWindow", u"Overview", None))
        self.events_group_box.setTitle(QCoreApplication.translate("MainWindow", u"Events", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Event", None))
        self.load_event_button.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.previous_event_button.setText(QCoreApplication.translate("MainWindow", u"Previous", None))
        self.next_event_button.setText(QCoreApplication.translate("MainWindow", u"Next", None))
        self.show_channels_with_picks_button.setText(QCoreApplication.translate("MainWindow", u"Show Channels with Picks", None))
        self.save_classification_button.setText(QCoreApplication.translate("MainWindow", u"Save Classification", None))
        self.relocate_push_button.setText(QCoreApplication.translate("MainWindow", u"Relocate", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Pick", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.waveform_tab), QCoreApplication.translate("MainWindow", u"Waveforms", None))
    # retranslateUi

