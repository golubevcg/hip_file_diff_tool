import os
from typing import Dict

from hutil.Qt.QtCore import Qt


"""
This module provides utilities for handling some constants.
"""

# --- Constants ---
ICONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
ICONS_MAPPING_PATH = os.path.join(ICONS_PATH, "IconMapping")
ICONS_ZIP_PATH = os.path.join(ICONS_PATH, "icons.zip")

ICON_MAPPINGS: Dict[str, str] = {}

# Load icon mappings from file
with open(ICONS_MAPPING_PATH, "r") as file:
    for line in file:
        if line.startswith("#") or ":=" not in line:
            continue
        key, value = line.split(":=")
        ICON_MAPPINGS[key.strip()] = value.strip().rstrip(";").replace("_", "/", 1)

PATH_ROLE = Qt.UserRole + 1
DATA_ROLE = Qt.UserRole + 2
