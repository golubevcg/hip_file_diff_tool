from collections import OrderedDict
from enum import auto, Enum
from typing import Any, Optional

class NodeState(Enum):
    """
    An enum representing the state of a node.
    """
    UNCHANGED = None
    EDITED = auto()
    DELETED = auto()
    CREATED = auto()

    def __str__(self):
        return f"{self.name.lower()}"

    def __format__(self, spec):
        return f"{self.name.lower()}"


class NodeData:
    """
    A class to represent some of the Houdini node data.

    Attributes:
        name (str): Name of the node.
        path (str): Path to the node, usually represented as a unique string.
                    None by default.
        type (str): Type of the node, represented as a string.
                    Empty string by default.
        icon (str): Path to the icon representing the node.
                    Empty string by default.
        state (NodeState): The state of the node.
        parent_path (str): Path to the parent of this node.
                           Empty string by default.
        parms (OrderedDict): An ordered dictionary containing node parameters.
        color (Optional[str]): The color associated with the node.
                               None by default.
        alpha (int): The opacity value (0-255) for the node visualization.
                     255 by default.
        is_hatched (bool): Indicates whether the node has a hatched pattern.
                           False by default.
    """

    def __init__(self, name: str):
        """
        Initialize a new instance of the NodeData class.

        :param name: The name of the node.
        """
        self.name: str = name
        self.path: str = None
        self.type: str = ""
        self.icon: str = ""
        self.state: str = NodeState.UNCHANGED
        self.parent_path: str = ""
        self.parms: OrderedDict[str, Any] = OrderedDict()
        self.color: Optional[str] = None
        self.alpha: int = 255
        self.is_hatched: bool = False

    def add_parm(self, name: str, param: Any) -> None:
        """
        Add a parameter to the node's parameter dictionary.

        :param name: The name of the parameter.
        :param param: The parameter data to be added.
        """
        self.parms[name] = param

    def get_parm_by_name(self, name: str) -> Any:
        """
        Retrieve a parameter by its name from the node's parameter dictionary.

        :param name: The name of the parameter to be retrieved.
        :return: The parameter data associated with the provided name.
        :raises ValueError: If the parameter name is not found
                            in the dictionary.
        """
        if name not in self.parms:
            raise ValueError(
                f"Parameter '{name}' is not found in the dictionary."
            )

        return self.parms[name]

    def __repr__(self):
        return f"{self.name}: {self.state}\n"
