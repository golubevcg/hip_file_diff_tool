import os
from collections import OrderedDict
import hou
from api.node_data import NodeData
from api.param_data import ParamData
from api.utilities import ordered_dict_insert, get_ordered_dict_key_index


SUPPORTED_FILE_FORMATS = {"hip", "hipnc"}
COLORS = {
    "red": "#b50400",
    "green": "#6ba100",
}


class HipFileComparator:
    """Comparator class for comparing two Houdini HIP files."""

    def __init__(self, source_hip_file: str, target_hip_file: str):
        """
        Initialize the comparator with source and target HIP files.

        :param source_hip_file: Path to the source HIP file.
        :param target_hip_file: Path to the target HIP file.
        """
        self._check_file_path(source_hip_file, "source")
        self._check_file_path(target_hip_file, "target")

        self.source_hip_file = source_hip_file
        self.target_hip_file = target_hip_file

        self.source_data = OrderedDict()
        self.target_data = OrderedDict()
        self.diff_data = OrderedDict()

        self.is_compared = False

    def _check_file_path(self, path: str, file_type: str) -> None:
        """Check if the provided path is valid and of a supported format."""
        if not os.path.exists(path):
            raise RuntimeError(
                f"Incorrect {file_type} path specified. Such file doesn't exist."
            )

        _, extension = os.path.splitext(path)
        if extension[1:] not in SUPPORTED_FILE_FORMATS:
            raise RuntimeError(
                f"Incorrect {file_type} file format. Supported formats are: {', '.join(SUPPORTED_FILE_FORMATS)}."
            )

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
        """Load a specified HIP file into Houdini."""
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
            node_data.add_parm(parm.name(), ParamData(parm.name(), parm.eval(), None))
        return node_data

    def _get_parent_path(self, node) -> str:
        """Return the path of a node's parent or None if no parent is found."""
        try:
            return node.parent().path()
        except AttributeError:
            return None

    def compare(self) -> None:
        """Compare the source and target HIP files to identify differences."""
        self._validate_file_paths()
        self.source_data = self.get_hip_data(self.source_hip_file)
        self.target_data = self.get_hip_data(self.target_hip_file)
        self._handle_deleted_and_edited_nodes()
        self._handle_created_nodes()
        self._handle_created_params()
        self.is_compared = True

    def _validate_file_paths(self) -> None:
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
        new_data.is_hatched = True
        index = get_ordered_dict_key_index(self.source_data, path)
        self.target_data = ordered_dict_insert(self.target_data, index, path, new_data)

        source_node_data.tag = "deleted"
        source_node_data.color = COLORS["red"]
        source_node_data.alpha = 100

    def _compare_node_params(self, path: str, source_node_data):
        """
        Compare parameters of nodes between source and target data.

        :param path: The path of the node.
        :param source_node_data: The data associated with the source node.
        """

        for parm_name in list(
            source_node_data.parms
        ):  # Avoids copying the entire dictionary
            source_parm = source_node_data.get_parm_by_name(parm_name)

            # deleted param
            if parm_name not in self.target_data[path].parms:
                # add empty parm to target data
                self.source_data[path].tag = "edited"
                self.source_data[path].color = COLORS["red"]
                self.source_data[path].alpha = 100

                source_parm = self.source_data[path].get_parm_by_name(parm_name)
                source_parm.tag = "edited"
                source_parm.color = "red"
                source_parm.alpha = 55

                self.target_data[path].tag = "edited"
                self.target_data[path].color = COLORS["red"]
                self.target_data[path].alpha = 100

                parm = ParamData(parm_name, "", "deleted")
                parm.alpha = 55
                parm.is_active = False
                parm.is_hatched = True

                self.target_data[path].add_parm(parm_name, parm)
                continue

            target_parm = self.target_data[path].get_parm_by_name(parm_name)

            if str(source_parm.value) == str(target_parm.value):
                continue

            source_parm.tag = "edited"
            source_parm.color = COLORS["red"]
            source_parm.alpha = 55

            source_node_data.tag = "edited"
            source_node_data.color = COLORS["red"]
            source_node_data.alpha = 100

            target_parm.tag = "edited"
            target_parm.color = COLORS["green"]
            target_parm.alpha = 55

            self.target_data[path].tag = "edited"
            self.target_data[path].color = COLORS["green"]
            self.target_data[path].alpha = 100

    def _handle_created_params(self):
        """Handle items for node params that are newly created."""
        for path, target_data in self.target_data.items():
            for parm_name in list(target_data.parms):
                if parm_name in self.source_data[path].parms:
                    continue

                # created param
                target_parm = target_data.get_parm_by_name(parm_name)
                target_parm.tag = "created"
                target_parm.color = COLORS["green"]
                target_parm.alpha = 55

                target_data.tag = "edited"
                target_data.color = COLORS["green"]
                target_data.alpha = 100

                parm = ParamData(parm_name, "", "created")
                parm.alpha = 55
                parm.is_hatched = True
                parm.is_active = False

                self.source_data[path].add_parm(parm_name, parm)

                self.source_data[path].tag = "edited"
                self.source_data[path].alpha = 100

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
        self.source_data[path].alpha = 100
        self.source_data[path].is_hatched = True

        self.target_data[path].tag = "created"
        self.target_data[path].color = COLORS["green"]
        self.target_data[path].alpha = 100
