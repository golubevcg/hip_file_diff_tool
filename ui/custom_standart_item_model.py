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

from ui.hatched_pattern_item_delegate import HatchedItemDelegate
from ui.constants import *


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
        parm_path = f"{path}/{parm_name}"
        parm_item = QStandardItem(updated_parm_name)
        parm_item.setData(parm, self.data_role)
        parm_item.setData(parm_path, self.path_role)
        parm_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
        
        if parm.is_active:
            self._set_icon_from_zip(parm_item, "VOP/parameter.svg", icons_zip)

        item.appendRow(parm_item)
        self.item_dictionary[parm_path] = parm_item

        value = ""
        if parm.is_active != False:
            value = parm.value

        value_path = f"{parm_path}/value"
        value_item = QStandardItem(str(value))
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
        qcolor = QColor(color)
        if color:
            qcolor.setAlpha(item_data.alpha)
            item.setBackground(QBrush(qcolor))

        if item_data.is_hatched:
            self.fill_item_with_hatched_pattern(item, self.view)

        if item_data.tag and item_data.tag != "value":
            self.view.expand_to_index(item, self.view)

    def fill_item_with_hatched_pattern(self, item: QStandardItem, view) -> None:
        """
        Fill the background of a QStandardItem with a diagonal hatched pattern.

        :param item: The QStandardItem to fill.
        :param view: The QAbstractItemView in which the item is displayed.
        """
        # Create a QPixmap for the global hatching pattern
        hatch_width = 1000  # Adjust for desired frequency
        '''
        pixmap = QPixmap(hatch_width, hatch_width)
        pixmap.fill(Qt.transparent)  # or any background color

        # Create a brush for the hatching pattern
        pen_color = QColor("#505050")  # Change for desired line color
        pen_width = 3  # Change for desired line thickness
        pen = QPen(pen_color, pen_width)
        pen.setCapStyle(Qt.FlatCap)

        painter = QPainter(pixmap)
        painter.setPen(pen)

        # Create the hatching pattern across the entire pixmap
        for i in range(-hatch_width, hatch_width, pen_width * 6):
            painter.drawLine(i, hatch_width, hatch_width + i, 0)

        painter.end()

        hatch_brush = QBrush(pixmap)

        # Calculate the offset based on the item's position in the view
        index = item.index()
        item_rect = view.visualRect(index)
        hatch_brush.setTransform(QTransform().translate(item_rect.x(), item_rect.y()))

        item.setBackground(hatch_brush)
        '''
