# flake8: noqa: F405
"""
Heavily based on the default GLGridItem class of pyqtgraph.

Custom grid to support grids that go from [x0, x1] and [y0, y1].

The default class only support symmetric grids.
"""
from OpenGL.GL import *
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from PySide6 import QtGui
from pyqtgraph import functions as fn


class GLGridItem(GLGraphicsItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`

    Displays a wire-frame grid.
    """

    def __init__(
        self,
        x_grid,
        y_grid,
        color=(255, 255, 255, 76.5),
        antialias=True,
        glOptions="translucent",
    ):
        GLGraphicsItem.__init__(self)

        self.x_grid = x_grid
        self.y_grid = y_grid

        self.setGLOptions(glOptions)
        self.antialias = antialias

        self.setColor(color)

    def setColor(self, color):
        """Set the color of the grid. Arguments are the same as those accepted by functions.mkColor()"""
        self.__color = fn.Color(color)
        self.update()

    def color(self):
        return self.__color

    def paint(self):
        self.setupGLState()

        if self.antialias:
            glEnable(GL_LINE_SMOOTH)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        glBegin(GL_LINES)

        glColor4f(*self.color().glColor())
        for x in self.x_grid:
            glVertex3f(x, self.y_grid[0], 0)
            glVertex3f(x, self.y_grid[-1], 0)
        for y in self.y_grid:
            glVertex3f(self.x_grid[0], y, 0)
            glVertex3f(self.x_grid[-1], y, 0)

        glEnd()
