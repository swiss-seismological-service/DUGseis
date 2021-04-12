import typing
import numpy as np
import pyqtgraph as pg


class WaveformPlotCurveItem(pg.PlotCurveItem):
    def __init__(
        self,
        channel_id: str,
        waveform_handler,
        main_window,
        horizontal_pixel_threshold: int = 2000,
    ):
        """
        Args:
            channel_id: The channel id for this plot.
            waveform_handler: The waveform handler instance for the data.
            horizontal_pixel_threshold: Threshold in horizontal pixels when to
                load higher load data.
        """
        self.wh = waveform_handler
        self.channel_id = channel_id
        self.x_range = (self.wh.starttime.timestamp, self.wh.endtime.timestamp)
        self.horizontal_pixel_threshold = horizontal_pixel_threshold
        pg.PlotCurveItem.__init__(self)
        self.main_window = main_window

        # Always get the binned data.
        self.binned_data = self.wh.get_binned_index_data(channel_id=self.channel_id)
        self.plot_binned_data()

    def plot_binned_data(self):
        self.setData(x=self.binned_data[0], y=self.binned_data[1])
        self.currently_plotted = "binned_data"

    def viewRangeChanged(self):
        self.updatePlot()

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
        samples_in_data = duration / self.wh.dt

        # Use indexed data if more than threshold pixels of it would be shown.
        if (
            samples_in_index >= self.horizontal_pixel_threshold
            and self.currently_plotted != "binned_data"
        ):
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

            self.setData(x=out["times"], y=out["data"])

            self.currently_plotted = {
                "start_time": out["start_time"],
                "end_time": out["end_time"],
                "npts": out["npts"],
                "delta": out["delta"],
                "is_max_resolution": out["is_max_resolution"],
            }