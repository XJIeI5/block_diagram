# -*- coding: utf-8 -*-
import sys
import traceback
from enum import Enum
from PyQt5 import QtWidgets, QtGui, QtCore
import blocks
import interpreter
import visual_elements
from exceptions import SequenceError
import save_diagram
import os


def excepthook(exc_type, exc_value, exc_tb):
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb)


class ProgramState(Enum):
    """состояния, в которых может находится программа"""
    PLACING = 1
    CONNECTING = 2


class MainWindow:
    """макет для основоного окна программы"""
    def __init__(self):
        super(MainWindow, self).__init__()

    def setup(self, main_window: QtWidgets.QMainWindow):
        main_window.setWindowTitle('Тест')
        main_window.setMinimumSize(800, 700)
        self.central_widget = QtWidgets.QWidget(main_window)
        self.central_widget.setObjectName("central_widget")
        main_window.setCentralWidget(self.central_widget)
        main_window.statusBar()


        self.menu_bar = QtWidgets.QMenuBar(main_window)
        self.menu_bar.setObjectName("menu_bar")
        main_window.setMenuBar(self.menu_bar)

        self.file_menu = self.menu_bar.addMenu('File')

        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("status_bar")
        main_window.setStatusBar(self.status_bar)

        self.add_function_block_action = QtWidgets.QAction(QtGui.QIcon('pictures/function.png'), 'function', self)
        self.add_variable_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/variable.png'), 'variable', self)
        self.add_for_loop_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/for.png'), 'for loop', self)
        self.add_while_loop_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/while.png'), 'while loop', self)
        self.add_if_block_action = QtWidgets.QAction(QtGui.QIcon('./pictures/if.png'), 'if block', self)
        self.execute_program_action = QtWidgets.QAction('Execute', self)
        self.save_file_action = QtWidgets.QAction('Save', self)
        self.save_file_action.setShortcut('Ctrl+S')
        self.save_as_file_action = QtWidgets.QAction('Save as', self)
        self.open_file_action = QtWidgets.QAction('Open', self)

        self.block_toolbar = QtWidgets.QToolBar('blocks', self)
        main_window.addToolBar(self.block_toolbar)
        self.block_toolbar.addAction(self.add_function_block_action)
        self.block_toolbar.addAction(self.add_variable_block_action)
        self.block_toolbar.addAction(self.add_for_loop_block_action)
        self.block_toolbar.addAction(self.add_while_loop_block_action)
        self.block_toolbar.addAction(self.add_if_block_action)
        self.menu_bar.addAction(self.execute_program_action)
        self.file_menu.addAction(self.save_file_action)
        self.file_menu.addAction(self.save_as_file_action)
        self.file_menu.addAction(self.open_file_action)


