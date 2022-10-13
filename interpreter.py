# -*- coding: utf-8 -*-
import subprocess
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import blocks


class Interpreter:
    def __init__(self, _blocks: list[blocks.Block]):
        self.blocks: list[blocks.Block] = _blocks

    @property
    def program(self):
        return self.convert_to_py()

    def convert_to_py(self) -> str:
        if self.blocks[0].__class__ != blocks.StartBlock and self.blocks[-1].__class__ != blocks.EndBlock:
            return ''
        result = ''

        for block in self.blocks:
            if not (block.__class__ == blocks.StartBlock or block.__class__ == blocks.EndBlock) and not block.arg:
                raise ValueError
            result += block.get_func() + '\n'
        result += 'input("press ENTER to close")\n'
        return result

    def execute(self):
        with open('./execute.py', mode='w', encoding='utf-8') as file:
            file.write(self.program)
        proc = subprocess.Popen(['python', 'execute.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
