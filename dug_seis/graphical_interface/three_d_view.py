import enum
import typing

import numpy as np
import obspy
from PySide6 import QtCore
import pyqtgraph.opengl as gl

from .components.grid import GLGridItem


class Item(enum.Enum):
    all_channels = enum.auto()
    all_events = enum.auto()
    active_event = enum.auto()
    active_channels = enum.auto()
    xy_grid = enum.auto()
    axis = enum.auto()


class ThreeDView:
    """
    Helper class dealing with the 3D View.
    """

    def __init__(self, gl_widget, config: typing.Dict, parent):
        """
        Args:
            gl_widget: The GLWidget.
            config: Configuration.
            parent: The parent windows.
        """
        self.__gl_widget = gl_widget
        self.__gl_widget.mouseReleaseEvent = self.mouseReleaseEvent
        self.__plot_items = {}

        self.parent = parent
        self.config = config

    def mouseReleaseEvent(self, event):
        # Only trigger on right mouse buttons.
        if event.button() != QtCore.Qt.MouseButton.RightButton:
            return

        # Normal right click == events.
        if event.modifiers() == QtCore.Qt.NoModifier:
            # Shoot ray + compute normal distance to all events.
            point, direction = self.get_camera_ray(event)
            dist = np.linalg.norm(
                np.cross(-direction, point - self.event_coordinates), axis=1
            )
            event_index = np.argmin(dist)
            self.parent.load_event(event_number=event_index + 1)
        # Control + right click -> select channel.
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            # Shoot ray + compute normal distance to all channels.
            point, direction = self.get_camera_ray(event)
            dist = np.linalg.norm(
                np.cross(-direction, point - self.channel_coordinates), axis=1
            )
            channel_index = np.argmin(dist)
            self.parent._select_or_deselect_channel_by_coordinates(
                self.channel_coordinates[channel_index]
            )

    def get_camera_ray(self, event):
        """
        Compute the ray from the camera to the mouse click.

        After https://antongerdelan.net/opengl/raycasting.html

        Args:
            event: Mouse event.

        Returns:
            A tuple of camera position, ray direction.
        """
        g = self.__gl_widget

        # Step 1: Normalized device coordinates.
        ray_nds = np.array(
            [
                2.0 * event.x() / g.width() - 1.0,
                1.0 - (2.0 * event.y() / g.height()),
                1.0,
            ]
        )

        # Step 2: 4-D homogeneous clip coordinates.
        ray_clip = np.array([ray_nds[0], ray_nds[1], -1.0, 1.0])

        # Step 3: Eye coordinates.
        inv_projection_matrix = (
            np.array(g.projectionMatrix().inverted()[0].data()).reshape(4, 4).T
        )
        ray_eye = inv_projection_matrix @ ray_clip
        ray_eye[2] = -1.0
        ray_eye[3] = 0.0

        # Step 4: 4-D world coordinates.
        inv_view_matrix = np.array(g.viewMatrix().inverted()[0].data()).reshape(4, 4).T
        ray_world = (inv_view_matrix @ ray_eye)[:3]
        ray_world /= np.linalg.norm(ray_world)

        camera = np.array(g.cameraPosition())

        return (camera, ray_world)

    def remove_item_if_exists(self, key):
        item = self.__plot_items.pop(key, None)
        if item is not None:
            self.__gl_widget.removeItem(item)

    def add_item(self, key, item):
        """
        Add item to the GL View. Remove any pre-existing items with the same
        key.
        """
        self.remove_item_if_exists(key=key)
        self.__plot_items[key] = item
        self.__gl_widget.addItem(item)

    def update_active_channels(self, coordinates: typing.Optional[np.ndarray]):
        """
        Update the active channels.
        """
        # Just remove if no new one is given.
        if coordinates is None:
            self.remove_item_if_exists(key=Item.active_channels)
            return

        size = np.ones(len(coordinates)) * self.config["size_active_channels_in_pixel"]
        color = np.tile(self.config["color_active_channels"], len(coordinates)).reshape(
            (len(coordinates), 4)
        )
        self.add_item(
            key=Item.active_channels,
            item=gl.GLScatterPlotItem(pos=coordinates, size=size, color=color),
        )

    def update_active_event(self, coordinates: typing.Optional[np.ndarray]):
        """
        Update the active event.
        """
        # Just remove if no new one is given.
        if coordinates is None:
            self.remove_item_if_exists(key=Item.active_event)
            return

        size = np.ones(len(coordinates)) * self.config["size_active_event_in_pixel"]
        color = np.tile(self.config["color_active_event"], len(coordinates)).reshape(
            (len(coordinates), 4)
        )
        self.add_item(
            key=Item.active_event,
            item=gl.GLScatterPlotItem(pos=coordinates, size=size, color=color),
        )

    def update_events(
        self,
        event_coordinates: np.ndarray,
        event_times: typing.List[obspy.UTCDateTime],
    ):
        """
        Update all events.

        Args:
            event_coordinates: The event coordinates.
            event_times: The times for each event.
        """
        if not len(event_coordinates):
            self.remove_item_if_exists(key=Item.all_events)
            return

        self.event_coordinates = event_coordinates.copy()

        size = np.ones(len(event_coordinates)) * self.config["size_events_in_pixel"]

        event_color = self.config["color_events"]
        if isinstance(event_color, str):
            import matplotlib.cm  # NOQA

            start_time = min(event_times)
            end_time = max(event_times)

            cmap = getattr(matplotlib.cm, event_color)
            r = end_time - start_time
            r = max(r, 0.0001)
            color = np.array(
                [
                    cmap(np.clip((t - start_time) / r, a_min=0.0, a_max=1.0))
                    for t in event_times
                ]
            )
        else:
            color = np.tile(
                self.config["color_events"], len(event_coordinates)
            ).reshape((len(event_coordinates), 4))
        self.add_item(
            key=Item.all_events,
            item=gl.GLScatterPlotItem(pos=event_coordinates, size=size, color=color),
        )

    def update_channels(self, channel_coordinates: np.ndarray, set_camera: bool):
        """
        Update the channels. It will remove any existing ones and also redraw
        the grid and axis because the channels defined the actual geometry.

        Args:
            channel_coordinates: The coordinates of the channels.
            set_camera: Set the camera automatically. Useful for the very first
                initialization.
        """
        self.channel_coordinates = channel_coordinates.copy()
        bounds = self.compute_bounds(coordinates=channel_coordinates)

        # Add xy grid.
        grid = GLGridItem(x_grid=bounds["x_grid"], y_grid=bounds["y_grid"])
        grid.translate(0, 0, bounds["z_min"])
        self.add_item(key=Item.xy_grid, item=grid)

        # Add axis.
        axis = gl.GLAxisItem()
        axis.setSize(x=bounds["scale"], y=bounds["scale"], z=bounds["scale"])
        axis.translate(
            bounds["x_grid"].min(),
            bounds["y_grid"].min(),
            bounds["z_min"] + 0.01 * bounds["scale"],
        )
        self.add_item(key=Item.axis, item=axis)

        # Plot line segments if desired.
        for segment in self.config["line_segments"]:
            s = np.array(segment)
            color = np.tile(self.config["line_segments_color"], len(s)).reshape(
                (len(s), 4)
            )
            plot_item = gl.GLLinePlotItem(
                pos=s, width=self.config["line_segments_width"], color=color
            )
            # Directly add these. If they ever need to be removed again the
            # logic has to be changed a bit.
            self.__gl_widget.addItem(plot_item)

        # Set the camera position if so desired.
        if set_camera:
            self.__gl_widget.opts["center"].setX(bounds["x_center"])
            self.__gl_widget.opts["center"].setY(bounds["y_center"])
            self.__gl_widget.opts["center"].setZ(bounds["z_min"])
            self.__gl_widget.opts["distance"] = bounds["scale"] * 2

        # Create size and color arrays.
        size = np.ones(len(channel_coordinates)) * self.config["size_channels_in_pixel"]
        color = np.tile(
            self.config["color_channels"], len(channel_coordinates)
        ).reshape((len(channel_coordinates), 4))
        # Actually show the events.
        self.add_item(
            key=Item.all_channels,
            item=gl.GLScatterPlotItem(pos=channel_coordinates, size=size, color=color),
        )

    def compute_bounds(
        self, coordinates: np.ndarray
    ) -> typing.Dict[str, typing.Union[float, np.ndarray]]:
        """
        Compute appropriate bounds and grids from a given array of coordinates.

        Args:
            coordinates: The coordinates as a numpy array.
        """
        x0, x1 = coordinates[:, 0].min(), coordinates[:, 0].max()
        y0, y1 = coordinates[:, 1].min(), coordinates[:, 1].max()
        z_min = coordinates[:, 2].min()

        xr = x1 - x0
        yr = y1 - y0

        # Add some buffer and recompute the extent.
        x0 -= xr
        x1 += xr
        y0 -= yr
        y1 += yr
        xr = x1 - x0
        yr = y1 - y0

        # Some heuristics to get nice axes.
        scale = max(coordinates.ptp(axis=0))
        exponent = len(str(int(scale / 10))) - 1
        dx = 10 ** exponent
        # Symmetric length.
        length = round(max(xr, yr) / 2, -exponent) + dx

        # Rounded mid values.
        x = round(x0 + 0.5 * xr, -exponent)
        y = round(y0 + 0.5 * xr, -exponent)

        # Finally construct a nice grid.
        count = int(round(length * 2 / dx)) + 1
        x_grid = np.linspace(x - length, x + length, count)
        y_grid = np.linspace(y - length, y + length, count)

        return {
            "scale": scale,
            "x_center": x,
            "y_center": y,
            "z_min": z_min,
            "x_grid": x_grid,
            "y_grid": y_grid,
        }
