# Additional classes for GUI, functions between GUI and calculating modules
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import copy
import datetime
import logging
from math import ceil
# from logging.handlers import FileHandler
from multiprocessing import Process, Pipe, Value
import os
import re
import sys
import time
import traceback

import numpy as np
from obspy import UTCDateTime
from PySide6 import QtGui
from PySide6.QtCore import Qt, QSize, QObject, QRunnable, Signal, Slot
from PySide6.QtWidgets import (QSizePolicy, QHBoxLayout, QVBoxLayout,
    QWidget, QLabel, QPlainTextEdit, QGroupBox, QCheckBox, QPushButton)

from dug_seis.processing.processing import processing as dugseis_processing


def setup_logging(proc_folder):

    os.chdir(proc_folder)

    # shut up libraries
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    # Setup logging.
    # By default we log to stdout with ERROR level and to a log file (if specified)
    # with INFO level. Setting verbose logs to both handlers with DEBUG level.
    verbose = False

    logger = logging.getLogger('dug-seis')
    logger.setLevel(logging.WARNING)
    formatter = logging.Formatter('[%(filename)-22s:%(lineno)4d] %(levelname)-7s %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    log = os.path.join(
        proc_folder,
        'dug-seis_%s.log' % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    fh = logging.FileHandler(log)
    fh.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)-7s %(message)s')
    fh.formatter = formatter
    logger.addHandler(fh)
    logger.info('DUG-Seis started')


def param_flatten_hierarchy(my_dict):
    lol = parse_param_recursive(my_dict)
    return {tuple(lol[i][0]): lol[i][1]
        for i in range(0, len(lol))}


def parse_param_recursive(my_dict):
    lol = []
    for key in my_dict.keys():
        if type(my_dict[key]) is dict:
            tmp = parse_param_recursive(my_dict[key])
            for t in tmp:
                t[0].insert(0, key)
                lol.append(t)
        else:
            lol.append([[key], my_dict[key]])

    return lol


def param_get_value(param, tup):
    l = list(tup)
    x = param
    while len(l):
        x = x[l.pop(0)]
    return x


def format_traceback(txt):
    msg = re.sub(r'\n', '<br>', txt)
    return re.sub(r' ', '&nbsp;', msg)


def check_dir(dir):
    testfile = os.path.join(dir, 'dugseis-test.txt')
    try:
        filehandle = open(testfile, 'w')
    except FileNotFoundError:
        return 'Directory not found:<br>' + dir
    except PermissionError:
        return 'Permission denied:<br>' + dir
    except Exception as e:
        return (e.args[1])
    else:
        filehandle.close()
        os.remove(testfile)


def validate_yaml_param(param, check_dirs=False):
    '''Check SOME properties of the parameters'''
    errors = []

    # directories
    if check_dirs:
        for tup in [
            ('General', 'asdf_folder'),
            ('General', 'processing_folder'),
        ]:
            dir = param_get_value(param, tup)
            err = check_dir(dir)
            if err:
                errors.append(f'“{".".join(tup)}”:<br>{err}')

    # length of lists
    ct = param['General']['sensor_count']
    for xyz in ['x', 'y', 'z']:
        length = len(param['Channels'][xyz +'_coord'])
        if length != ct:
            errors.append(f'Wrong number of {xyz}_coord: {length}')

    for field in ['station_naming', 'tr_channels', 'tr_threshold_on',
            'tr_threshold_off', 'tr_st_window', 'tr_lt_window']:
        length = len(param['Channels'][field])
        if length != ct:
            errors.append(f'Wrong number of <code>{field}</code> values: {length}')
    return '<br><br>'.join(errors)


def param_yaml_to_gui(yaml_param):
    param = copy.deepcopy(yaml_param)

    param['General']['operator'] = '\n'.join(param['General']['operator'])

    ch = param['Channels']
    for coord in ['x_coord', 'y_coord', 'z_coord']:
        ch[coord] = [round(x, 3) for x in ch[coord]]

    bool_mapping = {
        'y': True,
        'n': False,
        True: True,
        False: False,
    }
    ch['tr_channels'] = [bool_mapping[el] for el in ch['tr_channels']]
    for field in ['tr_threshold_on', 'tr_threshold_off',
            'tr_st_window', 'tr_lt_window']:
        for i in range(len(ch[field])):
            ch[field][i] = '' if not ch['tr_channels'][i] else ch[field][i]

    return param


def setup_acquitision_dirs(param):
    # create directories if necessary
    dir_asdf = os.path.join(param['General']['acquisition_folder'], 'asdf')
    dir_tmp = os.path.join(param['General']['acquisition_folder'], 'tmp')
    param['Acquisition']['asdf_settings']['data_folder'] = dir_asdf
    param['Acquisition']['asdf_settings']['data_folder_tmp'] = dir_tmp

    error = ''
    try:
        if not os.path.isdir(dir_asdf):
            os.makedirs(dir_asdf)
        if not os.path.isdir(dir_tmp):
            os.makedirs(dir_tmp)
    except:
        exctype, value = sys.exc_info()[:2]
        error = (exctype, value, traceback.format_exc())
        error = (f'Error with acquitision directories:<br>'
            + format_traceback(error))

    return error


