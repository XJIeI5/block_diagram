import sys
from PyQt5 import QtWidgets
from program import Program

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    program = Program()

    program.show()
    sys.exit(app.exec())
