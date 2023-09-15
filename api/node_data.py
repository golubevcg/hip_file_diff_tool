from collections import OrderedDict

from api.utilities import ordered_dict_insert, get_ordered_dict_key_index

class NodeData:
    """
    A class to represent some of the Houdini node data.
    
    Attributes:
        name (str): Name of the node.
        path (str): Path to the node, usually represented as a unique string. None by default.
        type (str): Type of the node, represented as a string. Empty string by default.
        icon (str): path to the icon representing the node. Empty string by default.
        tag (str or None): A tag for categorization or special marking of the node. None by default.
        parent_path (str): Path to the parent of this node. Empty string by default.
        parms (OrderedDict): An ordered dictionary containing node parameters.
    """
    
    def __init__(self, name: str):
        """
        Initialize a new instance of the NodeData class.
        
        :param name: The name of the node.
        """
        self.name = name
        self.path = None
        self.type = ""
        self.icon = ""
        self.tag = None
        self.parent_path = ""
        self.parms = OrderedDict()

        self.color = None
        self.alpha = 255
        self.is_hatched = False

    def add_parm(self, name: str, parm) -> None:
        """
        Add a parameter to the node's parameter dictionary.
        
        :param name: The name of the parameter.
        :param parm: The parameter data to be added.
        """
        self.parms[name] = parm

    def get_parm_by_name(self, name: str):
        """
        Retrieve a parameter by its name from the node's parameter dictionary.
        
        :param name: The name of the parameter to be retrieved.
        :return: The parameter data associated with the provided name.
        :raises ValueError: If the parameter name is not found in the dictionary.
        """
        if name not in self.parms:
            raise ValueError("this parm not in dict")
        
        return self.parms[name]
    
    def __repr__(self):
        # return f"{self.name}, {','.join(self.parms.keys())}\n"
        return f"{self.name}\n"
