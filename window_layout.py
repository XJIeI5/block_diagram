from PyQt5 import QtWidgets, QtGui, QtCore


class MainWindow:
    """макет для основоного окна программы"""
    def __init__(self):
        super(MainWindow, self).__init__()

    def setup(self, main_window: QtWidgets.QMainWindow):
        main_window.setWindowTitle('test')
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