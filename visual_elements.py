# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import math


def get_line_rect_intersection(line: QtCore.QLine, widget: QtWidgets.QWidget) -> QtCore.QPoint:
    x, y = 0, 0
    rect = widget.rect
    try:
        s = (line.y1() - line.y2()) / (line.x1() - line.x2())
    except ZeroDivisionError:
        s = 1

    if -rect().height() <= s * rect().width() <= rect().height():
        if line.x1() < line.x2():  # Right
            return get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().topLeft()),
                                                                 widget.mapToParent(rect().bottomLeft())))
        else:  # Left
            return get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().topRight()),
                                                                 widget.mapToParent(rect().bottomRight())))
    else:
        if line.y1() < line.y2():  # Up
            return get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().topLeft()),
                                                                 widget.mapToParent(rect().topRight())))
        else:  # Down
            return get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().bottomLeft()),
                                                                 widget.mapToParent(rect().bottomRight())))


def get_line_line_intersection(line1: QtCore.QLine, line2: QtCore.QLine) -> QtCore.QPoint:
    x1, y1, x2, y2 = line1.x1(), line1.y1(), line1.x2(), line1.y2()
    x3, y3, x4, y4 = line2.x1(), line2.y1(), line2.x2(), line2.y2()

    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    x_divisible = (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
    y_divisible = (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
    try:
        x = x_divisible / denominator
        y = y_divisible / denominator
    except ZeroDivisionError:
        return QtCore.QPoint(0, 0)
    return QtCore.QPoint(int(x), int(y))


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
            right_triangle.lineTo(-0.3 * math.sqrt(3) * l, 0.2 * l)
            right_triangle.lineTo(-0.3 * math.sqrt(3) * l, -0.2 * l)
            right_triangle.closeSubpath()
            right_triangle.translate(x_right)

            painter.setBrush(QtGui.QColor("black"))
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
