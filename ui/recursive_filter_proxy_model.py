from typing import Dict, Optional, Set

from hutil.Qt.QtCore import QSortFilterProxyModel, QModelIndex
from hutil.Qt.QtGui import QStandardItem

from ui.custom_standart_item_model import DATA_ROLE, PATH_ROLE

class RecursiveFilterProxyModel(QSortFilterProxyModel):
    """
    Subclass of QSortFilterProxyModel that enables recursive filtering.
    Provides custom behaviors like path-specific filtering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = None
        self.item_dictionary = None
        self.path_role = PATH_ROLE
        self.data_role = DATA_ROLE
        self._filtered_paths: Set[str] = set()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determine if a row should be included based on filtering conditions.
        
        :param source_row: Row number in the source model.
        :param source_parent: Parent index in the source model.
        :return: True if the row is accepted, False otherwise.
        """
        
        index = self.sourceModel().index(source_row, 0, source_parent)
        item_path = self.sourceModel().data(index, self.path_role)

        if self.sourceModel().show_only_edited:
            return self.conditionForItem(index)
            
        # Path-specific filtering
        if self._filtered_paths and item_path not in self._filtered_paths:
            return False
        
        # Original recursive behavior:
        if self.filter_accepts_row_itself(source_row, source_parent):
            return True
        
        # Check children matches
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        for i in range(self.sourceModel().rowCount(source_index)):
            if self.filterAcceptsRow(i, source_index):
                return True
        return False
    
    def conditionForItem(self, index: QModelIndex) -> bool:
        """Check the new condition for a given item."""
    
        tag_value = self.sourceModel().data(index, self.data_role).tag
        print("tag_value", tag_value)
        if tag_value:
            print("returning true")
            return True
        
        # Recursively check child items
        for i in range(self.sourceModel().rowCount(index)):
            child_index = self.sourceModel().index(i, 0, index)
            if self.conditionForItem(child_index):
                print("returning true in child")
                return True
            
        return False

    def filter_accepts_row_itself(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Check if the source row itself meets the filter criteria.
        
        :param source_row: Row number in the source model.
        :param source_parent: Parent index in the source model.
        :return: True if the row is accepted, False otherwise.
        """
        return super().filterAcceptsRow(source_row, source_parent)

    def filter_accepts_any_parent(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Check if any parent of the source row meets the filter criteria.
        
        :param source_row: Row number in the source model.
        :param source_parent: Parent index in the source model.
        :return: True if any parent is accepted, False otherwise.
        """
        parent = source_parent
        while parent.isValid():
            if self.filter_accepts_row_itself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()
        return False

    def has_accepted_children(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Check if the source row has any children that meet the filter criteria.
        
        :param source_row: Row number in the source model.
        :param source_parent: Parent index in the source model.
        :return: True if any child is accepted, False otherwise.
        """
        child = self.sourceModel().index(source_row, 0, source_parent)
        if child.isValid() and super().hasChildren(child):
            for i in range(self.sourceModel().rowCount(child)):
                if self.filterAcceptsRow(i, child):
                    return True
        return False

    def itemFromIndex(self, proxy_index: QModelIndex) -> QStandardItem:
        """
        Retrieve the item from the source model corresponding to the given proxy index.
        
        :param proxy_index: The proxy model index.
        :return: The QStandardItem corresponding to the proxy_index.
        """
        source_index = self.mapToSource(proxy_index)
        return self.sourceModel().itemFromIndex(source_index)

    def indexFromItem(self, item: QStandardItem) -> QModelIndex:
        """
        Retrieve the proxy model index corresponding to the given QStandardItem.
        
        :param item: The QStandardItem.
        :return: The QModelIndex in the proxy model.
        """
        source_index = self.sourceModel().indexFromItem(item)
        return self.mapFromSource(source_index)

    def get_item_by_path(self, path: str) -> Optional[QStandardItem]:
        """
        Retrieve an item by its unique path.
        
        :param path: Unique path identifier for the item.
        :return: QStandardItem if found, otherwise None.
        """
        if not self.item_dictionary:
            self.item_dictionary = self.sourceModel().item_dictionary

        return self.item_dictionary.get(path)

    def set_filtered_paths(self, paths: Set[str]) -> None:
        """
        Define a set of paths to filter by.
        
        :param paths: Set of paths to be used for filtering.
        """
        self._filtered_paths = paths
        self.invalidateFilter()
