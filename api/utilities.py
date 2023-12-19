from collections import OrderedDict
import difflib
from typing import List, TypeVar


K = TypeVar("K")
V = TypeVar("V")


def ordered_dict_insert(
    d: OrderedDict[K, V], index: int, key: K, value: V
) -> OrderedDict[K, V]:
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


def get_ordered_dict_key_index(
    ordered_dict: OrderedDict[K, V], target_key: K
) -> int:
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


def file_diff(file_path_a: str, file_path_b: str) -> List[str]:
    with open(file_path_a, "r") as file_a, open(file_path_b, "r") as file_b:
        file_diff_list = [
            i
            for i in difflib.unified_diff(
                file_a.readlines(), file_b.readlines(), lineterm=""
            )
        ]

    return file_diff_list


def string_diff(string_a: str, string_b: str) -> List[str]:
    string_lines_a = string_a.splitlines()
    string_lines_b = string_b.splitlines()
    diff_list = [
        i for i in difflib.unified_diff(string_lines_a, string_lines_b, lineterm="")
    ]

    return diff_list
