import os
import hou


SUPPORTED_FILE_FORMATS = ["hip", "hipnc"]


class HipFileComparator():
    def __init__(self, source_hip_file, target_hip_file):
        self.check_file_path(source_hip_file)
        self.check_file_path(target_hip_file)
        
        self.source_hip_file = source_hip_file
        self.target_hip_file = target_hip_file
        
        self.data_from_source = {}
        self.data_from_target = {}
        self.diff_data = {}

    def check_file_path(self, path):
        if not os.path.exists(path):
            incorrect_path_text = "Incorrect source path specified, such file don't exists."
            raise RuntimeError(incorrect_path_text)
        
        _, extension = os.path.splitext(path)
        if extension not in SUPPORTED_FILE_FORMATS:
            only_hip_supported_text = "Incorrect source file specified, only .hip files supported."
            raise RuntimeError(only_hip_supported_text)

    def get_hip_data(self, hip_path):
        if not hip_path:
            raise ValueError("No source file specified!")
        
        hou.hipFile.clear()
        hou.hipFile.load(self.source_hip_file)

        data_dict = {}

        for object in hou.node("/").allNodes():
            path = object.path()

            parms = object.parms()
            if not parms:
                parms_and_values[name] = None
            
            parms_and_values = {}
            for parm in parms:
                name = parm.name()
                val = parm.eval()
                parms_and_values[name] = val  
            data_dict[path] = parms_and_values

        return data_dict

    def compare(self):
        if not self.source_hip_file:
            raise ValueError("Error, no source file specified!")
        
        if not self.target_hip_file:
            raise ValueError("Error, no target file specified!")

        source_file_data = self.get_hip_data(self.source_hip_file)
        target_file_data = self.get_hip_data(self.target_hip_file)

        