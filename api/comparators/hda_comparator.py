import os
from collections import OrderedDict
from api.data.hda_data import HdaData, HdaSection, HdaSectionState, HDA_SECTIONS_PARENT_NAME
from api.utilities import ordered_dict_insert, get_ordered_dict_key_index

import hou
import toolutils # $HFS/houdini/python3.9libs/toolutils.py

from api.comparators.houdini_base_comparator import HoudiniComparator, COLORS


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

        self.source_data = OrderedDict(
            OrderedDict(list(self.source_nodes.items()) + list(self.source_sections.items()))
        )
        self.target_data = OrderedDict(
            OrderedDict(list(self.target_nodes.items()) + list(self.target_sections.items()))
        )

        self.is_compared = True
        

    def _handle_sections(self):
        source_parent_section = self.create_parent_section(self.source_nodes[0])
        target_parent_section = self.create_parent_section(self.target_nodes[0])

        # deleted
        for source_section in self.source_sections.values:
            if source_section.name not in self.target_sections:
                self._mark_section_as_deleted(source_section)

        # created
        for target_section in self.target_sections.values():
            if target_section.name not in self.source_sections:
                self._mark_section_as_created(target_section)

        for source_section, target_section in zip(
            self.source_sections.values(), self.target_sections.values()
        ):
            self._compare_sections(source_section, target_section)

    def _compare_sections(self, source_section, target_section):
        diff = HdaSection.diff_sections(source_section, target_section)

        if diff:
            self.source_sections[source_section.section_path].state = HdaSectionState.EDITED
            self.source_sections[source_section.section_path].alpha = 100
            self.source_sections[source_section.section_path].color = COLORS["red"]

            self.target_sections[target_section.section_path].state = HdaSectionState.EDITED
            self.target_sections[target_section.section_path].alpha = 100
            self.target_sections[target_section.section_path].color = COLORS["green"]

            self.diff_sections[source_section.section_path] = diff

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
            section.paernt_path = HDA_SECTIONS_PARENT_NAME
            section.section_path = f'{HDA_SECTIONS_PARENT_NAME}/{section.name}'
            sections_dict[section.section_path] = section

        return node_dict, sections_dict

    def _mark_section_as_created(self, target_section):
        target_section.state = HdaSectionState.CREATED
        target_section.color = COLORS["green"]
        target_section.alpha = 100

        new_section = HdaSection("")
        new_section.name = self.target_sections[target_section.section_path].name
        new_section.state = HdaSectionState.CREATED
        new_section.color = COLORS["red"]
        new_section.alpha = 100

        index = get_ordered_dict_key_index(self.target_sections, target_section.section_path)
        self.source_sections = ordered_dict_insert(
            self.source_sections, index, target_section.section_path, new_section
        )

    def _mark_section_as_deleted(self, source_section):
        source_section.state = HdaSectionState.DELETED
        source_section.color = COLORS["green"]
        source_section.alpha = 100

        new_section = HdaSection("")
        new_section.name = source_section.name
        new_section.section_path = source_section.section_path
        new_section.state = HdaSectionState.DELETED
        new_section.color = COLORS["red"]
        new_section.alpha = 100

        index = get_ordered_dict_key_index(self.source_sections, source_section.section_path)
        self.source_sections = ordered_dict_insert(
            self.target_sections, index, source_section.section_path, new_section
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

    def create_parent_section(self, parent_node):
        hda_source_root_node = parent_node
        source_sections_parent = HdaData(HDA_SECTIONS_PARENT_NAME)
        source_sections_parent.path = f'{hda_source_root_node}/{HDA_SECTIONS_PARENT_NAME}'
        source_sections_parent.type = None
        source_sections_parent.icon = None
        source_sections_parent.parent_path = hda_source_root_node.path