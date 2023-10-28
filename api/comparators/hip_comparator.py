import hou
from api.comparators.houdini_base_comparator import HoudiniComparator


class HipFileComparator(HoudiniComparator):
    """Comparator class for comparing two Houdini HIP files."""

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
        hou.hipFile.load(
            hip_path, suppress_save_prompt=True, ignore_load_warnings=True
        )

    def compare(self) -> None:
        """Compare the source and target HIP files to identify differences."""
        self._validate_file_paths()

        self.source_nodes = self.get_hip_data(self.source_file)
        self.target_nodes = self.get_hip_data(self.target_file)

        self._handle_deleted_and_edited_nodes()
        self._handle_created_nodes()
        self._handle_created_params()

        self.is_compared = True
