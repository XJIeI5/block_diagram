# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import math


class Arrow(QtWidgets.QWidget):
    def __init__(self, begin: QtCore.QPoint, destination: QtCore.QPoint, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.drawingPath = None
        self.begin, self.destination = begin, destination
        self.resize(500, 500)
        self.image = QtGui.QPixmap(500, 500)
        self.image.fill(QtCore.Qt.GlobalColor.white)

    def draw(self, parent):
        painter = QtGui.QPainter(parent)
        self.set_painter_render_hints(painter)

        if not self.begin.isNull() and not self.destination.isNull():
            painter.drawLine(self.begin, self.destination)

            l = 30
            x_right = QtCore.QPointF(self.destination)

            right_triangle = QtGui.QPainterPath()
            right_triangle.lineTo(-0.4 * math.sqrt(3) * l, 0.3 * l)
            right_triangle.lineTo(-0.4 * math.sqrt(3) * l, -0.3 * l)
            right_triangle.closeSubpath()
            right_triangle.translate(x_right)

            painter.setBrush(QtGui.QColor("blue"))
            painter.translate(self.destination)

            x1, y1 = self.begin.x(), self.begin.y()
            x2, y2 = self.destination.x(), self.destination.y()
            a = y2 - y1
            c = x2 - x1
            b = math.sqrt(a ** 2 + c ** 2)

            angle = self.get_angle(a, b, c)

            painter.rotate(-angle)
            painter.translate(-self.destination)
            painter.drawPath(right_triangle)

    def set_painter_render_hints(self, painter: QtGui.QPainter):
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.HighQualityAntialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)

    def get_angle(self, a: int, b: int, c: float) -> float:
        if a == 0 and b == c:
            return 0
        elif c == 0 and -a == b:
            return 90
        elif a == 0 and b == -c:
            return 180
        elif c == 0 and a == b:
            return 270
        elif a < 0 and b > 0:
            return math.degrees(math.acos((b * b + c * c - a * a) / (2.0 * b * c)))
        return 360 - math.degrees(math.acos((b * b + c * c - a * a) / (2.0 * b * c)))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(QtCore.QPoint(), self.image)
        self.draw(self)

    def __repr__(self):
        return f'Arrow({self.begin.x()}, {self.begin.y()}, {self.destination.x()}, {self.destination.y()})'


class Drawer:
    """класс, который отвечает за отрисовку линий в окне"""

    def __init__(self):
        self._arrows = []

    @property
    def arrows(self):
        return self._arrows

    @arrows.setter
    def arrows(self, l):
        self._arrows = l[:]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QtGui.QPainter(self)
        for arrow in self.arrows:
            arrow.draw(self)
