import os
import re
from typing import Dict, Optional

from hutil.Qt.QtWidgets import QLineEdit, QAbstractItemView, QAction
from hutil.Qt.QtCore import Qt, QSortFilterProxyModel, QModelIndex, QRegularExpression
from hutil.Qt.QtGui import QStandardItem, QPixmap, QIcon

from ui.custom_standart_item_model import DATA_ROLE, PATH_ROLE, ICONS_PATH


class QTreeViewSearch(QLineEdit):
    def __init__(self, treeview, target_model, parent=None):
        super(QTreeViewSearch, self).__init__(parent)
        
        self.treeview = treeview
        self.target_model = target_model

        # Setup a QSortFilterProxyModel to handle filtering
        self.proxy_model = RecursiveFilterProxyModel(self.treeview)
        self.proxy_model.setSourceModel(self.target_model)
        self.treeview.setModel(self.proxy_model)
        
        self.expanded_state_captured = False

        # Set placeholder for the search field
        self.setPlaceholderText("Search")
        # Add a search action (icon) to the right of the line edit
        self.search_action = QAction(self)
        # Setting button icon
        pixmap = QPixmap(os.path.join(ICONS_PATH, "search.png"))
        self.search_action.setIcon(QIcon(pixmap))
        self.addAction(self.search_action, QLineEdit.TrailingPosition)
        self.search_action.triggered.connect(self.on_search_icon_clicked)

        # Connect signals
        self.textChanged.connect(self.filter_tree_view)
        self.returnPressed.connect(self.select_and_scroll_to_first_match)

        self.secondary_proxy_model = None
        self.secondary_treeview = None

        self.setStyleSheet(
            '''
            QLineEdit{
                font: 10pt "Arial";
                color: #818181;
                background-color: white;
                border-radius: 10px;
                padding-left: 5px;
                padding-right: 5px;
                padding-top: 2px;
                padding-bottom: 2px;
            }
            QLineEdit:hover, QLineEdit:selected {
                color: #919191;
                background-color: white;
            }            
            '''
        )

    def on_search_icon_clicked(self):
        self.filter_tree_view(self.text())

    def filter_tree_view(self, text):
        """Filter the tree view based on the entered text."""
        # Use filterRegExp to search for partial matches
        if not text:  # if the search box is cleared
            self.restore_expanded_state()
            self.expanded_state_captured = False  # reset the flag
            # Also, you might want to clear the filter on the proxy model
            self.proxy_model.setFilterRegExp(".*")
            return

        # Capture the current expanded state only if it hasn't been captured yet
        if not self.expanded_state_captured:
            self.capture_expanded_state()
            self.expanded_state_captured = True

        # Now filter the tree as per the search text
        regex_str = f".*{text}.*"
        self.proxy_model.setFilterRole(Qt.DisplayRole)
        self.proxy_model.setFilterRegExp(regex_str)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.synchronize_secondary_tree()

    def synchronize_secondary_tree(self):
        """Filter items in the secondary tree view based on the visible items in the primary tree view."""
        visible_paths = self.get_visible_paths_from_primary_tree()
        self.filter_secondary_tree_by_paths(visible_paths)

    def get_visible_paths_from_primary_tree(self):
        """Collect path attributes from the visible items in the primary tree view."""
        visible_paths = set()
        root = self.proxy_model.index(0, 0)
        self.collect_paths(root, visible_paths)
        return visible_paths

    def collect_paths(self, index, visible_paths):
        if not index.isValid():
            return
        
        item = self.proxy_model.itemFromIndex(index)
        path = item.data(PATH_ROLE)
        visible_paths.add(path)

        # Iterate over the children
        row_count = self.proxy_model.rowCount(index)
        for row in range(row_count):
            child_index = self.proxy_model.index(row, 0, index)
            self.collect_paths(child_index, visible_paths)
    
    def filter_secondary_tree_by_paths(self, paths):
        """Filter the secondary tree view to only show items with the given paths."""
        self.secondary_proxy_model.setFilterFixedString("")  # Clear any existing filter
        
        self.secondary_proxy_model.setFilterRole(1)
        self.secondary_proxy_model.setFilterRegularExpression(QRegularExpression("|".join(re.escape(path) for path in paths)))
        self.secondary_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.secondary_proxy_model.invalidateFilter()

        # Ensure all matches are shown
        self.secondary_treeview.expandAll()

    def select_and_scroll_to_first_match(self):
        """Select and scroll to the first item that matches the search."""
        first_index = self.proxy_model.index(0, 0)
        if first_index.isValid():
            self.treeview.setCurrentIndex(first_index)
            self.treeview.scrollTo(first_index, QAbstractItemView.PositionAtTop)

    def capture_expanded_state(self):
        self.expanded_state = {}
        model = self.treeview.model()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            self._capture_recursive(index)

    def _capture_recursive(self, index):
        model = self.treeview.model()
        if index.isValid():
            item = model.itemFromIndex(index)
            if item:
                path = item.data(model.path_role)
                self.expanded_state[path] = self.treeview.isExpanded(index)
            for row in range(model.rowCount(index)):
                child_index = model.index(row, 0, index)
                self._capture_recursive(child_index)
    
    def restore_expanded_state(self):
        if not hasattr(self, 'expanded_state'):
            return
        model = self.treeview.model()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            self._restore_recursive(index)

    def _restore_recursive(self, index):
        model = self.treeview.model()
        if index.isValid():
            item = model.itemFromIndex(index)
            if item:
                path = item.data(model.path_role)
                is_expanded = self.expanded_state.get(path, False)
                self.treeview.setExpanded(index, is_expanded)
            for row in range(model.rowCount(index)):
                child_index = model.index(row, 0, index)
                self._restore_recursive(child_index)



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
