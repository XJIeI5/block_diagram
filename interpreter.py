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
        self.handle_errors(blocks)

        blocks_result = []
        closing_bracket_countdown = []
        for block in blocks:
            if block.highest_layer == block and block.depth == 0:
                blocks_result.append(block.get_func())
            elif block.highest_layer == block and block.depth != 0:
                construct = ''
                current_block = block
                while current_block.depth + 1 != 0:
                    func = current_block.get_func()
                    if current_block.is_python_function:
                        func = func.replace(')', '')
                        closing_bracket_countdown.append(current_block.depth)
                    if 0 in closing_bracket_countdown:
                        func += ')'
                    if closing_bracket_countdown:
                        closing_bracket_countdown = [i - 1 for i in closing_bracket_countdown]
                    construct += func
                    current_block = current_block.layer_down_block
                    if current_block is None:
                        break
                blocks_result.append(construct)
            else:
                pass

        result.extend(map(lambda x: '\t' + x, blocks_result))
        result = self.add_standart_code(result)
        return '\n'.join(result)

    def add_standart_code(self, program: list[str]) -> list[str]:
        program.insert(0, 'try:')
        program.insert(0, 'import traceback')
        # program.insert(0, 'import sys')
        program.append('')
        program.append('')
        program.append('\tpass')
        program.append('except BaseException:')
        program.append('\tprint(traceback.format_exc())')
        program.append('input("press ENTER to close")')
        return program

    def handle_errors(self, blocks):
        current_block: Block = blocks[0]
        inherited_from_start_blocks: list[Block] = []
        try:
            while current_block.__class__ != EndBlock:
                if current_block.highest_layer != current_block:
                    continue
                if current_block.__class__ != StartBlock:
                    if not any([i.highest_layer.child == current_block for i in inherited_from_start_blocks]):
                        raise SequenceError
                inherited_from_start_blocks.append(current_block)

                if current_block.depth != 0:
                    current_block_down = current_block
                    for i in range(current_block.depth):
                        current_block_down = current_block_down.layer_down_block
                        inherited_from_start_blocks.append(current_block_down)

                current_block = current_block.child
        except AttributeError:
            raise SequenceError
        if len(inherited_from_start_blocks) + 1 < len(blocks):
            raise SequenceError

    def execute(self, blocks: list[Block]):
        self.__program = self.convert_to_py(blocks)
        with open('./execute.py', mode='w', encoding='utf-8') as file:
            file.write(self.__program)
        proc = subprocess.Popen(['python', 'execute.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
