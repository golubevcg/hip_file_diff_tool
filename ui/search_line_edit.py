import os
from typing import Set, Optional

from hutil.Qt.QtWidgets import QLineEdit, QAbstractItemView, QAction
from hutil.Qt.QtCore import Qt
from hutil.Qt.QtGui import QPixmap, QIcon

from ui.custom_standart_item_model import DATA_ROLE, PATH_ROLE, ICONS_PATH
from ui.recursive_filter_proxy_model import RecursiveFilterProxyModel


class QTreeViewSearch(QLineEdit):
    """Search widget for filtering items within a QTreeView."""
    
    def __init__(self, treeview, target_model, parent=None):
        super().__init__(parent)
        self.init_ui(treeview, target_model)
        self.init_events()
        self.init_styles()

    def init_ui(self, treeview, target_model):
        """Initialize UI components."""
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
        """Connect UI events."""
        self.search_action.triggered.connect(self.filter_tree_view)
        self.textChanged.connect(self.filter_tree_view)
        self.textChanged.connect(self.handle_text_change)
        self.returnPressed.connect(self.select_first_match)

    def init_styles(self):
        """Set widget styles."""
        self.setStyleSheet(
            '''
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
            '''
        )

    def filter_tree_view(self):
        """Filter the tree view based on the search input."""
        regex_str = f".*{self.text()}.*"
        self.proxy_model.setFilterRole(Qt.DisplayRole)
        self.proxy_model.setFilterRegExp(regex_str)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.synchronize_trees()

    def synchronize_trees(self):
        """Synchronize primary and secondary tree views."""
        visible_paths = self.get_visible_paths()
        self.filter_secondary_tree(visible_paths)

    def get_visible_paths(self) -> Set[str]:
        """Return set of visible paths in the primary tree."""
        visible_paths = set()
        root = self.proxy_model.index(0, 0)
        self.collect_paths(root, visible_paths)
        return visible_paths

    def collect_paths(self, index, paths: Set[str]):
        """Recursively collect paths from the given index."""
        if not index.isValid():
            return
        paths.add(self.proxy_model.data(index, PATH_ROLE))
        for row in range(self.proxy_model.rowCount(index)):
            child_index = self.proxy_model.index(row, 0, index)
            self.collect_paths(child_index, paths)
    
    def filter_secondary_tree(self, paths: Set[str]):
        """Filter the secondary tree view based on the visible paths."""

        self.secondary_proxy_model.setFilterFixedString("")
        if not paths:
            self.secondary_proxy_model.setFilterFixedString("ImpossibleStringThatMatchesNothing")
            return

        if self.secondary_proxy_model:
            self.secondary_proxy_model.set_filtered_paths(paths)
            self.secondary_treeview.expandAll()

    def select_first_match(self):
        """Select the first matching item in the tree view."""
        first_index = self.proxy_model.index(0, 0)
        if first_index.isValid():
            self.treeview.setCurrentIndex(first_index)
            self.treeview.scrollTo(first_index, QAbstractItemView.PositionAtTop)

    def capture_tree_state(self):
        """Capture the expanded state of the tree view items."""
        model = self.treeview.model()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            self._capture_state(index)

    def _capture_state(self, index):
        """Recursively capture the expanded state of tree view items."""
        if index.isValid():
            path = self.treeview.model().data(index, PATH_ROLE)
            self.expanded_state[path] = self.treeview.isExpanded(index)
            for row in range(self.treeview.model().rowCount(index)):
                child_index = self.treeview.model().index(row, 0, index)
                self._capture_state(child_index)

    def restore_tree_state(self):
        """Restore the expanded state of the tree view items."""
        model = self.treeview.model()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            self._restore_state(index)

    def _restore_state(self, index):
        """Recursively restore the expanded state of tree view items."""
        if index.isValid():
            path = self.treeview.model().data(index, PATH_ROLE)
            self.treeview.setExpanded(index, self.expanded_state.get(path, False))
            for row in range(self.treeview.model().rowCount(index)):
                child_index = self.treeview.model().index(row, 0, index)
                self._restore_state(child_index)

    def handle_text_change(self):
        """Handle text change event in the search widget."""
        if self.text():
            return
        self.restore_tree_state()
        if self.second_search:
            self.second_search.restore_tree_state()

    def focusInEvent(self, event):
        """Override focus in event to capture the state of the tree view."""
        super().focusInEvent(event)
        if not self.text():
            self.capture_tree_state()
            if self.second_search:
                self.second_search.capture_tree_state()
