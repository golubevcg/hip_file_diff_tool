from enum import auto, Enum
from collections import OrderedDict

class ParamState(Enum):
    """
    An enum representing the diff state of a param.
    """
    UNCHANGED = auto()
    VALUE = auto()

    def __str__(self):
        return f"{self.name.lower()}"

    def __format__(self, spec):
        return f"{self.name.lower()}"

class ParamData:
    """
    A class to represent parameter data associated with a node.

    Attributes:
        name (str): The name identifier for the parameter.
        value: The value associated with the parameter.
        state (ParamState): The state of the parameter.
                            ParamState.UNCHANGED by default.
        is_active (bool): Indicates whether the parameter is active.
                          True by default.
        color (Optional[str]): The color associated with the parameter.
                               None by default.
        alpha (int): The opacity value (0-255) for the parameter visualization.
                     255 by default.
        is_hatched (bool): Indicates whether the parameter has
                           a hatched pattern. False by default.
    """

    def __init__(
        self,
        name: str,
        value: str,
        state: ParamState = ParamState.UNCHANGED,
        color: str = None,
        alpha: int = 255,
        is_hatched: bool = False,
    ):
        """
        Initialize a new instance of the ParamData class.

        :param name: The name identifier for the parameter.
        :param value: The value associated with the parameter.
        :param state: A state for the parameter. Default is ParamState.UNCHANGED.
        :param color: The color associated with the parameter.
                      Default is None.
        :param alpha: The opacity value for the parameter visualization.
                      Default is 255.
        :param is_hatched: Indicates whether the parameter has
                           a hatched pattern. Default is False.
        """
        self.name = name
        self.value = value

        self.state = state
        self.is_active = True
        self.color = color
        self.alpha = alpha
        self.is_hatched = is_hatched

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value and type(value) in (dict, OrderedDict):
            self._value = "\n".join(f"{key}: {value}" for key, value in value.items())
        else:
            self._value = value

    def __repr__(self):
        return f"ParamData(\
                    name={self.name!r}, \
                    value={self.value!r}, \
                    state={self.state!r}, \
                    color={self.color!r}, \
                    alpha={self.alpha}, \
                    is_hatched={self.is_hatched}\
                )"

    def __str__(self):
        return f"{self.name}: {self.state}"
