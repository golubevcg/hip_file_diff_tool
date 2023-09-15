
class ParamData():
    """
    A class to represent parameter data associated with a node.
    
    Attributes:
        name (str): The name identifier for the parameter.
        value: The value associated with the parameter.
        tag (str or None): A tag for categorization or special marking of the parameter. None by default.
    """
    
    def __init__(self, name, value, tag):
        """
        Initialize a new instance of the ParamData class.
        
        :param name: The name identifier for the parameter.
        :param value: The value associated with the parameter.
        :param tag: An tag for the parameter.
        """
        self.name = name
        self.value = value
        self.tag = tag
        self.is_active = True
        self.color = None
        self.alpha = 255
        self.is_hatched = False
    
    def __repr__(self):
        return f"{self.name}, {self.tag}"