def setup_ac_logging(dir):

    # shut up libraries
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    # By default we log to a log file (if specified) with INFO level.
    # Setting verbose logs with DEBUG level.
    verbose = False

    logger = logging.getLogger('dug-seis')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(filename)-22s:%(lineno)4d] %(levelname)-7s %(message)s')
    log = os.path.join(
        dir,
        'dug-seis_acquisition-%s.log' % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    fh = logging.FileHandler(log)
    fh.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)-7s %(message)s')
    fh.formatter = formatter
    logger.addHandler(fh)
    logger.info('DUG-Seis started')
    return logger


def param_yaml_to_processing(gui_param):
    '''
    Conversion of values to dimensions needed in processing
    '''
    param = copy.deepcopy(gui_param)

    # conversions
    param['General']['sensor_coords'] = np.array(list(zip(
        param['Channels']['x_coord'],
        param['Channels']['y_coord'],
        param['Channels']['z_coord']
    )), dtype=np.float64)

    param['Acquisition']['hardware_settings']['input_range'] = param['Channels']['input_range']
    param['Acquisition']['hardware_settings']['preamp_gain'] = param['Channels']['preamp_gain']
    param['Acquisition']['hardware_settings']['internal_gain'] = param['Channels']['internal_gain']
    param['Acquisition']['asdf_settings']['station_naming'] = param['Channels']['station_naming']

    param['Trigger']['recstalta'] = {}
    param['Trigger']['channels'] = [i + 1
        for i, v in enumerate(param['Channels']['tr_channels']) if v]

    for name in ['threshold_on', 'threshold_off', 'st_window', 'lt_window']:
        tmp_list = param['Channels']['tr_' + name]
        tmp_list = [v for i, v in enumerate(tmp_list) if param['Channels']['tr_channels'][i]]
        param['Trigger']['recstalta'][name] = tmp_list

    del(param['Channels'])

    # change ms to s
    param['Trigger']['offset'] = param['Trigger']['offset'] / 1000
    param['Trigger']['interval_length'] = param['Trigger']['interval_length'] / 1000
    pp = param['Picking']
    if pp['algorithm'] == 'sta_lta':
        pp['sta_lta']['s_wave']['gap'] = pp['sta_lta']['s_wave']['gap'] / 1000
        pp['sta_lta']['s_wave']['length'] = pp['sta_lta']['s_wave']['length'] / 1000

    return param


def indent_yaml_values(txt):
    lines = txt.split('\n')
    result = []
    for line in lines:
        pos_colon = line.find(':')
        if pos_colon >= 0:
            if line[pos_colon + 1:pos_colon + 2] == ' ':
                result.append(line[:pos_colon] + (' ' * (30 - pos_colon)) + line[pos_colon:])
            else:
                result.append(line)
        else:
            result.append(line)
    return '\n'.join(result)


def make_button(caption, small=False):
    btn = QPushButton(caption)
    if small:
        btn.setFixedSize(120, 24)
    else:
        btn.setFixedSize(200, 40)
    btn.setStyleSheet('QPushButton {font-weight: bold;}')
    return btn



