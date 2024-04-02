# -*- coding: utf-8 -*-
import builtins
import inspect

from PyQt5 import QtCore, QtGui, QtWidgets


class BaseBlock(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()
    deleted = QtCore.pyqtSignal()
    merged_new_block = QtCore.pyqtSignal()

    """Родительский класс для блоков на схеме"""

    def __init__(self, parent, image: QtGui.QPixmap, minimum_width: int = 55, minimum_height: int = 35):
        super(BaseBlock, self).__init__(parent)
        self.parent = parent
        self.position = (0, 0)
        self.arg = ''
        self.child = None
        self.minimum_width = minimum_width
        self.minimum_height = minimum_height
        self.general_block: BaseBlock = None
        self.layer_up_block: BaseBlock = None
        self.layer_down_block: BaseBlock = None
        self.is_python_function = False
        self.is_general_block = False

        self.pixmap = QtGui.QPixmap(image)
        self.arg_label = QtWidgets.QLabel(self)
        self.arg_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.arg_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.arg_label)

        self.delete_action = QtWidgets.QAction('delete', self)
        self.set_arg_action = QtWidgets.QAction('set argument', self)
        self.set_connection_action = QtWidgets.QAction('connect', self)
        self.merge_block_action = QtWidgets.QAction('merge blocks', self)

        self.initUI()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(BaseBlock, self).paintEvent(a0)
        painter = QtGui.QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

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
        super(BaseBlock, self).mouseReleaseEvent(a0)
        self.clicked.emit()

    def set_argument(self):
        new_arg, ok = QtWidgets.QInputDialog.getText(self, "Enter the argument", "Argument:")
        if not ok:
            return
        self.arg = new_arg
        self.arg_label.setText(self.arg)
        self.resize_block()
        self.move_related_blocks()
        self.setFixedSize(self.width(), self.height() + 5)
        self.resize_block()

    def resize_block(self):
        if self.text_width > self.minimum_width:
            self.setFixedSize(self.text_width, self.height())
        else:
            self.setFixedSize(self.minimum_width, self.height())

        if self.text_height > self.minimum_height:
            self.setFixedSize(self.width(), self.text_height)
        else:
            self.setFixedSize(self.width(), self.minimum_height)

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
    def text_width(self) -> int:
        return self.arg_label.fontMetrics().boundingRect(self.arg_label.text()).width() + 28

    @property
    def text_height(self) -> int:
        return self.arg_label.fontMetrics().boundingRect(self.arg_label.text()).height() + 23

    def delete(self):
        self.deleteLater()
        self.deleted.emit()

        if self.layer_up_block is not None:
            self.layer_up_block.layer_down_block = None
            self.layer_up_block.resize_block()
            self.reduce_layer_up_blocks_height()
            self.highest_layer.move_related_blocks()
        if self.layer_down_block is not None:
            self.layer_down_block.delete()
        current_block = self.highest_layer.general_block
        while current_block is not None:
            current_block.delete_related_block(self)
            current_block.resize_block()
            current_block.move_related_blocks()
            current_block = current_block.highest_layer.general_block

    def delete_related_block(self, block):
        """удаляет связанный с general_block блок, используется для инкапсуляции удаления блоков,
         стоящих ниже general_block"""
        block.delete()

    def reduce_layer_up_blocks_height(self):
        """уменьшает высоту всех стоящих выше блоков"""
        current_block = self
        while current_block.layer_up_block is not None:
            if current_block.layer_up_block.is_general_block and current_block.layer_up_block.layer_depth == 0:
                current_block = current_block.layer_up_block
                continue
            current_block.layer_up_block.setFixedSize(
                current_block.layer_up_block.width(), current_block.layer_up_block.height() - 8
            )
            current_block = current_block.layer_up_block

    def merge_block(self):
        if self.layer_down_block:
            self.parent.status_bar.showMessage("Can't merge another one block")
            return
        self.merged_new_block.emit()
        self.resize_block()  # Здесь мы изменяем блок, к которому мерджили
        self.highest_layer.move_related_blocks()
        if self.highest_layer.general_block:
            current_block = self.highest_layer.general_block  # Здесь изменяем все обобщяющие (general) блоки
            while current_block is not None:
                current_block.resize_block()
                current_block.move_related_blocks()
                current_block = current_block.general_block
        if issubclass(self.highest_layer.__class__, BaseGeneralBlockWithAdditionalBlocks):
            self.highest_layer.move_related_blocks()
        self.highest_layer.resize_block()

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
            while 0 in closing_bracket_countdown:
                func += ')'
                closing_bracket_countdown.remove(0)
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
    

