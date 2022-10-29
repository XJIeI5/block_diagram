# -*- coding: utf-8 -*-
import sys
import traceback
from enum import Enum
from PyQt5 import QtWidgets, QtGui, QtCore
import blocks
import interpreter
import visual_elements
from exceptions import SequenceError


def excepthook(exc_type, exc_value, exc_tb):
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb)


class ProgramState(Enum):
    """состояния, в которых может находится программа"""
    PLACING = 1
    CONNECTING = 2
    EXECUTING = 3


class MainWindow:
    """макет для основоного окна программы"""
    def __init__(self):
        super(MainWindow, self).__init__()

    def setup(self, main_window: QtWidgets.QMainWindow):
        main_window.setWindowTitle('Тест')
        main_window.setFixedSize(500, 500)
        self.central_widget = QtWidgets.QWidget(main_window)
        self.central_widget.setObjectName("central_widget")
        main_window.setCentralWidget(self.central_widget)

        self.menu_bar = QtWidgets.QMenuBar(main_window)
        self.menu_bar.setObjectName("menu_bar")
        main_window.setMenuBar(self.menu_bar)

        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("status_bar")
        main_window.setStatusBar(self.status_bar)

        self.add_input_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/input.png'), 'input', self)
        self.add_output_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/output.png'), 'output', self)
        self.add_variable_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/variable.png'), 'variable', self)
        self.execute_program_action = QtWidgets.QAction('execute', self)

        self.block_toolbar = QtWidgets.QToolBar('blocks', self)
        main_window.addToolBar(self.block_toolbar)
        self.block_toolbar.addAction(self.add_input_block_action)
        self.block_toolbar.addAction(self.add_output_block_action)
        self.block_toolbar.addAction(self.add_variable_block_action)
        self.block_toolbar.addAction(self.execute_program_action)


