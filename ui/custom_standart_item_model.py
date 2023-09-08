import os
import copy
import zipfile
from hutil.Qt.QtGui import QPixmap, QIcon, QStandardItemModel, QStandardItem, QColor, QBrush, QPen, QPainter
from hutil.Qt.QtCore import Qt

# Setting the path for the icons directory
ICONS_PATH = os.path.dirname(os.path.abspath(__file__))
ICONS_PATH = os.path.join(ICONS_PATH, "icons")

# Path to the icon mappings and the compressed icons file
ICONS_MAPPING_PATH = os.path.join(ICONS_PATH, 'IconMapping')
ICONS_ZIP_PATH = os.path.join(ICONS_PATH, 'icons.zip')

# Dictionary to hold the mapping of icon keys to their respective icon filenames
ICON_MAPPINGS = {}

# Reading the ICONS_MAPPING_PATH to populate the ICON_MAPPINGS dictionary
with open(ICONS_MAPPING_PATH, 'r') as file:
    for line in file:
        # Skipping comments and lines without proper mapping syntax
        if line.startswith("#") or ":=" not in line:
            continue
        key, value = line.split(":=")
        ICON_MAPPINGS[key.strip()] = value.strip().rstrip(";").replace("_", "/", 1)

TAG_COLOR_MAP = {
    "deleted": "#b50400",
    "edited": "#ffea00",
    "created": "#6ba100",
}


class CustomStandardItemModel(QStandardItemModel):
    """
    Custom implementation of QStandardItemModel with added functionality 
    for handling items with unique paths and icon management.
    """

    def __init__(self, *args, **kwargs):
        super(CustomStandardItemModel, self).__init__(*args, **kwargs)
        
        # Dictionary to keep track of items by their unique paths
        self.item_dictionary = {}
        
        # Define custom roles for setting and fetching data from items
        self.path_role = Qt.UserRole + 1
        self.data_role = Qt.UserRole + 2

        self.view = None

    def set_view(self, tree_view):
        self.view = tree_view

    def _set_icon_from_zip(self, item, icon_name, icons_zip):
        """
        Helper method to set the icon for an item by reading it from a zip archive.

        :param item: The QStandardItem object to which the icon should be set.
        :param icon_name: The filename of the icon inside the zip archive.
        :param icons_zip: The zip archive containing the icon.
        """
        try:
            with icons_zip.open(icon_name) as file:
                icon_data = file.read()
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                item.setIcon(QIcon(pixmap))
        except Exception:
            pass

    def add_item_with_path(self, item_text, path, data, icons_zip, parent=None):
        """
        Adds an item to the model with additional metadata like path and data.

        :param item_text: The display text of the item.
        :param path: The unique path identifier for the item (node path in the tree).
        :param data: The associated data with the item.
        :param icons_zip: The zip archive containing icons.
        :param parent: The parent item, if the item to be added is a child.
        """
        item = QStandardItem(item_text)
        item.setData(path, self.path_role)
        item.setData(data, self.data_role)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.item_dictionary[path] = item

        icon_path = ICON_MAPPINGS.get(data.icon, data.icon)
        if icon_path:
            icon_path = icon_path.replace("_", "/", 1) + ".svg"
            self._set_icon_from_zip(item, icon_path, icons_zip)

        (parent.appendRow if parent else self.appendRow)(item)

        # Handling parameters for the item
        for parm_name in data.parms:
            parm = data.get_parm_by_name(parm_name)
            if parm.tag != "edited":
                continue

            parm_path = f"{path}/{parm_name}"
            parm_item = QStandardItem(parm.name)
            parm_item.setData(parm, self.data_role)
            parm_item.setData(parm_path, self.path_role)
            parm_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
            
            self._set_icon_from_zip(parm_item, "VOP/parameter.svg", icons_zip)
            
            item.appendRow(parm_item)
            self.item_dictionary[parm_path] = parm_item

            # Setting value for the parameter
            value_path = f"{parm_path}/value"
            value_item = QStandardItem(str(parm.value))
            value_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
            value_data = copy.copy(parm)
            value_data.tag = 'value'
            value_item.setData(value_data, self.data_role)
            value_item.setData(value_path, self.path_role)
            parm_item.appendRow(value_item)
            self.item_dictionary[value_path] = value_item

    def get_item_by_path(self, path):
        """
        Retrieve a QStandardItem based on its unique path identifier.

        :param path: The unique path identifier for the item.
        :return: The QStandardItem associated with the path or None if not found.
        """
        return self.item_dictionary.get(path)

    def populate_with_data(
            self, 
            data,
            view_name
    ):

        with zipfile.ZipFile(ICONS_ZIP_PATH, 'r') as zip_ref:
            for path in data:
                node_data = data[path]

                node_name = node_data.name
                parent_path = node_data.parent_path
                parent_item = self.get_item_by_path(parent_path)
                if node_name == "/":
                    node_name = view_name

                self.add_item_with_path(
                    node_name, 
                    path, 
                    node_data, 
                    zip_ref,
                    parent=parent_item,
                )
        
        self.paint_items_and_expand(self.invisibleRootItem(), view_name)

    def paint_items_and_expand(self, parent_item, view_name):
        """Recursive function to iterate over all items in a QStandardItemModel."""
        for row in range(parent_item.rowCount()):
            for column in range(parent_item.columnCount()):
                item = parent_item.child(row, 0)
                item_data = item.data(Qt.UserRole + 2)
                tag = item_data.tag
                
                if tag == "created" and view_name == "source":
                    self.fill_item_with_hatched_pattern(item)
                    self.view.expand_to_index(self.indexFromItem(item), self.view)
                        
                elif tag in ["edited", "value"] and view_name == "source":
                    color = TAG_COLOR_MAP["deleted"]
                    qcolor = QColor(color)
                    qcolor.setAlpha(40)
                    item.setBackground(QBrush(qcolor))
                    if tag != "value":
                        self.view.expand_to_index(self.indexFromItem(item), self.view)
                        
                elif tag in ["edited", "value"] and view_name == "target":
                    color = TAG_COLOR_MAP["created"]
                    qcolor = QColor(color)
                    qcolor.setAlpha(40)
                    item.setBackground(QBrush(qcolor))
                    if tag != "value":
                        self.view.expand_to_index(self.indexFromItem(item), self.view)

                elif tag == "deleted" and view_name == "target":
                    self.fill_item_with_hatched_pattern(item)
                    self.view.expand_to_index(self.indexFromItem(item), self.view)

                elif tag:
                    color = TAG_COLOR_MAP[tag]
                    qcolor = QColor(color)
                    qcolor.setAlpha(150)
                    item.setBackground(QBrush(qcolor))
                    self.view.expand_to_index(self.indexFromItem(item), self.view)

                if item:
                    self.paint_items_and_expand(item, view_name)

    def fill_item_with_hatched_pattern(self, item):
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
            painter.drawLine(i, hatch_width, hatch_width+i, 0)

        painter.end()

        hatch_brush = QBrush(pixmap)
        item.setBackground(hatch_brush)