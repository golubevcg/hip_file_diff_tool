import os
import copy
import uuid

from collections import OrderedDict

import hou


SUPPORTED_FILE_FORMATS = ["hip", "hipnc"]


def ordered_dict_insert(d, index, key, value):
    # Split the dictionary into two parts
    before = list(d.items())[:index]
    after = list(d.items())[index:]
    
    # Insert the new item between the two parts
    before.append((key, value))
    
    # Create a new OrderedDict from the parts
    return OrderedDict(before + after)

def get_ordered_dict_key_index(ordered_dict, target_key):
    return list(ordered_dict.keys()).index(target_key)


class NodeData:
    def __init__(
            self, 
            name
        ):
        self.name = name
        self.path = None
        self.type = ""
        self.icon = ""
        self.tag = None
        self.parent_path = ""
        self.parms = OrderedDict()

    def add_parm(self, name, parm):
        self.parms[name] = parm

    def get_parm_by_name(self, name):
        if name not in self.parms:
            raise ValueError("this parm not in dict")
        
        return self.parms[name]


class ParamData():
    def __init__(self, name, value, tag):
        self.name = name
        self.value = value
        self.tag = None


class HipFileComparator():
    def __init__(self, source_hip_file, target_hip_file):
        self.check_file_path(source_hip_file)
        self.check_file_path(target_hip_file)
        
        self.source_hip_file = source_hip_file
        self.target_hip_file = target_hip_file
        
        self.source_data = OrderedDict()
        self.target_data = OrderedDict()
        self.diff_data = OrderedDict()

        self.is_compared = False

    def check_file_path(self, path):
        if not os.path.exists(path):
            incorrect_path_text = "Incorrect source path specified, such file don't exists."
            raise RuntimeError(incorrect_path_text)
        
        _, extension = os.path.splitext(path)
        if extension[1:] not in SUPPORTED_FILE_FORMATS:
            only_hip_supported_text = "Incorrect source file specified, only .hip files supported."
            raise RuntimeError(only_hip_supported_text)

    def get_hip_data(self, hip_path):
        if not hip_path:
            raise ValueError("No source file specified!")
        
        hou.hipFile.clear()
        hou.hipFile.load(
            hip_path, 
            suppress_save_prompt=True, 
            ignore_load_warnings=True
        )

        data_dict = {}

        for node in hou.node("/").allNodes():
            if node.isInsideLockedHDA():
                continue

            path = node.path()
            parent_path = None 
            parent = node.parent()
            try:
                parent_path = parent.path()
            except:
                pass
            node_data = NodeData(node.name())
            node_data.path = node.path() 
            node_data.type = node.type()
            node_data.icon = node.type().icon()
            node_data.parent_path = parent_path

            parms = node.parms()
            if parms:            
                for parm in parms:
                    node_data.add_parm(
                        parm.name(),
                        ParamData(parm.name(), parm.eval(), False)
                    )

            data_dict[path] = node_data

        return data_dict

    def compare(self):
        if not self.source_hip_file:
            raise ValueError("Error, no source file specified!")
        
        if not self.target_hip_file:
            raise ValueError("Error, no target file specified!")

        self.source_data = self.get_hip_data(self.source_hip_file)
        self.target_data = self.get_hip_data(self.target_hip_file)

        # deleted nodes
        # and edited params
        for path in self.source_data:
            source_node_data = self.source_data[path]
            if path not in self.target_data:
                new_data = NodeData(path)
                new_data.parent_path = self.source_data[path].parent_path
                new_data.tag = "deleted"
                new_data.name = ""
                new_data.icon = ""

                index = get_ordered_dict_key_index(self.source_data, path)
                self.target_data = ordered_dict_insert(self.target_data, index, path, new_data)
                source_node_data.tag = "deleted"
                continue

            for parm_name in copy.copy(source_node_data.parms):
                source_parm = source_node_data.get_parm_by_name(parm_name)
                target_parm = self.target_data[path].get_parm_by_name(parm_name)
                if source_parm.value != target_parm.value:
                    print("PARM IS EDITED", source_parm.name)
                    source_parm.tag = "edited"
                    target_parm.tag = "edited"

        # created nodes
        for path in self.target_data:
            if path in self.source_data:
                continue

            new_data = NodeData(path)
            new_data.parent_path = self.target_data[path].parent_path
            new_data.tag = "created"
            new_data.name = ""
            new_data.icon = ""
            
            index = get_ordered_dict_key_index(self.target_data, path)
            self.source_data = ordered_dict_insert(self.source_data, index, path, new_data)

            self.target_data[path].tag = "created"
                    
        self.is_compared = True

        '''
        what you need in diff:
            what was deleted in source 
                mark with red in source
                mark with dashed lines empty spots in target

            what was edited in source 
                mark with yellow in both trees
            
            what new nodes have been created in target
                mark with green in target
                mark with dashed line in source
        '''