from PyQt5 import QtCore, QtGui, QtWidgets


class Block(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()

    """Родительский класс для блоков на схеме"""
    def __init__(self, parent, image: QtGui.QPixmap):
        super(Block, self).__init__(parent)
        self.parent = parent
        self.position = (0, 0)
        self.arg = ''
        self.child = None

        self.pixmap_label = QtWidgets.QLabel(self, pixmap=image)
        self.pixmap_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.arg_label = QtWidgets.QLabel(self)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.pixmap_label) #, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.arg_label) #, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.delete_action = QtWidgets.QAction('delete', self)
        self.set_arg_action = QtWidgets.QAction('set argument', self)
        self.set_connection_action = QtWidgets.QAction('connect', self)

        self.initUI()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(Block, self).paintEvent(a0)
        painter = QtGui.QPainter(self)
        painter.drawLine(self.rect().topLeft(), self.rect().bottomRight())
        painter.drawLine(self.rect().bottomLeft(), self.rect().topRight())
        painter.drawLine(self.pixmap_label.rect().topLeft(), self.pixmap_label.rect().bottomRight())
        painter.drawLine(self.pixmap_label.rect().bottomLeft(), self.pixmap_label.rect().topRight())
        painter.drawLine(self.arg_label.rect().topLeft(), self.arg_label.rect().bottomRight())
        painter.drawLine(self.arg_label.rect().bottomLeft(), self.arg_label.rect().topRight())

    def initUI(self) -> None:
        self.setFixedSize(80, 45)
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
        self.set_arg_action.triggered.connect(lambda: self.set_argument('ttt'))
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

    def set_argument(self, arg):
        self.arg = arg
        self.arg_label.setText(self.arg)

    @classmethod
    def is_overriding(cls, funcs_to_override: list):
        if cls == Block.__class__:
            return
        if not issubclass(cls, Block.__class__):
            return
        # if cls.get_func()

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
