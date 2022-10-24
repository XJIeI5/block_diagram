# -*- coding: utf-8 -*-
import subprocess
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from blocks import Block, StartBlock, EndBlock
from exceptions import SequenceError


class Interpreter:
    def __init__(self):
        self.__program = ''

    def convert_to_py(self, blocks: list[Block]) -> str:
        if blocks[0].__class__ != StartBlock and blocks[-1].__class__ != EndBlock:
            return ''
        result = []

        inherit_from_start: list[Block] = []
        if not blocks[0].child:
            raise SequenceError(f"StartBlock doesn't have child")
        for block in blocks[1:]:
            if blocks[0].child == block:  # является ли блок ребенком старта?
                inherit_from_start += [block]
            else:  # иначе если не является
                if inherit_from_start[-1].child != block:  # если не является ребенком ребенка старта
                    raise SequenceError(f'{block.__class__.__name__} not inherited from StartBlock')
                else:
                    inherit_from_start.append(block)

        blocks_result = []
        for block in blocks:
            # if not (block.__class__ == StartBlock or block.__class__ == EndBlock) and not block.arg:
            #     raise ValueError('no arguments specified')
            blocks_result.append(block.get_func())

        result.extend(map(lambda x: '\t' + x, blocks_result))
        result = self.add_standart_code(result)
        return '\n'.join(result)

    def add_standart_code(self, program: list[str]) -> list[str]:
        program.insert(0, 'try:')
        # program.insert(0, '\tprint(tb)')
        # program.insert(0, '\ttb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))')
        # program.insert(0, 'def excepthook(exc_type, exc_value, exc_tb):')
        program.insert(0, 'import traceback')
        program.insert(0, 'import sys')
        program.append('')
        program.append('')
        # program.append('sys.excepthook = excepthook')
        program.append('\tpass')
        program.append('except BaseException:')
        program.append('\tprint(traceback.format_exc())')
        program.append('input("press ENTER to close")')
        return program

    def execute(self, blocks: list[Block]):
        self.__program = self.convert_to_py(blocks)
        with open('./execute.py', mode='w', encoding='utf-8') as file:
            file.write(self.__program)
        proc = subprocess.Popen(['python', 'execute.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
