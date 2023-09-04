import os
import copy

import hou


SUPPORTED_FILE_FORMATS = ["hip", "hipnc"]


class HipFileComparator():
    def __init__(self, source_hip_file, target_hip_file):
        self.check_file_path(source_hip_file)
        self.check_file_path(target_hip_file)
        
        self.source_hip_file = source_hip_file
        self.target_hip_file = target_hip_file
        
        self.source_data = {}
        self.target_data = {}
        self.diff_data = {}

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
        hou.hipFile.load(self.source_hip_file)

        data_dict = {}

        for node in hou.node("/").allNodes():
            path = node.path()
            name = node.name()
            node_type = node.type()
            icon = node_type.icon()
            parent_path = None 
            parent = node.parent()
            try:
                parent_path = parent.path()
            except:
                pass

            parms_and_values = {}
            parms = node.parms()

            if parms:            
                for parm in parms:
                    parm_name = parm.name()
                    val = parm.eval()
                    parms_and_values[parm_name] = val  

            data_dict[path] = {
                "name" : name,
                "type" : str(node_type),
                "icon" : icon,
                "tag" : None,
                "parent_path": parent_path,
                "parms" : parms_and_values
            }

        return data_dict

    def compare(self):
        if not self.source_hip_file:
            raise ValueError("Error, no source file specified!")
        
        if not self.target_hip_file:
            raise ValueError("Error, no target file specified!")

        self.source_data = self.get_hip_data(self.source_hip_file)
        self.target_data = self.get_hip_data(self.target_hip_file)

        for path in self.source_data:
            if path not in self.target_data:
                data = {}
                data["tag"] = "deleted"
                self.diff_data[path] = data

            source_node_parms = self.source_data[path]["parms"]
            target_node_parms = self.target_data[path]["parms"]
            for parm in copy.copy(source_node_parms):
                source_value = source_node_parms[parm]
                target_value = target_node_parms[parm]
                if source_value != target_value:
                    data = {}
                    data["tag"] = "edited"
                    self.diff_data[path] = {
                        "parms":parm,
                        "tag" : "edited",
                    }

                    self.target_data[path]["parms"]["tag"] = "edited"
                    self.source_data[path]["parms"]["tag"] = "edited"
            
            
        for path in self.target_data:
            if path not in self.source_data:
                data = {}
                data["tag"] = "created"
                self.diff_data[path] = data
            

        for path in self.diff_data:
            tag = self.diff_data[path]["tag"]

            if tag == "deleted":
                self.target_data[path] = None

            if tag == "created":
                self.source_data[path] = None


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