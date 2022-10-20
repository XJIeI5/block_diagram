# -*- coding: utf-8 -*-
import subprocess
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from blocks import Block, StartBlock, EndBlock
from exceptions import SequenceError


class Interpreter:
    def __init__(self, _blocks: list[Block]):
        self.__blocks: list[Block] = _blocks
        self.__program = ''

    @property
    def program(self) -> str:
        return self.__program

    @property
    def blocks(self) -> list[Block]:
        return self.__blocks

    @blocks.setter
    def blocks(self, value: list[Block]):
        self.__blocks: list[Block] = value
        self.__program: str = self.convert_to_py()

    def convert_to_py(self) -> str:
        print(self.blocks)
        if self.blocks[0].__class__ != StartBlock and self.blocks[-1].__class__ != EndBlock:
            return ''
        result = ''

        inherit_from_start: list[Block] = []
        if not self.blocks[0].child:
            raise SequenceError(f"StartBlock doesn't have child")
        for block in self.blocks[1:]:
            if self.blocks[0].child == block:
                inherit_from_start += [block]
            else:
                if inherit_from_start[-1].child != block:
                    raise SequenceError(f'{block.__class__.__name__} not inherited from StartBlock')
                else:
                    inherit_from_start.append(block)

        for block in self.blocks:
            if not (block.__class__ == StartBlock or block.__class__ == EndBlock) and not block.arg:
                raise ValueError('no arguments specified')
            result += block.get_func() + '\n'
        result += 'input("press ENTER to close")\n'
        return result

    def execute(self):
        with open('./execute.py', mode='w', encoding='utf-8') as file:
            file.write(self.program)
        proc = subprocess.Popen(['python', 'execute.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
