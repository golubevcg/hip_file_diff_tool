import os
import copy
import zipfile
from hutil.Qt.QtGui import (
    QPixmap, QIcon, QStandardItemModel, QStandardItem,
    QColor, QBrush, QPen, QPainter
)
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


# --- CustomStandardItemModel ---

class CustomStandardItemModel(QStandardItemModel):
    """
    Custom implementation of QStandardItemModel with functionality 
    for handling items with unique paths and icon management.
    """

    def __init__(self, *args, **kwargs):
        super(CustomStandardItemModel, self).__init__(*args, **kwargs)
        
        self.item_dictionary = {}
        self.path_role = PATH_ROLE
        self.data_role = DATA_ROLE
        self.view = None
        self.show_only_edited = False
        self.hatched_pattern_index_offset = 0

    def set_view(self, tree_view) -> None:
        """Set the tree view widget to which the model is attached."""
        self.view = tree_view

    def _set_icon_from_zip(self, item: QStandardItem, icon_name: str, icons_zip: zipfile.ZipFile) -> None:
        """
        Extract the specified icon from a zip archive and set it to the given item.

        :param item: The QStandardItem object.
        :param icon_name: Name of the icon in the archive.
        :param icons_zip: Zip archive containing icons.
        """
        try:
            with icons_zip.open(icon_name) as file:
                icon_data = file.read()
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                item.setIcon(QIcon(pixmap))
        except Exception:
            pass

    def add_item_with_path(self, item_text: str, path: str, data, icons_zip: zipfile.ZipFile, parent: Optional[QStandardItem] = None) -> None:
        """
        Create a QStandardItem with specified properties and add it to the model.

        :param item_text: Display text for the item.
        :param path: Unique path associated with the item.
        :param data: Data associated with the item.
        :param icons_zip: Zip archive containing icons.
        :param parent: Parent item (if any).
        """
        
        item = QStandardItem(item_text)
        item.setData(path, self.path_role)
        item.setData(data, self.data_role)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        icon_path = ICON_MAPPINGS.get(data.icon, data.icon)
        if icon_path:
            icon_path = icon_path.replace("_", "/", 1) + ".svg"
            self._set_icon_from_zip(item, icon_path, icons_zip)

        (parent.appendRow if parent else self.appendRow)(item)

        self.item_dictionary[path] = item

        for parm_name in data.parms:
            self._add_parm_items(item, data, parm_name, icons_zip)

    def _add_parm_items(self, item: QStandardItem, data, parm_name: str, icons_zip: zipfile.ZipFile) -> None:
        """
        Add parameter items (associated with a data object) as children of the given item.

        :param item: The QStandardItem object.
        :param data: Data object containing parameter information.
        :param parm_name: Name of the parameter.
        :param icons_zip: Zip archive containing icons.
        """
        parm = data.get_parm_by_name(parm_name)

        if not parm.tag:
            return
        
        updated_parm_name = parm_name
        if parm.is_active == False:
            updated_parm_name = ""

        path = item.data(self.path_role)
        parm_path = f"{path}/{updated_parm_name}"
        parm_item = QStandardItem(updated_parm_name)
        parm_item.setData(parm, self.data_role)
        parm_item.setData(parm_path, self.path_role)
        parm_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
        
        self._set_icon_from_zip(parm_item, "VOP/parameter.svg", icons_zip)

        item.appendRow(parm_item)
        self.item_dictionary[parm_path] = parm_item

        if parm.is_active == False:
            return

        value_path = f"{parm_path}/value"
        value_item = QStandardItem(str(parm.value))
        value_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
        value_data = copy.copy(parm)
        value_data.tag = 'value'
        value_item.setData(value_data, self.data_role)
        value_item.setData(value_path, self.path_role)

        parm_item.appendRow(value_item)
        self.item_dictionary[value_path] = value_item

    def get_item_by_path(self, path: str) -> Optional[QStandardItem]:
        """
        Retrieve the QStandardItem associated with a specific path.

        :param path: Unique path of the desired item.
        :return: Corresponding QStandardItem, or None if not found.
        """

        return self.item_dictionary.get(path)

    def populate_with_data(self, data, view_name: str) -> None:
        """
        Populate the model using a provided dataset.

        :param data: Dataset to populate from.
        :param view_name: Name of the associated view.
        """

        with zipfile.ZipFile(ICONS_ZIP_PATH, 'r') as zip_ref:
            for path in data:
                node_data = data[path]

                node_name = node_data.name if node_data.name != "/" else view_name
                parent_path = node_data.parent_path
                parent_item = self.get_item_by_path(parent_path)

                if parent_path != "/" and not parent_item:
                    continue

                self.add_item_with_path(node_name, path, node_data, zip_ref, parent=parent_item)
        
        self.paint_items_and_expand(self.invisibleRootItem(), view_name)

    def paint_items_and_expand(self, parent_item, view_name: str) -> None:
        """
        Recursively iterate over items to style and possibly expand them.

        :param parent_item: Starting item for the recursive traversal.
        :param view_name: Name of the associated view.
        """
        for row in range(parent_item.rowCount()):
            for column in range(parent_item.columnCount()):
                child_item = parent_item.child(row, 0)
                item_data = child_item.data(Qt.UserRole + 2)
                tag = item_data.tag

                # Using the new _apply_item_style function
                if tag:
                    self._apply_item_style_and_expansion(child_item)

                if child_item:
                    self.paint_items_and_expand(child_item, view_name)

    def _apply_item_style_and_expansion(self, item: QStandardItem) -> None:
        """
        Apply the appropriate style and expansion to the item based on its tag and view_name.

        :param item: The QStandardItem to apply the style to.
        """

        item_data = item.data(Qt.UserRole + 2)

        color = item_data.color
        qcolor = color = QColor(color)
        if color:
            qcolor.setAlpha(item_data.alpha)
            item.setBackground(QBrush(qcolor))

        if item_data.is_hatched:
            self.fill_item_with_hatched_pattern(item)

        if item_data.tag and item_data.tag != "value":
            self.view.expand_to_index(item, self.view)

    def fill_item_with_hatched_pattern(self, item: QStandardItem) -> None:
        """
        Fill the background of a QStandardItem with a diagonal hatched pattern.

        :param item: The QStandardItem to fill.
        """
        # Create a QPixmap for hatching pattern
        hatch_width = 1000  # Adjust for desired frequency
        pixmap = QPixmap(hatch_width, 100)
        pixmap.fill(Qt.transparent)  # or any background color

        # Create a brush for the hatching pattern
        pen_color = QColor("#505050")  # Change for desired line color
        pen_width = 3  # Change for desired line thickness
        pen = QPen(pen_color, pen_width)
        pen.setCapStyle(Qt.FlatCap)

        painter = QPainter(pixmap)
        painter.setPen(pen)

        # Adjusted loop and coordinates for the hatching pattern
        for i in range(-hatch_width, hatch_width, pen_width * 6):  
            # add self.hatched_pattern_index_offset 
            # wand update this index after function finished
            painter.drawLine(
                i - self.hatched_pattern_index_offset*2, 
                hatch_width, 
                hatch_width + i - self.hatched_pattern_index_offset*2, 
                0)

        painter.end()

        hatch_brush = QBrush(pixmap)
        item.setBackground(hatch_brush)

        self.hatched_pattern_index_offset+=1