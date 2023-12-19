from collections import OrderedDict
from enum import auto, Enum
from typing import Any, Optional
from dataclasses import dataclass, field


class ItemState(Enum):
    """
    An enum representing the diff state of a item.
    """
    UNCHANGED = None
    EDITED = auto()
    DELETED = auto()
    CREATED = auto()
    VALUE = auto()

    def __str__(self):
        return f"{self.name.lower()}"

    def __format__(self, spec):
        return f"{self.name.lower()}"
    
@dataclass
class ItemData:
    """
    A class to represent default item data which is required for the UI.
    """
    name: str  # The only required argument in the constructor
    path: Optional[str] = None
    type: str = ""
    icon: str = ""
    state: ItemState = ItemState.UNCHANGED
    parent_path: str = ""
    color: Optional[str] = None
    alpha: int = 255
    is_hatched: bool = False
    parms: OrderedDict[str, Any] = field(default_factory=OrderedDict)
    user_data: OrderedDict = field(default_factory=OrderedDict)
