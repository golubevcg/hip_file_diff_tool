from typing import Dict, Optional

from hutil.Qt.QtWidgets import QLineEdit, QAbstractItemView
from hutil.Qt.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from hutil.Qt.QtGui import QStandardItem

from ui.custom_standart_item_model import DATA_ROLE, PATH_ROLE


class QTreeViewSearch(QLineEdit):
    def __init__(self, treeview, target_model, parent=None):
        super(QTreeViewSearch, self).__init__(parent)
        
        self.treeview = treeview
        self.target_model = target_model

        # Setup a QSortFilterProxyModel to handle filtering
        self.proxy_model = RecursiveFilterProxyModel(self.treeview)
        self.proxy_model.setSourceModel(self.target_model)
        self.treeview.setModel(self.proxy_model)

        # Set placeholder for the search field
        self.setPlaceholderText("Search...")

        # Connect signals
        self.textChanged.connect(self.filter_tree_view)
        self.returnPressed.connect(self.select_and_scroll_to_first_match)

    def filter_tree_view(self, text):
        """Filter the tree view based on the entered text."""
        # Use filterRegExp to search for partial matches
        regex_str = f".*{text}.*" if text else ".*"
        self.proxy_model.setFilterRegExp(regex_str)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def select_and_scroll_to_first_match(self):
        """Select and scroll to the first item that matches the search."""
        first_index = self.proxy_model.index(0, 0)
        if first_index.isValid():
            self.treeview.setCurrentIndex(first_index)
            self.treeview.scrollTo(first_index, QAbstractItemView.PositionAtTop)


class RecursiveFilterProxyModel(QSortFilterProxyModel):
    """Subclassing QSortFilterProxyModel to enable recursive filtering."""

    def __init__(self, *args, **kwargs):
        super(RecursiveFilterProxyModel, self).__init__(*args, **kwargs)
        self.view = None
        self.item_dictionary = None
        self.path_role = PATH_ROLE
        self.data_role = DATA_ROLE

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self.filter_accepts_row_itself(source_row, source_parent):
            return True
        
        # Check if any of the children matches
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        for i in range(self.sourceModel().rowCount(source_index)):
            if self.filterAcceptsRow(i, source_index):
                return True
        return False


    def filter_accepts_row_itself(self, source_row: int, source_parent: QModelIndex) -> bool:
        return super(RecursiveFilterProxyModel, self).filterAcceptsRow(source_row, source_parent)

    def filter_accepts_any_parent(self, source_row: int, source_parent: QModelIndex) -> bool:
        parent = source_parent
        while parent.isValid():
            if self.filter_accepts_row_itself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()
        return False

    def has_accepted_children(self, source_row: int, source_parent: QModelIndex) -> bool:
        child = self.sourceModel().index(source_row, 0, source_parent)
        if not child.isValid():
            return False

        if super(RecursiveFilterProxyModel, self).hasChildren(child):
            rows = self.sourceModel().rowCount(child)
            for i in range(rows):
                if self.filterAcceptsRow(i, child):
                    return True
        return False
    
    def itemFromIndex(self, proxy_index):
        """
        Get the item from the source model corresponding to the provided proxy index.
        
        :param proxy_index: The proxy model index.
        :return: The QStandardItem corresponding to the proxy_index.
        """
        source_index = self.mapToSource(proxy_index)
        return self.sourceModel().itemFromIndex(source_index)
    
    def indexFromItem(self, item):
        """
        Get the proxy model index corresponding to the provided QStandardItem.
        
        :param item: The QStandardItem.
        :return: The QModelIndex in the proxy model.
        """
        source_index = self.sourceModel().indexFromItem(item)
        return self.mapFromSource(source_index)
    
    def get_item_by_path(self, path: str) -> Optional[QStandardItem]:
        """Retrieve an item by its unique path."""

        if not self.item_dictionary:
            self.item_dictionary = self.sourceModel().item_dictionary

        return self.item_dictionary.get(path)
