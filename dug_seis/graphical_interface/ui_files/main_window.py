# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFrame, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QMenuBar,
    QPushButton, QScrollArea, QSizePolicy, QSlider,
    QSpacerItem, QSpinBox, QSplitter, QStatusBar,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from pyqtgraph import GraphicsLayoutWidget
from pyqtgraph.opengl import GLViewWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1400, 800)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.waveform_tab = QWidget()
        self.waveform_tab.setObjectName(u"waveform_tab")
        self.verticalLayout = QVBoxLayout(self.waveform_tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.waveform_3d_view_splitter = QSplitter(self.waveform_tab)
        self.waveform_3d_view_splitter.setObjectName(u"waveform_3d_view_splitter")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.waveform_3d_view_splitter.sizePolicy().hasHeightForWidth())
        self.waveform_3d_view_splitter.setSizePolicy(sizePolicy)
        self.waveform_3d_view_splitter.setFrameShape(QFrame.NoFrame)
        self.waveform_3d_view_splitter.setFrameShadow(QFrame.Plain)
        self.waveform_3d_view_splitter.setOrientation(Qt.Horizontal)
        self.waveform_3d_view_splitter.setHandleWidth(5)
        self.groupBox = QGroupBox(self.waveform_3d_view_splitter)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.horizontalLayout_14 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_7.addWidget(self.label_3)

        self.filter_combo_box = QComboBox(self.groupBox)
        self.filter_combo_box.setObjectName(u"filter_combo_box")

        self.horizontalLayout_7.addWidget(self.filter_combo_box)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_6)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_7)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_7.addWidget(self.label_5)

        self.duration_label = QLabel(self.groupBox)
        self.duration_label.setObjectName(u"duration_label")
        self.duration_label.setMinimumSize(QSize(0, 0))
        self.duration_label.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_7.addWidget(self.duration_label)

        self.horizontalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_4)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_7.addWidget(self.label_6)

        self.start_time_label = QLabel(self.groupBox)
        self.start_time_label.setObjectName(u"start_time_label")
        self.start_time_label.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_7.addWidget(self.start_time_label)

        self.horizontalSpacer_5 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_5)

        self.label_8 = QLabel(self.groupBox)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_7.addWidget(self.label_8)

        self.end_time_label = QLabel(self.groupBox)
        self.end_time_label.setObjectName(u"end_time_label")
        self.end_time_label.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_7.addWidget(self.end_time_label)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)

        self.scrollArea = QScrollArea(self.groupBox)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 951, 393))
        self.verticalLayout_9 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.plotWidget = GraphicsLayoutWidget(self.scrollAreaWidgetContents)
        self.plotWidget.setObjectName(u"plotWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.plotWidget.sizePolicy().hasHeightForWidth())
        self.plotWidget.setSizePolicy(sizePolicy1)
        self.plotWidget.setMinimumSize(QSize(0, 0))

        self.verticalLayout_9.addWidget(self.plotWidget)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_6.addWidget(self.scrollArea)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.fast_backward_button = QPushButton(self.groupBox)
        self.fast_backward_button.setObjectName(u"fast_backward_button")

        self.horizontalLayout_2.addWidget(self.fast_backward_button)

        self.backward_button = QPushButton(self.groupBox)
        self.backward_button.setObjectName(u"backward_button")

        self.horizontalLayout_2.addWidget(self.backward_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.reset_zoom_button = QPushButton(self.groupBox)
        self.reset_zoom_button.setObjectName(u"reset_zoom_button")

        self.horizontalLayout_2.addWidget(self.reset_zoom_button)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.forward_button = QPushButton(self.groupBox)
        self.forward_button.setObjectName(u"forward_button")

        self.horizontalLayout_2.addWidget(self.forward_button)

        self.fast_forward_button = QPushButton(self.groupBox)
        self.fast_forward_button.setObjectName(u"fast_forward_button")

        self.horizontalLayout_2.addWidget(self.fast_forward_button)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_8)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_9)

        self.label_9 = QLabel(self.groupBox)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_2.addWidget(self.label_9)

        self.mouse_position_label = QLabel(self.groupBox)
        self.mouse_position_label.setObjectName(u"mouse_position_label")

        self.horizontalLayout_2.addWidget(self.mouse_position_label)


        self.verticalLayout_6.addLayout(self.horizontalLayout_2)


        self.horizontalLayout_14.addLayout(self.verticalLayout_6)

        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.groupBox_6 = QGroupBox(self.groupBox)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setMinimumSize(QSize(150, 0))
        self.groupBox_6.setMaximumSize(QSize(150, 16777215))
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_6)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(2, -1, 2, 2)
        self.channel_list_widget = QListWidget(self.groupBox_6)
        self.channel_list_widget.setObjectName(u"channel_list_widget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.channel_list_widget.sizePolicy().hasHeightForWidth())
        self.channel_list_widget.setSizePolicy(sizePolicy2)
        self.channel_list_widget.setMinimumSize(QSize(0, 0))
        self.channel_list_widget.setMaximumSize(QSize(16777215, 16777215))
        self.channel_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.verticalLayout_5.addWidget(self.channel_list_widget)

        self.show_channels_with_picks_button = QPushButton(self.groupBox_6)
        self.show_channels_with_picks_button.setObjectName(u"show_channels_with_picks_button")
        font = QFont()
        font.setPointSize(7)
        self.show_channels_with_picks_button.setFont(font)
        self.show_channels_with_picks_button.setFlat(False)

        self.verticalLayout_5.addWidget(self.show_channels_with_picks_button)

        self.show_closest_channels_button = QPushButton(self.groupBox_6)
        self.show_closest_channels_button.setObjectName(u"show_closest_channels_button")
        self.show_closest_channels_button.setFont(font)

        self.verticalLayout_5.addWidget(self.show_closest_channels_button)


        self.verticalLayout_10.addWidget(self.groupBox_6)

        self.groupBox_5 = QGroupBox(self.groupBox)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy3)
        self.horizontalLayout_11 = QHBoxLayout(self.groupBox_5)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.height_per_trace_slider = QSlider(self.groupBox_5)
        self.height_per_trace_slider.setObjectName(u"height_per_trace_slider")
        self.height_per_trace_slider.setMinimum(10)
        self.height_per_trace_slider.setMaximum(200)
        self.height_per_trace_slider.setSingleStep(10)
        self.height_per_trace_slider.setPageStep(25)
        self.height_per_trace_slider.setValue(100)
        self.height_per_trace_slider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_11.addWidget(self.height_per_trace_slider)

        self.height_per_trace_label = QLabel(self.groupBox_5)
        self.height_per_trace_label.setObjectName(u"height_per_trace_label")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.height_per_trace_label.sizePolicy().hasHeightForWidth())
        self.height_per_trace_label.setSizePolicy(sizePolicy4)
        self.height_per_trace_label.setMinimumSize(QSize(20, 0))
        self.height_per_trace_label.setMaximumSize(QSize(20, 16777215))
        self.height_per_trace_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_11.addWidget(self.height_per_trace_label)


        self.verticalLayout_10.addWidget(self.groupBox_5)


        self.horizontalLayout_14.addLayout(self.verticalLayout_10)

        self.horizontalLayout_14.setStretch(0, 2)
        self.waveform_3d_view_splitter.addWidget(self.groupBox)
        self.groupBox_2 = QGroupBox(self.waveform_3d_view_splitter)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_7 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(2, -1, 2, 2)
        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")
        sizePolicy3.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy3)
        self.label_10.setFont(font)

        self.verticalLayout_7.addWidget(self.label_10)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")
        sizePolicy3.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy3)
        self.label_11.setFont(font)

        self.verticalLayout_7.addWidget(self.label_11)

        self.stationViewGLWidget = GLViewWidget(self.groupBox_2)
        self.stationViewGLWidget.setObjectName(u"stationViewGLWidget")
        sizePolicy.setHeightForWidth(self.stationViewGLWidget.sizePolicy().hasHeightForWidth())
        self.stationViewGLWidget.setSizePolicy(sizePolicy)
        self.stationViewGLWidget.setMinimumSize(QSize(0, 0))

        self.verticalLayout_7.addWidget(self.stationViewGLWidget)

        self.waveform_3d_view_splitter.addWidget(self.groupBox_2)

        self.verticalLayout.addWidget(self.waveform_3d_view_splitter)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.groupBox_3 = QGroupBox(self.waveform_tab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_2 = QLabel(self.groupBox_3)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_5.addWidget(self.label_2)

        self.pick_type_combo_box = QComboBox(self.groupBox_3)
        self.pick_type_combo_box.setObjectName(u"pick_type_combo_box")

        self.horizontalLayout_5.addWidget(self.pick_type_combo_box)


        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_9.addWidget(self.label_4)

        self.polarity_combo_box = QComboBox(self.groupBox_3)
        self.polarity_combo_box.setObjectName(u"polarity_combo_box")

        self.horizontalLayout_9.addWidget(self.polarity_combo_box)


        self.verticalLayout_3.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_7 = QLabel(self.groupBox_3)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_12.addWidget(self.label_7)

        self.uncertainty_combo_box = QComboBox(self.groupBox_3)
        self.uncertainty_combo_box.setObjectName(u"uncertainty_combo_box")

        self.horizontalLayout_12.addWidget(self.uncertainty_combo_box)


        self.verticalLayout_3.addLayout(self.horizontalLayout_12)

        self.verticalSpacer = QSpacerItem(20, 117, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.save_picks_in_dummy_arrival = QPushButton(self.groupBox_3)
        self.save_picks_in_dummy_arrival.setObjectName(u"save_picks_in_dummy_arrival")

        self.verticalLayout_3.addWidget(self.save_picks_in_dummy_arrival)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_4)

        self.show_all_picks_check_box = QCheckBox(self.groupBox_3)
        self.show_all_picks_check_box.setObjectName(u"show_all_picks_check_box")

        self.verticalLayout_3.addWidget(self.show_all_picks_check_box)


        self.horizontalLayout_10.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.waveform_tab)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.horizontalLayout_15 = QHBoxLayout(self.groupBox_4)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.classification_combo_box = QComboBox(self.groupBox_4)
        self.classification_combo_box.setObjectName(u"classification_combo_box")

        self.verticalLayout_8.addWidget(self.classification_combo_box)

        self.save_classification_button = QPushButton(self.groupBox_4)
        self.save_classification_button.setObjectName(u"save_classification_button")

        self.verticalLayout_8.addWidget(self.save_classification_button)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_2)

        self.relocate_push_button = QPushButton(self.groupBox_4)
        self.relocate_push_button.setObjectName(u"relocate_push_button")

        self.verticalLayout_8.addWidget(self.relocate_push_button)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_3)

        self.save_visible_data_button = QPushButton(self.groupBox_4)
        self.save_visible_data_button.setObjectName(u"save_visible_data_button")

        self.verticalLayout_8.addWidget(self.save_visible_data_button)

        self.create_trace_plot_push_button = QPushButton(self.groupBox_4)
        self.create_trace_plot_push_button.setObjectName(u"create_trace_plot_push_button")

        self.verticalLayout_8.addWidget(self.create_trace_plot_push_button)


        self.horizontalLayout_15.addLayout(self.verticalLayout_8)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_5)

        self.reload_data_button = QPushButton(self.groupBox_4)
        self.reload_data_button.setObjectName(u"reload_data_button")

        self.verticalLayout_4.addWidget(self.reload_data_button)

        self.reload_on_data_change_check_box = QCheckBox(self.groupBox_4)
        self.reload_on_data_change_check_box.setObjectName(u"reload_on_data_change_check_box")

        self.verticalLayout_4.addWidget(self.reload_on_data_change_check_box)


        self.horizontalLayout_15.addLayout(self.verticalLayout_4)

        self.horizontalLayout_15.setStretch(0, 1)
        self.horizontalLayout_15.setStretch(1, 1)

        self.horizontalLayout_10.addWidget(self.groupBox_4)

        self.events_group_box = QGroupBox(self.waveform_tab)
        self.events_group_box.setObjectName(u"events_group_box")
        sizePolicy5 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.events_group_box.sizePolicy().hasHeightForWidth())
        self.events_group_box.setSizePolicy(sizePolicy5)
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

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_12 = QLabel(self.events_group_box)
        self.label_12.setObjectName(u"label_12")
        sizePolicy6 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy6)

        self.horizontalLayout_8.addWidget(self.label_12)

        self.origin_selection_combo_box = QComboBox(self.events_group_box)
        self.origin_selection_combo_box.setObjectName(u"origin_selection_combo_box")

        self.horizontalLayout_8.addWidget(self.origin_selection_combo_box)

        self.horizontalLayout_8.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.previous_event_button = QPushButton(self.events_group_box)
        self.previous_event_button.setObjectName(u"previous_event_button")

        self.horizontalLayout_4.addWidget(self.previous_event_button)

        self.next_event_button = QPushButton(self.events_group_box)
        self.next_event_button.setObjectName(u"next_event_button")

        self.horizontalLayout_4.addWidget(self.next_event_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_6.addLayout(self.verticalLayout_2)

        self.event_text_browser = QTextBrowser(self.events_group_box)
        self.event_text_browser.setObjectName(u"event_text_browser")
        self.event_text_browser.setMaximumSize(QSize(16777215, 200))

        self.horizontalLayout_6.addWidget(self.event_text_browser)

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 4)

        self.horizontalLayout_10.addWidget(self.events_group_box)

        self.horizontalLayout_10.setStretch(2, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_10)

        self.verticalLayout.setStretch(0, 10)
        self.verticalLayout.setStretch(1, 1)
        self.tabWidget.addTab(self.waveform_tab, "")
        self.info_tab = QWidget()
        self.info_tab.setObjectName(u"info_tab")
        self.horizontalLayout_13 = QHBoxLayout(self.info_tab)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.info_text_browser = QTextBrowser(self.info_tab)
        self.info_text_browser.setObjectName(u"info_text_browser")

        self.horizontalLayout_13.addWidget(self.info_text_browser)

        self.tabWidget.addTab(self.info_tab, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1400, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"DUGSeis", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Waveform View", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Choose waveform filter:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Plotted duration:", None))
        self.duration_label.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Start time:", None))
        self.start_time_label.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"End time:", None))
        self.end_time_label.setText(QCoreApplication.translate("MainWindow", u"---", None))
        self.fast_backward_button.setText(QCoreApplication.translate("MainWindow", u"<<", None))
        self.backward_button.setText(QCoreApplication.translate("MainWindow", u"<", None))