class Program(QtWidgets.QMainWindow, MainWindow, visual_elements.Drawer):
    """основное окно"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state: ProgramState = ProgramState.PLACING
        self.arrows: list[visual_elements.Arrow] = self.arrows
        self.connecting_parent = None
        self.connecting_child = None
        self.interpreter = interpreter.Interpreter()

        self.blocks = []

        self.setAcceptDrops(True)
        self.setup(self)
        self.initUI()

    def initUI(self) -> None:
        start = blocks.StartBlock(self)
        start.move(self.rect().center().x() - start.rect().width() // 2,
                   0 + self.block_toolbar.rect().height() + self.menu_bar.rect().height())
        self.blocks.append(start)

        end = blocks.EndBlock(self)
        end.move(self.rect().center().x() - start.rect().width() // 2,
                 self.rect().height() - self.block_toolbar.rect().height() - self.menu_bar.rect().height())
        self.blocks.append(end)

        self.add_input_block_action.triggered.connect(lambda: self.add_block(blocks.InputBlock))
        self.add_output_block_action.triggered.connect(lambda: self.add_block(blocks.OutputBlock))
        self.add_variable_block_action.triggered.connect(lambda: self.add_block(blocks.VariableBlock))
        self.execute_program_action.triggered.connect(self.execute_program)

    def add_block(self, block_type: blocks.Block) -> blocks.Block:
        """добавляет block_type в окно программы, block_type обязательно должен быть наследником Block"""
        if not self.state == ProgramState.PLACING:
            return
        if not issubclass(block_type.__class__, blocks.Block.__class__):
            return
        new_block = block_type(self)
        new_block.deleted.connect(self.delete_block)
        new_block.merged_new_block.connect(self.merge_block)
        self.blocks.insert(-1, new_block)
        return new_block

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if not self.state == ProgramState.CONNECTING:
            return

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        self.move_blocks(event.source(), event.pos())

        event.setDropAction(QtCore.Qt.DropAction.MoveAction)
        event.accept()

    def move_blocks(self, source_block: blocks.Block, mouse_pos: QtCore.QPoint):
        current_block = source_block.highest_layer
        for i in range(source_block.highest_layer.depth + 1):
            if current_block.layer_up_block is None:
                new_position = mouse_pos - current_block.rect().center()
            else:
                # Заменить на current_block.move_layer_down_block_to_parent()
                new_position = current_block.highest_layer.mapToParent(current_block.highest_layer.rect().topRight())
                new_position += QtCore.QPoint(-3 * i - current_block.width(), 4 * i)
            current_block.move(new_position)
            current_block = current_block.layer_down_block

    def recalculate_position(self) -> None:
        """пересчитывает позицию QLine между блоками, между которыми установлена связь"""
        arrows = []
        for previous_block in self.blocks:
            if not previous_block.child:
                continue
            next_block = previous_block.child
            try:
                line = QtCore.QLine(previous_block.pos() + previous_block.rect().center(),
                                    next_block.pos() + next_block.rect().center())
                intersect_point = self.get_line_rect_intersection(line, next_block)
                new_arrow = visual_elements.Arrow(previous_block.pos() + previous_block.rect().center(), intersect_point)
                arrows.append(new_arrow)
            except RuntimeError:
                previous_block.child = None
                continue

            # arrows.append(arrowhead2)
        self.arrows = arrows

    def get_line_rect_intersection(self, line: QtCore.QLine, widget: QtWidgets.QWidget) -> QtCore.QPoint:
        x, y = 0, 0
        rect = widget.rect
        try:
            s = (line.y1() - line.y2()) / (line.x1() - line.x2())
        except ZeroDivisionError:
            s = 1

        if -rect().height() <= s * rect().width() / 2 <= rect().height() / 2:
            if line.x1() < line.x2():  # Right
                return self.get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().topLeft()),
                                                                          widget.mapToParent(rect().bottomLeft())))
            else:  # Left
                return self.get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().topRight()),
                                                                          widget.mapToParent(rect().bottomRight())))
        else:
            if line.y1() < line.y2():  # Up
                return self.get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().topLeft()),
                                                                          widget.mapToParent(rect().topRight())))
            else:  # Down
                return self.get_line_line_intersection(line, QtCore.QLine(widget.mapToParent(rect().bottomLeft()),
                                                                          widget.mapToParent(rect().bottomRight())))

    def get_line_line_intersection(self, line1: QtCore.QLine, line2: QtCore.QLine) -> QtCore.QPoint:
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

    def eventFilter(self, a0: QtCore.QObject, a1: QtCore.QEvent) -> bool:
        if a1.type() == QtCore.QEvent.Move and a0 in self.blocks:
            self.recalculate_position()
        return super(Program, self).eventFilter(a0, a1)

    def change_state(self, new_state: ProgramState) -> None:
        """меняет текущее состояние программы"""
        self.state = new_state

    def start_connection(self):
        """начинает строить connection"""
        self.change_state(ProgramState.CONNECTING)
        self.connecting_parent = self.sender().data().highest_layer

    def end_connection(self):
        """заканчивает строить connection"""
        if not self.state == ProgramState.CONNECTING:
            self.change_state(ProgramState.PLACING)
            return
        self.connecting_parent.child = self.sender().highest_layer
        self.connecting_parent = None
        self.change_state(ProgramState.PLACING)
        self.recalculate_position()

    def execute_program(self):
        self.change_state(ProgramState.EXECUTING)
        try:
            self.interpreter.execute(self.blocks)
        except ValueError as error:
            self.status_bar.showMessage(repr(error))
        except SequenceError as error:
            self.status_bar.showMessage(repr(error))
        self.change_state(ProgramState.PLACING)

    def delete_block(self):
        sender_block: blocks.Block = self.sender()
        self.delete_from_blocks(sender_block)
        if sender_block.layer_down_block is not None:
            current_block = sender_block.layer_down_block
            for i in range(sender_block.depth):
                self.delete_from_blocks(current_block)
                current_block = current_block.layer_down_block
        if sender_block.layer_up_block is not None:
            sender_block.layer_up_block.layer_down_block = None
        self.recalculate_position()

    def delete_from_blocks(self, block_to_delete: blocks.Block):
        index = self.blocks.index(block_to_delete)
        if self.blocks[index - 1].child == self.sender():
            self.blocks[index - 1].child = None
        del self.blocks[index]

    def merge_block(self):
        parent_block: blocks.Block = self.sender()
        items_data = {'Method Block': blocks.MethodBlock, 'Variable Block': blocks.VariableBlock,
                      'Operator Block': blocks.OperatorBlock, 'Data Block': blocks.DataBlock}
        block_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose block type', 'block type:', items_data.keys())
        if ok:
            new_block = self.add_block(items_data[block_type])

            parent_block.layer_down_block = new_block
            new_block.layer_up_block = parent_block


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    program = Program()

    program.show()
    sys.exit(app.exec())
