import builtins
import inspect


from PyQt5 import QtCore, QtGui, QtWidgets
from base_block import BaseBlock, BaseGeneralBlock, BaseGeneralBlockWithAdditionalBlocks

class StartBlock(BaseBlock):
    """стартовый блок, обязательно должен быть в программе"""

    def __init__(self, parent):
        super(StartBlock, self).__init__(parent, QtGui.QPixmap('./pictures/start.png'))

    def actions_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.set_connection_action])
        menu.exec_(QtGui.QCursor.pos())

    def get_func(self) -> str:
        return ''


class EndBlock(BaseBlock):
    """конечный блок, обязательно должен быть в программе"""

    def __init__(self, parent):
        super(EndBlock, self).__init__(parent, QtGui.QPixmap('./pictures/end.png'))

    def actions_menu(self) -> None:
        pass

    def get_func(self) -> str:
        return ''


class MethodBlock(BaseBlock):
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
            try:
                new_arg, ok2 = QtWidgets.QInputDialog.getItem(self, 'Choose method', 'method name:',
                                                              reversed(data_to_dialog[method_type]))
                self.arg = "." + new_arg + "()"
                self.arg_label.setText(self.arg)
                self.resize_block()
                self.move_related_blocks()
            except KeyError:
                self.parent.status_bar.showMessage('Incorrect Block type')


class VariableBlock(BaseBlock):
    """блок, который обозначает переменную"""

    def __init__(self, parent):
        super(VariableBlock, self).__init__(parent, QtGui.QPixmap('./pictures/variable.png'))

    def get_self_func(self) -> str:
        return self.arg + ' '


class OperatorBlock(BaseBlock):
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
            self.move_related_blocks()

    def get_self_func(self) -> str:
        return ' ' + self.arg + ' '


class DataBlock(BaseBlock):
    """блок, который обозначает просто кусок данных, не присвоенных переменной"""

    def __init__(self, parent):
        super(DataBlock, self).__init__(parent, QtGui.QPixmap('./pictures/data.png'))
        self.data_type = None

    def set_argument(self):
        data_to_dialog = ['str', 'int', 'float', 'bool', 'lict', 'tuple', 'dict', 'set']
        data_type, ok = QtWidgets.QInputDialog.getItem(self, 'Choose data type', 'data type:', data_to_dialog)
        if ok:
            if data_type not in data_to_dialog:
                self.parent.status_ber.showMessage('Incorrect Block type')
                return
            new_arg, ok2 = QtWidgets.QInputDialog.getText(self, 'Type data', 'data:')
            if ok2:
                self.data_type = data_type
                self.arg = new_arg
                self.arg_label.setText(self.arg)
                self.resize_block()
                self.move_related_blocks()

    def get_self_func(self) -> str:
        if self.data_type is not None:
            return self.data_type + '("' + self.arg + '")'
        return ''


class FunctionBlock(BaseBlock):
    def __init__(self, parent):
        super(FunctionBlock, self).__init__(parent, QtGui.QPixmap('pictures/function.png'))
        self.is_python_function = True

    def set_argument(self):
        data_to_dialog = [name for name, func in sorted(vars(builtins).items())
                          if ('attr' not in name and 'is' not in name and '__' not in name) and
                          inspect.isbuiltin(func) or inspect.isfunction(func)]
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose function', 'function:', data_to_dialog)
        if ok:
            if new_arg not in data_to_dialog:
                self.parent.status_bar.showMessage('Incorrect Block type')
                return
            self.arg = new_arg + '()'
            self.arg_label.setText(self.arg)
            self.resize_block()
            self.move_related_blocks()

    def get_self_func(self) -> str:
        return self.arg


class DataTypeBlock(BaseBlock):
    def __init__(self, parent):
        super(DataTypeBlock, self).__init__(parent, QtGui.QPixmap('./pictures/output.png'))
        self.is_python_function = True

    def set_argument(self):
        data_to_dialog = ['bool', 'bytearray', 'bytes', 'classmethod', 'complex', 'dict', 'enumerate', 'float',
                          'frozenset', 'int', 'list', 'memoryview', 'object', 'property', 'range', 'reversed',
                          'set', 'slice', 'staticmethod', 'str', 'super', 'tuple', 'type']
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose data type', 'data type:', data_to_dialog)
        if ok:
            self.arg = new_arg + '()'
            self.arg_label.setText(self.arg)
            self.resize_block()
            self.move_related_blocks()

    def get_self_func(self) -> str:
        return self.arg


class LogicalBlock(BaseBlock):
    def __init__(self, parent):
        super(LogicalBlock, self).__init__(parent, QtGui.QPixmap('./pictures/operator.png'))

    def set_argument(self):
        data_to_dialog = ['==', '!=', '>', '<', '>=', '<=', 'not', 'in']
        new_arg, ok = QtWidgets.QInputDialog.getItem(self, 'Choose operator', 'operator:', data_to_dialog)
        if ok:
            self.arg = new_arg + ' '
            self.arg_label.setText(self.arg)
            self.resize_block()
            self.move_related_blocks()

    def get_self_func(self) -> str:
        return self.arg


class BaseLoopBlock(BaseGeneralBlock):
    def __init__(self, parent, image: QtGui.QPixmap, minimum_width: int = 50, minimum_height: int = 33):
        super(BaseLoopBlock, self).__init__(parent, image, minimum_width, minimum_height)


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
        self.move_related_blocks()

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


class IfBlock(BaseGeneralBlockWithAdditionalBlocks):
    def __init__(self, parent):
        super(IfBlock, self).__init__(parent, QtGui.QPixmap('./pictures/if.png'))
        self.arg = 'if '
        self.arg_label.setText(self.arg)

    def add_additional_block_method(self):
        super(IfBlock, self).add_additional_block_method()
        if self.all_additional_blocks_classes.count(ElseBlock) >= 2:
            self.layer_down_additional_block.delete()
            self.parent.status_bar.showMessage("Can't add another one Else")

    def get_self_func(self) -> str:
        return self.arg


class ElifBlock(BaseGeneralBlockWithAdditionalBlocks):
    def __init__(self, parent):
        super(ElifBlock, self).__init__(parent, QtGui.QPixmap('./pictures/if.png'))
        self.arg = 'elif '
        self.arg_label.setText(self.arg)

    def add_additional_block_method(self):
        super(ElifBlock, self).add_additional_block_method()
        if self.all_additional_blocks_classes.count(ElseBlock) >= 2:
            self.layer_down_additional_block.delete()
            self.parent.status_bar.showMessage("Can't add another one Else")

    def get_self_func(self) -> str:
        return self.arg


class ElseBlock(BaseGeneralBlockWithAdditionalBlocks):
    def __init__(self, parent):
        super(ElseBlock, self).__init__(parent, QtGui.QPixmap('./pictures/if.png'))
        self.arg = 'else '
        self.arg_label.setText(self.arg)

    def actions_menu(self) -> None:
        """создает контекстное меню блока"""
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.delete_action, self.set_connection_action, self.add_line_action])
        menu.exec_(QtGui.QCursor.pos())

    def get_self_func(self) -> str:
        return self.arg
