import os
import copy
from collections import OrderedDict
import hou
from api.node_data import NodeData
from api.param_data import ParamData

SUPPORTED_FILE_FORMATS = {"hip", "hipnc"}

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


class HipFileComparator:
    """
    Comparator class for comparing two Houdini HIP files.

    Attributes:
    - source_hip_file: Path to the source HIP file.
    - target_hip_file: Path to the target HIP file.
    """
    
    def __init__(self, source_hip_file: str, target_hip_file: str):
        """
        Initialize the comparator with source and target HIP files.

        :param source_hip_file: Path to the source HIP file.
        :param target_hip_file: Path to the target HIP file.
        """
        self.check_file_path(source_hip_file)
        self.check_file_path(target_hip_file)
        
        self.source_hip_file = source_hip_file
        self.target_hip_file = target_hip_file
        
        self.source_data = OrderedDict()
        self.target_data = OrderedDict()
        self.diff_data = OrderedDict()

        self.is_compared = False

    def check_file_path(self, path: str):
        """
        Check if the provided path is valid and corresponds to a supported file format.

        :param path: The file path to check.
        :raises RuntimeError: If the path doesn't exist or the file format is unsupported.
        """
        if not os.path.exists(path):
            raise RuntimeError("Incorrect source path specified, such file doesn't exist.")
        
        _, extension = os.path.splitext(path)
        if extension[1:] not in SUPPORTED_FILE_FORMATS:
            raise RuntimeError("Incorrect source file specified, only .hip files supported.")

    def get_hip_data(self, hip_path: str) -> dict:
        """
        Retrieve data from a given HIP file.

        :param hip_path: The path to the HIP file.
        :return: A dictionary containing data extracted from the HIP file.
        """
        if not hip_path:
            raise ValueError("No source file specified!")
        
        self._load_hip_file(hip_path)

        data_dict = {}

        for node in hou.node("/").allNodes():
            if node.isInsideLockedHDA():
                continue
            data_dict[node.path()] = self._extract_node_data(node)

        return data_dict

    def _load_hip_file(self, hip_path: str) -> None:
        """
        Load a specified HIP file into Houdini.

        :param hip_path: The path to the HIP file.
        """
        hou.hipFile.clear()
        hou.hipFile.load(hip_path, suppress_save_prompt=True, ignore_load_warnings=True)

    def _extract_node_data(self, node) -> NodeData:
        """
        Extracts data from a given node.

        :param node: The node from which to extract data.
        :return: A NodeData object containing extracted data.
        """
        node_data = NodeData(node.name())
        node_data.path = node.path()
        node_data.type = node.type()
        node_data.icon = node.type().icon()
        node_data.parent_path = self._get_parent_path(node)

        for parm in node.parms():
            node_data.add_parm(parm.name(), ParamData(parm.name(), parm.eval(), False))

        return node_data

    def _get_parent_path(self, node):
        """
        Returns the path of a node's parent.

        :param node: The node for which to retrieve the parent's path.
        :return: The path of the parent, or None if no parent is found.
        """
        try:
            return node.parent().path()
        except:
            return None

    def compare(self):
        """
        Compare the source and target HIP files to identify differences.

        :raises ValueError: If either source or target file paths are not set.
        """
        self._validate_file_paths()
        self.source_data = self.get_hip_data(self.source_hip_file)
        self.target_data = self.get_hip_data(self.target_hip_file)
        
        self._handle_deleted_and_edited_nodes()
        self._handle_created_nodes()
        
        self.is_compared = True

    def _validate_file_paths(self):
        """Validate that both source and target file paths are set."""
        if not self.source_hip_file:
            raise ValueError("Error, no source file specified!")
        if not self.target_hip_file:
            raise ValueError("Error, no target file specified!")

    def _handle_deleted_and_edited_nodes(self):
        """Handle nodes that are deleted or have edited parameters."""
        for path, source_node_data in self.source_data.items():
            if path not in self.target_data:
                self._mark_node_as_deleted(path, source_node_data)
            else:
                self._compare_node_params(path, source_node_data)

    def _mark_node_as_deleted(self, path: str, source_node_data):
        """
        Mark a node as deleted and update target data accordingly.

        :param path: The path of the node.
        :param source_node_data: The data associated with the source node.
        """
        new_data = NodeData("")
        new_data.parent_path = source_node_data.parent_path
        new_data.tag = "deleted"
        index = get_ordered_dict_key_index(self.source_data, path)
        self.target_data = ordered_dict_insert(self.target_data, index, path, new_data)
        source_node_data.tag = "deleted"

    def _compare_node_params(self, path: str, source_node_data):
        """
        Compare parameters of nodes between source and target data.

        :param path: The path of the node.
        :param source_node_data: The data associated with the source node.
        """
        for parm_name in list(source_node_data.parms):  # Avoids copying the entire dictionary
            source_parm = source_node_data.get_parm_by_name(parm_name)
            target_parm = self.target_data[path].get_parm_by_name(parm_name)
            if str(source_parm.value) != str(target_parm.value):
                source_parm.tag = "edited"
                target_parm.tag = "edited"

    def _handle_created_nodes(self):
        """Handle nodes that are newly created."""
        source_paths = set(self.source_data.keys())
        target_paths = set(self.target_data.keys())
        
        for path in target_paths - source_paths:  # Faster set difference operation
            self._mark_node_as_created(path)

    def _mark_node_as_created(self, path: str):
        """
        Mark a node as created and update source data accordingly.

        :param path: The path of the node.
        """
        new_data = NodeData("")
        new_data.parent_path = self.target_data[path].parent_path
        new_data.tag = "created"
        index = get_ordered_dict_key_index(self.target_data, path)
        self.source_data = ordered_dict_insert(self.source_data, index, path, new_data)
        self.target_data[path].tag = "created"
