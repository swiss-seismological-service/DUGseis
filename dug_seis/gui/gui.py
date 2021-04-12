# GUI module of DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import copy
from datetime import datetime, timedelta
from functools import reduce
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

import oyaml as yaml
# from matplotlib.backends.backend_qt5agg import (
#     FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
# from matplotlib.backend_bases import MouseEvent as MplMouseEvent
# from matplotlib.figure import Figure

from obspy import UTCDateTime


from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import (QSize, QStandardPaths, Qt, QTimer,
    QThreadPool, Slot)
from PySide6.QtWidgets import (QApplication, #qApp,
    QMainWindow, #QShortcut,
    QMessageBox, QFileDialog, QSizePolicy,
    QGridLayout, QVBoxLayout, QHBoxLayout,
    QWidget, QStackedLayout, QScrollArea, QGroupBox,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QPushButton)
from PySide6.QtGui import QAction, QKeySequence


from dug_seis import util
import dug_seis.acquisition.acquisition as dugseis_acquisition
from dug_seis.gui import gui_util
from dug_seis.gui.gui_cfg import param_gui, param_hidden, help_content
from dug_seis.processing.processing import processing as dugseis_processing


WIDTH_SECTIONS = 640
# used to calculate an average size of ASDF files
FILE_COUNT_FOR_TIME_ESTIMATION = 5


