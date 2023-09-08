from hutil.Qt.QtWidgets import QTreeView
from hutil.Qt.QtCore import Qt


class CustomQTreeView(QTreeView):

    """
    CustomQTreeView class for drawing references as main data tree
    """

    def mousePressEvent(self, event):
        # deselect in empty item
        super(CustomQTreeView, self).mousePressEvent(event)

        # expand all childs when shift is pressed on click
        shift = event.modifiers() & Qt.ShiftModifier
        if shift:
            self.expand_all( self.indexAt(event.pos()) )

    def expand_all(self, index):

        """
        Expands/collapses (depends on current state) all the children and grandchildren etc. of index.
        :param index: QModelIndex from QTreeView
        """

        expand = self.isExpanded(index)
        if  expand:
            self.setExpanded(index, expand)    

        items_list = self.get_childs_list_for_index(index)
        self.recursive_expand(index, len(items_list), expand)

        if not expand: #if expanding, do that last (wonky animation otherwise)
            self.setExpanded(index, expand)

    def recursive_expand(self, index, childCount, expand):

        """
        Recursively expands/collpases all the children of index.
        :param index: QModelIndex from QTreeView
        :param childCount: int amount of childs for given index
        :param expand: bool expand parameter
        """

        for childNo in range(0, childCount):
            childIndex = index.child(childNo, 0)

            if not expand:
                self.setExpanded(index, expand)  

            items_list = self.get_childs_list_for_index(childIndex)
       
            if len(items_list) > 0:
                self.recursive_expand(childIndex, len(items_list), expand)

            if expand:
                self.setExpanded(childIndex, expand)

    def get_childs_list_for_index(self, index):
       
        """
        Return all child items for given item index.
        :param index: QModelIndex from QTreeView
        :return list: list of QStandardItems
        """

        items_list = []
        item = self.model().itemFromIndex(index)
        for row in range(item.rowCount()):
            children = item.child(row, 0)
            items_list.append(item)

        return items_list
