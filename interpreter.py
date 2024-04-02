# -*- coding: utf-8 -*-
import subprocess
from blocks import BaseBlock, StartBlock, EndBlock
from exceptions import SequenceError


class Interpreter:
    def __init__(self):
        self.__program: str = ''

    def convert_to_py(self, blocks) -> str:
        if StartBlock not in [i.__class__ for i in blocks] or EndBlock not in [i.__class__ for i in blocks]:
            return ''
        result = []

        blocks = self.get_blocks_in_right_order(next(i for i in blocks if i.__class__ == StartBlock))
        self.handle_errors(blocks)
        blocks_result = []
        for block in blocks:
            if block.layer_up_block is not None:
                continue
            if block.general_block is not None:
                continue
            if hasattr(block, 'layer_up_additional_block') and block.layer_up_additional_block is not None:
                continue
            blocks_result.extend(block.get_func().split('\n'))

        result.extend(map(lambda x: '\t' + x, blocks_result))
        result = self.add_standart_code(result)
        return '\n'.join(result)

    def add_standart_code(self, program):
        program.insert(0, 'try:')
        program.insert(0, 'import traceback')
        program.append('')
        program.append('')
        program.append('\tpass')
        program.append('except BaseException:')
        program.append('\tprint(traceback.format_exc())')
        program.append('\tinput("press ENTER to close")')
        program.append('input("press ENTER to close")')
        return program

    def handle_errors(self, blocks):
        current_block: BaseBlock = next(i for i in blocks if i.__class__ == StartBlock)
        connected_blocks_classes = []
        while current_block is not None:
            connected_blocks_classes.append(current_block.__class__)
            current_block = current_block.child
        if EndBlock not in connected_blocks_classes:
            raise SequenceError

    def get_blocks_in_right_order(self, start_block: StartBlock):
        result = []
        current_block = start_block
        while current_block is not None:
            result.append(current_block)
            current_block = current_block.child
        return result

    def execute(self, blocks):
        self.__program = self.convert_to_py(blocks)
        with open('./execute.py', mode='w', encoding='utf-8') as file:
            file.write(self.__program)
        proc = subprocess.Popen(['python', 'execute.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