class App(QMainWindow):
    '''
    GUI Application

    Meaning of variables
    param_gui       configuration data for GUI elements
    breadcrumb      hierarchical path of an element,
                    e. g. ['Trigger', 'classification', 'spread_int']

    Attributes
        param               hierarchical parameters for dug_seis calculations
        elems               QT widgets for parameters defined in gui_cfg
                            with values read from YAML files
        seis_events(dict)   keys: e. g. '2017-09-02  13:24:20.228_483'
                            values: dict containing event properties read
                                    from JSON file plus:
                                    - file name
                                    - sensor_count
    '''

    def __init__(self):
        super().__init__()
        self.dir = os.path.dirname(__file__)
        self.elems = {}
        self.group_boxes = {}
        self.communication = {}
        self.seis_events = {}
        self.axs = {}
        self.axs_lims = {}
        self.load_config_default()

        # needed for switching the visibility
        self.switchers = {}

        self.threadpool = QThreadPool()
        print('Multithreading with maximum %d threads'
              % self.threadpool.maxThreadCount())

        self.initUI()
        for key in self.switchers:
            self.generate_switcher(
                combo_box=self.elems[tuple(key)],
                breadcrumb_parent=tuple(key[:-1]),
                options=self.switchers[tuple(key)],
                initial_option_to_show=self.param_get_value(tuple(key)),
            )
        self.load_config_home()
        self.periodic_tasks_setup()

        # dev code
        # from gui_dev import gui_ready
        # gui_ready(self)


    ###########################################################################
    ##  Setup GUI                                                            ##
    ###########################################################################

    def generate_switcher(self, combo_box, breadcrumb_parent,
            options, initial_option_to_show):

        def switcher(option_to_show):
            # hide all groups
            for option in options:
                self.group_boxes[breadcrumb_parent + (option,)].hide()

            # show desired group
            self.group_boxes[breadcrumb_parent + (option_to_show,)].show()

        # select option according to self.param
        switcher(initial_option_to_show)

        # setup event for "value combo box is changed"
        # combo_box.currentIndexChanged[str].connect(switcher)


    def initUI(self):
        # main elements
        self.setup_menu()
        self.setup_central_widget()

        self.setWindowTitle('DUG-Seis')
        # self.setWindowIcon(QIcon('logo.gif'))

        with open(os.path.join(self.dir, 'style.css'), 'r') as file_handle:
            self.setStyleSheet(file_handle.read())
            file_handle.close()

        #self.init_shortcuts()
        self.showMaximized()


    # Main Areas

    def setup_central_widget(self):
        central = QWidget()

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.generate_sections_widget())
        #top_layout.addWidget(self.setup_canvas())

        vbox = QVBoxLayout()
        vbox.addLayout(self.setup_top_layout())
        vbox.addLayout(top_layout)
        vbox.addLayout(self.setup_log_and_events())
        central.setLayout(vbox)

        self.setCentralWidget(central)


    def setup_menu(self):
        self.menubar = self.menuBar()

        config_save_act = QAction('&Save config', self)
        config_save_act.setShortcut('Ctrl+S')
        config_save_act.setStatusTip('Write dug-seis.yaml')
        config_save_act.triggered.connect(self.diag_dump_yaml)

        config_open_act = QAction('&Open config', self)
        config_open_act.setShortcut('Ctrl+O')
        config_open_act.setStatusTip('Write dug-seis.yaml')
        config_open_act.triggered.connect(self.diag_load_config)

        config_menu = self.menubar.addMenu('&Configuration')
        config_menu.addAction(config_save_act)
        config_menu.addAction(config_open_act)

        quit_act = QAction('&Quit', self)
        quit_act.triggered.connect(self.quit_app)
        config_menu = self.menubar.addAction(quit_act)


    def setup_top_layout(self):
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.setup_section_buttons())

        acqu_group, proc_group, redis_group = self.setup_monitor_widget()
        top_layout.addLayout(acqu_group)
        top_layout.addLayout(redis_group)
        top_layout.addLayout(proc_group)
        top_layout.setAlignment(Qt.AlignLeft)
        #self.monitor_update_acqu()
        #self.monitor_update_redis()
        return top_layout


    def setup_section_buttons(self):
        btns_wid = QWidget()
        btns = QVBoxLayout()
        btns.setContentsMargins(0, 0, 0, 0)
        btns.setAlignment(Qt.AlignLeft)
        btns_wid.setFixedWidth(WIDTH_SECTIONS)
        btns_wid.setLayout(btns)

        btns_1 = QHBoxLayout()
        btns_2 = QHBoxLayout()

        self.section_buttons = {}

        btns_1.addWidget(self.setup_section_button(0, 'General', True))
        btns_1.addWidget(self.setup_section_button(2, 'Acquisition'))
        btns_1.addWidget(self.setup_section_button(4, 'Trigger'))
        btns_1.addWidget(self.setup_section_button(6, 'Location, Magn.'))

        btns_2.addWidget(self.setup_section_button(1, 'Channels'))
        btns_2.addWidget(self.setup_section_button(3, 'Processing'))
        btns_2.addWidget(self.setup_section_button(5, 'Picker'))
        btns_2.addWidget(self.setup_section_button(7, 'Help'))

        btns.addLayout(btns_1)
        btns.addLayout(btns_2)
        return btns_wid


    def setup_section_button(self, idx, title, is_initial=False):
        style_normal = 'background-color: #c8c8c8; font-weight: normal;'
        style_active = 'background-color: #f0f0f0; font-weight: bold;'

        btn = QPushButton(title)
        btn.setFixedSize(115, 26)
        if is_initial:
            btn.setStyleSheet(style_active)
            self.last_section_button = btn
        else:
            btn.setStyleSheet(style_normal)
        btn.clicked.connect(lambda: self.activate_section(idx))
        self.section_buttons[idx] = btn
        return btn


    def activate_section(self, idx):
        style_normal = 'background-color: #c8c8c8; font-weight: normal;'
        style_active = 'background-color: #f0f0f0; font-weight: bold;'
        if self.last_section_button is not None:
            self.last_section_button.setStyleSheet(style_normal)
        self.sections_layout.setCurrentIndex(idx)
        btn = self.section_buttons[idx]
        btn.setStyleSheet(style_active)
        self.last_section_button = btn


    def setup_monitor_widget(self):
        self.monitor = {}
        moni = self.monitor

        # acquisition
        acqu_group = QVBoxLayout()
        acqu_title = QHBoxLayout()
        label = QLabel('Acquisition')
        label.setStyleSheet('QLabel {font-weight: bold;}')
        acqu_title.addWidget(label)

        acqu_content = QHBoxLayout()
        wid = QLabel('stopped')
        wid.setFixedWidth(80)
        acqu_content.addWidget(wid)
        moni['ac_running'] = wid

        wid = QLabel('Disk space left: ')
        wid.setFixedWidth(190)
        acqu_content.addWidget(wid)
        moni['ac_disk_space'] = wid

        wid = QLabel('Full in: ?')
        wid.setFixedWidth(180)
        acqu_content.addWidget(wid)
        moni['ac_time_left'] = wid

        wid = QLabel('Files:')
        acqu_content.addWidget(wid)

        wid = QLabel('0')
        wid.setFixedWidth(50)
        acqu_content.addWidget(wid)
        moni['ac_files_count'] = wid

        acqu_group.addLayout(acqu_title)
        acqu_group.addLayout(acqu_content)

        # processing
        proc_group = QVBoxLayout()
        proc_title = QHBoxLayout()
        label = QLabel('Processing')
        label.setStyleSheet('QLabel {font-weight: bold;}')
        proc_title.addWidget(label)

        proc_content = QHBoxLayout()
        moni['proc_running'] = QLabel('stopped')
        proc_content.addWidget(moni['proc_running'])

        proc_group.addLayout(proc_title)
        proc_group.addLayout(proc_content)

        # redis
        redis_group = QVBoxLayout()
        redis_title = QHBoxLayout()
        label = QLabel('Redis')
        label.setFixedWidth(100)
        label.setStyleSheet('QLabel {font-weight: bold;}')
        redis_title.addWidget(label)

        redis_content = QHBoxLayout()
        moni['redis_running'] = QLabel('stopped')
        redis_content.addWidget(moni['redis_running'])

        redis_group.addLayout(redis_title)
        redis_group.addLayout(redis_content)

        return acqu_group, proc_group, redis_group


    def setup_log_and_events(self):
        bottom_layout = QVBoxLayout()
        # bottom_layout.setAlignment(Qt.AlignLeft)

        labels_box = QHBoxLayout()
        labels_box.setAlignment(Qt.AlignLeft)
        label = QLabel('Log')
        label.setMinimumSize(QtCore.QSize(600, 20))
        labels_box.addWidget(label)
        label = QLabel('Events')
        self.event_list_label = label
        labels_box.addWidget(label)

        btn1 = gui_util.make_button('Previous', small=True)
        btn2 = gui_util.make_button('Next', small=True)
        btn1.clicked.connect(self.plot_prev_event)
        btn2.clicked.connect(self.plot_next_event)

        labels_box.addWidget(btn1)
        labels_box.addWidget(btn2)
        labels_box.addStretch(1)

        btn_zoom_reset = gui_util.make_button('Reset zoom', small=True)
        btn_zoom_reset.clicked.connect(self.zoom_reset)
        labels_box.addWidget(btn_zoom_reset)
        labels_box.addStretch(1)
        bottom_layout.addLayout(labels_box)

        textedits_box = QHBoxLayout()
        textedits_box.setAlignment(Qt.AlignLeft)
        textedits_box.addWidget(self.setup_log_widget())
        textedits_box.addWidget(self.setup_events_widget())
        bottom_layout.addLayout(textedits_box)
        return bottom_layout


    def setup_log_widget(self):
        log_widget = gui_util.PlainTextEdit()
        log_widget.setFixedSize(QtCore.QSize(450, 100))
        self.log_widget = log_widget
        return log_widget


    def setup_events_widget(self):
        events_widget = gui_util.PlainTextEdit(self.event_clicked)
        events_widget.setFixedHeight(100)
        sizePolicy = QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        events_widget.setSizePolicy(sizePolicy)
        self.events_widget = events_widget
        return events_widget


    def setup_canvas(self):
        canvas = FigureCanvas(Figure())
        sizePolicy = QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(99)
        sizePolicy.setVerticalStretch(99)
        sizePolicy.setHeightForWidth(canvas.sizePolicy().hasHeightForWidth())
        canvas.setSizePolicy(sizePolicy)

        fig = canvas.figure
        self.fig = fig
        self.axs = None
        toolbar = NavigationToolbar(canvas, None)
        toolbar.pan()

        self.communication['fig'] = fig

        self.canvas = canvas
        self.canvas.wheelEvent = self.wheel_event
        # self.canvas.mpl_connect('button_press_event', self.zoom_reset)
        return canvas


    @staticmethod
    def set_standard_layout(widget, layout_instance, margin_zero=True):
        layout_instance.setSpacing(2)
        layout_instance.setAlignment(Qt.AlignTop)
        if margin_zero:
            layout_instance.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout_instance)


    # Sections

    def generate_sections_widget(self):
        wid = QWidget()
        layout = QStackedLayout()
        wid.setLayout(layout)
        wid.setFixedWidth(WIDTH_SECTIONS)

        self.sections = {}

        layout.addWidget(self.generate_scroll_widget('General'))
        layout.addWidget(self.channels_widgets_create())
        layout.addWidget(self.generate_scroll_widget('Acquisition'))
        layout.addWidget(self.generate_scroll_widget('Processing'))
        layout.addWidget(self.generate_scroll_widget('Trigger'))
        layout.addWidget(self.generate_scroll_widget('Picking'))
        layout.addWidget(self.generate_scroll_widget('Loc_Mag'))
        layout.addWidget(self.help_widget())
        self.sections_layout = layout

        self.general_controls()
        self.acquisition_controls()
        self.processing_controls()
        return wid


    def generate_scroll_widget(self, section_name):
        scroll = QScrollArea()
        scroll.setWidget(self.section_widget(section_name))
        self.scroll_set_size(scroll)
        return scroll


    def scroll_set_size(self, scroll):
        scroll.setWidgetResizable(True)
        policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        scroll.setSizePolicy(policy)
        scroll.setFixedWidth(WIDTH_SECTIONS)


    def section_widget(self, section_name):
        '''
        Beim ersten Mal
            – muss keine Caption geschrieben werden
            – muss keine QGroupBox angelegt werden
        '''
        widget = QWidget()
        self.sections[section_name] = widget

        layout = QVBoxLayout()
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        widget.setSizePolicy(policy)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop)
        widget.setProperty('cssClass', 'indigo')
        widget.setLayout(layout)

        self.widgets_recursive(
            parent_widget=widget,
            breadcrumb=[section_name],
            is_toplevel=True,
        )
        return widget


    def channels_widgets_create(self):
        scroll = QScrollArea()
        widget = QWidget()
        self.set_standard_layout(widget, QGridLayout(), margin_zero=False)
        self.channels_widgets_content(widget.layout())
        self.scroll_set_size(scroll)
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        self.channels_scroll_area = scroll
        return scroll


    def channels_widgets_udpate(self):
        # delete entries in self.elems
        channel_elem_keys = [key for key in self.elems.keys() if key[0] == 'Channels']
        for key in channel_elem_keys:
            del self.elems[key]

        # delete all child elements
        wid = self.channels_scroll_area.widget()
        for i in reversed(range(wid.layout().count())):
            wid.layout().takeAt(i).widget().setParent(None)
        self.channels_widgets_content(wid.layout())


    def channels_widgets_content(self, layout):
        '''
        Generate the whole content of the "Channels" tab
        '''
        channel_elem_keys = [key for key in self.elems.keys() if key[0] == 'Channels']
        for key in channel_elem_keys:
            del self.elems[key]

        # column head
        layout.addWidget(QLabel('x'), 0, 1)
        layout.addWidget(QLabel('y'), 0, 2)
        layout.addWidget(QLabel('y'), 0, 3)

        label = QLabel('In. range')
        label.setToolTip('Input range [mV]')
        layout.addWidget(label, 0, 4)

        label = QLabel('PA gain')
        label.setToolTip('Preamplifier gain [dB]')
        layout.addWidget(label, 0, 5)

        label = QLabel('Int. gain')
        label.setToolTip('Internal gain [dB]')
        layout.addWidget(label, 0, 6)

        label = QLabel('Trig.')
        label.setToolTip(
            'Used for triggering:<br>' +
            'The channels that the trigger is applied<br>' +
            'up on. The active trigger channel should<br>' +
            'normally be included since this channel<br>' +
            'will be used by the software to determine<br>' +
            'if an event is active or passive.')
        layout.addWidget(label, 0, 7)

        label = QLabel('thr_on')
        label.setToolTip('threshold on [counts]')
        layout.addWidget(label, 0, 8)
        label = QLabel('thr_off')
        label.setToolTip('threshold off [counts]')
        layout.addWidget(label, 0, 9)

        label = QLabel('ST')
        label.setToolTip(
            'ST window [samples]')
        layout.addWidget(label, 0, 10)

        label = QLabel('LT')
        label.setToolTip(
            'LT window [samples]')
        layout.addWidget(label, 0, 11)

        type_checkbox = ['tr_channels']
        for idx in range(0, self.param['General']['sensor_count']):
            label = QLabel(str(idx + 1))
            layout.addWidget(label, idx + 1, 0)

            for col, name in enumerate([
                'x_coord',
                'y_coord',
                'z_coord',
                'input_range',
                'preamp_gain',
                'internal_gain',
                'tr_channels',
                'tr_threshold_on',
                'tr_threshold_off',
                'tr_st_window',
                'tr_lt_window',
            ]):
                value = self.param['Channels'][name][idx]
                if name in type_checkbox:
                    edit = QCheckBox()
                    edit.setChecked(value)
                else:
                    edit = QLineEdit()
                    edit.setText(str(value))

                layout.addWidget(edit, idx + 1, col + 1)
                self.elems[('Channels', idx, name)] = edit


    def help_widget(self):
        scroll = QScrollArea()

        widget = QWidget()
        self.set_standard_layout(widget, QGridLayout(), margin_zero=False)
        lay = widget.layout()

        for item in help_content:
            label = QLabel(item[1])
            if item[0] == 'heading1':
                label.setObjectName('heading1')
            elif item[0] == 'heading2':
                label.setObjectName('heading2')
            elif item[0] == 'heading3':
                label.setObjectName('heading3')
            elif item[0] == 'text':
                label.setStyleSheet('QLabel {margin-bottom: 5px;}')
            label.setWordWrap(True)
            lay.addWidget(label)

        self.scroll_set_size(scroll)
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll


    # Misc

    def widgets_recursive(self, parent_widget, breadcrumb, is_toplevel=False):
        param_gui_elem = self.gui_param_from_breadcrumb(breadcrumb)
        sub_params_keys = [p for p in param_gui_elem.keys() \
            if p != 'has_children' and p != 'is_group' and p != 'caption']

        if 'hidden' in param_gui_elem and param_gui_elem['hidden']:
            # do nothing
            return

        if not 'has_children' in param_gui_elem:
            self.set_widget_row(
                param_name=breadcrumb[-1],
                elem=param_gui_elem,
                parent_widget=parent_widget,
                breadcrumb=breadcrumb
            )
            return

        if is_toplevel:
            widget = parent_widget
        else:
            if 'is_group' in param_gui_elem:
                widget = QGroupBox(param_gui_elem['caption'])
                self.set_standard_layout(widget, QVBoxLayout(), margin_zero=False)
                self.group_boxes[tuple(breadcrumb)] = widget
            else:
                widget = QWidget()
                self.set_standard_layout(widget, QVBoxLayout())

                label = QLabel(param_gui_elem['caption'])
                label.setFixedHeight(35)
                label.setObjectName('heading')

                widget.layout().addWidget(label)

        for _, sub_param_name in enumerate(sub_params_keys):
            self.widgets_recursive(
                parent_widget=widget,
                breadcrumb=breadcrumb + [sub_param_name],
            )
        if not is_toplevel:
            parent_widget.layout().addWidget(widget)
        return


    def set_widget_row(self, param_name, elem, parent_widget, breadcrumb):
        '''
        Create label and input field widgets for one parameter
        '''

        if 'function' in elem:
            getattr(self, elem['function'])(parent_widget.layout())
            return

        hbox = QHBoxLayout()
        label = QLabel(elem['caption'])
        label.setMinimumSize(QSize(180, 20))
        label.setSizePolicy(QSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed))
        if 'is_bold' in elem:
            label.setObjectName('heading')

        if 'description' in elem:
            label.setToolTip(elem['description'])
        if 'is_heading' in elem:
            label.setStyleSheet('QLabel {font-weight: bold;}')
            label.setFixedHeight(35)
            hbox.addWidget(label)
            hbox.setAlignment(Qt.AlignLeft)
            parent_widget.layout().addLayout(hbox)
            return

        if 'breadcrumb' in elem:
            breadcrumb = elem['breadcrumb']
        value = self.param_get_value(breadcrumb)

        hbox.addWidget(label)

        # Choose widget type
        if 'widget_type' in elem:
            if elem['widget_type'] == 'QTextEdit':
                edit = QTextEdit()
                edit.setText(str(value))
                edit.setFixedHeight(46)
                edit.updateGeometry()

            elif elem['widget_type'] == 'QCheckBox':
                edit = QCheckBox()
                edit.setChecked(value)
            elif elem['widget_type'] == 'QComboBox':
                edit = QComboBox()
                edit.addItems(elem['items'])
                combo_idx = edit.findText(str(value), Qt.MatchFixedString)
                if combo_idx < 0:
                    combo_idx = 0
                edit.setCurrentIndex(combo_idx)
                if 'is_switching' in elem:
                    self.switchers[tuple(breadcrumb)] = elem['items']
        else:
            edit = QLineEdit()
            edit.setText(str(value))

        self.elems[tuple(breadcrumb)] = edit
        hbox.addWidget(edit)

        parent_widget.layout().addLayout(hbox)


    def general_controls(self):
        layout = self.sections['General'].layout()
        spacer = QLabel('')
        layout.addWidget(spacer)

        btn_validate = QPushButton('Validate')
        btn_validate.setFixedSize(200, 40)
        btn_validate.clicked.connect(self.validate_test)
        layout.addWidget(btn_validate)
        layout.addStretch(1)
        self.btn_validate = btn_validate


    def acquisition_controls(self):
        self.ac_ctrls = {}

        layout = self.sections['Acquisition'].layout()
        spacer = QLabel('')

        btn_start = gui_util.make_button('Start acquisition')
        btn_stop = gui_util.make_button('Stop acquisition')
        btn_start.clicked.connect(self.start_acquisition)
        btn_stop.clicked.connect(self.stop_acquisition)

        self.ac_ctrls = {
            'btn_start': btn_start,
            'btn_stop': btn_stop,
        }
        self.ac_ctrls['btn_stop'].hide()

        layout.addWidget(spacer)
        layout.addWidget(btn_start)
        layout.addWidget(btn_stop)
        layout.addStretch(1)


    def processing_controls(self):
        self.proc_ctrls = {}

        layout = self.sections['Processing'].layout()
        spacer = QLabel('')

        btn_single = gui_util.make_button('Plot snippet')
        btn_single.clicked.connect(self.plot_snippet)
        layout.addWidget(btn_single)

        btn1 = gui_util.make_button('Start processing')
        btn2 = gui_util.make_button('Stop processing')
        btn1.clicked.connect(self.start_processing)
        btn2.clicked.connect(self.stop_processing)

        layout.addWidget(spacer)
        layout.addWidget(btn1)
        layout.addWidget(btn2)

        self.proc_ctrls = {
            'btn_start': btn1,
            'btn_stop': btn2,
        }
        self.proc_ctrls['btn_stop'].hide()

        # TODO  development code
        btn_find_events = QPushButton('Find Events')
        btn_find_events.setFixedSize(200, 40)
        btn_find_events.clicked.connect(self.seis_events_search)
        layout.addWidget(btn_find_events)
        self.btn_find_events = btn_find_events

        self.elems[('Processing', 'periodic_plotting')].stateChanged.connect(
            self.periodic_plotting_changed)


    def create_channels_selector(self, parent_layout):
        self.channels_selector = gui_util.ChannelsSelector(
            int(self.elem_get_value(('General', 'sensor_count'))))
        parent_layout.addWidget(self.channels_selector.widget)

        hbox = QHBoxLayout()
        label = QLabel('All channels with picks')
        label.setFixedSize(QSize(180, 20))
        hbox.addWidget(label)
        cb = QCheckBox()
        hbox.addWidget(cb)
        cb.toggled.connect(self.pick_channels_toggled)
        self.pick_channels = cb
        parent_layout.addLayout(hbox)


    # def init_shortcuts(self):
    #     self.shortcuts = {}

    #     def activator(i):
    #         def func():
    #             self.activate_section(i)
    #         return func

    #     for item in [
    #         [0, 'G'],
    #         [2, 'A'],
    #         [4, 'T'],
    #         [6, 'L'],
    #         [1, 'C'],
    #         [3, 'P'],
    #         [5, 'K'],
    #         [7, 'H'],
    #     ]:
    #         self.shortcuts[item[1]] = QShortcut(QKeySequence('Ctrl+' + item[1]), self)
    #         self.shortcuts[item[1]].activated.connect(activator(item[0]))

    #     # toggle fullscreen mode
    #     self.is_fullscreen = False
    #     def toggle_fullscreen():
    #         if self.is_fullscreen:
    #             self.showMaximized()
    #         else:
    #             self.showFullScreen()
    #         self.is_fullscreen = not self.is_fullscreen

    #     self.shortcuts['F11'] = QShortcut(QKeySequence('F11'), self)
    #     self.shortcuts['F11'].activated.connect(toggle_fullscreen)


    ###########################################################################
    ##  Event Handlers, Business Logic                                       ##
    ###########################################################################

    def start_acquisition(self):
        self.gui_to_param()
        error_suffix = '<br><br><b style="color:red;">Acquisition not started</b>!'

        errors = gui_util.validate_yaml_param(self.param, check_dirs=False)
        if len(errors):
            self.alert(errors + error_suffix)
            return

        errors = gui_util.setup_acquitision_dirs(self.param)
        if len(errors):
            self.alert(errors + error_suffix)
            return

        self.ac_param = gui_util.param_yaml_to_processing(self.param)
        ac_yaml = os.path.join(
            self.elem_get_value(('General', 'acquisition_folder')),
            'dug-seis-ac.yaml',
        )
        self.dump_yaml(ac_yaml)

        self.ac_finishing = False

        errors = util.redis_server_start(
            self.ac_param['General']['acquisition_folder'])
        if len(errors):
            self.alert(errors + error_suffix)
            return

        util.redis_set_ac_continue('yes')
        #self.monitor_update_redis()

        subprocess.Popen([
            'python',
            dugseis_acquisition.__file__,
            ac_yaml,
        ])
        self.ac_ctrls['btn_start'].hide()
        self.ac_ctrls['btn_stop'].show()
        # monitor
        self.tasks['moni_ac']['active'] = True
        self.monitor['ac_running'].setText('started')
        self.periodic_tasks_check()


    def stop_acquisition(self):
        if util.redis_set_ac_continue('no'):
            self.ac_finishing = True
            self.tasks['moni_ac']['active'] = False
            self.ac_ctrls['btn_start'].show()
            self.ac_ctrls['btn_stop'].hide()
            self.monitor['ac_running'].setText('stopped')
            self.periodic_tasks_check()
        else:
            self.alert('<b style="color:red;">No connction to redis!</b>')


    def start_processing(self):
        self.gui_to_param()
        errors = gui_util.validate_yaml_param(self.param, check_dirs=True)
        self.proc_param = gui_util.param_yaml_to_processing(self.param)

        if len(errors):
            self.alert(errors
                + '<br><br><b style="color:red;">Processing not started<b>!')
            return

        gui_util.setup_logging(self.proc_param['General']['processing_folder'])
        self.dump_yaml(os.path.join(
            self.elem_get_value(('General', 'processing_folder')),
            'dug-seis.yaml'
        ))

        self.proc_continue = True
        # This starts a thread, which
        # – starts a new python process
        # – manages communication between GUI and dugseis_processing
        self.proc_worker = gui_util.ProcessingStarter(
            self.proc_param,
            self.communication,
            self,
        )
        self.proc_worker.signals.logging.connect(self.handle_feedback)
        self.threadpool.start(self.proc_worker)

        time.sleep(0.2)
        self.start_event_watcher()
        self.periodic_plotting_changed()

        self.proc_ctrls['btn_start'].hide()
        self.proc_ctrls['btn_stop'].show()

        self.monitor['proc_running'].setText('running')


    def stop_processing(self):
        self.proc_continue = False
        self.monitor['proc_running'].setText('finishing')
        self.proc_ctrls['btn_stop'].setText('Processing finishing')
        self.proc_ctrls['btn_stop'].setEnabled(False)


    def stop_processing_finished(self):
        self.proc_ctrls['btn_stop'].hide()
        self.proc_ctrls['btn_stop'].setText('Stop processing')
        self.proc_ctrls['btn_stop'].setEnabled(True)
        self.proc_ctrls['btn_start'].show()
        self.monitor['proc_running'].setText('stopped')


    def handle_feedback(self, feedback):
        if 'stop_processing' in feedback:
            self.stop_processing_finished()
        if 'logger' in feedback:
            self.log_widget.appendPlainText(feedback['logger'])
        if 'error' in feedback:
            print(feedback['error'])
            self.alert(f'Error in processing:<br>' +
                gui_util.format_traceback(feedback['error']))


    def get_json_dir(self):
        return os.path.join(
            self.elem_get_value(('General', 'processing_folder')), 'json'
        )


    # Periodic

    def start_event_watcher(self):
        self.fs_watcher = QtCore.QFileSystemWatcher([self.get_json_dir()])
        self.fs_watcher.directoryChanged.connect(self.seis_events_search)


    @Slot()
    def seis_events_search(self):
        try:
            files = sorted(os.listdir(self.get_json_dir()))
        except Exception as e:
            self.alert('<b>Searching events:</b><br><br>'
                + e.args[1] + '\n' + e.filename)
            return

        new_files = [f for f in files
            if f not in [evt['file_name'] for _, evt in self.seis_events.items()]]
        time.sleep(0.1)
        for file in new_files:
            self.seis_event_add(file)


    def seis_event_add(self, file_name):
        try:
            with open(os.path.join(
                    self.elem_get_value(('General', 'processing_folder')),
                    'json',
                    file_name), 'r') as read_file:
                data = json.load(read_file)
                data['file_name'] = file_name

            pick_stations = [int(p['wfid_stcode']) for p in data['picks']]
            key = util.utc_format(UTCDateTime(data['start_time']), 'key')
            text = key
            text += '  ' + gui_util.chunks_string(
                pick_stations,
                data['sensor_count'],
                'P',
                '-',
                8
            )
            self.seis_events[key] = data
            self.event_list_label.setText('Events: '
                + str(len(self.seis_events.keys())))
            self.events_widget.appendPlainText(text)

        except Exception as e:
            err = (f'Error while reading JSON file "{file_name}": ' + str(e))
            print(err)
            return


    def event_clicked(self, event_string):
        r = re.search('^([^ ]+ +[^ ]+)', event_string)

        calc=self.elem_get_value(('Processing', 'single_plot_reprocess'))
        title='Event ' + str(self.seis_events[r.group(1)]['event_id'])
        if calc:
            title += ', reprocessed'

        self.plot_event(
            self.seis_events[r.group(1)],
            title=title,
            calc=calc,
            waiting_msg=r.group(1),
        )
        self.current_event_key = r.group(1)


    def periodic_plotting_changed(self):
        val = self.elem_get_value(('Processing', 'periodic_plotting'))
        self.tasks['plot']['active'] = val
        if val and hasattr(self, 'proc_continue') and self.proc_continue:
            self.tasks['plot']['start_time'] = datetime.now()
            self.periodic_tasks_check()


    def periodic_tasks_setup(self):
        self.tasks = {}
        self.monitor_setup()
        self.periodic_plot_setup()
        self.task_timer = QTimer()
        self.task_timer.setInterval(200)
        self.task_timer.timeout.connect(self.periodic_tasks_exec)


    def periodic_tasks_check(self):
        '''
        Check if the timer is to be started

        Is run AFTER changes of task parameters.
        '''
        any_active = reduce(lambda a, b: a or b, [t['active']
            for _, t in self.tasks.items()])
        if any_active and not self.task_timer.isActive():
            self.task_timer.start()


    def periodic_tasks_exec(self):
        any_active = False
        for _, t in self.tasks.items():
            any_active = any_active or t['active']
            if not t['active']:
                continue
            if ((datetime.now() - t['start_time']).seconds < t['interval']):
                continue

            # set new start_time and execute
            t['start_time'] = t['start_time'] + timedelta(seconds=t['interval'])
            t['callback']()

        if not any_active:
            self.task_timer.stop()


    def monitor_setup(self):
        self.tasks['moni_ac'] = {
            'active': False,
            #'callback': self.monitor_update_acqu,
            'start_time': datetime.now(),
            'interval': 1,
        }


    def periodic_plot_setup(self):
        plot_task = {
            'active': False,
            'callback': self.periodic_plot,
            'start_time': datetime.now(),
            'interval': 10,
            'noise_period': 0,
            'noise_counter': 0,
            'last_key' : '',
        }
        if self.elem_get_value(('Processing', 'noise_vis')):
            plot_task['noise_period'] = int(self.elem_get_value(
                ('Processing', 'noise_vis_interval')))
        self.tasks['plot'] = plot_task


    def periodic_plot(self):
        plot_task = self.tasks['plot']

        plot_task['noise_counter'] += 1
        if (plot_task['noise_period'] != 0
                and plot_task['noise_counter'] >= plot_task['noise_period']):
            plot_task['start_time'] = datetime.now()
            plot_task['start_time_noise'] = datetime.now()
            plot_task['noise_counter'] = 0

            # TODO  devel code to find a time for the snapshot
            keys = sorted(self.seis_events.keys())
            if len(keys) == 0:
                return
            key = keys[-1]
            self.plot_snippet(
                start_time_utc=util.timestr_to_UTCDateTime(key) - 0.1,
                title='Snapshot',
                waiting_msg='',
                waiting=False,
            )

            # TODO  This is the production code version.
            # self.plot_snippet(start_time_utc=UTCDateTime.now(),
            #     waiting_msg=False)
            # TODO  end devel code

            return

        # plot event
        plot_task['start_time'] = datetime.now()
        keys = sorted(self.seis_events.keys())
        if len(keys) == 0:
            return
        key = keys[-1]
        if key == plot_task['last_key']:
            return
        plot_task['last_key'] = key

        self.plot_event(
            self.seis_events[key],
            title='Event ' + str(self.seis_events[key]['event_id']),
            waiting_msg='',
        )
        self.current_event_key = key


    def monitor_update_redis(self):
        if util.redis_server_check():
            self.monitor['redis_running'].setText('running')
            self.monitor['redis_running'].setStyleSheet(
                'QLabel {color: #56a050; font-weight: bold;}')
        else:
            self.monitor['redis_running'].setText('stopped')
            self.monitor['redis_running'].setStyleSheet(
                'QLabel {color: #000000; font-weight: normal;}')


    def monitor_update_acqu(self):
        # disk space
        data_folder = os.path.join(
            self.elem_get_value(('General', 'acquisition_folder')), 'asdf')
        try:
            _, _, space_left = shutil.disk_usage(data_folder)
        except FileNotFoundError:
            try:
                # This can be used before the asdf directory is created.
                data_folder = self.elem_get_value(('General', 'acquisition_folder'))
                _, _, space_left = shutil.disk_usage(data_folder)
            except FileNotFoundError:
                return

        gib = (space_left // 1000000) / 1000
        gib = str(gib).rjust(8, ' ')
        self.monitor['ac_disk_space'].setText(f'Disk space left: {gib} GiB')

        # time left until disk full
        files = sorted(os.listdir(data_folder))
        size = 0
        if len(files) == 0:
            return

        self.monitor['ac_files_count'].setText(str(len(files)))

        for f in files[-FILE_COUNT_FOR_TIME_ESTIMATION:]:
            size += os.path.getsize(os.path.join(data_folder, f))
        size_per_file = size / len(files[-FILE_COUNT_FOR_TIME_ESTIMATION:])

        seconds_left = space_left / size_per_file * float(self.elem_get_value(
            ('Acquisition', 'asdf_settings', 'file_length_sec')))
        time_left = timedelta(seconds=seconds_left)
        self.monitor['ac_time_left'].setText(
            f'Full in: ' + re.sub(r'\..*', '', str(time_left)))

        if seconds_left < 3600:
            self.monitor['ac_disk_space'].setStyleSheet('QLabel {color: red;}')
            self.monitor['ac_time_left'].setStyleSheet('QLabel {color: red;}')


    # Plot

    def title_of_event(self, name):
        calc = self.elem_get_value(('Processing', 'single_plot_reprocess'))
        title = name
        if calc:
            title += ', reprocessed'
        return calc, title


    def plot_snippet(self, start_time_utc=None, title='',
                     waiting_msg='', waiting=True):
        '''
        Display waveforms at selected time

        In most cases this is not an event.
        '''

        if not start_time_utc:
            # TODO  Validation, try
            start_time_utc = util.timestr_to_UTCDateTime(
                self.elem_get_value(('Processing', 'single_plot_time'))
            )

        calc = self.elem_get_value(('Processing', 'single_plot_reprocess'))
        start_time = str(start_time_utc)
        # TODO  delete?
        trigger_time = str(start_time_utc + 0.005)

        seis_evt = {
            'event_id': 0,
            'file_name': None,
            'start_time': start_time,
            'trigger_time': trigger_time,
        }
        if not waiting_msg and waiting:
            waiting_msg = start_time
        if not title:
            # Notice: It is correct that title_of_event is NOT used here
            #         because "processed" is intended, not "reprocessed".
            title = 'selected time'
            if calc:
                title += ', processed'
        self.plot_event(seis_evt,
            title=title,
            calc=calc,
            waiting_msg=waiting_msg if waiting else '',
        )


    def plot_prev_event(self):
        keys = list(self.seis_events.keys())
        idx = keys.index(self.current_event_key)
        if idx == 0:
            return
        prev_key = keys[idx - 1]
        self.events_widget.select_block_by_idx(idx - 1, -1)
        self.current_event_key = prev_key
        id = str(self.seis_events[prev_key]['event_id'])
        calc, title = self.title_of_event(f'Event {id}')
        self.plot_event(
            self.seis_events[prev_key],
            title=title,
            calc=calc,
            waiting_msg=prev_key,
        )


    def plot_next_event(self):
        keys = list(self.seis_events.keys())
        idx = keys.index(self.current_event_key)
        if idx >= len(keys) - 1:
            return
        next_key = keys[idx + 1]
        self.events_widget.select_block_by_idx(idx + 1, 1)
        self.current_event_key = next_key
        id = str(self.seis_events[next_key]['event_id'])
        calc, title = self.title_of_event(f'Event {id}')
        self.plot_event(
            self.seis_events[next_key],
            title=title,
            calc=calc,
            waiting_msg=next_key,
        )


    def plot_event(self, seis_evt, title='', calc=False, waiting_msg=''):
        '''Display a single event'''

        # display message that calculating the plot has started
        if waiting_msg:
            self.fig.suptitle(
                'Waiting for plot ' + waiting_msg,
                fontsize=15,
                color='#009022',
                backgroundcolor='#ffffff',
                zorder=1000,
            )
            self.canvas.draw()
            self.canvas.repaint()

        self.gui_to_param()
        errors = gui_util.validate_yaml_param(self.param, check_dirs=True)
        self.proc_param = gui_util.param_yaml_to_processing(self.param)

        if len(errors):
            self.alert(errors)
            return

        signals = gui_util.WorkerSignals()
        signals.single_event.connect(self.handle_feedback)

        if seis_evt['file_name'] is not None:
            file_path = os.path.join(self.get_json_dir(), seis_evt['file_name'])
        else:
            file_path = None

        spectro_show = self.elem_get_value(
            ('Processing', 'spectro', 'spectro_show'))
        spectro_logx = self.elem_get_value(
            ('Processing', 'spectro', 'spectro_logx'))
        spectro_start_pick = self.elem_get_value(
            ('Processing', 'spectro', 'spectro_start_pick'))

        communication = {
            'callback_signal': signals.single_event,
            'app': self,
            'fig': self.fig,
            'axs': self.axs,
            'proc_continue': True,
            'single_event': {
                'id': int(seis_evt['event_id']),
                'display_channels' : self.channels_selector.selected(),
                'display_pick_channels': self.pick_channels.isChecked(),
                'trigger_time': UTCDateTime(seis_evt['trigger_time']),
                'start_time': UTCDateTime(seis_evt['start_time']),
                'file_path': file_path,
                'calc': calc,
                'spectro_show': spectro_show,
                'spectro_logx': spectro_logx,
                'spectro_start_pick': spectro_start_pick,
                'title':util.utc_format(
                    UTCDateTime(seis_evt['start_time']), 'human_time') + ', ' + title,
            }
        }

        try:
            dugseis_processing(self.proc_param, communication)
            self.canvas.draw()
        except Exception as _:
            logging.exception('message')
            return


    def wheel_event(self, ev):
        if self.axs is None:
            return

        # create mpl event from QEvent to get cursor position in data coords
        x = ev.x()
        y = self.canvas.height() - ev.y()
        mpl_ev = MplMouseEvent('scroll_event', self.canvas, x, y, 'up', guiEvent=ev)

        if ev.modifiers() == QtCore.Qt.NoModifier:
            ax = self.axs[list(self.axs.keys())[0]]
            (left, right) = ax.get_xbound()
            # x zoom
            # in
            if ev.angleDelta().y() < 0:
                left -= (mpl_ev.xdata - left) / 2
                right += (right - mpl_ev.xdata) / 2
            # out
            elif ev.angleDelta().y() > 0:
                left += (mpl_ev.xdata - left) / 2
                right -= (right - mpl_ev.xdata) / 2
            ax.set_xbound(lower=left, upper=right)

        elif ev.modifiers() == getattr(QtCore.Qt,'ShiftModifier'):
            for _, ax in self.axs.items():
                (bottom, top) = ax.get_ybound()
                # y zoom
                # in
                if ev.angleDelta().y() < 0:
                    top *= 2
                    bottom *= 2
                # out
                elif ev.angleDelta().y() > 0:
                    top /= 2
                    bottom /= 2
                ax.set_ybound(lower=bottom, upper=top)

        self.canvas.draw()


    def zoom_reset(self, evt):
        for key, lim in self.axs_lims.items():
            self.axs[key].set_xbound(lower=lim['x'][0], upper=lim['x'][1])
            self.axs[key].set_ybound(lower=lim['y'][0], upper=lim['y'][1])
        self.canvas.draw()
        self.canvas.repaint()


    # Misc

    def pick_channels_toggled(self):
        val = self.pick_channels.isChecked()
        self.channels_selector.set_enabled(not val)


    def alert(self, text):
        msg = QMessageBox()
        msg.setAttribute(Qt.WA_DeleteOnClose)
        msg.setText(text)
        msg.exec()


    def validate_test(self):
        self.gui_to_param()
        errors = gui_util.validate_yaml_param(self.param, check_dirs=True)
        if len(errors):
            self.alert('<b style="color:red;">Errors found:</b><br><br>'
                + errors)
        else:
            self.alert('No errors found')


    def quit_app(self):
        pass
        #qApp.quit()


    ###########################################################################
    ##  Manage Configurations                                                ##
    ###########################################################################

    def load_config_default(self):
        # NOTICE  This YAML file is part of the software,
        #         so no validation is necessary.
        default_path = os.path.realpath(os.path.join(
            self.dir, '../../config/dug-seis.yaml'))
        with open(default_path) as file_handle:
            param = yaml.load(file_handle, Loader=yaml.FullLoader)
        self.param = gui_util.param_yaml_to_gui(param)


    def load_config_home(self):
        '''
        Load configuration from YAML file
        '''
        user_home_path = QStandardPaths.writableLocation(
            QStandardPaths.HomeLocation)
        user_yaml_path = os.path.join(user_home_path, 'dug-seis.yaml')
        if os.path.isfile(user_yaml_path):
            self.load_config_file(user_yaml_path)
        # Not necessary – or is it?
        # else:
        #     self.alert('Could not find dug-seis.yaml in home directory.')


    def load_config_file(self, path):
        with open(path) as file_handle:
            try:
                param = yaml.load(file_handle, Loader=yaml.FullLoader)
            except IOError:
                self.alert(f'Could not read parameter file at {path}.')
                return

            errors = gui_util.validate_yaml_param(param)
            if len(errors):
                self.alert(f'<b>Errors in parameter file</b><br>'
                    + '<code>{path}</code>' + ':<br><br>' + errors
                    + '<br><br><b style="color:red;">File not loaded<b>!')
                return

            try:
                # TODO  Das gehört nicht alles in das try!
                self.param = gui_util.param_yaml_to_gui(param)
                new_param_dict = gui_util.param_flatten_hierarchy(self.param)
                self.channels_widgets_udpate()
                self.update_gui_values(new_param_dict)
                self.channels_selector.show_channels(
                    self.param['General']['sensor_count'])
                #self.monitor_update_acqu()
            except Exception as _:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_msg = ''.join(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                print(err_msg)
                self.alert(f'<b>Error in param_yaml_to_gui:</b><br><br>' +
                    gui_util.format_traceback(err_msg))


    def diag_load_config(self):
        path = QFileDialog.getOpenFileName(
            self,
            'Open YAML file',
            QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
            'YAML Files (*.yaml)')

        if os.path.isfile(str(path[0])):
            self.load_config_file(path[0])


    def update_gui_values(self, new_param_dict):
        for key, val in new_param_dict.items():
            if key in param_hidden:
                continue
            if key[0] == 'Channels':
                for i in range(0, self.param['General']['sensor_count']):
                    self.elem_set_val(('Channels', i, key[1]), val[i])

            if key not in self.elems.keys():
                continue

            if type(val) is not list:
                self.param_set_value(key, val)
                self.elem_set_val(key, val)


    def diag_dump_yaml(self):
        path = QFileDialog.getSaveFileName(
            self,
            'Save File',
            self.elem_get_value(
                ('General', 'processing_folder')) + '/dug-seis.yaml',
            'YAML Files (*.yaml)')
        if path[0]:
            self.dump_yaml(path[0])


    def gui_to_param(self):
        '''
        Read all fields in GUI and write them to self.param
        '''
        def set_channel_param(name):
            length = self.param['General']['sensor_count']
            li = [self.elem_get_value(('Channels', i, name))
                for i in range(0, length)]

            # TODO  maybe this info can be moved to gui_cfg
            if name != 'tr_channels':
                li = [float(i) for i in range(0, length)]
            return li

        channel_param = {}
        for key in self.param['Channels'].keys():
            if key in [ph[1] for ph in param_hidden if ph[0] == 'Channels']:
                continue
            channel_param[key] = set_channel_param(key)

        for key in self.elems.keys():
            if key in param_hidden:
                continue

            val = self.elem_get_value(key)

            if key[0] == 'Channels':
                continue

            # Convert value to correct type
            gp = self.gui_param_from_breadcrumb(key)
            if 'type' in gp and gp['type'] == 'int_or_None':
                old_val = 1
            else:
                old_val = self.param_get_value(key)
            if isinstance(old_val, bool):
                pass
            elif isinstance(old_val, int):
                if val == '':
                    val = None
                else:
                    val = int(val)
            elif isinstance(old_val, float):
                val = float(val)
            self.param_set_value(key, val)


    def dump_yaml(self, path):
        self.gui_to_param()

        self.param['General']['operator'] = (
            self.param['General']['operator']).split('\n')

        # prettify YAML content

        # print values that are lists in one line
        delim = 'QXJXQ'
        param_tmp = copy.deepcopy(self.param)

        def list_to_string(li):
            return f'{delim}{repr(li)}{delim}'

        for key in param_tmp['Channels'].keys():
            param_tmp['Channels'][key] = list_to_string(param_tmp['Channels'][key])

        param_tmp['General']['operator'] = list_to_string(
            param_tmp['General']['operator'])

        yaml_text = yaml.dump(param_tmp)
        yaml_text = re.sub(delim, '', yaml_text)

        yaml_text = re.sub(' +\n', '\n', yaml_text)
        yaml_text = gui_util.indent_yaml_values(yaml_text)

        file_handle = open(path, 'w')
        file_handle.write(yaml_text)
        file_handle.close()


    ###########################################################################
    ##  Tools for Parameters, Getters, Setters                               ##
    ###########################################################################

    def gui_param_from_breadcrumb(self, breadcrumb):
        '''
        Return the subelement of param_gui according to breadcrumb
        '''
        l = list(breadcrumb)
        x = param_gui
        while len(l):
            x = x[l.pop(0)]
        return x


    def elem_get_value(self, key):
        elem = self.elems[key]
        if isinstance(elem, QLineEdit):
            return elem.text()
        elif isinstance(elem, QCheckBox):
            return elem.isChecked()
        elif isinstance(elem, QTextEdit):
            return elem.toPlainText()
        elif isinstance(elem, QComboBox):
            return elem.currentText()


    def elem_set_val(self, key, value):
        '''
        Set value in GUI element
        '''
        elem = self.elems[key]
        if isinstance(elem, QLineEdit):
            elem.setText(str(value))

        elif isinstance(elem, QTextEdit):
            elem.setText(str(value))

        elif isinstance(elem, QCheckBox):
            elem.setChecked(value)

        elif isinstance(elem, QComboBox):
            combo_idx = elem.findText(str(value), Qt.MatchFixedString)
            if combo_idx < 0:
                combo_idx = 0
            elem.setCurrentIndex(combo_idx)


    def param_get_value(self, tup):
        l = list(tup)
        x = self.param
        while len(l):
            x = x[l.pop(0)]
        return x


    def param_set_value(self, tup, val):
        l = list(tup)
        last = l.pop()
        x = self.param
        while len(l):
            x = x[l.pop(0)]
        x[last] = val



if __name__ == '__main__':
    app = QApplication(sys.argv)
    App()
    sys.exit(app.exec_())
