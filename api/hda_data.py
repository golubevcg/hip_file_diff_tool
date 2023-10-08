# FIXME | WIP remove me when done

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Union
from xml.etree import ElementTree as ET

import hou

class HdaSectionType(Enum):
    UNDEFINED = auto()
    SCRIPT = auto()
    EXPRESSION = auto()
    HELP = auto()
    TOOLS_SHELF = auto()

@dataclass
class HdaSection:
    """
    Extra files contained within an HDA that can be diffed appropriately
    depending on their content.
    """
    name: str
    type: HdaSectionType
    content: Union[str, ET.Element]
    is_python: bool

    def __repr__(self):
        return f"{self.name}"

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

            if is_expression:
                filetype = HdaSectionType.EXPRESSION
            elif is_script:
                filetype = HdaSectionType.SCRIPT
            else:
                filetype = HdaSectionType.UNDEFINED

            is_python = extra_file_options.get(f"{extra_file_name}/IsPython")

            hda_script = HdaSection(
                name=extra_file_name,
                type=filetype,
                content=content,
                is_python=is_python
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
            content=ET.fromstring(tools_shelf_xml_content),
            is_python=False
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
            is_python=False
        )
        return help_file
    
class HdaData:
    """
    A class to represent a Houdini HDA containing one or multiple HDA 
    definitions.
    """
    def __init__(self, hda_path: str) -> None:
        self.path = hda_path
        self.definitions: List[HdaDefintion] = self._get_definitions()

    def _get_definitions(self) -> List[HdaDefintion]:
        return [
            HdaDefintion.from_hou_hda_definition(hda_def) 
            for hda_def in hou.hda.definitionsInFile(hda_path)
        ]

    def latest_definition(self) -> HdaDefintion:
        # TODO: is `definition.isCurrent()` ever better? if yes add this info
        # to HdaDefinition
        return self.definitions[-1]


if __name__ == "__main__":
    hda_path = Path(
        Path(__file__).parent.parent, "test/test_scenes/BoxHDA_edited.hda"
    ).as_posix()

    hda = HdaData(hda_path)
    latest_hda_def = hda.latest_definition()
    print(latest_hda_def)

