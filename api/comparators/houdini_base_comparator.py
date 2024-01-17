from abc import ABC, abstractmethod
from collections import OrderedDict
import os

from api.data.item_data import ItemState
from api.data.node_data import NodeData
from api.data.param_data import ParamData
from api.utilities import ordered_dict_insert, get_ordered_dict_key_index

import hou


COLORS = {
    "red": "#b50400",
    "green": "#6ba100",
}

HIP_FILE_FORMATS = {"hip", "hipnc", "hiplc", "hdt"}


class HoudiniComparator(ABC):
    """Comparator class for comparing two Houdini related files."""
    def __init__(self, source_file: str, target_file: str):
        """
        Initialize the comparator with source and target files.

        :param source_file: Path to the source file.
        :param target_file: Path to the target file.
        """
        self.source_file = source_file
        self.target_file = target_file

        self.source_nodes = OrderedDict()
        self.target_nodes = OrderedDict()
        self.diff_nodes = OrderedDict()

        self.source_data = OrderedDict()
        self.target_data = OrderedDict()

        self.is_compared = False

    @property
    def source_file(self):
        return self._source_file

    @source_file.setter
    def source_file(self, value):
        self._check_file_path(value, "source")
        self._source_file = value

    @property
    def target_file(self):
        return self._target_file

    @target_file.setter
    def target_file(self, value):
        self._check_file_path(value, "target")
        self._target_file = value

    def _check_file_path(self, path: str, file_type: str) -> None:
        """Check if the provided path is valid and of a supported format."""
        if not path or not os.path.exists(path):
            raise RuntimeError(
                f"Incorrect {file_type} path specified. "
                "Such file doesn't exist."
            )

        _, extension = os.path.splitext(path)
        if not extension or extension[1:] not in HIP_FILE_FORMATS:
            raise RuntimeError(
                f"Incorrect {file_type} file format. "
                "Supported formats are: {', '.join(HIP_FILE_FORMATS)}."
            )

    def _extract_node_data(self, node: hou.Node) -> NodeData:
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

        input_connections = [inp_node.name() for inp_node in node.inputs() if inp_node]
        if input_connections:
            inp_conn_param = ParamData(
                "-> input connections", 
                ", ".join(input_connections), 
                None
            )
            inp_conn_param.icon = False
            node_data.add_parm(
                "-> input connections", 
                inp_conn_param
            )

        user_data = node.userDataDict()
        param_user_data = ParamData("userData", None, None)
        if user_data:
            param_user_data.value = user_data
        node_data.user_data = param_user_data

        for parm in node.parms():
            node_data.add_parm(
                parm.name(), ParamData(parm.name(), parm.eval(), None)
            )

        return node_data

    def _validate_file_paths(self) -> None:
        """Validate that both source and target file paths are set."""
        if not self.source_file:
            raise ValueError("Error, no source file specified!")
        if not self.target_file:
            raise ValueError("Error, no target file specified!")

    def _mark_node_as_created(self, path: str):
        """
        Mark a node as created and update source data accordingly.

        :param path: The path of the node.
        """
        new_data = NodeData("")
        new_data.parent_path = self.target_nodes[path].parent_path
        new_data.state = ItemState.CREATED
        index = get_ordered_dict_key_index(self.target_nodes, path)

        self.source_nodes = ordered_dict_insert(
            self.source_nodes, index, path, new_data
        )
        self.source_nodes[path].alpha = 55
        self.source_nodes[path].is_hatched = True

        self.target_nodes[path].state = ItemState.CREATED
        self.target_nodes[path].color = COLORS["green"]
        self.target_nodes[path].alpha = 55

    def _mark_node_as_deleted(self, path: str, source_node_data):
        """
        Mark a node as deleted and update target data accordingly.

        :param path: The path of the node.
        :param source_node_data: The data associated with the source node.
        """
        new_data = NodeData("")
        new_data.parent_path = source_node_data.parent_path
        new_data.state = ItemState.DELETED
        new_data.is_hatched = True
        index = get_ordered_dict_key_index(self.source_nodes, path)
        self.target_nodes = ordered_dict_insert(
            self.target_nodes, index, path, new_data
        )

        source_node_data.state = ItemState.DELETED
        source_node_data.color = COLORS["red"]
        source_node_data.alpha = 100

    def _handle_deleted_and_edited_nodes(self):
        """Handle nodes that are deleted or have edited parameters."""
        for path, source_node_data in self.source_nodes.items():
            if path not in self.target_nodes:
                self._mark_node_as_deleted(path, source_node_data)
            else:
                self._compare_node_user_data(path, source_node_data)
                self._compare_node_params(path, source_node_data)

    def _compare_node_params(self, path: str, source_node_data: NodeData):
        """
        Compare parameters of nodes between source and target data.

        :param path: The path of the node.
        :param source_node_data: The data associated with the source node.
        """
        for parm_name in list(source_node_data.parms):
            source_parm = source_node_data.get_parm_by_name(parm_name)

            # deleted param
            if parm_name not in self.target_nodes[path].parms:
                # add empty parm to target data
                self.source_nodes[path].state = ItemState.EDITED
                self.source_nodes[path].color = COLORS["red"]
                self.source_nodes[path].alpha = 100

                source_parm = self.source_nodes[path].get_parm_by_name(
                    parm_name
                )
                source_parm.state = ItemState.EDITED
                source_parm.color = "red"
                source_parm.alpha = 55

                self.source_nodes[path].state = ItemState.EDITED
                self.target_nodes[path].color = COLORS["red"]
                self.target_nodes[path].alpha = 100

                parm = ParamData(parm_name, "", ItemState.DELETED)
                parm.alpha = 55
                parm.is_active = False
                parm.is_hatched = True

                self.target_nodes[path].add_parm(parm_name, parm)
                continue

            target_parm = self.target_nodes[path].get_parm_by_name(parm_name)

            if str(source_parm.value) == str(target_parm.value):
                continue

            source_parm.state = ItemState.EDITED
            source_parm.color = COLORS["red"]
            source_parm.alpha = 55

            source_node_data.state = ItemState.EDITED
            source_node_data.color = COLORS["red"]
            source_node_data.alpha = 100

            target_parm.state = ItemState.EDITED
            target_parm.color = COLORS["green"]
            target_parm.alpha = 55

            self.target_nodes[path].state = ItemState.EDITED
            self.target_nodes[path].color = COLORS["green"]
            self.target_nodes[path].alpha = 100

    def _compare_node_user_data(self, path: str, source_node_data: NodeData):
        """
        Compare userData dict of nodes between source and target data.

        :param path: The path of the node.
        :param source_node_data: The data associated with the source node.
        """
        source_user_data_parm = source_node_data.user_data

        node_from_target_scene = self.target_nodes[path]
        target_user_data_parm = node_from_target_scene.user_data

        if source_user_data_parm.value == target_user_data_parm.value:
            return

        source_user_data_parm.state = ItemState.EDITED
        source_user_data_parm.alpha = 100
        source_user_data_parm.color = COLORS["red"]
        self.source_nodes[path].user_data = source_user_data_parm

        target_user_data_parm.state = ItemState.EDITED
        target_user_data_parm.alpha = 55
        target_user_data_parm.color = COLORS["green"]
        self.target_nodes[path].user_data = target_user_data_parm

    def _handle_created_params(self):
        """Handle items for node params that are newly created."""
        for path, target_data in self.target_nodes.items():
            for parm_name in list(target_data.parms):
                if parm_name in self.source_nodes[path].parms:
                    continue

                # created param
                target_parm = target_data.get_parm_by_name(parm_name)
                target_parm.state = ItemState.CREATED
                target_parm.color = COLORS["green"]
                target_parm.alpha = 55

                target_data.state = ItemState.EDITED
                target_data.color = COLORS["green"]
                target_data.alpha = 100

                parm = ParamData(parm_name, "", ItemState.CREATED)
                parm.alpha = 55
                parm.is_hatched = True
                parm.is_active = False

                self.source_nodes[path].add_parm(parm_name, parm)

                self.source_nodes[path].state = ItemState.EDITED
                self.source_nodes[path].alpha = 100

    def _handle_created_nodes(self):
        """Handle nodes that are newly created."""
        source_paths = set(self.source_nodes.keys())
        target_paths = set(self.target_nodes.keys())

        # Faster set difference operation
        for path in (target_paths - source_paths):  
            self._mark_node_as_created(path)

    def _get_parent_path(self, node) -> str:
        """Return the path of a node's parent or None if no parent is found."""
        try:
            return node.parent().path()
        except AttributeError:
            return None

    @abstractmethod
    def compare(self) -> None:
        """
        Abstract method for comparing the source and target data structures.
        To be implemented by the child classes.
        """
        raise NotImplementedError(
            "The compare method is an abstract one and should be implemented."
        )
