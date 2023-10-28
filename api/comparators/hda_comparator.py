import os
from collections import OrderedDict
from api.data.hda_data import HdaData, HdaSection, HdaSectionState
from api.utilities import ordered_dict_insert, get_ordered_dict_key_index

import hou
import toolutils # $HFS/houdini/python3.9libs/toolutils.py

from api.comparators.houdini_base_comparator import HoudiniComparator


HDA_FILE_FORMATS = {"hda", "hdanc", "hdanc"}


class HdaFileComparator(HoudiniComparator):
    """Comparator class for comparing two Houdini Digital Asset HDA files."""

    def __init__(self, source_file: str, target_file: str):
        super().__init__(source_file=source_file, target_file=target_file)

        self.source_sections = OrderedDict()
        self.target_sections = OrderedDict()
        self.diff_sections = OrderedDict()

    def _check_file_path(self, path: str, file_type: str) -> None:
        """Check if the provided path is valid and of a supported format."""
        if not path or not os.path.exists(path):
            raise RuntimeError(
                f"Incorrect {file_type} path specified. "
                "Such file doesn't exist."
            )

        _, extension = os.path.splitext(path)
        if not extension or extension[1:] not in HDA_FILE_FORMATS:
            raise RuntimeError(
                f"Incorrect {file_type} file format. "
                f"Supported formats are: {', '.join(HDA_FILE_FORMATS)}."
            )

    def compare(self):
        """
        Compare both HDAs
        """

        self._validate_file_paths()

        self.source_nodes, self.source_sections = self.get_hda_data(self.source_file)
        self.target_nodes, self.target_sections = self.get_hda_data(self.target_file)

        self._handle_sections()

        self._handle_deleted_and_edited_nodes()
        self._handle_created_nodes()

        self._handle_created_params()
        self.is_compared = True

    def get_hda_sections(self, hda_path: str) -> dict:
        if not hda_path:
            raise ValueError("No hda file specified!")

    def _handle_sections(self):
        for source_section, target_section in zip(
            self.source_sections.values(), self.target_sections.values()
        ):
            # deleted
            if source_section.name not in self.target_sections:
                self._mark_section_as_deleted(source_section.name, source_section)

            # created
            elif target_section.name not in self.source_sections:
                self._mark_section_as_created(target_section.name)

            # potentially edited
            else:
                self._compare_sections(source_section, target_section)

    def _compare_sections(self, source_section, target_section):
        diff = HdaSection.diff_sections(source_section, target_section)

        if diff:
            self.source_sections[source_section.name].state = HdaSectionState.EDITED
            self.target_sections[target_section.name].state = HdaSectionState.EDITED
            self.diff_sections[source_section.name] = diff

    def get_hda_data(self, hda_path: str) -> (dict, dict):
        """
        Retrieve data from a given HDA file.

        :param hda_path: The path to the HDA file.
        :return: A dictionary containing data extracted from the HIP file.
        """
        if not hda_path:
            raise ValueError("No hda file specified!")

        hou.hipFile.clear()
        node_dict = {}
        sections_dict = {}

        hda_node = self._load_hda_file(hda_path)
        for node in hda_node.allNodes():
            if node.isInsideLockedHDA():
                continue
            node_dict[node.path()] = self._extract_node_data(node)

        hda_data = HdaData(hda_path)
        latest_definition = hda_data.latest_definition()
        for section in latest_definition.sections:
            sections_dict[section.name] = section

        return node_dict, sections_dict

    def _mark_section_as_created(self, name: str):
        new_section = HdaSection("")
        new_section.name = self.target_sections[name].name
        new_section.state = HdaSectionState.CREATED
        index = get_ordered_dict_key_index(self.target_sections, name)

        self.source_sections = ordered_dict_insert(
            self.source_sections, index, name, new_section
        )

    def _mark_section_as_deleted(self, name: str, source_section):
        new_section = HdaSection("")
        new_section.name = source_section.name
        new_section.state = HdaSectionState.DELETED

        index = get_ordered_dict_key_index(self.source_sections, name)
        self.source_sections = ordered_dict_insert(
            self.target_sections, index, name, new_section
        )

    def _load_hda_file(self, hda_path: str) -> hou.Node:
        """Load a specified hda file as node and allow to edit its contents."""
        hou.hda.installFile(hda_path, force_use_assets=True)
        hda_defs = hou.hda.definitionsInFile(hda_path)
        latest_hda_def = hda_defs[-1]
        hda_node = toolutils.createNodeInContainer(
            container=hou.node("/obj"),
            nodetypecategory=latest_hda_def.nodeTypeCategory(),
            nodetypename=latest_hda_def.nodeTypeName(),
            nodename=latest_hda_def.nodeTypeName(), # TODO might not always work
            exact_node_type=False)[1]
        
        hda_node.allowEditingOfContents()
        return hda_node
