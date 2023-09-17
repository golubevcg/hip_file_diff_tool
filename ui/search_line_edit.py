import os
from typing import Set, Optional

from hutil.Qt.QtWidgets import QWidget, QLineEdit, QAbstractItemView, QAction
from hutil.Qt.QtCore import Qt
from hutil.Qt.QtGui import QPixmap, QIcon

from ui.constants import DATA_ROLE, PATH_ROLE, ICONS_PATH
from ui.recursive_filter_proxy_model import RecursiveFilterProxyModel


class QTreeViewSearch(QLineEdit):
    """Search widget for filtering items within a QTreeView."""

    def __init__(self, treeview, target_model, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui(treeview, target_model)
        self.init_events()
        self.init_styles()

    def init_ui(self, treeview, target_model):
        """Initialize user interface components."""
        self.treeview = treeview
        self.target_model = target_model
        self.proxy_model = RecursiveFilterProxyModel(self.treeview)
        self.proxy_model.setSourceModel(self.target_model)
        self.treeview.setModel(self.proxy_model)

        self.expanded_state = {}
        self.setPlaceholderText("Search")

        pixmap = QPixmap(os.path.join(ICONS_PATH, "search.png"))
        self.search_action = QAction(self)
        self.search_action.setIcon(QIcon(pixmap))
        self.addAction(self.search_action, QLineEdit.TrailingPosition)

        self.secondary_proxy_model = None
        self.secondary_treeview = None
        self.second_search = None

    def init_events(self):
        """Connect UI events to their handlers."""
        self.search_action.triggered.connect(self.filter_tree_view)
        self.textChanged.connect(self.filter_tree_view)
        self.returnPressed.connect(self.select_first_match)

    def init_styles(self):
        """Set the visual styles for the search widget."""
        self.setStyleSheet(
            """
            QLineEdit{
                font: 10pt "Arial";
                color: #818181;
                background-color: white;
                border-radius: 10px;
                padding: 2px 5px;
            }
            QLineEdit:hover, QLineEdit:selected {
                color: #919191;
                background-color: white;
            }            
            """
        )

    def filter_tree_view(self):
        """Apply filter on tree view based on search input."""
        self.proxy_model.reset_proxy_view()
        self.secondary_proxy_model.reset_proxy_view()

        search_text = self.text().strip()
        if not search_text:
            self.restore_tree_state()
            if self.second_search:
                self.second_search.restore_tree_state()
            return

        self.proxy_model.setFilterRole(Qt.DisplayRole)
        self.proxy_model.setFilterFixedString(search_text)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.proxy_model.invalidateFilter()
        self.synchronize_trees()

    def synchronize_trees(self):
        """Keep the primary and secondary tree views in sync."""
        visible_paths = self.get_visible_paths()
        self.filter_secondary_tree(visible_paths)

    def get_visible_paths(self) -> Set[str]:
        """Retrieve paths that are visible in the primary tree view."""
        visible_paths = set()
        root = self.proxy_model.index(0, 0)
        self.collect_paths(root, visible_paths)
        return visible_paths

    def collect_paths(self, index, paths: Set[str]):
        """Recursively gather paths visible from the given index."""
        if not index.isValid():
            return

        paths.add(self.proxy_model.data(index, PATH_ROLE))
        for row in range(self.proxy_model.rowCount(index)):
            child_index = self.proxy_model.index(row, 0, index)
            self.collect_paths(child_index, paths)

    def filter_secondary_tree(self, paths: Set[str]):
        """Update items in the secondary tree view based on provided paths."""
        self.secondary_proxy_model.setFilterFixedString("")
        if not paths:
            self.secondary_proxy_model.setFilterFixedString(
                "ImpossibleStringThatMatchesNothing"
            )
            return

        if self.secondary_proxy_model:
            self.secondary_proxy_model.set_filtered_paths(paths)
            self.proxy_model.set_filtered_paths(paths)
            self.secondary_treeview.expandAll()

    def select_first_match(self):
        """Highlight the first item in tree view that matches the search."""
        first_index = self.proxy_model.index(0, 0)
        if first_index.isValid():
            self.treeview.setCurrentIndex(first_index)
            self.treeview.scrollTo(first_index, QAbstractItemView.PositionAtTop)

    def capture_tree_state(self):
        """Remember the current expanded/collapsed state of tree view items."""
        for row in range(self.treeview.model().rowCount()):
            index = self.treeview.model().index(row, 0)
            self._capture_state(index)

    def _capture_state(self, index):
        """Recursively store the expansion state of tree view items."""
        if index.isValid():
            path = self.treeview.model().data(index, PATH_ROLE)
            self.expanded_state[path] = self.treeview.isExpanded(index)
