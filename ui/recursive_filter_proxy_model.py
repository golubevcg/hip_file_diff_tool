from typing import Optional, Set

from hutil.Qt.QtCore import QSortFilterProxyModel, QModelIndex
from hutil.Qt.QtGui import QStandardItem

from ui.constants import DATA_ROLE, PATH_ROLE
from api.node_data import NodeState
from api.param_data import ParamState


class RecursiveFilterProxyModel(QSortFilterProxyModel):
    """
    Subclass of QSortFilterProxyModel that enables recursive filtering.
    Provides custom behaviors like path-specific filtering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path_role = PATH_ROLE
        self.data_role = DATA_ROLE
        self._filtered_paths: Set[str] = set()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        """Check if a row in the source model should be included in the proxy model."""
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        item_path = self.sourceModel().data(source_index, self.path_role)

        # If there's an active filter for paths and the item's path isn't in it, reject this row.
        if self._filtered_paths and item_path not in self._filtered_paths:
            return False

        # If source model has a condition to show only edited items
        if (
            hasattr(self.sourceModel(), "show_only_edited")
            and self.sourceModel().show_only_edited
        ):
            if not self.conditionForItem(source_index):
                return False

        # Check if the current row matches the filter itself
        if self.filter_accepts_row_itself(source_row, source_parent):
            return True

        # Recursively check child items
        for i in range(self.sourceModel().rowCount(source_index)):
            if self.filterAcceptsRow(i, source_index):
                return True

        return False

    def conditionForItem(self, index: QModelIndex) -> bool:
        """
        Check the condition for a given item.

        :param index: QModelIndex representing the item.
        :return: True if the item matches the condition, False otherwise.
        """
        state_value = self.sourceModel().data(index, self.data_role).state
        if state_value not in [NodeState.UNCHANGED, ParamState.UNCHANGED]:
            return True

        for i in range(self.sourceModel().rowCount(index)):
            child_index = self.sourceModel().index(i, 0, index)
            if self.conditionForItem(child_index):
                return True

        return False

    def filter_accepts_row_itself(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        """Check if the source row itself meets the filter criteria."""
        return super().filterAcceptsRow(source_row, source_parent)

    def itemFromIndex(self, proxy_index: QModelIndex) -> QStandardItem:
        """Retrieve the item from the source model corresponding to the given proxy index."""
        source_index = self.mapToSource(proxy_index)
        return self.sourceModel().itemFromIndex(source_index)

    def indexFromItem(self, item: QStandardItem) -> QModelIndex:
        """Retrieve the proxy model index corresponding to the given QStandardItem."""
        source_index = self.sourceModel().indexFromItem(item)
        return self.mapFromSource(source_index)

    def get_item_by_path(self, path: str) -> Optional[QStandardItem]:
        """
        Retrieve an item by its unique path.

        :param path: Unique path identifier for the item.
        :return: QStandardItem if found, otherwise None.
        """
        item_dictionary = getattr(self.sourceModel(), "item_dictionary", None)
        return item_dictionary.get(path) if item_dictionary else None

    def set_filtered_paths(self, paths: Set[str]) -> None:
        """
        Define a set of paths to filter by.

        :param paths: Set of paths to be used for filtering.
        """
        self._filtered_paths = paths
        self.invalidateFilter()

    def reset_proxy_view(self) -> None:
        """Reset the view by clearing filters and sorting."""
        self.set_filtered_paths(set())  # Clear the paths filter
        self.setFilterFixedString("")
        self.sort(-1)
        self.invalidateFilter()
