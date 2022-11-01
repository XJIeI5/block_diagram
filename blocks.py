# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import builtins
import inspect

import exceptions


class Block(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()
    deleted = QtCore.pyqtSignal()
    merged_new_block = QtCore.pyqtSignal()
    added_new_line = QtCore.pyqtSignal()

    """Родительский класс для блоков на схеме"""

    def __init__(self, parent, image: QtGui.QPixmap, minimum_width: int = 50, minimum_height: int = 33):
        super(Block, self).__init__(parent)
        self.parent = parent
        self.position = (0, 0)
        self.arg = ''
        self.child = None
        self.minimum_width = minimum_width
        self.minimum_height = minimum_height
        self.general_block: Block = None
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
        self.setFixedSize(self.minimum_width, self.minimum_height)
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
        self.deleted.connect(self.parent.delete_block)
        self.merged_new_block.connect(self.parent.merge_block)

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

    def move_related_blocks(self):
        self.move_layer_down_block_to_parent()

    def move_layer_down_block_to_parent(self):
        current_block = self.highest_layer
        for i in range(current_block.layer_depth + 1):
            new_position = current_block.highest_layer.mapToParent(current_block.highest_layer.rect().topRight())
            new_position += QtCore.QPoint(-3 * i - current_block.width(), 4 * i)
            current_block.move(new_position)
            current_block = current_block.layer_down_block

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
        if self.highest_layer.general_block:
            self.highest_layer.general_block.delete_related_block(self)
            self.highest_layer.general_block.resize_block()
            self.highest_layer.general_block.move_related_blocks()
        self.deleted.emit()

    def delete_related_block(self, block):
        """удаляет связанный с general_block блок, используется для инкапсуляции удаления блоков,
         стоящих ниже general_block"""
        block.delete()

    def reduce_layer_up_blocks_height(self):
        """уменьшает высоту всех стоящих выше блоков"""
        current_block = self
        while current_block.layer_up_block is not None:
            if issubclass(current_block.layer_up_block.__class__, BaseLoopBlock):
                continue
            current_block.layer_up_block.setFixedSize(
                current_block.layer_up_block.width(), current_block.layer_up_block.height() - 8
            )
            current_block = current_block.layer_up_block

    def delete_all_layer_down_blocks(self):
        blocks_to_delete = []

        current_block = self.layer_down_block
        for i in range(self.layer_depth):
            blocks_to_delete.append(current_block)
            current_block = current_block.layer_down_block

        for block in blocks_to_delete:
            block.delete()

    def merge_block(self):
        if self.layer_down_block:
            return
        self.merged_new_block.emit()
        self.resize_block()
        self.move_related_blocks()
        if not self.highest_layer.general_block:
            return
        self.highest_layer.general_block.resize_block()
        self.highest_layer.general_block.move_related_blocks()

    def get_self_func(self) -> str:
        return ''

    def get_func(self) -> str:
        result = self.get_self_func()
        if self.layer_down_block is None:
            return result
        construct = ''
        closing_bracket_countdown = []
        current_block = self
        while current_block.layer_depth + 1 != 0:
            func = current_block.get_self_func()
            if current_block.is_python_function:
                func = func.replace(')', '')
                closing_bracket_countdown.append(current_block.layer_depth)
            if 0 in closing_bracket_countdown:
                func += ')'
            if closing_bracket_countdown:
                closing_bracket_countdown = [i - 1 for i in closing_bracket_countdown]
            construct += func
            current_block = current_block.layer_down_block
            if current_block is None:
                break
        return construct

    @property
    def layer_depth(self) -> int:
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

    @property
    def highest_general_block(self):
        current_block = self
        while current_block.general_block is not None:
            current_block = current_block.general_block
        return current_block


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

    def get_self_func(self) -> str:
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

    def get_self_func(self) -> str:
        return self.arg + ' '


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

    def get_self_func(self) -> str:
        return ' ' + self.arg + ' '


class DataBlock(Block):
    """блок, который обозначает просто кусок данных, не присвоенных переменной"""

    def __init__(self, parent):
        super(DataBlock, self).__init__(parent, QtGui.QPixmap('./pictures/data.png'))
        self.data_type = None

    def set_argument(self):
        data_to_dialog = ['str', 'int', 'float', 'bool', 'lict', 'tuple', 'dict', 'set']
        data_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose data type', 'data type:', data_to_dialog)
        if ok:
            new_arg, ok2 = QtWidgets.QInputDialog.getText(self, 'Type data', 'data:')
            if ok2:
                self.data_type = data_type
                self.arg = new_arg
                self.arg_label.setText(self.arg)
                self.resize_block()

    def get_self_func(self) -> str:
        if self.data_type is not None:
            return self.data_type + '("' + self.arg + '")'


class FunctionBlock(Block):
    def __init__(self, parent):
        super(FunctionBlock, self).__init__(parent, QtGui.QPixmap('pictures/function.png'))
        self.is_python_function = True

    def set_argument(self):
        data_to_dialog = [name for name, function in sorted(vars(builtins).items())
                          if inspect.isbuiltin(function) or inspect.isfunction(function)]
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose function', 'function:', data_to_dialog)
        if ok:
            self.arg = new_arg + '()'
            self.arg_label.setText(self.arg)
            self.resize_block()

    def get_self_func(self) -> str:
        return self.arg


class DataTypeBlock(Block):
    def __init__(self, parent):
        super(DataTypeBlock, self).__init__(parent, QtGui.QPixmap('./pictures/output.png'))
        self.is_python_function = True

    def set_argument(self):
        data_to_dialog = ['str', 'int', 'float', 'bool', 'lict', 'tuple', 'dict', 'set']
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose data type', 'data type:', data_to_dialog)
        if ok:
            self.arg = new_arg + '()'
            self.arg_label.setText(self.arg)
            self.resize_block()


class LogicalBlock(Block):
    def __init__(self, parent):
        super(LogicalBlock, self).__init__(parent, QtGui.QPixmap('./pictures/operator.png'))

    def set_argument(self):
        data_to_dialog = ['==', '!=', '>', '<', '>=', '<=']
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose operator', 'operator:', data_to_dialog)
        if ok:
            self.arg = new_arg
            self.arg_label.setText(self.arg)
            self.resize_block()

    def get_self_func(self) -> str:
        return self.arg


class BaseLoopBlock(Block):
    def __init__(self, parent, image: QtGui.QPixmap,  minimum_width: int = 50, minimum_height: int = 33):
        super(Block, self).__init__(parent)
        self.add_line_action: QtWidgets.QAction = QtWidgets.QAction('add line', self)
        self.lines: list[Block] = []
        super(BaseLoopBlock, self).__init__(parent, image, minimum_width, minimum_height)

    def define_actions(self):
        super(BaseLoopBlock, self).define_actions()
        self.add_line_action.triggered.connect(self.add_line)
        self.added_new_line.connect(self.parent.add_line)

    def actions_menu(self) -> None:
        """создает контекстное меню блока"""
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.delete_action, self.set_arg_action, self.set_connection_action, self.merge_block_action,
                         self.add_line_action])
        menu.exec_(QtGui.QCursor.pos())

    def add_line(self):
        self.added_new_line.emit()
        self.resize_block()
        self.move_related_blocks()

    def resize_block_according_merged_block(self):
        if self.text_width > self.minimum_width:
            self.setFixedSize(self.text_width, self.height())
        else:
            self.setFixedSize(self.minimum_width, self.height())

        if self.layer_down_block is not None:
            self.setFixedSize(self.layer_down_block.width() + 18 + self.text_width, self.layer_down_block.height() + 8)

        if self.layer_up_block is not None:
            self.layer_up_block.resize_block()

    def resize_block(self):
        self.setFixedSize(self.minimum_width, self.minimum_height)
        self.resize_block_according_merged_block()
        added_height = 0
        maximum_block_width_in_lines = 0
        for block in self.lines:
            added_height += 3 + block.highest_layer.height()
            if block.highest_layer.width() > maximum_block_width_in_lines:
                maximum_block_width_in_lines = block.highest_layer.width()
        maximum_block_width_in_lines += 15
        new_width = self.width()
        if maximum_block_width_in_lines > new_width:
            new_width = maximum_block_width_in_lines
        self.setFixedSize(new_width, self.height() + added_height)

    def move_related_blocks(self):
        self.move_layer_down_block_to_parent()
        self.move_lines_to_general_block()

    def move_lines_to_general_block(self):
        if not self.lines:
            return
        previous_blocks_height = 0
        for block in reversed(self.lines):
            new_position = self.highest_layer.mapToParent(self.rect().bottomLeft())
            new_position += QtCore.QPoint(12, -4 - block.highest_layer.height() + previous_blocks_height)
            previous_blocks_height += -4 - block.highest_layer.height()
            block.move(new_position)
            block.move_layer_down_block_to_parent()

    def delete(self):
        super(BaseLoopBlock, self).delete()
        if not self.lines:
            return
        for block in self.lines:
            block.delete()

    def delete_related_block(self, block: Block):
        if block not in self.lines:
            return
        self.lines.remove(block)
        self.resize_block()

    def get_full_self_func(self):
        result = self.get_self_func()
        if self.layer_down_block is None:
            return result
        construct = ''
        closing_bracket_countdown = []
        current_block = self
        while current_block.layer_depth + 1 != 0:
            func = current_block.get_self_func()
            if current_block.is_python_function:
                func = func.replace(')', '')
                closing_bracket_countdown.append(current_block.layer_depth)
            if 0 in closing_bracket_countdown:
                func += ')'
            if closing_bracket_countdown:
                closing_bracket_countdown = [i - 1 for i in closing_bracket_countdown]
            construct += func
            current_block = current_block.layer_down_block
            if current_block is None:
                break
        return construct

    def get_func(self) -> str:
        result = [self.get_full_self_func()]
        result[0] = result[0] + ':'
        for block in self.lines:
            result.append('\t' + block.get_func())
        return '\n'.join(result)


class ForLoopBlock(BaseLoopBlock):
    def __init__(self, parent):
        super(ForLoopBlock, self).__init__(parent, QtGui.QPixmap('./pictures/for.png'), minimum_width=53)
        self.arg = 'for _ ' + 'in '
        self.arg_label.setText(self.arg)

    def set_argument(self):
        new_arg, ok = QtWidgets.QInputDialog.getText(self, "Enter the argument", "Argument:")
        if not ok:
            return
        self.arg = 'for ' + new_arg + ' in '
        self.arg_label.setText(self.arg)
        self.resize_block()
        self.move_layer_down_block_to_parent()

    def get_self_func(self) -> str:
        return self.arg


class WhileLoopBlock(BaseLoopBlock):
    def __init__(self, parent):
        super(WhileLoopBlock, self).__init__(parent, QtGui.QPixmap('./pictures/while.png'))
        self.arg = 'while '
        self.arg_label.setText(self.arg)

    def actions_menu(self) -> None:
        """создает контекстное меню блока"""
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.delete_action, self.set_connection_action, self.merge_block_action, self.add_line_action])
        menu.exec_(QtGui.QCursor.pos())

    def get_self_func(self) -> str:
        return self.arg
