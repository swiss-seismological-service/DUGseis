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
Low level waveform plot item.
"""

import typing

import obspy
import numpy as np
import pyqtgraph as pg


class WaveformPlotCurveItem(pg.PlotCurveItem):
    def __init__(
        self,
        channel_id: str,
        waveform_handler,
        main_window,
        horizontal_pixel_threshold: int = 2000,
        filter_function: typing.Optional[typing.Callable] = None,
    ):
        """
        Args:
            channel_id: The channel id for this plot.
            waveform_handler: The waveform handler instance for the data.
            horizontal_pixel_threshold: Threshold in horizontal pixels when to
                load higher load data.
            filter_function: Optional filter function.
        """
        self.wh = waveform_handler
        self.channel_id = channel_id
        self.x_range = (self.wh.starttime.timestamp, self.wh.endtime.timestamp)
        self.horizontal_pixel_threshold = horizontal_pixel_threshold
        pg.PlotCurveItem.__init__(self)
        self.main_window = main_window

        self.filter_function = filter_function

        # Always get the binned data.
        bd = list(self.wh.get_binned_index_data(channel_id=self.channel_id))
        # Cast because pyqtgraph does some computations and it otherwise
        # underflows.
        if bd[1].dtype == np.int16:
            bd[1] = np.require(bd[1], dtype=np.int32)
        self.binned_data = bd
        self.plot_binned_data()

    def plot_binned_data(self):
        self.setData(x=self.binned_data[0], y=self.binned_data[1])
        self.currently_plotted = "binned_data"

    def set_filter_function(self, filter_function: typing.Optional[typing.Callable]):
        self.filter_function = filter_function
        self.updatePlot()

    def viewRangeChanged(self):
        self.updatePlot()
        vb = self.getViewBox()
        # No view exists yet.
        if vb is None or not hasattr(vb, "viewRange"):
            return
        self.main_window.update_time_range_status(*vb.viewRange()[0])

    def mouseDoubleClickEvent(self, e):
        self.main_window._add_pick(channel_id=self.channel_id, timestamp=e.pos().x())

    def updatePlot(self):
        vb = self.getViewBox()

        # No view exists yet.
        if vb is None or not hasattr(vb, "viewRange"):
            return

        time_range = vb.viewRange()[0]
        duration = time_range[1] - time_range[0]

        samples_in_index = duration / (self.wh._cache_dt_ns / 1e9)

        # Use indexed data if more than threshold pixels of it would be shown.
        if samples_in_index >= self.horizontal_pixel_threshold:
            # Nothing to do it the is already binned.
            if self.currently_plotted == "binned_data":
                return
            self.plot_binned_data()
        # Otherwise some form of higher resolution data should be plotted.
        elif samples_in_index < self.horizontal_pixel_threshold:
            # We absolutely need to cover this range with the data - otherwise
            # we want new data.
            min_acceptable_start_time = max(
                self.wh.starttime.timestamp, time_range[0] - duration * 0.1
            )
            max_acceptable_end_time = min(
                self.wh.endtime.timestamp, time_range[1] + duration * 0.1
            )

            # We might not have to do anything at all.
            if (
                # Not binned data.
                self.currently_plotted != "binned_data"
                # Start time is okay.
                and self.currently_plotted["start_time"] <= min_acceptable_start_time
                # As is the end time.
                and self.currently_plotted["end_time"] >= max_acceptable_end_time
                # And the resolution is high enough.
                and (
                    duration / self.currently_plotted["delta"]
                    >= self.horizontal_pixel_threshold
                    or self.currently_plotted["is_max_resolution"] is True
                )
                # And the filter did not change.
                and self.currently_plotted["filter_function"]
                == id(self.filter_function)
            ):
                # Nothing to do.
                return

            # Figure out if we need to do something here or if the currently
            # shown data is still suitable.
            min_t = max(self.wh.starttime.timestamp, time_range[0] - duration)
            max_t = min(self.wh.endtime.timestamp, time_range[1] + duration)
            out = self.wh.get_waveform_data(
                channel_id=self.channel_id, start_time=min_t, end_time=max_t, npts=30000
            )

            data = out["data"]
            if self.filter_function and out["is_max_resolution"]:
                tr = obspy.Trace(data=out["data"], header={"delta": out["delta"]})
                data = self.filter_function(tr).data

            self.setData(x=out["times"], y=data)

            self.currently_plotted = {
                "filter_function": id(self.filter_function),
                "start_time": out["start_time"],
                "end_time": out["end_time"],
                "npts": out["npts"],
                "delta": out["delta"],
                "is_max_resolution": out["is_max_resolution"],
            }
        else:
            raise NotImplementedError
