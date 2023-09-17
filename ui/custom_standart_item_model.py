import os
import copy
import zipfile
from typing import Dict, Optional

from hutil.Qt.QtGui import (
    QPixmap,
    QIcon,
    QStandardItemModel,
    QStandardItem,
    QColor,
    QBrush,
)
from hutil.Qt.QtCore import Qt

from ui.constants import ICONS_ZIP_PATH, PATH_ROLE, DATA_ROLE, ICON_MAPPINGS


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
        """Associate the model with a tree view widget."""
        self.view = tree_view

    def _set_icon_from_zip(
        self, item: QStandardItem, icon_name: str, icons_zip: zipfile.ZipFile
    ) -> None:
        """Extract and set icon to item from given zip file."""
        try:
            with icons_zip.open(icon_name) as file:
                icon_data = file.read()
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                item.setIcon(QIcon(pixmap))
        except Exception:
            pass

    def add_item_with_path(
        self,
        item_text: str,
        path: str,
        data,
        icons_zip: zipfile.ZipFile,
        parent: Optional[QStandardItem] = None,
    ) -> None:
        """Add item with given attributes and associated path to the model."""
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

    def _add_parm_items(
        self, item: QStandardItem, data, parm_name: str, icons_zip: zipfile.ZipFile
    ) -> None:
        """Add parameters as child items to given item."""
        parm = data.get_parm_by_name(parm_name)

        if not parm.tag:
            return

        updated_parm_name = parm_name if parm.is_active else ""

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

        value = str(parm.value) if parm.is_active else ""
        value_path = f"{parm_path}/value"
        value_item = QStandardItem(value)
        value_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
        value_data = copy.copy(parm)
        value_data.tag = "value"
        value_item.setData(value_data, self.data_role)
        value_item.setData(value_path, self.path_role)

        parm_item.appendRow(value_item)
        self.item_dictionary[value_path] = value_item

    def get_item_by_path(self, path: str) -> Optional[QStandardItem]:
        """Return the item associated with given path."""
        return self.item_dictionary.get(path)

    def populate_with_data(self, data, view_name: str) -> None:
        """Populate the model with given data and associate with a view."""
        with zipfile.ZipFile(ICONS_ZIP_PATH, "r") as zip_ref:
            for path in data:
                node_data = data[path]
                node_name = node_data.name if node_data.name != "/" else view_name
                parent_path = node_data.parent_path
                parent_item = self.get_item_by_path(parent_path)
                if parent_item or parent_path == "/":
                    self.add_item_with_path(
                        node_name, path, node_data, zip_ref, parent=parent_item
                    )

        self.paint_items_and_expand(self.invisibleRootItem(), view_name)

    def paint_items_and_expand(self, parent_item, view_name: str) -> None:
        """Recursively style and expand items starting from the parent item."""
        for row in range(parent_item.rowCount()):
            for column in range(parent_item.columnCount()):
                child_item = parent_item.child(row, 0)
                if child_item:
                    self._apply_item_style_and_expansion(child_item)
                    self.paint_items_and_expand(child_item, view_name)

    def _apply_item_style_and_expansion(self, item: QStandardItem) -> None:
        """Style and expand the given item based on its properties."""
        item_data = item.data(Qt.UserRole + 2)
        color = item_data.color
        if color:
            qcolor = QColor(color)
            qcolor.setAlpha(item_data.alpha)
            item.setBackground(QBrush(qcolor))
        if item_data.tag and item_data.tag != "value":
            self.view.expand_to_index(item, self.view)
