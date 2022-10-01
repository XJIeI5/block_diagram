# -*- coding: utf-8 -*-
import sys
from enum import Enum
from PyQt5 import QtWidgets, QtGui, QtCore


class ProgramState(Enum):
    """состояния, в которых может находится программа"""
    PLACING = 1
    CONNECTING = 2


class Drawer:
    """класс, который отвечает за отрисовку линий в окне"""
    def __init__(self):
        self._lines = []

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, l):
        self._lines = l[:]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QtGui.QPainter(self)
        for line in self.lines:
            painter.drawLine(line)


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

        self.block_toolbar = QtWidgets.QToolBar('blocks', self)
        main_window.addToolBar(self.block_toolbar)
        self.block_toolbar.addAction(self.add_input_block_action)
        self.block_toolbar.addAction(self.add_output_block_action)


class Block(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()

    """Родительский класс для блоков на схеме"""
    def __init__(self, parent, image: QtGui.QPixmap):
        super(Block, self).__init__(parent)
        self.position = (0, 0)
        self.arg = ''
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setPixmap(image)
        self.child = None

        self.delete_action = QtWidgets.QAction('delete', self)
        self.set_arg_action = QtWidgets.QAction('set argument', self)
        self.set_connection_action = QtWidgets.QAction('connect', self)

        self.initUI()

    def initUI(self) -> None:
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.actions_menu)
        self.set_connection_action.setData(self)
        self.setAcceptDrops(True)
        self.show()

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


class InputBlock(Block):
    """блок, который ожидает ввода значения пользователем и передает его в переменную arg"""
    def __init__(self, parent):
        super(InputBlock, self).__init__(parent, QtGui.QPixmap('./pictures/input.png'))


class OutputBlock(Block):
    """блок, который выводит переменную arg"""
    def __init__(self, parent):
        super(OutputBlock, self).__init__(parent, QtGui.QPixmap('./pictures/output.png'))


class StartBlock(Block):
    """стартовый блок, обязательно должен быть в программе"""
    def __init__(self, parent):
        super(StartBlock, self).__init__(parent, QtGui.QPixmap('./pictures/start.png'))

    def actions_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.set_connection_action])
        menu.exec_(QtGui.QCursor.pos())


class EndBlock(Block):
    """конечный блок, обязательно должен быть в программе"""
    def __init__(self, parent):
        super(EndBlock, self).__init__(parent, QtGui.QPixmap('./pictures/end.png'))

    def actions_menu(self) -> None:
        pass


class Program(QtWidgets.QMainWindow, MainWindow, Drawer):
    """основное окно"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state: ProgramState = ProgramState.PLACING
        self.lines: list[QtCore.QLine] = self.lines
        self.connecting_parent = None
        self.connecting_child = None

        self.blocks = []

        self.setAcceptDrops(True)
        self.setup(self)
        self.initUI()

    def initUI(self) -> None:
        self.add_input_block_action.triggered.connect(lambda: self.add_block(InputBlock))
        self.add_output_block_action.triggered.connect(lambda: self.add_block(OutputBlock))

    def add_block(self, block_type) -> None:
        """добавляет block_type в окно программы, block_type обязательно должен быть наследником Block"""
        if not self.state == ProgramState.PLACING:
            return
        if not issubclass(block_type.__class__, Block.__class__):
            return
        new_block = block_type(self)
        new_block.installEventFilter(self)
        new_block.set_connection_action.triggered.connect(lambda: self.start_connection())
        new_block.clicked.connect(self.end_connection)
        self.blocks.append(new_block)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if not self.state == ProgramState.CONNECTING:
            return

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        dropped_block = event.source()
        new_position = event.pos() - dropped_block.rect().center() * 0.5
        dropped_block.move(new_position)

        event.setDropAction(QtCore.Qt.DropAction.MoveAction)
        event.accept()
    
    def recalculate_position(self) -> None:
        """пересчитывает позицию QLine между блоками, между которыми установлена связь"""
        lines = []
        for previous_block in self.blocks:
            if not previous_block.child:
                continue
            next_block = previous_block.child
            line = QtCore.QLine(previous_block.pos() + previous_block.rect().center() * 0.5,
                                next_block.pos() + next_block.rect().center() * 0.5)
            lines.append(line)
        self.lines = lines

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
        self.connecting_parent = self.sender().data()

    def end_connection(self):
        """заканчивает строить connection"""
        if not self.state == ProgramState.CONNECTING:
            self.change_state(ProgramState.PLACING)
            return
        self.connecting_parent.child = self.sender()
        self.connecting_parent = None
        self.change_state(ProgramState.PLACING)
        self.recalculate_position()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    program = Program()

    start = StartBlock(program)
    start.move(program.rect().center().x() - start.rect().width() // 2,
               0 + program.block_toolbar.rect().height() + program.menu_bar.rect().height())
    start.installEventFilter(program)
    start.set_connection_action.triggered.connect(lambda: program.start_connection())
    start.clicked.connect(program.end_connection)
    program.blocks.append(start)

    end = EndBlock(program)
    end.move(program.rect().center().x() - start.rect().width() // 2,
             program.rect().height() - program.block_toolbar.rect().height() - program.menu_bar.rect().height())
    end.installEventFilter(program)
    end.clicked.connect(program.end_connection)
    program.blocks.append(end)

    program.show()
    sys.exit(app.exec())