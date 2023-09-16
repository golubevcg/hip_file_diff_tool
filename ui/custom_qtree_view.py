from typing import List

from hutil.Qt.QtWidgets import QTreeView
from hutil.Qt.QtCore import Qt, QModelIndex
from hutil.Qt.QtGui import QMouseEvent, QPainter


class CustomQTreeView(QTreeView):
    """
    A custom QTreeView that provides additional functionalities such as 
    recursive expanding/collapsing of items and enhanced mouse click handling.
    """

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events to detect a Shift+Click and expand or collapse
        all children of the clicked node accordingly.

        :param event: The mouse event triggered by user's action.
        """
        super().mousePressEvent(event)

        if event.modifiers() & Qt.ShiftModifier:
            self.expand_or_collapse_all(self.indexAt(event.pos()))

    def expand_or_collapse_all(self, index: QModelIndex) -> None:
        """
        Toggle the expansion state for the specified index and its descendants.

        :param index: The QModelIndex of the item in the QTreeView.
        """
        toggle_expansion = not self.isExpanded(index)
        self.recursive_expand_or_collapse(index, toggle_expansion)
        self.setExpanded(index, toggle_expansion)

    def recursive_expand_or_collapse(self, index: QModelIndex, expand: bool) -> None:
        """
        Recursively set the expansion state for the given index and its descendants.

        :param index: QModelIndex of the item in the QTreeView.
        :param expand: Boolean indicating desired state (True for expand, False for collapse).
        """
        for child_row in range(self.model().rowCount(index)):
            child_index = index.child(child_row, 0)
            self.recursive_expand_or_collapse(child_index, expand)
            self.setExpanded(child_index, expand)

    def expand_to_index(self, item, treeview: QTreeView) -> None:
        """
        Expand the QTreeView to reveal the specified item.

        :param item: The QStandardItem whose position in the tree you want to reveal.
        :param treeview: The QTreeView in which the item resides.
        """
        index = treeview.model().indexFromItem(item)
        parent = index.parent()
        while parent.isValid():
            treeview.expand(parent)
            parent = parent.parent()

    def get_child_indices(self, index: QModelIndex) -> List[QModelIndex]:
        """
        Retrieve all child indices for the given index.

        :param index: QModelIndex of the item in the QTreeView.
        :return: List of QModelIndex instances representing each child.
        """
        return [index.child(row, 0) for row in range(self.model().rowCount(index))]

    def paintEvent(self, event) -> None:
        """
        Handle painting the QTreeView, enabling anti-aliasing for smoother visuals.

        :param event: The paint event triggered by the Qt framework.
        """
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)
        super().paintEvent(event)
