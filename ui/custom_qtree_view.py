from typing import List

from hutil.Qt.QtWidgets import QTreeView
from hutil.Qt.QtCore import Qt, QModelIndex
from hutil.Qt.QtGui import QMouseEvent

class CustomQTreeView(QTreeView):
    """
    CustomQTreeView class for drawing references as main data tree.
    """

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events. Expands or collapses all children when 
        the shift key is pressed during the click.

        :param event: The mouse event.
        """
        super(CustomQTreeView, self).mousePressEvent(event)

        if event.modifiers() & Qt.ShiftModifier:
            self.expand_or_collapse_all(self.indexAt(event.pos()))

    def expand_or_collapse_all(self, index: QModelIndex) -> None:
        """
        Toggles the expansion state (expand if collapsed, collapse if expanded)
        for the given index and all its descendants.

        :param index: QModelIndex from the QTreeView.
        """
        toggle_expansion = not self.isExpanded(index)
        self.recursive_expand_or_collapse(index, toggle_expansion)
        self.setExpanded(index, toggle_expansion)

    def recursive_expand_or_collapse(self, index: QModelIndex, expand: bool) -> None:
        """
        Recursively toggles the expansion state for the given index and its descendants.

        :param index: QModelIndex from the QTreeView.
        :param expand: Boolean indicating whether to expand or collapse.
        """
        for child_row in range(self.model().rowCount(index)):
            child_index = index.child(child_row, 0)
            self.recursive_expand_or_collapse(child_index, expand)
            self.setExpanded(child_index, expand)

    def expand_to_index(self, item, treeview: QTreeView) -> None:
        """
        Expands the treeview to the specified item's index.
        
        :param item: The item to expand to.
        :param treeview: The QTreeView to expand.
        """
        index = treeview.model().indexFromItem(item)
        parent = index.parent()
        while parent.isValid():
            treeview.expand(parent)
            parent = parent.parent()

    def get_child_indices(self, index: QModelIndex) -> List[QModelIndex]:
        """
        Return all child indices for the given index.

        :param index: QModelIndex from the QTreeView.
        :return: A list of QModelIndex representing each child.
        """
        return [index.child(row, 0) for row in range(self.model().rowCount(index))]
