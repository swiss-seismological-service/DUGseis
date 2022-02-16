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
Main window and entry point for the graphical DUGSeis interface.
"""

import collections
import logging
import pathlib
import pprint
import sys
import time
import typing

from PySide6 import QtCore, QtWidgets

import pyqtgraph as pg

import numpy as np
import obspy
import obspy.core.event
import obspy.core.event.base
from obspy.core.event.origin import Pick
from obspy.core.event.base import Comment


from .three_d_view import ThreeDView
from .ui_files.main_window import Ui_MainWindow
from .waveform_plot_curve_item import WaveformPlotCurveItem
from ..project.project import DUGSeisProject
from ..util import filter_settings_to_function

logger = logging.getLogger(__name__)


class ReloadDataWorker(QtCore.QObject):
    """
    Worker thread to reload the waveform data to not block the UI.
    """

    finished = QtCore.Signal()

    def __init__(self, project: DUGSeisProject, mutex: QtCore.QMutex):
        super().__init__()
        self._project = project
        self._mutex = mutex

    @QtCore.Slot()
    def run(self):
        try:
            self._run()
        except Exception as e:
            print(f"Failed running thread due to: {str(type(e))}: {e}")
        self.finished.emit()

    def _run(self):
        try:
            self._mutex.lock()
            self._project._load_waveforms()
        # Always release the lock.
        finally:
            self._mutex.unlock()


class MainWindow(QtWidgets.QMainWindow):
    """
    Main window of the graphical DUGSeis interface.
    """

    def __init__(
        self, config: typing.Union[pathlib.Path, str, typing.Dict], operator: str
    ):
        """
        Args:
            config: The DUGSeis project configuration as a filename or a
                dictionary.
            operator: The name of the operator. Will be saved in the manual
                picks.
        """
        # PySide init.
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Dictionary storing the state of things.
        self._state = {}

        # Keep track of everything that is already plotted.
        self.plots = {}

        # Load the project.
        self.project = DUGSeisProject(config=config)

        # Set the operator and show the name in the status bar.
        self.operator = operator
        self.statusBar().showMessage(f"Operator: {operator}")

        # Set up the possible classifications, pick types, and filters.
        self._possible_classifications = self.project.config["graphical_interface"][
            "classifications"
        ]
        self.ui.classification_combo_box.insertItems(0, self._possible_classifications)
        self.ui.pick_type_combo_box.insertItems(
            0, self.project.config["graphical_interface"]["pick_types"]
        )
        self.ui.polarity_combo_box.insertItems(
            0, ["none", "undecidable", "positive", "negative"]
        )
        self.ui.uncertainty_combo_box.insertItems(
            0,
            ["none"]
            + [
                str(i)
                for i in self.project.config["graphical_interface"][
                    "uncertainties_in_ms"
                ]
            ],
        )
        self.ui.filter_combo_box.insertItems(
            0, ["no filter"] + [i["filter_id"] for i in self.project.config["filters"]]
        )
        # Also set up all filter functions - this is cheap to do and makes the
        # futher logic simpler.
        self.filter_functions = {
            f["filter_id"]: filter_settings_to_function(f["filter_settings"])
            for f in self.project.config["filters"]
        }

        # XXX: Ugly and will go at one point.
        self._disable_channel_update = False

        # Extended setup.
        self._setup()

        # OpenGL is somehow only initialized once the window is fully loaded so
        # just create the 3-D view with a delay of 100ms.
        QtCore.QTimer.singleShot(100, self._init_3d_view)

        self.data_monitoring_timer = QtCore.QTimer()
        self.data_monitoring_timer.timeout.connect(self.check_if_data_changed)

    def _init_3d_view(self, set_camera: bool = True):
        """
        Function setting up the 3-D view of the stations.

        Can be called multiple times - it will then just update the 3-D view.
        """
        config = self.project.config["graphical_interface"]["3d_view"]

        # Get all coordinates from the project.
        coordinates = np.array(
            [
                v["coordinates"]
                for k, v in self.project.channels.items()
                # Don't show the hidden ones.
                if k not in config["hide_channels"]
            ]
        )

        if not len(coordinates):
            print("No channels => Cannot initialize 3d view")
            return

        # Guard the initialization to be able to call this method multiple times
        # to react to changes.
        if not hasattr(self, "three_d_view"):
            self.three_d_view = ThreeDView(
                gl_widget=self.ui.stationViewGLWidget, config=config, parent=self
            )

        self.three_d_view.update_channels(
            channel_coordinates=coordinates, set_camera=set_camera
        )
        self.update_events_in_3d_plot()

    def update_events_in_3d_plot(self):
        """
        Updates the events in the 3D view.
        """
        event_coordinates = np.array(
            [
                self.project.global_to_local_coordinates(
                    latitude=c["latitude"],
                    longitude=c["longitude"],
                    depth=c["depth"],
                )
                for c in self.event_summary
            ]
        )
        event_times = [c["origin_time"] for c in self.event_summary]
        assert len(event_coordinates) == len(event_times)
        self.three_d_view.update_events(event_coordinates, event_times)

    def _setup(self):
        """
        More detailed setup.
        """
        self.event_count = self.project.db.count("Event")
        self.ui.events_group_box.setTitle(f"Events ({self.event_count} available)")
        self.ui.event_number_spin_box.setMaximum(self.event_count)

        # Also load the resources ids.
        self.event_summary = self.project.db.get_event_summary()
        assert self.event_count == len(self.event_summary)

        self._load_data()

        self._setup_info_screen()

        # Globally keep track of the zoom level to retain it across operations
        # if necessary.
        self._state["common_plot_starttime"] = self.wh.starttime.timestamp
        self._state["common_plot_endtime"] = self.wh.endtime.timestamp

    def _setup_info_screen(self):
        """
        Fill the info view.
        """
        info = (
            f"Waveform folders: {len(self.project.waveforms._waveform_folders)}\n"
            f"Waveform files: {len(self.project.waveforms._files)}\n"
            f"Total waveform filesize: {self.project.waveforms._pretty_total_size}\n"
        )
        info += "\n\n"
        info += "=" * 50
        info += "\n"
        info += "=" * 50
        info += "\nConfiguration:\n\n"
        info += pprint.pformat(self.project.config)
        self.ui.info_text_browser.setText(info)

    def _load_data(self):
        """
        Load the data and set the channel list widget.
        """
        self.wh = self.project.waveforms

        # Only add the channels if they have not been added yet.
        if self.ui.channel_list_widget.count() == 0:
            for r in sorted(self.project.channels.keys()):
                item = QtWidgets.QListWidgetItem(r)
                self.ui.channel_list_widget.addItem(item)

    @property
    def picks_per_channel(self) -> typing.Dict:
        """
        Returns all picks in the database, sorted per channel.

        Loads the picks the first time this is accessed which can be a bit
        expensive.
        """
        if not hasattr(self, "_picks_per_channel") or not self._picks_per_channel:
            logger.info("Reading all picks from the database ...")
            a = time.time()
            picks = self.project.db.get_objects(object_type="Pick")
            b = time.time()
            logger.info(f"Read {len(picks)} picks in {b - a:.2} seconds.")
            # Sort picks by channel.
            picks_per_channel = {c: [] for c in sorted(self.project.channels.keys())}
            for p in picks:
                picks_per_channel.get(p.waveform_id.id, []).append(p)
            self._picks_per_channel = picks_per_channel
        return self._picks_per_channel

    def _update_active_event_in_3d_plot(self):
        if "current_event" not in self._state:
            self.three_d_view.update_active_event(coordinates=None)
            return

        event = self._state["current_event"]
        if not event.origins:
            self.three_d_view.update_active_event(coordinates=None)
            return

        origin = event.preferred_origin() or event.origins[0]

        event_coords = np.array(
            [
                self.project.global_to_local_coordinates(
                    latitude=origin.latitude,
                    longitude=origin.longitude,
                    depth=origin.depth,
                )
            ]
        )
        self.three_d_view.update_active_event(coordinates=event_coords)

    def _update_active_channels_in_3d_plot(self):
        if not self.plots:
            self.three_d_view.update_active_channels(coordinates=None)
            return

        coords = np.array(
            [self.project.cartesian_coordinates[c] for c in self.plots.keys()]
        )
        self.three_d_view.update_active_channels(coordinates=coords)

    def _add_pick(self, channel_id, timestamp):
        if "current_event" not in self._state:
            return
        event = self._state["current_event"]

        p = Pick()
        p.time = obspy.UTCDateTime(timestamp)
        p.waveform_id = obspy.core.event.base.WaveformStreamID(*channel_id.split("."))
        p.phase_hint = self.ui.pick_type_combo_box.currentText()

        # Store the polarity if given.
        polarity = self.ui.polarity_combo_box.currentText()
        if polarity != "none":
            p.polarity = polarity

        # Store the uncertainty if given.
        uncertainty = self.ui.uncertainty_combo_box.currentText()
        if uncertainty != "none":
            p.time_errors.uncertainty = float(uncertainty)

        # Store the filter id if given.
        applied_filter = self.ui.filter_combo_box.currentText()
        if applied_filter != "no filter":
            p.filter_id = applied_filter

        p.evaluation_mode = obspy.core.event.header.EvaluationMode.manual

        # If there is an event with the same phase hint and waveform id on this
        # event remove it.
        event_picks = []
        for pick in event.picks:
            if (
                pick.evaluation_mode == p.evaluation_mode
                and pick.waveform_id == p.waveform_id
                and pick.phase_hint == p.phase_hint
            ):
                # Also remove all arrivals with a reference to it.
                for origin in event.origins:
                    origin.arrivals = [
                        a for a in origin.arrivals if a.pick_id != pick.resource_id
                    ]
                continue
            event_picks.append(pick)

        event.picks = event_picks
        event.picks.append(p)

        self._update_picks()

    def _mouse_moved_in_graph(self, event):
        """
        Callback function to show the time under the cursor.

        Args:
            event: The mouse move event.
        """
        if not self.plots:
            return
        plot = next(iter(self.plots.values()))["plot_object"]

        x = plot.vb.mapSceneToView(event[0]).x()
        self.ui.mouse_position_label.setText(str(obspy.UTCDateTime(x)))

    def _select_or_deselect_channel_by_coordinates(self, coordinates):
        """
        Selects or deselects
        """

        channels = list(self.project.cartesian_coordinates.keys())
        channel_coords = np.array(list(self.project.cartesian_coordinates.values()))

        closest = np.argsort(np.linalg.norm(channel_coords - coordinates, axis=1))
        channel_name = channels[closest[0]]

        existing_channels = set(self.plots.keys())
        if channel_name in existing_channels:
            existing_channels.remove(channel_name)
        else:
            existing_channels.add(channel_name)

        self._show_channels(sorted(existing_channels))
        if "current_event" in self._state:
            event_number = self.ui.event_number_spin_box.value()
            self.load_event(event_number=event_number)

    def _show_channels(self, channels):
        # Nothing to do.
        if set(self.plots.keys()) == set(channels):
            return

        # Current shown time range.
        time_range = (
            self._state["common_plot_starttime"],
            self._state["common_plot_endtime"],
        )

        # For a while I had some smart logic in there that only modifies that
        # channels it had to with the idea of inducing less work. That was
        # really hard to get stable and always had some subtle issues. So now
        # we just recreate all plots always. Seems to be fast enough.
        if self.plots:
            self.ui.plotWidget.clear()

        self.plots = {}

        def setYRange(self, *args, **kwargs):
            self.enableAutoRange(axis="y")
            self.setAutoVisible(y=True)

        show_all_picks = self.ui.show_all_picks_check_box.isChecked()

        for i, channel_id in enumerate(sorted(channels)):
            if channel_id in self.plots:
                continue

            plot = self.ui.plotWidget.addPlot(
                i,
                0,
                title=channel_id,
                axisItems={
                    "bottom": pg.DateAxisItem(orientation="bottom", utcOffset=0)
                },
            )

            # Create a signal proxy to track the mouse location.
            proxy = pg.SignalProxy(
                plot.scene().sigMouseMoved,
                rateLimit=60,
                slot=self._mouse_moved_in_graph,
            )

            self.plots[channel_id] = {
                "plot_object": plot,
                "line_objects": [],
                # Keep the proxy around.
                "proxy": proxy,
                "all_picks": None,
            }

            # This must happen before `addItem()` is called to avoid triggering an
            # unnecessary viewRangeChanged() signal.

            # First that the absolute limits, e.g. how far one can pan.
            plot.setLimits(
                xMin=self.wh.starttime.timestamp, xMax=self.wh.endtime.timestamp
            )

            x_range = (self.wh.starttime.timestamp, self.wh.endtime.timestamp)
            plot.setXRange(*x_range, padding=0.0)

            plot.addItem(
                WaveformPlotCurveItem(
                    channel_id=channel_id, waveform_handler=self.wh, main_window=self
                )
            )

            # Picks per channel if necessary.
            if show_all_picks:
                self._add_all_picks_to_plot(channel_id=channel_id)

            plot.sigXRangeChanged.connect(setYRange)

        plot_list = [v["plot_object"] for v in self.plots.values()]
        # Always link the time axis.
        for p in plot_list[1:]:
            p.setXLink(plot_list[0])

        # Now all are linked so set the time range.
        if plot_list:
            plot_list[0].setXRange(*time_range, padding=0.0)

        # XXX: There must be a better way to do this ...
        # The problem is that otherwise the
        # on_channel_list_widget_itemSelectionChanged slot is triggered.
        self._disable_channel_update = True
        try:
            for i in range(self.ui.channel_list_widget.count()):
                item = self.ui.channel_list_widget.item(i)
                if item.text() in channels:
                    item.setSelected(True)
                else:
                    item.setSelected(False)
        finally:
            self._disable_channel_update = False

        self._update_picks()
        self._update_active_channels_in_3d_plot()

        self.ui.plotWidget.setMinimumHeight(len(plot_list) * 100)

        # Force the recomputation of the internal size to workaround a bug in
        # pyqtgraph if the minimal size of the widget becomes larger than the
        # container and it does not properly update once it fits again.
        self.ui.plotWidget.resizeEvent(ev=None)

    def _update_event_str(self, event):
        pick_str = sorted([p.waveform_id.id for p in event.picks])
        origin_str = f"    {len(event.origins)} origins\n"
        for origin in event.origins:
            origin_str += (
                f"       Origin at {origin.time} with "
                f"{len(origin.arrivals)} arrivals.\n"
            )

        text_str = (
            f"Event {event.resource_id}\n"
            f"{event.comments[0].text}\n\n"
            f"    {len(event.picks)} picks\n"
            f"       Picks on: {', '.join(pick_str)}\n"
            f"{origin_str}"
            f"    {len(event.magnitudes)} magnitudes\n"
        )
        self.ui.event_text_browser.setText(text_str)

    def load_event(self, event_number: int):
        # Bound it.
        event_number = max(1, event_number)
        event_number = min(event_number, self.event_count)

        # Set the spin box.
        self.ui.event_number_spin_box.setValue(event_number)

        event = self.project.db.get_event_by_resource_id(
            # zero-based indexing.
            resource_id=self.event_summary[event_number - 1]["event_resource_id"]
        )

        # If the event is the same, we want to retain any picks that are not yet
        # saved to the database. This for example includes picks that have not
        # been used in a relocation.
        if (
            self._state.get("current_event", None)
            and self._state["current_event"].resource_id == event.resource_id
        ):
            existing_event = self._state["current_event"]
            picks_in_new_event = set(p.resource_id for p in event.picks)
            # Add the missing picks.
            for p in existing_event.picks:
                if p.resource_id not in picks_in_new_event:
                    event.picks.append(p)

        self._state["current_event"] = event
        # Show the default origin.
        self._update_active_event_in_3d_plot()

        # Update the origin combo box.
        origin_resource_ids = [str(o.resource_id.resource_id) for o in event.origins]
        self.ui.origin_selection_combo_box.clear()
        self.ui.origin_selection_combo_box.insertItems(0, origin_resource_ids)

        # Set the classification.
        classification = event.comments[0].text.split(":", 1)[1].strip()

        self.ui.classification_combo_box.setCurrentText(classification)
        self._update_event_str(event=event)

        all_times = [p.time for p in event.picks] + [o.time for o in event.origins]
        s = min(all_times)
        e = max(all_times)
        duration = e - s

        if self.plots:
            plot = next(iter(self.plots.values()))["plot_object"]
            plot.setXRange(
                (s - duration).timestamp, (e + duration).timestamp, padding=0.0
            )

            self._update_picks()

    def _update_picks(self):
        # No event - nothing to do.
        if "current_event" not in self._state:
            return

        event = self._state["current_event"]

        picks = collections.defaultdict(list)

        for p in event.picks:
            picks[p.waveform_id.id].append(p)

        origin_times = [o.time.timestamp for o in event.origins]

        for channel, value in self.plots.items():
            # Remove all old lines.
            for pick_object in value["line_objects"]:
                value["plot_object"].removeItem(pick_object)
            value["line_objects"] = []

            # Plot all picks.
            if channel in picks:
                for p in picks[channel]:
                    if not p.evaluation_mode:
                        evaluation_mode = "automatic"
                    else:
                        evaluation_mode = p.evaluation_mode

                    if evaluation_mode == "automatic":
                        color = "r"
                    elif evaluation_mode == "manual":
                        color = "g"
                    else:
                        color = "b"

                    # Use the phase hint, otherwise find a matching arrival.
                    phase_hint = None
                    if not p.phase_hint:
                        for o in event.origins:
                            if phase_hint:
                                break
                            for a in o.arrivals:
                                if a.pick_id == p.resource_id and a.phase:
                                    phase_hint = a.phase
                                    break
                    else:
                        phase_hint = p.phase_hint

                    label = phase_hint
                    if p.polarity == "positive":
                        label += "+"
                    elif p.polarity == "negative":
                        label += "-"
                    elif p.polarity == "undecidable":
                        label += "?"

                    timestamp = p.time.timestamp
                    pick_object = pg.InfiniteLine(
                        pos=timestamp,
                        angle=90,
                        pen={"color": color},
                        label=label,
                        labelOpts={"position": 0.95, "color": color},
                        movable=evaluation_mode == "manual",
                        name=p,
                    )

                    pick_object.sigPositionChangeFinished.connect(
                        self._pick_position_changed
                    )
                    pick_object.sigClicked.connect(self._pick_clicked)
                    value["plot_object"].addItem(pick_object)
                    value["line_objects"].append(pick_object)

                    if p.time_errors and p.time_errors.uncertainty:
                        u = p.time_errors.uncertainty
                        for d in [-1.0, 1.0]:
                            dependent_line = pg.InfiniteLine(
                                pos=timestamp + d * u,
                                angle=90,
                                pen={"color": color, "style": QtCore.Qt.DashLine},
                            )
                            dependent_line.setParentItem(pick_object)
                            value["plot_object"].addItem(dependent_line)
                            value["line_objects"].append(dependent_line)

            # Plot all origins.
            for origin in origin_times:
                origin_object = pg.InfiniteLine(
                    pos=origin,
                    angle=90,
                    pen={"color": "#EA53E7", "dash": [3, 3]},
                    label="origin",
                    labelOpts={"position": 0.9, "color": "#EA53E7"},
                )
                value["plot_object"].addItem(origin_object)
                value["line_objects"].append(origin_object)

    def _pick_position_changed(self, infinite_line):
        # Kind of a hack but not stupid if it works.
        pick = infinite_line.name()
        pick.time = obspy.UTCDateTime(infinite_line.pos().x())

        # event_filename = self._get_current_event_filename()

        # self.current_event.write(str(event_filename), format="quakeml", validate=True)

        self._update_picks()

    def _pick_clicked(self, inifinite_line, mouse_click):
        if "current_event" not in self._state:
            return
        event = self._state["current_event"]

        if mouse_click.modifiers() != QtCore.Qt.ControlModifier:
            return
        pick = inifinite_line.name()

        picks = [
            p
            for p in event.picks
            if (p.resource_id != pick.resource_id or p.waveform_id != pick.waveform_id)
        ]
        event.picks = picks

        self._update_picks()

    def update_time_range_status(self, starttime, endtime):
        self.ui.duration_label.setText(f"{endtime - starttime:.5g} s")
        self.ui.start_time_label.setText(str(obspy.UTCDateTime(starttime)))
        self.ui.end_time_label.setText(str(obspy.UTCDateTime(endtime)))
        self._state["common_plot_starttime"] = starttime
        self._state["common_plot_endtime"] = endtime

    def change_waveform_zoom(
        self, zoom_type: str, amount: typing.Optional[float] = None
    ):
        """
        Change the zoom of the waveform plot.

        Different types of zooms/shifts are possible with this helper method.

        Args:
            zoom_type: Possible are `"left"`, `"right"`, `"reset"`
            amount: Zoom amount in the chosen direction in percent. Thus a
                zoom_type of `"left"` and a amount of "1.0" will shift the
                view one screen to the left. If amount is negative it will keep
                the current zoom level but zoom all the way to the end in the
                given direction.
        """
        # No plots => Nothing to do!
        if not self.plots:
            return

        # The xranges of all plots are linked. Doing it for one is enough. So
        # get the first actual plot object.
        plot = next(iter(self.plots.values()))["plot_object"]

        current_view_range = plot.getViewBox().viewRange()[0]
        duration = current_view_range[1] - current_view_range[0]
        max_view_range = plot.items[0].x_range

        if zoom_type == "reset":
            assert amount is None
            new_view_range = max_view_range

        elif zoom_type == "left":
            assert amount is not None
            if amount > 0:
                x0 = current_view_range[0] - duration * amount
                new_view_range = (x0, x0 + duration)
            elif amount == 0:
                return
            else:
                new_view_range = (max_view_range[0], max_view_range[0] + duration)

        elif zoom_type == "right":
            assert amount is not None
            if amount > 0:
                x0 = current_view_range[0] + duration * amount
                new_view_range = (x0, x0 + duration)
            elif amount == 0:
                return
            else:
                new_view_range = (max_view_range[1] - duration, max_view_range[1])

        else:
            raise ValueError(
                "Possible 'zoom_type' values are: 'left', 'right', 'reset'."
            )

        plot.setXRange(*new_view_range, padding=0.0)

    def _reload_data_after_waveform_data(self):
        """
        All the other updates after the waveforms have been updated in a thread.
        """
        self._setup()
        self._init_3d_view(set_camera=False)

        # No plots => Nothing more to do!
        if not self.plots:
            return

        # Reload the data as well.
        plot = next(iter(self.plots.values()))["plot_object"]
        current_view_range = plot.getViewBox().viewRange()[0]

        current_channels = sorted(self.plots.keys())
        self._show_channels(channels=[])
        self._show_channels(channels=current_channels)

        plot = next(iter(self.plots.values()))["plot_object"]
        plot.setXRange(*current_view_range, padding=0.0)

    def reload_data(self):
        """
        Reload the data to react to changes.
        """
        # Reload the project's waveforms in thread.
        # Lock for the waveform update just to be safe.
        if "waveform_update_thread_lock" not in self._state:
            self._state["waveform_update_thread_lock"] = QtCore.QMutex()
        mutex = self._state["waveform_update_thread_lock"]

        if "thread" in self._state:
            print("Already running. Nothing will happen.")
            return

        self._state["thread"] = QtCore.QThread()
        self._state["worker_job"] = ReloadDataWorker(project=self.project, mutex=mutex)

        thread = self._state["thread"]
        worker_job = self._state["worker_job"]

        # Create worker job and move to the just created thread.
        worker_job.moveToThread(thread)

        # Signals and slots for the thread.
        thread.started.connect(worker_job.run)

        worker_job.finished.connect(self._reload_data_after_waveform_data)
        worker_job.finished.connect(worker_job.deleteLater)
        thread.finished.connect(lambda: self._state.pop("worker_job", None))
        thread.finished.connect(lambda: self._state.pop("thread", None))
        worker_job.finished.connect(thread.quit)

        thread.finished.connect(thread.deleteLater)

        # Finally start the thread.
        thread.start()

    def get_data_state(self) -> typing.Dict:
        """
        Get the state of the external data for monitoring purposes.
        """
        # We'll monitor two things: The ASDF folders and the size of the sqlite
        # database.
        asdf_files = set()
        for folder in self.project.config["paths"]["asdf_folders"]:
            asdf_files = asdf_files.union(set(folder.glob("*.h5")))

        db_size = (
            pathlib.Path(self.project.db._backend._connection_string).stat().st_size
        )

        state = {"asdf_files": asdf_files, "db_size": db_size}
        return state

    def check_if_data_changed(self):
        data_state = self.get_data_state()
        if not hasattr(self, "_data_state"):
            self._data_state = data_state
        else:
            if self._data_state != data_state:
                self._data_state = data_state
                logger.info("Data changed. Reloading ...")
                self.reload_data()
            else:
                logger.info("Data unchanged.")

    def _add_all_picks_to_plot(self, channel_id: str):
        """
        Helper method adding all picks for a certain channel to its
        corresponding plot object.
        """
        # Nothing to do.
        if channel_id not in self.plots:
            return

        timestamps = []
        for p in self.picks_per_channel[channel_id]:
            timestamps.append(p.time.timestamp)
        timestamps = np.array(timestamps)
        y = np.zeros_like(timestamps)

        symbolBrush = [
            int(i * 255)
            for i in self.project.config["graphical_interface"]["color_all_picks"]
        ]

        self.plots[channel_id]["all_picks"] = self.plots[channel_id][
            "plot_object"
        ].plot(
            timestamps,
            y,
            pen=None,
            symbol="o",
            symbolPen=None,
            symbolBrush=tuple(symbolBrush),
        )

    ################################################################################
    ################################################################################
    # Slots connecting UI elements can be found below this point.
    ################################################################################
    ################################################################################

    ################################################################################
    # Buttons
    ################################################################################

    @QtCore.Slot()
    def on_reset_zoom_button_released(self):
        self.change_waveform_zoom(zoom_type="reset")

    @QtCore.Slot()
    def on_fast_backward_button_released(self):
        self.change_waveform_zoom(zoom_type="left", amount=-1)

    @QtCore.Slot()
    def on_backward_button_released(self):
        self.change_waveform_zoom(zoom_type="left", amount=1.0)

    @QtCore.Slot()
    def on_fast_forward_button_released(self):
        self.change_waveform_zoom(zoom_type="right", amount=-1)

    @QtCore.Slot()
    def on_forward_button_released(self):
        self.change_waveform_zoom(zoom_type="right", amount=1.0)

    @QtCore.Slot()
    def on_load_event_button_released(self):
        event_number = self.ui.event_number_spin_box.value()
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_previous_event_button_released(self):
        event_number = self.ui.event_number_spin_box.value() - 1
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_next_event_button_released(self):
        event_number = self.ui.event_number_spin_box.value() + 1
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_save_classification_button_released(self):
        if "current_event" not in self._state:
            return
        event = self._state["current_event"]

        # Update the classification comment if necessary.
        current_classification = event.comments[0].text.split(":", 1)[1].strip()
        new_classification = self.ui.classification_combo_box.currentText().strip()
        if current_classification == new_classification:
            return
        event.comments = [Comment(text=f"Classification: {new_classification}")]

        # Now update the shown string.
        self._update_event_str(event=event)

        # And update the database by only updating the comments without touching
        # anything else.
        self.project.db.update_event_comments(event=event)

    @QtCore.Slot()
    def on_show_channels_with_picks_button_released(self):
        event = self._state.get("current_event", None)
        if not event:
            return
        channels = sorted(set([p.waveform_id.id for p in event.picks]))
        self._show_channels(channels)

        event_number = self.ui.event_number_spin_box.value()
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_show_closest_channels_button_released(self):
        ignore_channels = self.project.config["graphical_interface"]["3d_view"][
            "hide_channels"
        ]

        event = self._state.get("current_event", None)
        if not event or not event.origins:
            return

        origin = event.preferred_origin() or event.origins[0]

        coords = self.project.global_to_local_coordinates(
            latitude=origin.latitude,
            longitude=origin.longitude,
            depth=origin.depth,
        )

        channels = list(self.project.cartesian_coordinates.keys())
        channel_coords = np.array(list(self.project.cartesian_coordinates.values()))

        closest = np.argsort(np.linalg.norm(channel_coords - coords, axis=1))
        closest_channels = [
            channels[i] for i in closest if channels[i] not in ignore_channels
        ]

        # Arbitrary threshold here.
        self._show_channels(
            closest_channels[
                : self.project.config["graphical_interface"][
                    "number_of_closest_channels"
                ]
            ]
        )

        event_number = self.ui.event_number_spin_box.value()
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_relocate_push_button_released(self):
        event = self._state.get("current_event", None)
        if not event or not event.picks:
            return
        from .relocation_dialog import RelocationDialog

        d = RelocationDialog(
            self,
            event=event,
            project=self.project,
        )
        d.exec_()

    @QtCore.Slot()
    def on_save_visible_data_button_released(self):
        if not self.plots:
            mb = QtWidgets.QMessageBox(self)
            mb.setWindowTitle("No data")
            mb.setText("No waveform data selected")
            mb.exec()
            return

        # Get the times from the first plot.
        p = next(iter(self.plots.values()))["plot_object"]
        vb = p.getViewBox()
        if vb is None or not hasattr(vb, "viewRange"):
            mb = QtWidgets.QMessageBox(self)
            mb.setWindowTitle("No data")
            mb.setText("Cannot find waveform data range")
            mb.exec()
            return

        r = vb.viewRange()[0]
        starttime = obspy.UTCDateTime(r[0])
        endtime = obspy.UTCDateTime(r[1])

        npts_per_channel = int(
            round((endtime - starttime) / self.project.waveforms.dt + 1)
        )
        if npts_per_channel > 10000000:
            mb = QtWidgets.QMessageBox(self)
            mb.setWindowTitle(f"Requested {npts_per_channel} samples per channel.")
            mb.setText(
                "Please select less than 10M sample points per channel or consider using the DUGSeis API."
            )
            mb.exec()
            return

        channels = sorted(self.plots.keys())

        from .save_waveform_dialog import SaveWaveformsDialog

        d = SaveWaveformsDialog(
            self,
            starttime=starttime,
            endtime=endtime,
            channels=channels,
            project=self.project,
        )
        d.exec_()

    @QtCore.Slot()
    def on_save_picks_in_dummy_arrival_released(self):
        event = self._state.get("current_event", None)
        if not event or not event.picks:
            return

        picks_in_arrivals = []
        for o in event.origins:
            picks_in_arrivals.extend(a.pick_id.resource_id for a in o.arrivals)
        picks_in_arrivals = set(picks_in_arrivals)

        new_picks = []
        for p in event.picks:
            if p.resource_id.resource_id in picks_in_arrivals:
                continue
            new_picks.append(p)

        if not new_picks:
            print("No new picks => nothing to do.")
            return

        # Create a dummy origin.
        method_id = obspy.core.event.ResourceIdentifier("smi:local/dummy")
        eo = event.preferred_origin() or event.origins[0]
        origin = obspy.core.event.Origin(
            time=eo.time,
            latitude=eo.latitude,
            longitude=eo.longitude,
            depth=eo.depth,
            method_id=method_id,
        )

        for p in new_picks:
            origin.arrivals.append(
                obspy.core.event.Arrival(pick_id=p.resource_id, phase=p.phase_hint)
            )

        event.origins.append(origin)

        self.project.db.update_event(event=event)
        event_number = self.ui.event_number_spin_box.value()
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_reload_data_button_released(self):
        self.reload_data()

    ################################################################################
    # Others
    ################################################################################
    @QtCore.Slot()
    def on_filter_combo_box_currentIndexChanged(self, *args, **kwargs):
        if not getattr(self, "plots", None):
            return

        fct_name = self.ui.filter_combo_box.currentText()

        if fct_name == "no filter":
            ff = None
        else:
            ff = self.filter_functions[fct_name]

        for v in self.plots.values():
            v["plot_object"].items[0].set_filter_function(filter_function=ff)

    @QtCore.Slot()
    def on_origin_selection_combo_box_currentIndexChanged(self, *args, **kwargs):
        if "current_event" not in self._state:
            return
        event = self._state["current_event"]
        origin_id = self.ui.origin_selection_combo_box.currentText()
        if not origin_id:
            return
        origins = [o for o in event.origins if o.resource_id.resource_id == origin_id]
        if len(origins) != 1:
            print(f"Problem finding origin for {origin_id}. Found: {origins}")
            return

        origin = origins[0]
        event_coords = np.array(
            [
                self.project.global_to_local_coordinates(
                    latitude=origin.latitude,
                    longitude=origin.longitude,
                    depth=origin.depth,
                )
            ]
        )
        self.three_d_view.update_active_event(coordinates=event_coords)

    @QtCore.Slot()
    def on_channel_list_widget_itemSelectionChanged(self, *args, **kwargs):
        if self._disable_channel_update is True:
            return
        selected_channels = [
            i.text() for i in self.ui.channel_list_widget.selectedItems()
        ]
        self._show_channels(selected_channels)

    @QtCore.Slot()
    def on_show_all_picks_check_box_stateChanged(self, *args):
        show_all_picks = self.ui.show_all_picks_check_box.isChecked()
        for channel_id, plot in self.plots.items():
            if show_all_picks:
                # Show.
                if plot["all_picks"] is not None:
                    plot["all_picks"].show()
                # Or create.
                else:
                    self._add_all_picks_to_plot(channel_id=channel_id)
            # Otherwise hide if the exists.
            else:
                if plot["all_picks"] is not None:
                    plot["all_picks"].hide()

    @QtCore.Slot()
    def on_reload_on_data_change_check_box_stateChanged(self, *args):
        reload_on_data_change = self.ui.reload_on_data_change_check_box.isChecked()
        # Start or stop timer.
        if reload_on_data_change:
            if not hasattr(self, "_data_state"):
                self._data_state = self.get_data_state()
            self.data_monitoring_timer.start(
                # Given in milliseconds.
                int(
                    self.project.config["graphical_interface"][
                        "data_monitoring_ping_interval"
                    ]
                    * 1000
                )
            )
        else:
            self.data_monitoring_timer.stop()


def launch(config: typing.Dict, operator: str):
    app = QtWidgets.QApplication([])

    window = MainWindow(config=config, operator=operator)
    window.show()
    sys.exit(app.exec_())