#if QT_CONFIG(shortcut)
        self.backward_button.setShortcut(QCoreApplication.translate("MainWindow", u"Left", None))
#endif // QT_CONFIG(shortcut)
        self.reset_zoom_button.setText(QCoreApplication.translate("MainWindow", u"Reset Zoom", None))
        self.forward_button.setText(QCoreApplication.translate("MainWindow", u">", None))
#if QT_CONFIG(shortcut)
        self.forward_button.setShortcut(QCoreApplication.translate("MainWindow", u"Right", None))
#endif // QT_CONFIG(shortcut)
        self.fast_forward_button.setText(QCoreApplication.translate("MainWindow", u">>", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Mouse position:", None))
        self.mouse_position_label.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Channel Selector", None))
        self.show_channels_with_picks_button.setText(QCoreApplication.translate("MainWindow", u"Show [C]hannels with Picks", None))
#if QT_CONFIG(shortcut)
        self.show_channels_with_picks_button.setShortcut(QCoreApplication.translate("MainWindow", u"C", None))
#endif // QT_CONFIG(shortcut)
        self.show_closest_channels_button.setText(QCoreApplication.translate("MainWindow", u"Show Closest Channels", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Minimum Height per Trace", None))
        self.height_per_trace_label.setText(QCoreApplication.translate("MainWindow", u"100", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"3D View", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Right click to select event", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Ctrl + right click to (de)select a channel", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Pick Settings", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Phase", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Polarity", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Uncertainty [ms]", None))
        self.save_picks_in_dummy_arrival.setText(QCoreApplication.translate("MainWindow", u"Save Arrival-less Picks in Dummy Origin", None))
        self.show_all_picks_check_box.setText(QCoreApplication.translate("MainWindow", u"Show All Picks", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Actions", None))
        self.save_classification_button.setText(QCoreApplication.translate("MainWindow", u"Save Classification", None))
        self.relocate_push_button.setText(QCoreApplication.translate("MainWindow", u"Relocate Event", None))
#if QT_CONFIG(tooltip)
        self.save_visible_data_button.setToolTip(QCoreApplication.translate("MainWindow", u"Opens a dialogue box to save the visible data to disk in a selection of different file formats.", None))
#endif // QT_CONFIG(tooltip)
        self.save_visible_data_button.setText(QCoreApplication.translate("MainWindow", u"Save Visible Data", None))
        self.create_trace_plot_push_button.setText(QCoreApplication.translate("MainWindow", u"Plot all Traces", None))
        self.reload_data_button.setText(QCoreApplication.translate("MainWindow", u"Reload Data", None))
        self.reload_on_data_change_check_box.setText(QCoreApplication.translate("MainWindow", u"Reload on Data Change", None))
        self.events_group_box.setTitle(QCoreApplication.translate("MainWindow", u"Events", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Event", None))
        self.load_event_button.setText(QCoreApplication.translate("MainWindow", u"Load Event", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Origin in 3D View", None))
        self.previous_event_button.setText(QCoreApplication.translate("MainWindow", u"[P]revious Event", None))
#if QT_CONFIG(shortcut)
        self.previous_event_button.setShortcut(QCoreApplication.translate("MainWindow", u"P", None))
#endif // QT_CONFIG(shortcut)
        self.next_event_button.setText(QCoreApplication.translate("MainWindow", u"[N]ext Event", None))
#if QT_CONFIG(shortcut)
        self.next_event_button.setShortcut(QCoreApplication.translate("MainWindow", u"N", None))
#endif // QT_CONFIG(shortcut)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.waveform_tab), QCoreApplication.translate("MainWindow", u"Data Browser", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.info_tab), QCoreApplication.translate("MainWindow", u"Information", None))
    # retranslateUi

