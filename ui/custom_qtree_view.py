import os
from typing import List

from hutil.Qt.QtWidgets import QTreeView, QMenu, QAction
from hutil.Qt.QtCore import Qt, QModelIndex
from hutil.Qt.QtGui import QMouseEvent, QPainter, QPixmap, QIcon, QColor
from ui.constants import ICONS_PATH
from ui.ui_utils import generate_link_to_clipboard


class CustomQTreeView(QTreeView):
    """
    A custom QTreeView that provides additional functionalities such as
    recursive expanding/collapsing of items and enhanced mouse click handling.
    """

    def __init__(self, parent=None):
        super(CustomQTreeView, self).__init__(parent)
        self.parent_application = parent

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events to detect a Shift+Click
        and expand or collapse all children of the clicked node accordingly.

        :param event: The mouse event triggered by user's action.
        """
        super().mousePressEvent(event)

        if event.modifiers() & Qt.ShiftModifier:
            self.expand_or_collapse_all(self.indexAt(event.pos()))

    def expand_or_collapse_all(self, index: QModelIndex) -> None:
        """
        Toggle the expansion state for the specified index and its
        descendants.

        :param index: The QModelIndex of the item in the QTreeView.
        """
        toggle_expansion = not self.isExpanded(index)
        self.recursive_expand_or_collapse(index, toggle_expansion)
        self.setExpanded(index, toggle_expansion)

    def recursive_expand_or_collapse(
        self, index: QModelIndex, expand: bool
    ) -> None:
        """
        Recursively set the expansion state for the given index
         and its descendants.

        :param index: QModelIndex of the item in the QTreeView.
        :param expand: Boolean indicating desired state
                       (True for expand, False for collapse).
        """
        for child_row in range(self.model().rowCount(index)):
            child_index = index.child(child_row, 0)
            self.recursive_expand_or_collapse(child_index, expand)
            self.setExpanded(child_index, expand)

    def expand_to_index(self, item, treeview: QTreeView) -> None:
        """
        Expand the QTreeView to reveal the specified item.

        :param item: The QStandardItem whose position in the tree
                     you want to reveal.
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
        return [
            index.child(row, 0) for row in range(self.model().rowCount(index))
        ]

    def paintEvent(self, event) -> None:
        """
        Handle painting the QTreeView, enabling anti-aliasing
        for smoother visuals.

        :param event: The paint event triggered by the Qt framework.
        """
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)
        super().paintEvent(event)

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        
        item_path = index.data(index.model().path_role)

        copy_path_action = QAction("Copy node path", self)
        copy_path_action.triggered.connect(
            lambda checked=False, path=item_path: self._copy_path_to_clipboard(path)
        )

        copy_link_action = QAction("Copy link", self)
        copy_link_action.triggered.connect(
            lambda checked=False, path=item_path: self._copy_link_to_clipboard(path)
        )

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #505050;
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 10px 20px 10px 40px;
            }
            QMenu::item:selected {
                background-color: #606060;
            }
        """)
        menu.addAction(copy_path_action)
        menu.addAction(copy_link_action)
        menu.exec_(event.globalPos())


    def _copy_path_to_clipboard(self, item_path):
        print("ITEM_PATH_INSIDE_FUNC:", item_path)
        self.parent_application.clipboard.setText(item_path)

    def _copy_link_to_clipboard(self, item_path):
        generate_link_to_clipboard(self.parent_application, item_path)