class ChannelsSelector(QGroupBox):
    def __init__(self, ch_count):
        super().__init__()
        self.checkboxes = []
        self.rows = []
        # This is hardcoded, because destoying this widget (before rebuilding
        # with a different number of channels) is quite lengthy in PyQt.
        self.MAX_CHANNELS = 128
        self.widget = QGroupBox('Channels to plot')
        vbox = QVBoxLayout()
        for row_idx in range(0, self.MAX_CHANNELS // 8):
            hbox = QHBoxLayout()
            label = QLabel(f'{row_idx * 8 + 1}–{row_idx * 8 + 8}')
            label.setFixedSize(QSize(55, 20))
            hbox.addWidget(label)
            for i in range(0, 8):
                cb = QCheckBox()
                cb.setChecked(True)
                hbox.setAlignment(Qt.AlignLeft)
                hbox.addWidget(cb)
                self.checkboxes.append(cb)
            btn1 = QPushButton('All')
            btn2 = QPushButton('None')
            btn1.setFixedSize(QSize(60, 24))
            btn2.setFixedSize(QSize(60, 24))
            btn1.clicked.connect(self.create_handler(row_idx, True))
            btn2.clicked.connect(self.create_handler(row_idx, False))
            hbox.addWidget(btn1)
            hbox.addWidget(btn2)
            hbox.setContentsMargins(0, 0, 0, 0)

            wid = QWidget()
            wid.setLayout(hbox)
            vbox.addWidget(wid)
            wid.hide()
            self.rows.append(wid)

        self.widget.setLayout(vbox)
        self.show_channels(ch_count)


    def show_channels(self, num_channels):
        # Only groups of 8 channels are possible.
        for row_idx in range(0, self.MAX_CHANNELS // 8):
            if row_idx in range(0, num_channels // 8):
                self.rows[row_idx].show()
                self.set_row(row_idx, True)
            else:
                self.rows[row_idx].hide()
                self.set_row(row_idx, False)


    def selected(self):
        return [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]


    def create_handler(self, row_idx, bool):
        def func():
            self.set_row(row_idx, bool)
        return func


    def set_row(self, row_idx, bool):
        for i in range(0, 8):
            self.checkboxes[row_idx * 8 + i].setChecked(bool)


    def set_enabled(self, val):
        for cb in self.checkboxes:
            cb.setEnabled(val)



class PlainTextEdit(QPlainTextEdit):
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
        self.lineheight = self.fontMetrics().height()

        font = QtGui.QFont()
        font.setFamily('Monospace')
        font.setPointSize(10)
        self.setFont(font)

        # self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setAcceptDrops(False)
        self.setUndoRedoEnabled(False)
        self.setReadOnly(True)
        self.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.TextSelectableByMouse)

        sizePolicy = QSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.block_selected = None

        self.fmt_normal = QtGui.QTextCharFormat()
        self.fmt_normal.setForeground(QtGui.QColor('#000000'))
        self.fmt_normal.setBackground(QtGui.QColor('#ffffff'))

        self.fmt_selected = QtGui.QTextCharFormat()
        self.fmt_selected.setForeground(QtGui.QColor('#ffffff'))
        self.fmt_selected.setBackground(QtGui.QColor('#326c9d'))


    def find_visible_blocks(self):
        self.visible_blocks = []
        block = self.firstVisibleBlock()
        height = self.height()
        block_top = self.blockBoundingGeometry(block).translated(
            self.contentOffset()
        ).top()
        block_bottom = self.blockBoundingGeometry(block).height() + block_top

        while block.isValid():
            if not block_bottom <= height:
                break

            if block.isVisible():
                self.visible_blocks.append([block_top, block])

            block = block.next()
            block_top = block_bottom
            block_bottom = block_top + self.blockBoundingRect(block).height()


    def block_set_format(self, block, fmt):
        blockPos = block.position()
        cursor = QtGui.QTextCursor(self.document())
        cursor.setPosition(blockPos)
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        cursor.setCharFormat(fmt)


    def mousePressEvent(self, evt):
        if self.callback is None:
            return

        if self.block_selected is not None:
            self.block_set_format(self.block_selected, self.fmt_normal)

        y = evt.pos().y()
        self.find_visible_blocks()

        # If there is no entry, there is still a block.
        if (len(self.visible_blocks) == 1
                and self.visible_blocks[0][1].text() == ''):
            return

        block = None
        for array in self.visible_blocks:
            if array[0] < y < self.lineheight + array[0]:
                block = array[1]
                break

        # click on empty space
        if block == None:
            return

        self.block_selected = block

        self.block_set_format(block, self.fmt_selected)
        self.repaint()

        text = block.text()
        self.callback(text)


    def select_block_by_idx(self, idx0, step):
        if self.block_selected is not None:
            self.block_set_format(self.block_selected, self.fmt_normal)
        bl = self.document().findBlockByNumber(idx0)
        self.block_set_format(
            bl,
            self.fmt_selected
        )
        self.block_selected = bl

        vb = self.verticalScrollBar()
        pos = vb.value()

        if step < 0:
            new_pos = max(0, pos + step)
        else:
            new_pos = min(vb.maximum(), pos + step)
        vb.setValue(new_pos)
        self.parent().update()
        self.repaint()



class ProcessingStarterSignals(QObject):
    finished = Signal()
    error    = Signal(tuple)
    logging  = Signal(dict)



class ProcessingStarter(QRunnable):
    def __init__(self, param, communication, app):
        super().__init__()
        self.signals = ProcessingStarterSignals()

        self.param = param
        self.app = app
        self.communication = communication
        self.communication['callback_signal'] = self.signals.logging


    @Slot()
    def run(self):
        try:
            parent_conn, child_conn = Pipe()
            self.communication['pipe'] = child_conn
            proc_continue = Value('h', 1)
            proc = Process(target=dugseis_processing,
                args=(self.param, self.communication, proc_continue))
            proc.start()
            running = True

            while running:
                response = parent_conn.recv()
                self.signals.logging.emit(response)
                if not self.app.proc_continue:
                    proc_continue.value = 0
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))



class WorkerSignals(QObject):
    finished = Signal()
    error    = Signal(tuple)
    progress = Signal(dict)
    single_event = Signal(dict)



class ProcessingWorker(QRunnable):
    def __init__(self, fn, communication, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        communication['callback_signal'] = self.signals.progress
        self.kwargs['communication'] = communication

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()


def chunks_string(arr, n, char, empty_char, size):
    '''
    Generate a string like "P--P PP--" from a list like [1,4,5,6].

    Args:
        arr ([int]): selected stations
        n (int):     number of all stations
        char (str):  character for "is selected"
        size (int):  length of a block of character,
                     blocks are separated by a single space
    '''
    s = ''.join([char if i in arr else empty_char for i in range(1, n + 1)])
    res = [s[i*size : i*size+size] for i in range(0, ceil(len(s) / size))]
    return ' '.join(res)
