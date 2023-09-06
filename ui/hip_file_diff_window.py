import sys
import os
import random
import zipfile

import hou
from hutil.Qt.QtGui import *
from hutil.Qt.QtCore import *
from hutil.Qt.QtWidgets import *

from api.hip_file_comparator import HipFileComparator, SUPPORTED_FILE_FORMATS

TAG_COLOR_MAP = {
    "deleted" : "red",
    "edited" : "yellow",
    "created" : "green",
}

current_dir = os.path.dirname(os.path.abspath(__file__))
ICONS_ZIP_PATH = os.path.join(current_dir, 'icons')
ICONS_MAPPING_PATH = os.path.join(ICONS_ZIP_PATH, 'IconMapping')
ICONS_ZIP_PATH = os.path.join(ICONS_ZIP_PATH, 'icons.zip')

ICON_MAPPINGS = {}
with open(ICONS_MAPPING_PATH, 'r') as file:
    for line in file:
        if line.startswith("#") or ":=" not in line:
            continue

        key, value = line.split(":=")
        key = key.strip()
        value = value.strip().rstrip(";")
        ICON_MAPPINGS[key] = value.replace("_", "/", 1)


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



class CustomStandardItemModel(QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super(CustomStandardItemModel, self).__init__(*args, **kwargs)
        self.item_dictionary = {}
        self.path_role = Qt.UserRole + 1
        self.data_role = Qt.UserRole + 2

    def add_item_with_path(
            self, 
            item_text, 
            path, 
            data, 
            icons_zip,
            parent=None,
        ):
        """Adds an item to the model with a unique identifier."""
        item = QStandardItem(item_text)
        item.setData(path, self.path_role)
        item.setData(data, self.data_role)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        # item.setFlags(item.flags() & ~Qt.ItemIsSelectable)


        # Store the item reference in the dictionary
        self.item_dictionary[path] = item

        icon_path = data.icon
        if icon_path in ICON_MAPPINGS:
            icon_path = ICON_MAPPINGS[icon_path]
        elif icon_path:
            icon_path = icon_path.replace("_", "/", 1)

        icon_path_inside_zip = icon_path + ".svg"
        try:
            with icons_zip.open(icon_path_inside_zip) as file:
                data = file.read()
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                qicon = QIcon(pixmap)
                item.setIcon(qicon)
        except Exception as e:
            pass
        
        if parent:
            parent.appendRow(item)
        else:
            self.appendRow(item)

    def get_item_by_path(self, path):
        """Retrieve an item based on its unique identifier."""
        return self.item_dictionary.get(path)
            

class HipFileDiffWindow(QMainWindow):
    def __init__(self):
        super(HipFileDiffWindow, self).__init__()
        
        # Set window properties
        self.setWindowTitle('.hip files diff tool')
        self.setGeometry(300, 300, 1000, 800)

        # Main widget to set as central widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Main vertical layout
        self.main_layout = QVBoxLayout(self.main_widget)

        main_stylesheet = """
            QMainWindow{
                background-color: #333;
            }
            QLineEdit {
                font: 12pt "Arial";
                color: #FFFFFF;
                background-color: #333333;
                border: 1px solid black;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton {
                font: 12pt "Arial";
                color: #FFFFFF;
                background-color: #555555;
                border: 1px solid black;
                border-radius: 10px;
                padding: 6px;

            }
            CustomQTreeView {
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
                alternate-background-color: #3a3a3a;
                border: 1px solid black;
                border-radius: 5px;
                padding: 6px;
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
            QHeaderView::section {
                font: 12pt "Arial";
                background-color: #333333;
                color: white;
                border: none;
                border-bottom: 1px solid black;
                padding: 4px;
            }
        """
        
        self.setStyleSheet(main_stylesheet)

        # Horizontal layout at the top
        self.source_file_line_edit = QLineEdit(self)
        self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source.hipnc")
        self.source_file_line_edit.setMinimumWidth(100)
        self.source_file_line_edit.setPlaceholderText("source_file_line_edit")

        self.target_file_line_edit = QLineEdit(self)        
        self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source_edited.hipnc")
        self.target_file_line_edit.setMinimumWidth(100)
        self.target_file_line_edit.setPlaceholderText("target_file_line_edit")
        
        self.load_button = QPushButton("Compare", self)
        self.load_button.clicked.connect(self.handle_load_button_click)
        self.load_button.setMinimumWidth(100)

        self.top_hlayout = QHBoxLayout()
        self.top_hlayout.addWidget(self.source_file_line_edit)
        self.top_hlayout.addWidget(self.target_file_line_edit)
        self.top_hlayout.addWidget(self.load_button)
        self.main_layout.addLayout(self.top_hlayout)

        self.treeviews_layout = QHBoxLayout()
        self.main_layout.addLayout(self.treeviews_layout)

        self.source_treeview = CustomQTreeView(self)
        self.source_treeview.setObjectName("source")
        self.source_treeview.header().setDefaultAlignment(Qt.AlignCenter|Qt.AlignVCenter)
        self.source_treeview.setAlternatingRowColors(True)
        self.source_treeview.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.source_treeview.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.source_treeview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.source_treeview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.source_model = CustomStandardItemModel()
        self.source_model.setHorizontalHeaderLabels(["target"])
        self.source_treeview.setModel(self.source_model)

        self.target_treeview = CustomQTreeView(self)
        self.target_treeview.setObjectName("target")
        self.target_treeview.header().setDefaultAlignment(Qt.AlignCenter|Qt.AlignVCenter)
        self.target_treeview.setAlternatingRowColors(True)
        self.target_treeview.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.target_treeview.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.target_treeview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.target_treeview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.target_model = CustomStandardItemModel()
        self.target_model.setHorizontalHeaderLabels(["target"])
        self.target_treeview.setModel(self.target_model)

        self.treeviews_layout.addWidget(self.source_treeview)
        self.treeviews_layout.addWidget(self.target_treeview)

        self.hip_comparator = None
        self.load_button.click()

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
                    continue

                treeview.model().add_item_with_path(
                    node_name, 
                    path, 
                    node_data, 
                    zip_ref,
                    parent=parent_item,
                )
        
        self.iterate_items(treeview.model().invisibleRootItem(), treeview)


    def iterate_items(self, parent_item, treeview):
        """Recursive function to iterate over all items in a QStandardItemModel."""
        for row in range(parent_item.rowCount()):
            for column in range(parent_item.columnCount()):
                item = parent_item.child(row, 0)
                item_data = item.data(Qt.UserRole + 2)
                tag = item_data.tag
                
                print("treeview.objectName:", treeview.objectName())
                if tag == "created" and treeview.objectName() == "source":
                    self.fill_item_with_hatched_pattern(item)
                    index = treeview.model().indexFromItem(item)
                    while index.isValid():
                        treeview.expand(index)
                        index = index.parent()
                elif tag == "deleted" and treeview.objectName() == "target":
                    self.fill_item_with_hatched_pattern(item)
                    index = treeview.model().indexFromItem(item)
                    while index.isValid():
                        treeview.expand(index)
                        index = index.parent()

                elif tag:
                    color = TAG_COLOR_MAP[tag]
                    qcolor = QColor(color)
                    qcolor.setAlpha(64)
                    item.setBackground(QBrush(qcolor))
                    index = treeview.model().indexFromItem(item)
                    while index.isValid():
                        treeview.expand(index)
                        index = index.parent()

                if item:
                    self.iterate_items(item, treeview)
                
    def handle_load_button_click(self):

        source_scene_path = self.source_file_line_edit.text().strip('"')
        self.check_file_path(source_scene_path)
        
        target_scene_path = self.target_file_line_edit.text().strip('"')
        self.check_file_path(target_scene_path)

        print("source_scene_path", source_scene_path)
        print("target_scene_path", target_scene_path)

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

        print("")
        print("=="*10)
        print("")

        self.populate_tree_with_data(
            "target",
            self.target_treeview, 
            self.hip_comparator.target_data
        )

    def fill_item_with_hatched_pattern(self, item):
        # Create a QPixmap for hatching pattern
        hatch_size = 500  # Adjust for desired frequency
        pixmap = QPixmap(hatch_size, 100)
        pixmap.fill(Qt.transparent)  # or any background color

        # Create a brush for the hatching pattern
        pen_color = QColor("#505050")  # Change for desired line color
        pen_width = 3  # Change for desired line thickness
        pen = QPen(pen_color, pen_width)
        pen.setCapStyle(Qt.FlatCap)

        painter = QPainter(pixmap)
        painter.setPen(pen)

        # Adjusted loop and coordinates for the hatching pattern
        for i in range(-hatch_size, hatch_size, pen_width * 6):  
            painter.drawLine(i, hatch_size, hatch_size+i, 0)

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


