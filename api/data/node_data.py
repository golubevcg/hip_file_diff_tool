from dataclasses import dataclass, field
from typing import Any
from api.data.item_data import ItemData


@dataclass
class NodeData(ItemData):
    """
    A class to represent some of the Houdini node data.
    """

    def __init__(self, name: str):
        """
        Initialize a new instance of the NodeData class.

        :param name: The name of the node.
        """
        super().__init__(name)

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
