class ParamData:
    """
    A class to represent parameter data associated with a node.

    Attributes:
        name (str): The name identifier for the parameter.
        value: The value associated with the parameter.
        tag (str or None): A tag.
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
        tag: str = None,
        color: str = None,
        alpha: int = 255,
        is_hatched: bool = False,
    ):
        """
        Initialize a new instance of the ParamData class.

        :param name: The name identifier for the parameter.
        :param value: The value associated with the parameter.
        :param tag: A tag for the parameter. Default is None.
        :param color: The color associated with the parameter.
                      Default is None.
        :param alpha: The opacity value for the parameter visualization.
                      Default is 255.
        :param is_hatched: Indicates whether the parameter has
                           a hatched pattern. Default is False.
        """
        self.name = name
        self.value = value
        self.tag = tag
        self.is_active = True
        self.color = color
        self.alpha = alpha
        self.is_hatched = is_hatched

    def __repr__(self):
        return f"ParamData(\
                    name={self.name!r}, \
                    value={self.value!r}, \
                    tag={self.tag!r}, \
                    color={self.color!r}, \
                    alpha={self.alpha}, \
                    is_hatched={self.is_hatched}\
                )"

    def __str__(self):
        return f"{self.name}, {self.tag}"
