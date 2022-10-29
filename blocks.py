# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets


class Block(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()
    deleted = QtCore.pyqtSignal()
    merged_new_block = QtCore.pyqtSignal()

    """Родительский класс для блоков на схеме"""

    def __init__(self, parent, image: QtGui.QPixmap, minimum_width: int = 50):
        super(Block, self).__init__(parent)
        self.parent = parent
        self.position = (0, 0)
        self.arg = ''
        self.child = None
        self.minimum_width = minimum_width
        self.layer_up_block: Block = None
        self.layer_down_block: Block = None
        self.is_python_function = False

        self.pixmap = QtGui.QPixmap(image)
        self.arg_label = QtWidgets.QLabel(self, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.arg_label)

        self.delete_action = QtWidgets.QAction('delete', self)
        self.set_arg_action = QtWidgets.QAction('set argument', self)
        self.set_connection_action = QtWidgets.QAction('connect', self)
        self.merge_block_action = QtWidgets.QAction('merge blocks', self)

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
        self.setFixedSize(self.minimum_width, 33)
        self.pixmap.scaled(self.width(), self.height())
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
        self.merge_block_action.triggered.connect(self.merge_block)
        self.clicked.connect(self.parent.end_connection)

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
        menu.addActions([self.delete_action, self.set_arg_action, self.set_connection_action, self.merge_block_action])
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
        self.resize_block()
        self.move_layer_down_block_to_parent()

    def resize_block(self):
        if self.text_width > self.minimum_width:
            self.setFixedSize(self.text_width, self.height())
        else:
            self.setFixedSize(self.minimum_width, self.height())

        if self.layer_down_block is not None:
            self.setFixedSize(self.layer_down_block.width() + 18 + self.text_width, self.layer_down_block.height() + 8)

        if self.layer_up_block is not None:
            self.layer_up_block.resize_block()

    def move_layer_down_block_to_parent(self):
        if self.layer_down_block is None:
            return
        new_position = self.highest_layer.mapToParent(self.highest_layer.rect().topRight())
        new_position += QtCore.QPoint(-3 * self.highest_layer.depth - self.layer_down_block.width(),
                                      4 * self.highest_layer.depth)
        self.layer_down_block.move(new_position)

    @property
    def text_width(self) -> float:
        return self.arg_label.fontMetrics().boundingRect(self.arg_label.text()).width() + 18

    @classmethod
    def is_overriding(cls, funcs_to_override: list):
        if cls == Block.__class__:
            return
        if not issubclass(cls, Block.__class__):
            return
        # if cls.get_func()

    def delete(self):
        self.deleteLater()

        if self.layer_up_block is not None:
            self.layer_up_block.layer_down_block = None
            self.layer_up_block.resize_block()
            self.reduce_layer_up_blocks_height()
        if self.layer_down_block is not None:
            self.delete_all_layer_down_blocks()
        self.deleted.emit()

    def reduce_layer_up_blocks_height(self):
        current_block = self
        while current_block.layer_up_block is not None:
            current_block.layer_up_block.setFixedSize(
                current_block.layer_up_block.width(), current_block.layer_up_block.height() - 8
            )
            current_block = current_block.layer_up_block

    def delete_all_layer_down_blocks(self):
        blocks_to_delete = []

        current_block = self.layer_down_block
        for i in range(self.depth):
            blocks_to_delete.append(current_block)
            current_block = current_block.layer_down_block

        for block in blocks_to_delete:
            block.delete()

    def merge_block(self):
        self.merged_new_block.emit()
        self.resize_block()
        self.move_layer_down_block_to_parent()

    def get_func(self) -> str:
        return ''

    @property
    def depth(self) -> int:
        depth = 0
        current_block = self
        while current_block.layer_down_block is not None:
            depth += 1
            current_block = current_block.layer_down_block
        return depth

    @property
    def highest_layer(self):
        current_block = self
        while current_block.layer_up_block is not None:
            current_block = current_block.layer_up_block
        return current_block


class InputBlock(Block):
    """блок, который ожидает ввода значения пользователем и передает его в переменную arg"""

    def __init__(self, parent):
        super(InputBlock, self).__init__(parent, QtGui.QPixmap('./pictures/input.png'))
        self.is_python_function = True

    def get_func(self) -> str:
        if self.arg:
            return f'{self.arg} = input()'
        return 'input()'


class OutputBlock(Block):
    """блок, который выводит переменную arg"""

    def __init__(self, parent):
        super(OutputBlock, self).__init__(parent, QtGui.QPixmap('./pictures/output.png'))
        self.is_python_function = True

    def get_func(self) -> str:
        if self.arg:
            return f'print("{self.arg}")'
        return 'print()'


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


class MethodBlock(Block):
    """блок для проведения операций над переменными"""

    def __init__(self, parent):
        super(MethodBlock, self).__init__(parent, QtGui.QPixmap('pictures/method.png'))
        self.is_python_function = True

    def get_func(self) -> str:
        return self.arg

    def set_argument(self):
        data_to_dialog = {'str': tuple(dir(str)), 'list': tuple(dir(list)),
                          'dict': tuple(dir(dict)), 'set': tuple(dir(set))}
        method_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose method', 'method type:',
                                                         data_to_dialog.keys())
        if ok:
            new_arg, ok2 = QtWidgets.QInputDialog.getItem(self, 'Choose method', 'method name:',
                                                          reversed(data_to_dialog[method_type]))
            self.arg = "." + new_arg + "()"
            self.arg_label.setText(self.arg)
            self.resize_block()


class VariableBlock(Block):
    """блок, который обозначает переменную"""

    def __init__(self, parent):
        super(VariableBlock, self).__init__(parent, QtGui.QPixmap('./pictures/variable.png'))

    def get_func(self) -> str:
        return self.arg


class OperatorBlock(Block):
    """блок, который обозначает действия над данными"""
    
    def __init__(self, parent):
        super(OperatorBlock, self).__init__(parent, QtGui.QPixmap('./pictures/operator.png'))

    def set_argument(self):
        data_to_dialog = ['+', '-', '*', '/', '//', '%', '**']
        data_to_dialog.extend(['='] + [i + '=' for i in data_to_dialog])
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose operator', 'operator:', data_to_dialog)
        if ok:
            self.arg = new_arg
            self.arg_label.setText(self.arg)
            self.resize_block()

    def get_func(self) -> str:
        return ' ' + self.arg + ' '


class DataBlock(Block):
    """блок, который обозначает просто кусок данных, не присвоенных переменной"""

    def __init__(self, parent):
        super(DataBlock, self).__init__(parent, QtGui.QPixmap('./pictures/data.png'))

    def get_func(self) -> str:
        return self.arg
