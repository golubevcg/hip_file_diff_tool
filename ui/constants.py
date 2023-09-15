import os
import copy
import zipfile
from hutil.Qt.QtGui import (
    QPixmap, QIcon, QStandardItemModel, QStandardItem,
    QColor, QBrush, QPen, QPainter, QTransform
)
from hutil.Qt.QtWidgets import QStyledItemDelegate
from hutil.Qt.QtCore import Qt
from typing import Dict, Optional

# --- Constants ---

# Setting the path for the icons directory
ICONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# Paths to the icon mappings and the compressed icons file
ICONS_MAPPING_PATH = os.path.join(ICONS_PATH, 'IconMapping')
ICONS_ZIP_PATH = os.path.join(ICONS_PATH, 'icons.zip')

# Dictionary to hold the mapping of icon keys to their respective icon filenames
ICON_MAPPINGS: Dict[str, str] = {}

with open(ICONS_MAPPING_PATH, 'r') as file:
    for line in file:
        if line.startswith("#") or ":=" not in line:
            continue
        key, value = line.split(":=")
        ICON_MAPPINGS[key.strip()] = value.strip().rstrip(";").replace("_", "/", 1)

PATH_ROLE = Qt.UserRole + 1
DATA_ROLE = Qt.UserRole + 2