# FIXME | WIP remove me when done

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List
from api import utilities

import hou


HDA_SECTIONS_PARENT_NAME = "HDA_Sections"


class HdaSectionState(Enum):
    """
    An enum representing the diff state of a node.
    """

    UNCHANGED = None
    EDITED = auto()
    DELETED = auto()
    CREATED = auto()


class HdaSectionType(Enum):
    UNDEFINED = auto()
    SCRIPT = auto()
    EXPRESSION = auto()
    HELP = auto()
    TOOLS_SHELF = auto()


class HdaSectionContentType(Enum):
    PLAIN_TEXT = auto()
    PYTHON = auto()
    HSCRIPT = auto()
    XML = auto()
    WIKI_MARKUP = auto()  # https://www.sidefx.com/docs/houdini/help/format.html


@dataclass
class HdaSection:
    """
    Extra files contained within an HDA that can be diffed appropriately
    depending on their content.
    """
    name: str
    type: HdaSectionType = HdaSectionType.UNDEFINED
    content: str = ""
    content_type: HdaSectionContentType = HdaSectionContentType.PLAIN_TEXT
    state: HdaSectionState = HdaSectionState.UNCHANGED

    def __repr__(self):
        return f"{self.name}"

    @staticmethod
    # def diff_section(source_section: Self, target_section: Self) -> List[str]:
    def diff_sections(source_section, target_section) -> List[str]:
        if not isinstance(target_section.content, type(source_section.content)):
            raise TypeError(
                f"Provided hda sections {source_section.name} and {target_section.name} are not of the same type."
            )

        diff = utilities.string_diff(source_section.content, target_section.content)
        return diff

@dataclass
class HdaDefintion:
    name: str
    context: str
    icon: str
    sections: List[HdaSection] = field(default_factory=list)

    @classmethod
    def from_hou_hda_definition(cls, hou_hda_definition: hou.HDADefinition):
        name = hou_hda_definition.nodeTypeName()
        context = hou_hda_definition.nodeTypeCategory().name()
        icon = hou_hda_definition.icon()

        sections = []
        sections.extend(cls._get_extra_files(hou_hda_definition))
        sections.append(cls._get_help_file(hou_hda_definition))
        sections.append(cls._get_tools_shelf_file(hou_hda_definition))

        return cls(name, context, icon, sections)

    def _get_extra_files(hou_hda_definition: hou.HDADefinition) -> List[HdaSection]:
        """
        Get sections from a HDA definition that are also listed in the 
        extra_file_options.
        These contain all of the manually added extra files.
        """
        hda_extra_files = []
        
        extra_file_options = hou_hda_definition.extraFileOptions()
        hda_sections = hou_hda_definition.sections()
        for extra_file_name in hda_sections.keys():
            if not extra_file_options.get(f"{extra_file_name}/Cursor"):
                continue
            content = hda_sections.get(extra_file_name).contents()

            is_expression = extra_file_options.get(f"{extra_file_name}/IsExpr")
            is_script = extra_file_options.get(f"{extra_file_name}/IsScript")
            is_python = extra_file_options.get(f"{extra_file_name}/IsPython")

            if is_expression:
                filetype = HdaSectionType.EXPRESSION
            elif is_script:
                filetype = HdaSectionType.SCRIPT
            else:
                filetype = HdaSectionType.UNDEFINED

            if is_expression or is_script:
                if is_python:
                    content_type = HdaSectionContentType.PYTHON
                else:
                    content_type = HdaSectionContentType.HSCRIPT
            else:
                content_type = HdaSectionContentType.PLAIN_TEXT

            hda_script = HdaSection(
                name=extra_file_name,
                type=filetype,
                content=content,
                content_type=content_type,
                )

            hda_extra_files.append(hda_script)

        return hda_extra_files

    def _get_tools_shelf_file(hou_hda_definition: hou.HDADefinition) -> HdaSection:
        """
        Get the Tools.shelf file which contains xml data from the HDA's 
        shelftool.
        """
        hda_sections = hou_hda_definition.sections()
        tools_shelf_xml_content = hda_sections.get("Tools.shelf").contents()
        tools_shelf_file = HdaSection(
            name="Tools.shelf",
            type=HdaSectionType.TOOLS_SHELF,
            content=tools_shelf_xml_content,
            content_type=HdaSectionContentType.XML,
        )
        return tools_shelf_file

    def _get_help_file(hou_hda_definition: hou.HDADefinition) -> HdaSection:
        """
        Get the help file of the HDA
        """
        hda_sections = hou_hda_definition.sections()
        help_string = hda_sections.get("Help").contents()
        help_file = HdaSection(
            name="Help",
            type=HdaSectionType.HELP,
            content=help_string,
            content_type=HdaSectionContentType.WIKI_MARKUP,
        )
        return help_file

    @staticmethod
    # def diff_definition_sections(source_hda_definition: Self, target_hda_definition: Self):
    def diff_definition_sections(source_hda_definition, target_hda_definition) -> Dict:
        diffs = {}

        source_definition_section_names = {
            section.name for section in source_hda_definition.sections
        }
        target_definition_section_names = {
            section.name for section in target_hda_definition.sections
        }

        matching_source_sections = (
            section
            for section in source_hda_definition.sections
            if section.name in target_definition_section_names
        )
        matching_target_sections = (
            section
            for section in target_hda_definition.sections
            if section.name in source_definition_section_names
        )

        for source_section, target_section in zip(
            matching_source_sections, matching_target_sections
        ):
            diff = HdaSection.diff_sections(source_section, target_section)
            diffs[source_section.name] = diff

        return diffs
    
class HdaData:
    """
    A class to represent a Houdini HDA containing one or multiple HDA 
    definitions.
    """
    def __init__(self, hda_path: str) -> None:
        self.path = hda_path
        self.parent_path: str = ""
        self.definitions: List[HdaDefintion] = self._get_definitions()

    def _get_definitions(self) -> List[HdaDefintion]:
        return [
            HdaDefintion.from_hou_hda_definition(hda_def) 
            for hda_def in hou.hda.definitionsInFile(self.path)
        ]

    def latest_definition(self) -> HdaDefintion:
        # TODO: is `definition.isCurrent()` ever better? if yes add this info
        # to HdaDefinition
        return self.definitions[-1]
