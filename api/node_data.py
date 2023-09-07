from collections import OrderedDict

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