class BaseGeneralBlock(BaseBlock):
    added_new_line = QtCore.pyqtSignal()

    def __init__(self, parent, image: QtGui.QPixmap, minimum_width: int = 50, minimum_height: int = 33):
        super(BaseBlock, self).__init__(parent)
        self.add_line_action: QtWidgets.QAction = QtWidgets.QAction('add line', self)
        self._lines = []
        super(BaseGeneralBlock, self).__init__(parent, image, minimum_width, minimum_height)
        self.is_general_block = True

    @property
    def lines(self):
        result = []
        for block in self._lines:
            if issubclass(block.__class__, BaseGeneralBlockWithAdditionalBlocks):
                additional_blocks = []
                current_block = block
                while current_block is not None:
                    if current_block not in additional_blocks and current_block not in result:
                        additional_blocks.append(current_block)
                    current_block = current_block.layer_down_additional_block
                result.extend(additional_blocks)
            else:
                if block not in result:
                    result.append(block)
        return result

    @lines.setter
    def lines(self, value):
        self._lines.extend(value)

    def define_actions(self):
        super(BaseGeneralBlock, self).define_actions()
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
            added_height += 3 + block.height()
            if block.width() > maximum_block_width_in_lines:
                maximum_block_width_in_lines = block.width()
        maximum_block_width_in_lines += 15
        new_width = self.width()
        if maximum_block_width_in_lines > new_width:
            new_width = maximum_block_width_in_lines
        self.setFixedSize(new_width, self.height() + added_height)
        if self.general_block:
            self.general_block.resize_block()

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
            if block.is_general_block:
                block.move_related_blocks()

    def delete(self):
        super(BaseGeneralBlock, self).delete()
        if not self.lines:
            return
        for block in self.lines:
            block.delete()

    def delete_related_block(self, block: BaseBlock):
        if block not in self.lines:
            return
        try:
            self._lines.remove(block)
        except ValueError:
            pass
        self.resize_block()

    def get_full_self_func(self):
        if self.layer_down_block is None:
            return self.get_self_func()
        construct = ''
        closing_bracket_countdown = []
        current_block = self
        while current_block.layer_depth + 1 != 0:
            func = current_block.get_self_func()
            if current_block.is_python_function:
                func = func.replace(')', '')
                closing_bracket_countdown.append(current_block.layer_depth)
            while 0 in closing_bracket_countdown:
                func += ')'
                closing_bracket_countdown.remove(0)
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
            result.extend(list(map(lambda x: '\t' + x, block.get_func().split('\n'))))
        return '\n'.join(result)


class BaseGeneralBlockWithAdditionalBlocks(BaseGeneralBlock):
    added_additional_block = QtCore.pyqtSignal()

    def __init__(self, parent, image: QtGui.QPixmap, minimal_width: int = 50, minimal_height: int = 33):
        super(BaseBlock, self).__init__(parent)
        self.add_additional_block: QtWidgets.QAction = QtWidgets.QAction('add additional block', self)
        self.layer_up_additional_block: BaseGeneralBlockWithAdditionalBlocks = None
        self.layer_down_additional_block: BaseGeneralBlockWithAdditionalBlocks = None
        super(BaseGeneralBlockWithAdditionalBlocks, self).__init__(parent, image,
                                                                   minimum_width=minimal_width,
                                                                   minimum_height=minimal_height)

    def define_actions(self):
        super(BaseGeneralBlockWithAdditionalBlocks, self).define_actions()
        self.add_additional_block.triggered.connect(self.add_additional_block_method)
        self.added_additional_block.connect(lambda: self.parent.add_additional_block())

    def actions_menu(self) -> None:
        """создает контекстное меню блока"""
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.delete_action, self.set_connection_action, self.merge_block_action,
                         self.add_additional_block, self.add_line_action])
        menu.exec_(QtGui.QCursor.pos())

    def add_additional_block_method(self):
        self.added_additional_block.emit()
        self.move_related_blocks()
        self.resize_block()
        print(self.general_block.lines)

    def move_additional_blocks(self):
        current_block = self.highest_additional_block
        while current_block.layer_down_additional_block is not None:
            new_coords = QtCore.QPoint(current_block.x(), current_block.y() + current_block.height() + 1)
            current_block.layer_down_additional_block.move(new_coords)
            current_block = current_block.layer_down_additional_block

    def move_related_blocks(self):
        self.move_additional_blocks()
        current_block = self
        while current_block is not None:
            current_block.move_layer_down_block_to_parent()
            current_block.move_lines_to_general_block()
            current_block = current_block.layer_down_additional_block

    def delete(self):
        if self.general_block:
            print(self.general_block.lines)
        super(BaseGeneralBlockWithAdditionalBlocks, self).delete()

        if self.layer_up_additional_block is not None:
            if self.layer_down_additional_block:
                self.layer_down_additional_block.layer_up_additional_block = self.layer_up_additional_block
            else:
                self.layer_up_additional_block.layer_down_additional_block = None
        if self.layer_down_additional_block is not None:
            if self.layer_up_additional_block:
                self.layer_up_additional_block.layer_down_additional_block = self.layer_down_additional_block
            else:
                blocks_to_delete = []
                current_block = self.layer_down_additional_block
                while current_block is not None:
                    blocks_to_delete.append(current_block)
                    current_block = current_block.layer_down_additional_block

                for block in blocks_to_delete:
                    block.delete()
        self.highest_additional_block.move_related_blocks()
        if self.general_block:
            self.highest_general_block.resize_block()

    @property
    def additional_blocks_depth(self) -> int:
        depth = 0
        current_block = self
        while current_block.layer_down_additional_block is not None:
            depth += 1
            current_block = current_block.layer_down_additional_block
        return depth

    @property
    def highest_additional_block(self):
        current_block = self
        while current_block.layer_up_additional_block is not None:
            current_block = current_block.layer_up_additional_block
        return current_block

    @property
    def all_additional_blocks_classes(self) -> list:
        result = []
        current_block = self
        while current_block is not None:
            result.append(current_block.__class__)
            current_block = current_block.layer_down_additional_block
        return result

    def get_func(self) -> str:
        result = []
        result.append(self.get_full_self_func())
        result[-1] = result[-1] + ':'
        for block in self.lines:
            result.extend(list(map(lambda x: '\t' + x, block.get_func().split('\n'))))
        return '\n'.join(result)