class Program(QtWidgets.QMainWindow, MainWindow, visual_elements.Drawer):
    """основное окно"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state: ProgramState = ProgramState.PLACING
        self.arrows: list[visual_elements.Arrow] = self.arrows
        self.connecting_parent = None
        self.connecting_child = None
        self.current_file = None
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

        self.add_function_block_action.triggered.connect(lambda: self.add_block(blocks.FunctionBlock))
        self.add_variable_block_action.triggered.connect(lambda: self.add_block(blocks.VariableBlock))
        self.add_for_loop_block_action.triggered.connect(lambda: self.add_block(blocks.ForLoopBlock))
        self.add_while_loop_block_action.triggered.connect(lambda: self.add_block(blocks.WhileLoopBlock))
        self.add_if_block_action.triggered.connect(lambda: self.add_block(blocks.IfBlock))
        self.execute_program_action.triggered.connect(self.execute_program)
        self.save_file_action.triggered.connect(self.save_file)
        self.save_as_file_action.triggered.connect(self.save_as_file)
        self.open_file_action.triggered.connect(self.open_file)

    def add_block(self, block_type: blocks.BaseBlock.__class__) -> blocks.BaseBlock:
        """добавляет block_type в окно программы, block_type обязательно должен быть наследником BaseBlock"""
        if not self.state == ProgramState.PLACING:
            return
        if not issubclass(block_type.__class__, blocks.BaseBlock.__class__):
            return
        new_block = block_type(self)
        self.blocks.append(new_block)
        return new_block

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        self.move_blocks(event.source(), event.pos())

        event.setDropAction(QtCore.Qt.DropAction.MoveAction)
        event.accept()

    def move_blocks(self, source_block: blocks.BaseBlock, mouse_pos: QtCore.QPoint):
        """перемещает центр блока и все зависимые от него блоки в позицию мыши"""
        current_block = source_block.highest_layer
        while current_block.general_block is not None:
            current_block = current_block.general_block
        if issubclass(current_block.__class__, blocks.BaseGeneralBlockWithAdditionalBlocks):
            current_block = current_block.highest_additional_block
        current_block.move(mouse_pos.x() - current_block.width() // 2, mouse_pos.y() - current_block.height() // 2)
        current_block.move_related_blocks()

    def recalculate_position(self) -> None:
        """пересчитывает позицию Arrow между блоками, между которыми установлена связь"""
        arrows = []
        for previous_block in self.blocks:
            if not previous_block.child:
                continue
            next_block = previous_block.child
            try:
                line = QtCore.QLine(previous_block.pos() + previous_block.rect().center(),
                                    next_block.pos() + next_block.rect().center())
                intersect_point = visual_elements.get_line_rect_intersection(line, next_block)
                new_arrow = visual_elements.Arrow(previous_block.pos() + previous_block.rect().center(), intersect_point)
                arrows.append(new_arrow)
            except RuntimeError:
                previous_block.child = None
                continue

            # arrows.append(arrowhead2)
        self.arrows = arrows

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
        self.connecting_parent = self.sender().data().highest_layer.highest_general_block
        if issubclass(self.sender().data().highest_layer.highest_general_block.__class__,
                      blocks.BaseGeneralBlockWithAdditionalBlocks):
            self.connecting_parent = self.sender().data().highest_layer.highest_general_block.highest_additional_block

    def end_connection(self):
        """заканчивает строить connection"""
        if not self.state == ProgramState.CONNECTING:
            self.change_state(ProgramState.PLACING)
            return
        self.connecting_parent.child = self.sender().highest_layer.highest_general_block
        if issubclass(self.sender().highest_layer.highest_general_block.__class__,
                      blocks.BaseGeneralBlockWithAdditionalBlocks):
            self.connecting_parent.child = self.sender().highest_layer.highest_general_block.highest_additional_block
        self.connecting_parent = None
        self.change_state(ProgramState.PLACING)
        self.recalculate_position()

    def execute_program(self):
        """запускает выполнение составленной программы в консоли"""
        self.change_state(ProgramState.EXECUTING)
        try:
            self.interpreter.execute(self.blocks)
        except ValueError as error:
            self.status_bar.showMessage(repr(error))
        except SequenceError as error:
            self.status_bar.showMessage(repr(error))
        self.change_state(ProgramState.PLACING)

    def delete_block(self):
        """подчищает зависимости блка, который вызвал этот метод"""
        sender_block: blocks.BaseBlock = self.sender()
        self.delete_from_blocks(sender_block)
        if sender_block.layer_down_block is not None:
            current_block = sender_block.layer_down_block
            for i in range(sender_block.layer_depth):
                self.delete_from_blocks(current_block)
                current_block = current_block.layer_down_block
        if sender_block.layer_up_block is not None:
            sender_block.layer_up_block.layer_down_block = None
        self.recalculate_position()

    def delete_from_blocks(self, block_to_delete: blocks.BaseBlock):
        """удаляет блок из списка блоков"""
        try:
            index = self.blocks.index(block_to_delete)
        except ValueError:
            return
        for block in self.blocks:
            if block.child == self.blocks[index]:
                block.child = None
        del self.blocks[index]

    def merge_block(self):
        """обеспечивает интерфейс для выбора блока для мержда, устанавливает зависимости"""
        parent_block: blocks.BaseBlock = self.sender()
        items_data = {'Method Block': blocks.MethodBlock, 'Variable Block': blocks.VariableBlock,
                      'Operator Block': blocks.OperatorBlock, 'Data Block': blocks.DataBlock,
                      'Logical Block': blocks.LogicalBlock, 'Function Block': blocks.FunctionBlock,
                      'Data Type Block': blocks.DataTypeBlock}
        block_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose block type', 'block type:', items_data.keys())
        if ok:
            new_block = self.add_block(items_data[block_type])

            parent_block.layer_down_block = new_block
            new_block.layer_up_block = parent_block

    def add_line(self):
        """обеспечивает интерфейс для выбора блока для добавления к многострочной кострукции, устанавливает
         зависимости"""
        parent_block: blocks.BaseGeneralBlock = self.sender()
        items_data = {"Functional Block": blocks.FunctionBlock, "If Block": blocks.IfBlock,
                      "Variable Block": blocks.VariableBlock, "For Loop Block": blocks.ForLoopBlock,
                      "While Loop Block": blocks.WhileLoopBlock}
        block_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose block type', 'block type:', items_data.keys())
        if ok:
            new_block = self.add_block(items_data[block_type])
            parent_block.lines.append(new_block)
            new_block.general_block = parent_block

    def add_additional_block(self):
        """обеспечивает интерфейс для выобора дополнительной многострочной конструкции, устанавливает зависимости"""
        parent_block: blocks.BaseGeneralBlockWithAdditionalBlocks = self.sender()
        items_data = {"Else BaseBlock": blocks.ElseBlock, "Elif Block": blocks.ElifBlock}
        block_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose block type', 'block type:', items_data.keys())
        if ok:
            new_block: blocks.BaseGeneralBlockWithAdditionalBlocks = self.add_block(items_data[block_type])
            if parent_block.layer_down_additional_block is None:
                parent_block.layer_down_additional_block = new_block
                new_block.layer_up_additional_block = parent_block
            else:
                new_layer_up_block, new_layer_down_block = parent_block, parent_block.layer_down_additional_block
                new_layer_up_block.layer_down_additional_block = new_block
                new_block.layer_up_additional_block = new_layer_up_block
                new_block.layer_down_additional_block = new_layer_down_block
                new_layer_down_block.layer_up_additional_block = new_block

    def save_file(self):
        """обеспечивает интерфейс для выбора директории для сохранения файла и его имени в случае, если никакой файл
         открыт не был"""
        if self.current_file and os.path.exists(self.current_file):
            save_diagram.fill_data_base(self.current_file, self.blocks)
        else:
            self.save_as_file()

    def save_as_file(self):
        """обеспечивает интерфейс для выбора директории для сохранения файла"""
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '.', filter='*.sqlite')[0]
        if file_name:
            save_diagram.fill_data_base(file_name, self.blocks)
            self.current_file = file_name

    def open_file(self):
        """обеспечивает интерфейс для выбора загружаемого файла"""
        clone_blocks = self.blocks.copy()
        for block in clone_blocks:
            block.delete()
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Save File', '.', filter='*.sqlite')[0]
        if file_name:
            opened_blocks = save_diagram.load_data_base(file_name, self)
            self.blocks = opened_blocks.copy()
            for block in self.blocks:
                block.resize_block()
                block.move_related_blocks()
            self.current_file = file_name


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    program = Program()

    program.show()
    sys.exit(app.exec())
