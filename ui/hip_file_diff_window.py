import os
from zipfile import ZipFile

from hutil.Qt.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QMessageBox, QAbstractItemView
)
from hutil.Qt.QtCore import Qt, QSortFilterProxyModel

from api.hip_file_comparator import HipFileComparator
from ui.custom_qtree_view import CustomQTreeView
from ui.custom_standart_item_model import CustomStandardItemModel
from ui.file_selector import FileSelector
from ui.search_line_edit import QTreeViewSearch


class HipFileDiffWindow(QMainWindow):
    """
    Main window for displaying the differences between two .hip files.

    Attributes:
        hip_comparator (HipFileComparator): Instance to compare two hip files.
    """

    def __init__(self):
        super(HipFileDiffWindow, self).__init__()
        self.hip_comparator: HipFileComparator = None
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI components."""
        self.set_window_properties()
        self.setup_layouts()
        self.setup_tree_views()
        self.setup_signals_and_slots()
        self.apply_stylesheet()

    def set_window_properties(self) -> None:
        """Set main window properties."""
        self.setWindowTitle('.hip files diff tool')
        self.setGeometry(300, 300, 2000, 1300)
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

    def setup_layouts(self) -> None:
        """Setup main, source and target layouts for the main window."""
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.setup_source_layout()
        self.setup_target_layout()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.source_widget)
        splitter.addWidget(self.target_widget)
        splitter.setSizes([self.width() // 2, self.width() // 2])
        self.main_layout.addWidget(splitter)

    def setup_source_layout(self) -> None:
        """Setup layout for the source file section."""
        self.source_file_line_edit = FileSelector(self)
        self.source_file_line_edit.setPlaceholderText("Source file path")

        self.source_widget = QWidget()
        self.source_layout = QVBoxLayout(self.source_widget)
        self.source_layout.addWidget(self.source_file_line_edit)
        self.source_layout.setContentsMargins(3, 3, 3, 3)

    def setup_target_layout(self) -> None:
        """Setup layout for the target file section."""
        self.target_file_line_edit = FileSelector(self)
        self.target_file_line_edit.setObjectName("FileSelector")
        self.target_file_line_edit.setPlaceholderText("Target file path")

        self.load_button = QPushButton("Compare", self)
        self.load_button.setObjectName("compareButton")
        self.load_button.setFixedHeight(40)
        self.load_button.setFixedWidth(100)

        self.target_top_hlayout = QHBoxLayout()
        self.target_top_hlayout.addWidget(self.target_file_line_edit)
        self.target_top_hlayout.addWidget(self.load_button)

        self.target_widget = QWidget()
        self.target_layout = QVBoxLayout(self.target_widget)
        self.target_layout.addLayout(self.target_top_hlayout)
        self.target_layout.setContentsMargins(3, 3, 3, 3)

    def setup_tree_views(self) -> None:
        """Setup QTreeViews and associate models for source and target sections."""
        self.source_treeview = self.create_tree_view("source")
        self.source_model = CustomStandardItemModel()
        self.source_model.set_view(self.source_treeview)
        self.source_treeview.setModel(self.source_model)
        self.source_layout.addWidget(self.source_treeview)

        self.target_treeview = self.create_tree_view("target", hide_scrollbar=False)
        self.target_model = CustomStandardItemModel()
        self.target_model.set_view(self.target_treeview)
        self.target_treeview.setModel(self.target_model)
        self.target_layout.addWidget(self.target_treeview)

        self.source_search_qline_edit = QTreeViewSearch(self.source_treeview, self.source_model, self.target_treeview)
        self.source_search_qline_edit.setPlaceholderText("Search in source")
        self.source_layout.addWidget(self.source_search_qline_edit)

        self.target_search_qline_edit = QTreeViewSearch(self.target_treeview, self.target_model)
        self.target_search_qline_edit.setPlaceholderText("Search in target")
        self.target_layout.addWidget(self.target_search_qline_edit)

        self.source_search_qline_edit.second_search = self.target_search_qline_edit
        self.target_search_qline_edit.second_search = self.source_search_qline_edit

        self.target_search_qline_edit.secondary_treeview = self.source_treeview
        self.target_search_qline_edit.secondary_proxy_model = self.source_treeview.model()

        self.source_search_qline_edit.secondary_treeview = self.target_treeview
        self.source_search_qline_edit.secondary_proxy_model = self.target_treeview.model()

        
    def create_tree_view(self, obj_name: str, hide_scrollbar:bool = True ) -> CustomQTreeView:
        """
        Create a QTreeView with specified properties.

        :param obj_name: Object name for the QTreeView.
        :param hide_scrollbar: bool parameter hide scrollbar or not.

        :return: Configured QTreeView instance.
        """
        tree_view = CustomQTreeView(self)
        tree_view.setObjectName(obj_name)
        tree_view.header().hide()
        tree_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        tree_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        if hide_scrollbar:
            tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return tree_view

    def setup_signals_and_slots(self) -> None:
        """Connect signals to their respective slots."""
        self.load_button.clicked.connect(self.handle_compare_button_click)
        self.connect_tree_view_expansion(self.source_treeview)
        self.connect_tree_view_expansion(self.target_treeview)
        self.target_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.source_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)

    def connect_tree_view_expansion(self, tree_view: CustomQTreeView) -> None:
        """
        Connect expansion signals for a QTreeView.

        :param tree_view: The QTreeView instance.
        """
        tree_view.expanded.connect(lambda index: self.sync_expand(index, expand=True))
        tree_view.collapsed.connect(lambda index: self.sync_expand(index, expand=False))

    def apply_stylesheet(self) -> None:
        """Apply a custom stylesheet to the main window."""
        self.setStyleSheet(
        """
            QMainWindow{
                background-color: #3c3c3c;
            }
            QPushButton#compareButton {
                font: 10pt "Arial";
                color: #818181;
                background-color: #464646;
                border-radius: 10px;
            }
            QPushButton#compareButton:hover {
                color: #919191;
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
            }
            CustomQTreeView {
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
                border-radius: 10px;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url("ui/icons/vline.svg") 0;
                }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url("ui/icons/more.svg") 0;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url("ui/icons/end.svg") 0;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: url(ui/icons/closed.svg) 0;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: url("ui/icons/opened.svg") 0;
            }
            QTreeView::branch:!adjoins-item{
                border-image: url("ui/icons/empty.svg") 0;
            }
            QTreeView::item:hover {
                background: rgb(71, 71, 71);
            }
            QTreeView::item:selected {
                border: 1px solid rgb(185, 134, 32);
                background: rgb(96, 81, 50);
            }
            QScrollBar:vertical {
                border: none;
                background: #333333;
                width: 20px;
                border: 1px solid #3c3c3c;
            }
            QScrollBar::handle:vertical {
                background: #464646;
                min-width: 20px;
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 0;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QSplitter::handle {
                background-color: #3c3c3c;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
        """
        )

    def handle_compare_button_click(self) -> None:
        """Handle logic when the load button is clicked."""
        source_path = self.source_file_line_edit.text()
        target_path = self.target_file_line_edit.text()
        
        if not (os.path.exists(source_path) and os.path.exists(target_path)):
            QMessageBox.warning(self, "Invalid Paths", "Please select valid .hip files to compare.")
            return
        
        self.source_model.clear()
        self.target_model.clear()

        self.hip_comparator = HipFileComparator(source_path, target_path)
        self.hip_comparator.compare()

        # Assuming 'comparison_result' contains the differences, 
        # you can now update your tree views based on the results. 
        # This is a placeholder. You will likely have a more complex way of populating your views.
        self.source_model.populate_with_data(self.hip_comparator.source_data, self.source_treeview.objectName())
        self.target_model.populate_with_data(self.hip_comparator.target_data, self.target_treeview.objectName())

    def sync_expand(self, index, expand: bool = True) -> None:
        """
        Synchronize expansion state between tree views.

        :param index: QModelIndex of the item being expanded or collapsed.
        :param expand: Whether the item is expanded (True) or collapsed (False).
        """
        event_proxy_model = index.model()
        
        if isinstance(event_proxy_model, QSortFilterProxyModel):
            event_source_model = event_proxy_model.sourceModel()
        else:
            event_source_model = event_proxy_model

        if event_source_model == self.source_model:
            other_view = self.target_treeview
        else:
            other_view = self.source_treeview

        event_item = event_source_model.itemFromIndex(event_proxy_model.mapToSource(index))
        event_item_path = event_item.data(event_source_model.path_role)

        item_in_other_source_model = other_view.model().sourceModel().get_item_by_path(event_item_path)

        index_in_other_proxy = other_view.model().mapFromSource(other_view.model().sourceModel().indexFromItem(item_in_other_source_model))
        other_view.setExpanded(index_in_other_proxy, expand)

    def sync_scroll(self, value: int) -> None:
        """
        Synchronize vertical scrolling between tree views.

        :param value: Vertical scroll position.
        """
        # Fetch the source of the signal
        source_scrollbar = self.sender()
        
        # Determine the target scrollbar for synchronization
        if source_scrollbar == self.source_treeview.verticalScrollBar():
            target_scrollbar = self.target_treeview.verticalScrollBar()
        else:
            target_scrollbar = self.source_treeview.verticalScrollBar()
        
        # Update the target's scrollbar position to match the source's
        target_scrollbar.setValue(value)