from collections import OrderedDict
from typing import Any, TypeVar

K = TypeVar('K')
V = TypeVar('V')


def ordered_dict_insert(d: OrderedDict[K, V], index: int, key: K, value: V) -> OrderedDict[K, V]:
    """
    Insert a key-value pair into an OrderedDict at a specified index.

    :param d: The dictionary into which to insert.
    :param index: The position at which to insert the key-value pair.
    :param key: The key to insert.
    :param value: The corresponding value to insert.
    :return: A new OrderedDict with the key-value pair inserted.
    """
    before = list(d.items())[:index]
    after = list(d.items())[index:]
    before.append((key, value))
    return OrderedDict(before + after)


def get_ordered_dict_key_index(ordered_dict: OrderedDict[K, V], target_key: K) -> int:
    """
    Return the index of a key in an OrderedDict.

    :param ordered_dict: The dictionary to search in.
    :param target_key: The key to find the index for.
    :return: The index of the target_key if found, raises an error otherwise.
    """
    for idx, key in enumerate(ordered_dict):
        if key == target_key:
            return idx
    raise KeyError(f"'{target_key}' not found in the OrderedDict.")
