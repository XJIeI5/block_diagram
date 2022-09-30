import sys
from PyQt5 import QtWidgets, QtGui, QtCore


class MainWindow(object):
    """макет для основоного окна программы"""
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

        self.add_input_block_action = QtWidgets.QAction(QtGui.QIcon('input.png'), 'input', self)
        self.add_output_block_action = QtWidgets.QAction(QtGui.QIcon('output.png'), 'output', self)

        self.block_toolbar = QtWidgets.QToolBar('blocks', self)
        main_window.addToolBar(self.block_toolbar)
        self.block_toolbar.addAction(self.add_input_block_action)
        self.block_toolbar.addAction(self.add_output_block_action)


class Block(QtWidgets.QWidget):
    """Родительский класс для блоков на схеме"""
    def __init__(self, parent, image: QtGui.QPixmap):
        super(Block, self).__init__(parent)
        self.position = (0, 0)
        self.arg = ''
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setPixmap(image)

        self.delete_action = QtWidgets.QAction('delete', self)
        self.set_arg_action = QtWidgets.QAction('set argument', self)
        self.set_connection_action = QtWidgets.QAction('connect', self)

        self.initUI()

    def initUI(self) -> None:
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.actions_menu)
        self.setAcceptDrops(True)
        self.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() != QtCore.Qt.MouseButton.LeftButton:
            return

        mimeData = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())

        drag.exec_(QtCore.Qt.DropAction.MoveAction)  # drop action

    def actions_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.delete_action, self.set_arg_action, self.set_connection_action])
        menu.exec_(QtGui.QCursor.pos())


class InputBlock(Block):
    """блок, который ожидает ввода значения пользователем и передает его в переменную arg"""
    def __init__(self, parent):
        super(InputBlock, self).__init__(parent, QtGui.QPixmap('input.png'))


class OutputBlock(Block):
    """блок, который выводит переменную arg"""
    def __init__(self, parent):
        super(OutputBlock, self).__init__(parent, QtGui.QPixmap('output.png'))


class StartBlock(Block):
    """стартовый блок, обязательно должен быть в программе"""
    def __init__(self, parent):
        super(StartBlock, self).__init__(parent, QtGui.QPixmap('start.png'))

    def actions_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.set_connection_action)
        menu.exec_(QtGui.QCursor.pos())


class EndBlock(Block):
    """конечный блок, обязательно должен быть в программе"""
    def __init__(self, parent):
        super(EndBlock, self).__init__(parent, QtGui.QPixmap('end.png'))

    def actions_menu(self) -> None:
        pass


class Program(QtWidgets.QMainWindow, MainWindow):
    """основное окно"""
    def __init__(self):
        super(Program, self).__init__()

        self.blocks = []

        self.setAcceptDrops(True)
        self.setup(self)
        self.initUI()

    def initUI(self):
        self.add_input_block_action.triggered.connect(lambda: self.add_block(InputBlock))
        self.add_output_block_action.triggered.connect(lambda: self.add_block(OutputBlock))
        pass

    def add_block(self, block_type):
        """добавляет block_type в окно программы, block_type обязательно должен быть наследником Block"""
        if not issubclass(block_type.__class__, Block):
            return
        new_block = block_type(self)
        self.blocks.append(new_block)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        dropped_block = event.source()
        new_position = event.pos() - dropped_block.rect().center() * 0.5
        dropped_block.move(new_position)

        event.setDropAction(QtCore.Qt.DropAction.MoveAction)
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    program = Program()
    start = StartBlock(program)
    start.move(program.rect().center().x() - start.rect().width() // 2,
               0 + program.block_toolbar.rect().height() + program.menu_bar.rect().height())
    end = EndBlock(program)
    end.move(program.rect().center().x() - start.rect().width() // 2,
             program.rect().height() - program.block_toolbar.rect().height() - program.menu_bar.rect().height())
    program.show()
    sys.exit(app.exec())