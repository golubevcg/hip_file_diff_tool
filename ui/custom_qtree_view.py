from hutil.Qt.QtWidgets import QTreeView
from hutil.Qt.QtCore import Qt


class CustomQTreeView(QTreeView):
    """
    CustomQTreeView class for drawing references as main data tree.
    """

    def mousePressEvent(self, event):
        super(CustomQTreeView, self).mousePressEvent(event)

        # Expand or collapse all children when shift is pressed on click.
        if event.modifiers() & Qt.ShiftModifier:
            self.expand_or_collapse_all(self.indexAt(event.pos()))

    def expand_or_collapse_all(self, index):
        """
        Toggles the expansion state (expand if collapsed, collapse if expanded)
        for the given index and all its descendants.
        
        :param index: QModelIndex from QTreeView.
        """
        # Determine the opposite of the current expansion state for the index.
        toggle_expansion = self.isExpanded(index)
        self.recursive_expand_or_collapse(index, toggle_expansion)
        # Finally, toggle the expansion state for the provided index.
        self.setExpanded(index, toggle_expansion)

    def recursive_expand_or_collapse(self, index, expand):
        """
        Recursively toggles the expansion state for the given index and its descendants.
        
        :param index: QModelIndex from QTreeView.
        :param expand: Boolean indicating whether to expand or collapse.
        """
        for child_row in range(self.model().rowCount(index)):
            child_index = index.child(child_row, 0)
            self.recursive_expand_or_collapse(child_index, expand)
            self.setExpanded(child_index, expand)

    def expand_to_index(self, index, treeview):
        parent = index.parent()
        if not parent.isValid():
            return
        while parent.isValid():
            treeview.expand(parent)
            parent = parent.parent()

    def get_child_indices(self, index):
        """
        Return all child indices for the given index.
        
        :param index: QModelIndex from QTreeView.
        :return: A list of QModelIndex representing each child.
        """
        return [index.child(row, 0) for row in range(self.model().rowCount(index))]
