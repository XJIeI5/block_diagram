# -*- coding: utf-8 -*-
import inspect
import json
import sqlite3
import sys

import blocks


def get_values():
    classes = inspect.getmembers(sys.modules['blocks'], inspect.isclass)
    result = enumerate(classes)
    result = tuple(map(lambda x: ', '.join([str(x[0] + 1), '"' + x[1][0] + '"']), result))
    return result


def create_data_base(name: str):
    with sqlite3.connect(name) as con:
        cursor = con.cursor()
        # Создание базы данных с типами блоков
        cursor.execute('''CREATE TABLE IF NOT EXISTS BlockTypes(
        Id INT NOT NULL PRIMARY KEY,
        Name TEXT)''')
        values = get_values()
        # Заполнение
        for pack in values:
            cursor.execute(f'INSERT INTO BlockTypes(Id, Name) VALUES ({pack})')

        # Создание базы данных блоков
        cursor.execute('''CREATE TABLE IF NOT EXISTS Blocks(
        Hash INT PRIMARY KEY,
        BlockTypeId INT NOT NULL,
        XCoord INT,
        YCoord INT,
        Argument TEXT,
        DataType Text,
        ChildHash INT,
        LayerUpBlockHash INT,
        LayerDownBlockHash INT,
        GeneralBlockHash INT,
        LinesHash TEXT,
        LayerUpAdditionalBlockHash INT,
        LayerDownAdditionalBlockHash INT)''')


def fill_data_base(db_name: str, blocks_to_fill):
    with sqlite3.connect(db_name) as con:
        cursor = con.cursor()
        try:
            cursor.execute('DELETE from Blocks')
        except sqlite3.OperationalError:
            create_data_base(db_name)

        for block in blocks_to_fill:
            block_hash = hash(block)

            block_type_id = cursor.execute(f'SELECT Id FROM BlockTypes'
                                           f' WHERE Name == "{block.__class__.__name__}"').fetchone()[0]

            x_coord, y_coord = block.x(), block.y()
            
            argument = f'"{block.arg}"'
            
            data_type = f'"{block.data_type}"' if hasattr(block, 'data_type') else 'NULL'
            
            block_child = hash(block.child) if block.child else 'NULL'
            
            layer_up_block_hash = hash(block.layer_up_block) if block.layer_up_block else 'NULL'
            
            layer_down_block_hash = hash(block.layer_down_block) if block.layer_down_block else 'NULL'
            
            general_block_hash = hash(block.general_block) if block.general_block else 'NULL'

            lines_hash = f'"{json.dumps(tuple(map(hash, block.lines)))}"' if \
                issubclass(block.__class__, blocks.BaseGeneralBlock) else 'NULL'

            layer_up_additional_block_hash = hash(block.layer_up_additional_block) if \
                hasattr(block, 'layer_up_additional_block') else 'NULL'

            layer_down_additional_block_hash = hash(block.layer_down_additional_block) if \
                hasattr(block, 'layer_down_additional_block') else 'NULL'

            data = ", ".join([str(block_hash), str(block_type_id), str(x_coord), str(y_coord), argument, data_type,
                              str(block_child), str(layer_up_block_hash), str(layer_down_block_hash),
                              str(general_block_hash), lines_hash, str(layer_up_additional_block_hash),
                              str(layer_down_additional_block_hash)])
            cursor.execute(f'INSERT INTO Blocks VALUES({data})')


def load_data_base(db_name: str, blocks_parent):
    with sqlite3.connect(db_name) as con:
        cursor = con.cursor()
        result_blocks = []
        hashed_blocks: dict[int: blocks.BaseBlock] = {}

        # Создаем блоки
        blocks_type_and_hash = cursor.execute('SELECT BlockTypeId, Hash FROM Blocks').fetchall()
        block_types = tuple(map(lambda x: x[0], blocks_type_and_hash))
        blocks_hash = tuple(map(lambda x: x[1], blocks_type_and_hash))
        new_block_types = []
        for index in block_types:
            new_value = cursor.execute(f'SELECT Name FROM BlockTypes WHERE Id == {index}').fetchone()[0]
            new_block_types.append(new_value)
        block_types = tuple(new_block_types)
        for block_type, block_hash in zip(block_types, blocks_hash):
            block_class = getattr(blocks, block_type)
            new_block = block_class(blocks_parent)
            result_blocks.append(new_block)
            hashed_blocks[block_hash] = new_block

        # Двигаем блоки
        for block_hash, block in hashed_blocks.items():
            coords = cursor.execute(f'SELECT XCoord, YCoord FROM Blocks WHERE Hash == {block_hash}').fetchone()
            block.move(*coords)

        # Задаем аргументы блокам
        for block_hash, block in hashed_blocks.items():
            arg = cursor.execute(f'SELECT Argument FROM Blocks WHERE Hash == {block_hash}').fetchone()[0]
            block.arg = arg
            block.arg_label.setText(arg)

        # Задаем зависимости
        for block_hash, block in hashed_blocks.items():
            data = cursor.execute(f'SELECT DataType, ChildHash, LayerUpBlockHash, LayerDownBlockHash, GeneralBlockHash,'
                                  f' LinesHash, LayerUpAdditionalBlockHash, LayerDownAdditionalBlockHash FROM Blocks'
                                  f' WHERE Hash == {block_hash}').fetchone()
            attribute_names = ['data_type', 'child', 'layer_up_block', 'layer_down_block', 'general_block', 'lines',
                               'layer_up_additional_block', 'layer_down_additional_block']
            for attr_value, attr_name in zip(data, attribute_names):
                if hasattr(block, attr_name):
                    if isinstance(attr_value, int):
                        new_value = hashed_blocks.get(attr_value, None)
                    elif attr_value and '[' in attr_value and ']' in attr_value:
                        new_value = attr_value[1:-1].split(',')
                        new_value = [hashed_blocks[int(i)] for i in new_value]
                    else:
                        new_value = attr_value
                    setattr(block, attr_name, new_value)

        for block in hashed_blocks.values():
            block.resize_block()
            block.move_related_blocks()

        return result_blocks
