from collections import OrderedDict


def ordered_dict_insert(d: OrderedDict, index: int, key: str, value: any) -> OrderedDict:
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


def get_ordered_dict_key_index(ordered_dict: OrderedDict, target_key: str) -> int:
    """
    Return the index of a key in an OrderedDict.

    :param ordered_dict: The dictionary to search in.
    :param target_key: The key to find the index for.
    :return: The index of the target_key if found, raises an error otherwise.
    """
    return list(ordered_dict.keys()).index(target_key)