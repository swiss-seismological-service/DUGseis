import collections
import pathlib
import sys
import typing

from PySide6 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

import numpy as np
import obspy
import obspy.core.event
import obspy.core.event.base
from obspy.core.event.origin import Pick
from obspy.core.event.base import Comment


from .ui_files.main_window import Ui_MainWindow
from .waveform_plot_curve_item import WaveformPlotCurveItem


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # XXX: Ugly and will go at one point.
        self._disable_channel_update = False

        self.config = config

        # Get the folders from the config.
        self._waveform_folder = pathlib.Path(self.config["General"]["asdf_folder"])
        self._event_folder = (
            pathlib.Path(self.config["General"]["processing_folder"]) / "quakeml"
        )
        assert self._waveform_folder.exists(), self._waveform_folder
        if not self._event_folder.exists():
            print("No events exist!")

        self._cache_folder = pathlib.Path(self.config["General"]["cache_folder"])

        # Set up the possible classifications.
        self._possible_classifications = self.config["General"]["classifications"]
        self.ui.classification_combo_box.insertItems(0, self._possible_classifications)

        # Set up possible pick types.
        self.ui.pick_type_combo_box.insertItems(0, self.config["General"]["pick_types"])

        self._setup()

    def _setup(self):
        self.event_count = len(list(self._event_folder.glob("*.xml")))
        self.ui.events_group_box.setTitle(f"Events ({self.event_count} available)")
        self.ui.event_number_spin_box.setMaximum(self.event_count)
        self._load_data()

        # Keep track of everything that is already plotted.
        self.plots = {}
        self.current_event = None

    def _load_data(self):
        from dug_seis.waveform_handler.waveform_handler import WaveformHandler
        from dug_seis.waveform_handler.indexing import index_trace

        self.wh = WaveformHandler(
            waveform_folder=self._waveform_folder,
            cache_folder=self._cache_folder,
            index_sampling_rate_in_hz=100,
            start_time=obspy.UTCDateTime(self.config["General"]["start_time"]),
            end_time=obspy.UTCDateTime(self.config["General"]["end_time"]),
        )

        for r in self.wh.receivers:
            item = QtGui.QListWidgetItem(r)
            self.ui.channel_list_widget.addItem(item)

    def _add_pick(self, channel_id, timestamp):
        if self.current_event is None:
            return
        p = Pick()
        p.time = obspy.UTCDateTime(timestamp)
        p.waveform_id = obspy.core.event.base.WaveformStreamID(*channel_id.split("."))
        p.phase_hint = self.ui.pick_type_combo_box.currentText()
        p.evaluation_mode = obspy.core.event.header.EvaluationMode.manual
        self.current_event.picks.append(p)

        event_filename = self._get_current_event_filename()
        event_number = self.ui.event_number_spin_box.value()

        self.current_event.write(str(event_filename), format="quakeml", validate=True)

        self._update_picks()

    def _show_channels(self, channels):
        # Nothing to do.
        if set(self.plots.keys()) == set(channels):
            return

        time_range = None

        # For a while I had some smart logic in there that only modifies that
        # channels it had to with the idea of inducing less work. That was
        # really hard to get stable and always had some subtle issues. So now
        # we just recreate all plots always. Seems to be fast enough.
        for key, value in list(self.plots.items()):
            if time_range is None:
                time_range = value["plot_object"].getViewBox().viewRange()[0]
            self.ui.plotWidget.removeItem(value["plot_object"])
            del self.plots[key]

        self.plots = {}

        def setYRange(self, *args, **kwargs):
            self.enableAutoRange(axis="y")
            self.setAutoVisible(y=True)

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
            self.plots[channel_id] = {"plot_object": plot, "line_objects": []}

            # This must happen before `addItem()` is called to avoid triggering an
            # unnecessary viewRangeChanged() signal.

            # First that the absolute limits, e.g. how far one can pan.
            plot.setLimits(
                xMin=self.wh.starttime.timestamp, xMax=self.wh.endtime.timestamp
            )

            # And the initial extend on the x-axis.
            # if time_range is None:
            x_range = (self.wh.starttime.timestamp, self.wh.endtime.timestamp)
            # else:
            #     x_range = (time_range[0], time_range[1])
            plot.setXRange(*x_range)

            plot.addItem(
                WaveformPlotCurveItem(
                    channel_id=channel_id, waveform_handler=self.wh, main_window=self
                )
            )

            plot.sigXRangeChanged.connect(setYRange)

        plot_list = [v["plot_object"] for v in self.plots.values()]
        # Always link the time axis.
        for p in plot_list[1:]:
            p.setXLink(plot_list[0])

        if time_range is not None:
            for p in plot_list:
                p.setXRange(*time_range)

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

    @QtCore.Slot()
    def on_relocate_push_button_released(self, *args, **kwargs):
        from dug_seis.processing.location import locate

        event_filename = self._get_current_event_filename()
        new_event = locate(dug_seis_param=self.config, event=self.current_event)
        if not new_event:
            return

        self.current_event = new_event

        self.current_event.write(str(event_filename), format="quakeml", validate=True)
        event_number = self.ui.event_number_spin_box.value()
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_channel_list_widget_itemSelectionChanged(self, *args, **kwargs):
        if self._disable_channel_update is True:
            return
        selected_channels = [
            i.text() for i in self.ui.channel_list_widget.selectedItems()
        ]
        self._show_channels(selected_channels)

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
        if not self.current_event:
            return

        event_filename = self._get_current_event_filename()
        event_number = self.ui.event_number_spin_box.value()

        current_classification = (
            self.current_event.comments[0].text.split(":", 1)[1].strip()
        )
        new_classification = self.ui.classification_combo_box.currentText().strip()
        if current_classification == new_classification:
            return

        # Write the classification as a comment.
        self.current_event.comments = [
            Comment(text=f"Classification: {new_classification}")
        ]
        self.current_event.write(str(event_filename), format="quakeml", validate=True)
        self.load_event(event_number=event_number)

    @QtCore.Slot()
    def on_show_channels_with_picks_button_released(self):
        if not self.current_event:
            return
        channels = sorted(set([p.waveform_id.id for p in self.current_event.picks]))
        self._show_channels(channels)

        event_number = self.ui.event_number_spin_box.value()
        self.load_event(event_number=event_number)

    def _get_current_event_filename(self):
        event_number = self.ui.event_number_spin_box.value()
        # This is ghetto as fuck.
        event_candidates = list(self._event_folder.glob(f"*[tr]{event_number}.xml"))
        if not event_candidates:
            raise ValueError(f"Could not find event {event_number}")
        return event_candidates[0]

    def load_event(self, event_number: int):
        # Bound it.
        event_number = max(1, event_number)
        event_number = min(event_number, self.event_count)

        # Set the spin box.
        self.ui.event_number_spin_box.setValue(event_number)

        event_filename = self._get_current_event_filename()
        cat = obspy.read_events(str(event_filename))
        assert len(cat) == 1

        self.current_event = cat[0]
        event = self.current_event

        # Set the classification.
        classification = event.comments[0].text.split(":", 1)[1].strip()

        self.ui.classification_combo_box.setCurrentText(classification)

        pick_str = sorted([p.waveform_id.id for p in self.current_event.picks])
        origin_str = f"    {len(event.origins)} origins\n"
        for origin in event.origins:
            origin_str += (
                f"       Origin at {origin.time} with "
                f"{len(origin.arrivals)} arrivals.\n"
            )

        text_str = (
            f"Event {event_filename.name}\n"
            f"{event.comments[0].text}\n\n"
            f"    {len(event.picks)} picks\n"
            f"       Picks on: {', '.join(pick_str)}\n"
            f"{origin_str}"
            f"    {len(event.magnitudes)} magnitudes\n"
        )
        self.ui.event_text_browser.setText(text_str)

        all_times = [p.time for p in self.current_event.picks] + [
            o.time for o in self.current_event.origins
        ]
        s = min(all_times)
        e = max(all_times)
        duration = e - s

        if self.plots:
            plot = next(iter(self.plots.values()))["plot_object"]
            plot.setXRange((s - duration).timestamp, (e + duration).timestamp)

            self._update_picks()

    def _update_picks(self):
        # No event - nothing to do.
        if not self.current_event:
            return

        picks = collections.defaultdict(list)

        for p in self.current_event.picks:
            picks[p.waveform_id.id].append(p)

        origin_times = [o.time.timestamp for o in self.current_event.origins]

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
                        breakpoint()

                    # Use the phase hint, otherwise find a matching arrival.
                    phase_hint = None
                    if not p.phase_hint:
                        for o in self.current_event.origins:
                            if phase_hint:
                                break
                            for a in o.arrivals:
                                if a.pick_id == p.resource_id and a.phase:
                                    phase_hint = a.phase
                                    break
                    else:
                        phase_hint = p.phase_hint

                    timestamp = p.time.timestamp
                    pick_object = pg.InfiniteLine(
                        pos=timestamp,
                        angle=90,
                        pen={"color": color},
                        label=phase_hint,
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

        event_filename = self._get_current_event_filename()

        self.current_event.write(str(event_filename), format="quakeml", validate=True)

        self._update_picks()

    def _pick_clicked(self, inifinite_line, mouse_click):
        if mouse_click.modifiers() != QtCore.Qt.ControlModifier:
            return
        pick = inifinite_line.name()

        picks = [
            p
            for p in self.current_event.picks
            if (p.resource_id != pick.resource_id or p.waveform_id != pick.waveform_id)
        ]
        self.current_event.picks = picks

        event_filename = self._get_current_event_filename()
        self.current_event.write(str(event_filename), format="quakeml", validate=True)
        self._update_picks()


def launch(config: typing.Dict):
    app = QtWidgets.QApplication([])
    window = MainWindow(config=config)
    window.show()
    sys.exit(app.exec_())
