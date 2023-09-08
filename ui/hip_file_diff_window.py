import os
import zipfile

from hutil.Qt.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QMessageBox, QAbstractItemView
from hutil.Qt.QtCore import Qt
from hutil.Qt.QtGui import QColor, QBrush, QPixmap, QPen, QPainter

from api.hip_file_comparator import HipFileComparator, SUPPORTED_FILE_FORMATS
from ui.custom_qtree_view import CustomQTreeView
from ui.custom_standart_item_model import CustomStandardItemModel, ICONS_ZIP_PATH
from ui.file_selector import FileSelector


TAG_COLOR_MAP = {
    "deleted" : "#b50400",
    "edited" : "#ffea00",
    "created" : "#6ba100",
}
        

class HipFileDiffWindow(QMainWindow):
    def __init__(self):
        super(HipFileDiffWindow, self).__init__()
        
        # Set window properties
        self.setWindowTitle('.hip files diff tool')
        self.setGeometry(300, 300, 2000, 1300)

        # Main widget to set as central widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Main vertical layout
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(5,5,5,5)

        # Horizontal layout at the top
        self.source_file_line_edit = FileSelector(self)
        self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source.hipnc")
        self.source_file_line_edit.setPlaceholderText("source_file_line_edit")

        self.target_file_line_edit = FileSelector(self)    
        self.target_file_line_edit.setObjectName("FileSelector")    
        self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source_edited.hipnc")
        self.target_file_line_edit.setPlaceholderText("target_file_line_edit")

        self.source_treeview = CustomQTreeView(self)
        self.source_treeview.setObjectName("source")
        self.source_treeview.header().hide()
        self.source_treeview.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.source_treeview.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.source_treeview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.source_treeview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.source_model = CustomStandardItemModel()
        self.source_treeview.setModel(self.source_model)

        self.source_widget = QWidget()
        self.source_layout = QVBoxLayout(self.source_widget)
        self.source_layout.addWidget(self.source_file_line_edit)
        self.source_layout.addWidget(self.source_treeview)
        self.source_layout.setContentsMargins(5,5,5,5)
     
        self.load_button = QPushButton("Compare", self)
        self.load_button.setObjectName("compareButton")
        self.load_button.clicked.connect(self.handle_load_button_click)
        self.load_button.setFixedHeight(40)
        self.load_button.setFixedWidth(100)

        self.target_top_hlayout = QHBoxLayout()
        self.target_top_hlayout.addWidget(self.target_file_line_edit)
        self.target_top_hlayout.addWidget(self.load_button)

        self.target_treeview = CustomQTreeView(self)
        self.target_treeview.setObjectName("target")
        self.target_treeview.header().hide()
        self.target_treeview.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.target_treeview.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.target_treeview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.target_treeview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.target_model = CustomStandardItemModel()
        self.target_treeview.setModel(self.target_model)

        self.target_widget = QWidget()
        self.target_layout = QVBoxLayout(self.target_widget)
        self.target_layout.addLayout(self.target_top_hlayout)
        self.target_layout.addWidget(self.target_treeview)
        self.target_layout.setContentsMargins(5,5,5,5)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.source_widget)
        splitter.addWidget(self.target_widget)
        splitter.setSizes([self.width() // 2, self.width() // 2])

        self.main_layout.addWidget(splitter)

        self.load_button.click()

        self.target_treeview.expanded.connect(lambda index: self.sync_expand(index, expand=True))
        self.target_treeview.collapsed.connect(lambda index: self.sync_expand(index, expand=False))
        self.source_treeview.expanded.connect(lambda index: self.sync_expand(index, expand=True))
        self.source_treeview.collapsed.connect(lambda index: self.sync_expand(index, expand=False))

        self.target_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.source_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.hip_comparator = None

        main_stylesheet = """
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
        
        self.setStyleSheet(main_stylesheet)

    def populate_tree_with_data(
            self, 
            name,
            treeview, 
            data
    ):

        with zipfile.ZipFile(ICONS_ZIP_PATH, 'r') as zip_ref:
            for path in data:
                node_data = data[path]

                node_name = node_data.name
                parent_path = node_data.parent_path
                parent_item = treeview.model().get_item_by_path(parent_path)
                if node_name == "/":
                    node_name = treeview.objectName()

                treeview.model().add_item_with_path(
                    node_name, 
                    path, 
                    node_data, 
                    zip_ref,
                    parent=parent_item,
                )
        
        self.paint_items_and_expand(treeview.model().invisibleRootItem(), treeview)

    def paint_items_and_expand(self, parent_item, treeview):
        """Recursive function to iterate over all items in a QStandardItemModel."""
        for row in range(parent_item.rowCount()):
            for column in range(parent_item.columnCount()):
                item = parent_item.child(row, 0)
                item_data = item.data(Qt.UserRole + 2)
                tag = item_data.tag
                
                if tag == "created" and treeview.objectName() == "source":
                    self.fill_item_with_hatched_pattern(item)
                    self.expand_to_index(treeview.model().indexFromItem(item), treeview)
                        
                elif tag in ["edited", "value"] and treeview.objectName() == "source":
                    color = TAG_COLOR_MAP["deleted"]
                    qcolor = QColor(color)
                    qcolor.setAlpha(40)
                    item.setBackground(QBrush(qcolor))
                    if tag != "value":
                        self.expand_to_index(treeview.model().indexFromItem(item), treeview)
                        
                elif tag in ["edited", "value"] and treeview.objectName() == "target":
                    color = TAG_COLOR_MAP["created"]
                    qcolor = QColor(color)
                    qcolor.setAlpha(40)
                    item.setBackground(QBrush(qcolor))
                    if tag != "value":
                        self.expand_to_index(treeview.model().indexFromItem(item), treeview)

                elif tag == "deleted" and treeview.objectName() == "target":
                    self.fill_item_with_hatched_pattern(item)
                    self.expand_to_index(treeview.model().indexFromItem(item), treeview)

                elif tag:
                    color = TAG_COLOR_MAP[tag]
                    qcolor = QColor(color)
                    qcolor.setAlpha(150)
                    item.setBackground(QBrush(qcolor))
                    self.expand_to_index(treeview.model().indexFromItem(item), treeview)

                if item:
                    self.paint_items_and_expand(item, treeview)
                
    def expand_to_index(self, index, treeview):
        parent = index.parent()
        if not parent.isValid():
            return
        while parent.isValid():
            treeview.expand(parent)
            parent = parent.parent()

    def handle_load_button_click(self):

        source_scene_path = self.source_file_line_edit.text().strip('"')
        self.check_file_path(source_scene_path)
        
        target_scene_path = self.target_file_line_edit.text().strip('"')
        self.check_file_path(target_scene_path)

        self.hip_comparator = HipFileComparator(
            source_scene_path, 
            target_scene_path
        )        
        self.hip_comparator.compare()

        if self.hip_comparator.is_compared != True:
            error_during_comparasing_text = "There was an error during file comparasing"
            QMessageBox.critical(
                self, 
                "Error", 
                error_during_comparasing_text
            )
            raise RuntimeError(error_during_comparasing_text)
            
        self.populate_tree_with_data(
            "source",
            self.source_treeview, 
            self.hip_comparator.source_data
        )

        self.populate_tree_with_data(
            "target",
            self.target_treeview, 
            self.hip_comparator.target_data
        )

    def fill_item_with_hatched_pattern(self, item):
        # Create a QPixmap for hatching pattern
        hatch_width = 1000  # Adjust for desired frequency
        pixmap = QPixmap(hatch_width, 100)
        pixmap.fill(Qt.transparent)  # or any background color

        # Create a brush for the hatching pattern
        pen_color = QColor("#505050")  # Change for desired line color
        pen_width = 3  # Change for desired line thickness
        pen = QPen(pen_color, pen_width)
        pen.setCapStyle(Qt.FlatCap)

        painter = QPainter(pixmap)
        painter.setPen(pen)

        # Adjusted loop and coordinates for the hatching pattern
        for i in range(-hatch_width, hatch_width, pen_width * 6):  
            painter.drawLine(i, hatch_width, hatch_width+i, 0)

        painter.end()

        hatch_brush = QBrush(pixmap)
        item.setBackground(hatch_brush)

    def check_file_path(self, path):
        if not os.path.exists(path):
            incorrect_path_text = "Incorrect source path specified, such file don't exists."
            QMessageBox.critical(self, "Error", incorrect_path_text)
            raise RuntimeError(incorrect_path_text)
        
        _, extension = os.path.splitext(path)
        if extension[1:] not in SUPPORTED_FILE_FORMATS:
            only_hip_supported_text = "Incorrect source file specified, only .hip files supported."
            QMessageBox.critical(self, "Error", only_hip_supported_text)
            raise RuntimeError(only_hip_supported_text)


        # def sync_expansion(index):

    def sync_expand(self, index, expand=False):
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
        if self.target_treeview.verticalScrollBar().value() != value:
            self.target_treeview.verticalScrollBar().setValue(value)
        else:
            self.source_treeview.verticalScrollBar().setValue(value)
