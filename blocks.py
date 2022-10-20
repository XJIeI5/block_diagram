# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets


class Block(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()

    """Родительский класс для блоков на схеме"""

    def __init__(self, parent, image: QtGui.QPixmap, minimum_width: int = 50):
        super(Block, self).__init__(parent)
        self.parent = parent
        self.position = (0, 0)
        self.arg = ''
        self.child = None
        self.minimum_width = minimum_width
        self.merged_blocks: Block = []

        self.pixmap = QtGui.QPixmap(image)
        self.arg_label = QtWidgets.QLabel(self)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.arg_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        self.delete_action = QtWidgets.QAction('delete', self)
        self.set_arg_action = QtWidgets.QAction('set argument', self)
        self.set_connection_action = QtWidgets.QAction('connect', self)

        self.initUI()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(Block, self).paintEvent(a0)
        painter = QtGui.QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)
        # painter.drawLine(self.rect().topLeft(), self.rect().bottomRight())
        # painter.drawLine(self.rect().bottomLeft(), self.rect().topRight())
        # painter.drawLine(self.arg_label.rect().topLeft(), self.arg_label.rect().bottomRight())
        # painter.drawLine(self.arg_label.rect().bottomLeft(), self.arg_label.rect().topRight())

    def initUI(self) -> None:
        self.setFixedSize(self.minimum_width, 30)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.actions_menu)
        self.set_connection_action.setData(self)
        self.setAcceptDrops(True)
        self.define_actions()
        self.show()

    def define_actions(self):
        """определяет слоты для действий. подразумевает, что parent обладает подходящими по сигнатуре методами"""
        self.installEventFilter(self.parent)
        self.set_connection_action.triggered.connect(self.parent.start_connection)
        self.set_arg_action.triggered.connect(self.set_argument)
        self.delete_action.triggered.connect(self.delete)
        self.clicked.connect(self.parent.end_connection)

    def set_child(self, child) -> None:
        """устанавливает следующий за этим блок"""
        self.child = child

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() != QtCore.Qt.MouseButton.LeftButton:
            return

        mimeData = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())

        drag.exec_(QtCore.Qt.DropAction.MoveAction)  # drop action

    def actions_menu(self) -> None:
        """создает контекстное меню блока"""
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.delete_action, self.set_arg_action, self.set_connection_action])
        menu.exec_(QtGui.QCursor.pos())

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        super(Block, self).mouseReleaseEvent(a0)
        self.clicked.emit()

    def set_argument(self):
        new_arg, ok = QtWidgets.QInputDialog.getText(self, "Enter the argument", "Argument:")
        if not ok:
            return
        self.arg = new_arg
        self.arg_label.setText(self.arg)
        text_width = self.arg_label.fontMetrics().boundingRect(self.arg_label.text()).width()
        if text_width * 2 >= self.minimum_width:
            self.setFixedSize(text_width + text_width, self.height())
        else:
            self.setFixedSize(self.minimum_width, self.height())

    @classmethod
    def is_overriding(cls, funcs_to_override: list):
        if cls == Block.__class__:
            return
        if not issubclass(cls, Block.__class__):
            return
        # if cls.get_func()

    def delete(self):
        pass

    def get_func(self) -> str:
        return ''


class InputBlock(Block):
    """блок, который ожидает ввода значения пользователем и передает его в переменную arg"""

    def __init__(self, parent):
        super(InputBlock, self).__init__(parent, QtGui.QPixmap('./pictures/input.png'))

    def get_func(self) -> str:
        return f'{self.arg} = input()'


class OutputBlock(Block):
    """блок, который выводит переменную arg"""

    def __init__(self, parent):
        super(OutputBlock, self).__init__(parent, QtGui.QPixmap('./pictures/output.png'))

    def get_func(self) -> str:
        return f'print({self.arg})'


class StartBlock(Block):
    """стартовый блок, обязательно должен быть в программе"""

    def __init__(self, parent):
        super(StartBlock, self).__init__(parent, QtGui.QPixmap('./pictures/start.png'))

    def actions_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.set_connection_action])
        menu.exec_(QtGui.QCursor.pos())

    def get_func(self) -> str:
        return ''


class EndBlock(Block):
    """конечный блок, обязательно должен быть в программе"""

    def __init__(self, parent):
        super(EndBlock, self).__init__(parent, QtGui.QPixmap('./pictures/end.png'))

    def actions_menu(self) -> None:
        pass

    def get_func(self) -> str:
        return ''


class OperationBlock(Block):
    """блок для проведения операций над переменными"""

    def __init__(self, parent):
        super(OperationBlock, self).__init__(parent, QtGui.QPixmap('./pictures/operation.png'))

    def get_func(self) -> str:
        return self.arg


class SetValueBlock(Block):
    """блок для установления значений переменным"""

    def __init__(self, parent, minimum_width: int = 30, color: QtGui.QColor = QtGui.QColor(0, 162, 232)):
        self.color = color
        self.minimum_width = minimum_width
        super(SetValueBlock, self).__init__(parent, QtGui.QPixmap)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setBrush(self.color)
        painter.drawRect(self.rect())

