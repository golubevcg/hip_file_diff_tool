import os
import zipfile

from hutil.Qt.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
                                QMessageBox, QAbstractItemView)
from hutil.Qt.QtCore import Qt
from hutil.Qt.QtGui import QColor, QBrush, QPixmap, QPen, QPainter

from api.hip_file_comparator import HipFileComparator, SUPPORTED_FILE_FORMATS
from ui.custom_qtree_view import CustomQTreeView
from ui.custom_standart_item_model import CustomStandardItemModel, ICONS_ZIP_PATH
from ui.file_selector import FileSelector


class HipFileDiffWindow(QMainWindow):
    """Main window to show diff between two .hip files."""

    def __init__(self):
        super(HipFileDiffWindow, self).__init__()
        self.init_ui()
        self.hip_comparator = None

    def init_ui(self):
        """Initialize UI components."""
        self.set_window_properties()
        self.setup_layouts()
        self.setup_tree_views()
        self.setup_signals_and_slots()
        self.apply_stylesheet()
        self.load_button.click()

    def set_window_properties(self):
        """Set main window properties."""
        self.setWindowTitle('.hip files diff tool')
        self.setGeometry(300, 300, 2000, 1300)
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

    def setup_layouts(self):
        """Setup layouts."""
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.setup_source_layout()
        self.setup_target_layout()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.source_widget)
        splitter.addWidget(self.target_widget)
        splitter.setSizes([self.width() // 2, self.width() // 2])
        self.main_layout.addWidget(splitter)

    def setup_source_layout(self):
        """Setup source file layout."""
        self.source_file_line_edit = FileSelector(self)
        self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source.hipnc")
        self.source_file_line_edit.setPlaceholderText("source_file_line_edit")
        
        self.source_widget = QWidget()
        self.source_layout = QVBoxLayout(self.source_widget)
        self.source_layout.addWidget(self.source_file_line_edit)
        self.source_layout.setContentsMargins(5, 5, 5, 5)

    def setup_target_layout(self):
        """Setup target file layout."""
        self.target_file_line_edit = FileSelector(self)    
        self.target_file_line_edit.setObjectName("FileSelector")    
        self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source_edited.hipnc")
        self.target_file_line_edit.setPlaceholderText("target_file_line_edit")
        
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
        self.target_layout.setContentsMargins(5, 5, 5, 5)

    def setup_tree_views(self):
        """Setup QTreeViews for both source and target."""
        self.source_treeview = self.create_tree_view("source")
        self.source_model = CustomStandardItemModel()
        self.source_model.set_view(self.source_treeview)
        self.source_treeview.setModel(self.source_model)
        self.source_layout.addWidget(self.source_treeview)
        
        self.target_treeview = self.create_tree_view("target")
        self.target_model = CustomStandardItemModel()
        self.target_model.set_view(self.target_treeview)
        self.target_treeview.setModel(self.target_model)
        self.target_layout.addWidget(self.target_treeview)

    def create_tree_view(self, obj_name):
        """Create a QTreeView with common properties."""
        tree_view = CustomQTreeView(self)
        tree_view.setObjectName(obj_name)
        tree_view.header().hide()
        tree_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        tree_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return tree_view

    def setup_signals_and_slots(self):
        """Connect signals to slots."""
        self.load_button.clicked.connect(self.handle_load_button_click)
        self.connect_tree_view_expansion(self.source_treeview)
        self.connect_tree_view_expansion(self.target_treeview)
        self.target_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.source_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)

    def connect_tree_view_expansion(self, tree_view):
        """Connect expansion signals for a QTreeView."""
        tree_view.expanded.connect(lambda index: self.sync_expand(index, expand=True))
        tree_view.collapsed.connect(lambda index: self.sync_expand(index, expand=False))

    def apply_stylesheet(self):
        """Apply stylesheet to the main window."""
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
            QSplitter::handle {
                background-color: #3c3c3c;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
        """
        )

    def handle_load_button_click(self):
        """Handle the logic when the load button is clicked."""
        source_path = self.source_file_line_edit.text()
        target_path = self.target_file_line_edit.text()
        
        if not (os.path.exists(source_path) and os.path.exists(target_path)):
            QMessageBox.warning(self, "Invalid Paths", "Please select valid .hip files to compare.")
            return
        
        self.hip_comparator = HipFileComparator(source_path, target_path)
        self.hip_comparator.compare()

        # Assuming 'comparison_result' contains the differences, 
        # you can now update your tree views based on the results. 
        # This is a placeholder. You will likely have a more complex way of populating your views.
        self.source_model.populate_with_data(self.hip_comparator.source_data, self.source_treeview.objectName())
        self.target_model.populate_with_data(self.hip_comparator.target_data, self.target_treeview.objectName())

    def sync_expand(self, index, expand=True):
        """Synchronize the expansion state between tree views."""
        event_model = index.model()
        if event_model == self.source_model:
            other_view = self.target_treeview
        else:
            other_view = self.source_treeview

        event_item = event_model.itemFromIndex(index)
        event_item_path = event_item.data(event_model.path_role)

        item = other_view.model().get_item_by_path(event_item_path)

        index_in_other_tree = other_view.model().indexFromItem(item)
        other_view.setExpanded(index_in_other_tree, expand)

    def sync_scroll(self, value):
        """Synchronize the scroll position between tree views."""
        # Fetch the source of the signal
        source_scrollbar = self.sender()
        
        # Determine the target scrollbar for synchronization
        if source_scrollbar == self.source_treeview.verticalScrollBar():
            target_scrollbar = self.target_treeview.verticalScrollBar()
        else:
            target_scrollbar = self.source_treeview.verticalScrollBar()
        
        # Update the target's scrollbar position to match the source's
        target_scrollbar.setValue(value)