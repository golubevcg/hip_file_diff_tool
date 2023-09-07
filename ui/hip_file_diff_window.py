import os
import zipfile
import copy

from hutil.Qt.QtGui import *
from hutil.Qt.QtCore import *
from hutil.Qt.QtWidgets import *

from api.hip_file_comparator import HipFileComparator, SUPPORTED_FILE_FORMATS

TAG_COLOR_MAP = {
    "deleted" : "#b50400",
    "edited" : "#ffea00",
    "created" : "#6ba100",
}

syncing = False

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



# Flag to prevent circular sync events
syncing = False


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

        self.item_dictionary[path] = item

        icon_path = data.icon
        if icon_path in ICON_MAPPINGS:
            icon_path = ICON_MAPPINGS[icon_path]
        elif icon_path:
            icon_path = icon_path.replace("_", "/", 1)

        icon_path_inside_zip = icon_path + ".svg"
        try:
            with icons_zip.open(icon_path_inside_zip) as file:
                icon_data = file.read()
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                qicon = QIcon(pixmap)
                item.setIcon(qicon)
        except Exception as e:
            pass
        
        if parent:
            parent.appendRow(item)
        else:
            self.appendRow(item)

        for parm_name in data.parms:
            parm = data.get_parm_by_name(parm_name)
            if parm.tag != "edited":
                continue

            value = parm.value
            parm_item = QStandardItem(parm.name)
            parm_item.setData(parm, self.data_role)
            parm_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
            try:
                with icons_zip.open("VOP/parameter.svg") as file:
                    parm_icon_data = file.read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(parm_icon_data)
                    qicon = QIcon(pixmap)
                    parm_item.setIcon(qicon)
            except Exception as e:
                pass

            item.appendRow(parm_item)

            value = parm.value
            value_item = QStandardItem(str(value))
            value_item.setData(parm, self.data_role)
            value_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
            value_data = copy.copy(parm)
            value_data.tag = 'value'
            value_item.setData(value_data, self.data_role)
            parm_item.appendRow(value_item)


    def get_item_by_path(self, path):
        """Retrieve an item based on its unique identifier."""
        return self.item_dictionary.get(path)
            

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

        main_stylesheet = """
            QMainWindow{
                background-color: #3c3c3c;
            }
            QPushButton {
                font: 10pt "Arial";
                color: white;
                background-color: #464646;
                border-radius: 10px;
                margins: 2px
            }
            CustomQTreeView {
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
                alternate-background-color: #3a3a3a;
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

        # Horizontal layout at the top
        self.source_file_line_edit = QLineEdit(self)
        self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source.hipnc")
        self.source_file_line_edit.setMinimumWidth(100)
        self.source_file_line_edit.setFixedHeight(30)
        self.source_file_line_edit.setPlaceholderText("source_file_line_edit")
        self.source_file_line_edit.setStyleSheet('''
            font: 10pt "Arial";
            color: #818181;
            background-color: #464646;
            border-radius: 10px;
        ''')

        self.target_file_line_edit = QLineEdit(self)        
        self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source_edited.hipnc")
        self.target_file_line_edit.setMinimumWidth(100)
        self.target_file_line_edit.setFixedHeight(30)
        self.target_file_line_edit.setPlaceholderText("target_file_line_edit")
        self.target_file_line_edit.setStyleSheet('''
            font: 10pt "Arial";
            color: #818181;
            background-color: #464646;
            border-radius: 10px;
        ''')

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
        self.load_button.clicked.connect(self.handle_load_button_click)
        self.load_button.setFixedHeight(30)
        self.load_button.setMinimumWidth(100)

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

        # self.target_treeview.expanded.connect(sync_expansion)
        # self.target_treeview.collapsed.connect(sync_collapse)
        # self.source_treeview.expanded.connect(sync_expansion)
        # self.source_treeview.collapsed.connect(sync_collapse)

        self.target_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.source_treeview.verticalScrollBar().valueChanged.connect(self.sync_scroll)

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
                    node_name = treeview.objectName()

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
                
                if tag == "created" and treeview.objectName() == "source":
                    self.fill_item_with_hatched_pattern(item)
                    index = treeview.model().indexFromItem(item)
                    while index.isValid():
                        treeview.expand(index)
                        index = index.parent()
                        
                elif tag in ["edited", "value"] and treeview.objectName() == "source":
                    color = TAG_COLOR_MAP["deleted"]
                    qcolor = QColor(color)
                    qcolor.setAlpha(40)
                    item.setBackground(QBrush(qcolor))
                    index = treeview.model().indexFromItem(item)
                    if tag != "value":
                        while index.isValid():
                            treeview.expand(index)
                            index = index.parent()
                elif tag in ["edited", "value"] and treeview.objectName() == "target":
                    color = TAG_COLOR_MAP["created"]
                    qcolor = QColor(color)
                    qcolor.setAlpha(40)
                    item.setBackground(QBrush(qcolor))
                    index = treeview.model().indexFromItem(item)
                    if tag != "value":
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
                    qcolor.setAlpha(150)
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
    #     global syncing
    #     if syncing:
    #         return
    #     syncing = True
        
    #     item = treeView1.model().itemFromIndex(index)
    #     if treeView1.sender() == treeView1:
    #         other_view = treeView2
    #     else:
    #         other_view = treeView1
            
    #     index_in_other_tree = treeView2.model().indexFromItem(item)
    #     other_view.expand(index_in_other_tree)
        
    #     syncing = False

    # def sync_collapse(index):
    #     global syncing
    #     if syncing:
    #         return
    #     syncing = True
        
    #     item = treeView1.model().itemFromIndex(index)
    #     if treeView1.sender() == treeView1:
    #         other_view = treeView2
    #     else:
    #         other_view = treeView1
            
    #     index_in_other_tree = treeView2.model().indexFromItem(item)
    #     other_view.collapse(index_in_other_tree)
        
    #     syncing = False

    def sync_scroll(self, value):
        if self.target_treeview.verticalScrollBar().value() != value:
            self.target_treeview.verticalScrollBar().setValue(value)
        else:
            self.source_treeview.verticalScrollBar().setValue(value)
