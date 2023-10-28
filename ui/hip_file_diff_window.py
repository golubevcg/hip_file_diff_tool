import os
from pathlib import Path

from hutil.Qt.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QMessageBox,
    QAbstractItemView,
    QCheckBox
)
from hutil.Qt.QtCore import Qt, QSortFilterProxyModel, QEvent
from hutil.Qt.QtGui import QHoverEvent

from api.comparators.houdini_base_comparator import HoudiniComparator, HIP_FILE_FORMATS
from api.comparators.hip_comparator import HipFileComparator
from api.comparators.hda_comparator import HdaFileComparator, HDA_FILE_FORMATS

from ui.custom_qtree_view import CustomQTreeView
from ui.custom_standart_item_model import CustomStandardItemModel
from ui.hatched_pattern_item_delegate import HatchedItemDelegate
from ui.file_selector import FileSelector
from ui.search_line_edit import QTreeViewSearch
from ui.string_diff_dialog import StringDiffDialog


class HipFileDiffWindow(QMainWindow):
    """
    Main window for displaying the differences between two .hip files.

    Attributes:
        hip_comparator (HipFileComparator): Instance to compare two hip files.
    """

    def __init__(self, args):
        super(HipFileDiffWindow, self).__init__()
        self.houdini_comparator: HoudiniComparator = None
        self.args = args
        self.init_ui(args)

    def init_ui(self, args) -> None:
        """Initialize UI components."""
        self.set_window_properties()
        self.setup_layouts()
        self.setup_tree_views()
        self.setup_checkboxes()
        self.setup_signals_and_slots()
        self.apply_stylesheet()

        self.clipboard = QApplication.clipboard()
        self.main_path = args.main_path

        # TODO: TEMP CODE REMOVE BEFORE MERGE
        if args.source_file_path:
            self.source_file_line_edit.setText(args.source_file_path)

        if args.target_file_path:
            self.target_file_line_edit.setText(args.target_file_path)

        if args.source_file_path and args.target_file_path:
            self.handle_compare_button_click()

        if args.item_path:
            item = self.source_model.get_item_by_path(args.item_path)
            if not item:
                QMessageBox.critical(
                    None, "Error", "Specified item on this path was not found!"
                )
            else:
                self.source_treeview.expand_to_index(item, self.source_treeview)
                self.on_item_double_clicked(item.index())

        # self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test/fixtures/billowy_smoke_source.hipnc")
        # self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test/fixtures/billowy_smoke_source_edited.hipnc")
        # self.handle_compare_button_click()


    def set_window_properties(self) -> None:
        """Set main window properties."""
        self.setWindowTitle(".hip files diff tool")
        self.setGeometry(300, 300, 2000, 1300)
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

    def setup_layouts(self) -> None:
        """Setup main, source and target layouts for the main window."""
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(3, 5, 3, 3)
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
        self.load_button.setFixedHeight(30)
        self.load_button.setFixedWidth(100)

        self.target_top_hlayout = QHBoxLayout()
        self.target_top_hlayout.addWidget(self.target_file_line_edit)
        self.target_top_hlayout.addWidget(self.load_button)

        self.target_widget = QWidget()
        self.target_layout = QVBoxLayout(self.target_widget)
        self.target_layout.addLayout(self.target_top_hlayout)
        self.target_layout.setContentsMargins(3, 3, 3, 3)

    def setup_tree_views(self) -> None:
        """
        Setup QTreeViews and associate models for source and target sections.
        """
        self.source_treeview = self.create_tree_view("source")
        self.source_model = CustomStandardItemModel()
        self.source_model.set_view(self.source_treeview)
        self.source_treeview.setModel(self.source_model)
        self.source_layout.addWidget(self.source_treeview)

        self.target_treeview = self.create_tree_view(
            "target", hide_scrollbar=False
        )
        self.target_model = CustomStandardItemModel()
        self.target_model.set_view(self.target_treeview)
        self.target_treeview.setModel(self.target_model)
        self.target_layout.addWidget(self.target_treeview)

        self.source_search_qline_edit = QTreeViewSearch(
            self.source_treeview, self.source_model
        )
        self.source_search_qline_edit.setPlaceholderText("Search in source")
        self.source_layout.addWidget(self.source_search_qline_edit)

        self.target_search_qline_edit = QTreeViewSearch(
            self.target_treeview, self.target_model
        )
        self.target_search_qline_edit.setPlaceholderText("Search in target")
        self.target_layout.addWidget(self.target_search_qline_edit)

        self.source_search_qline_edit.second_search = (
            self.target_search_qline_edit
        )
        self.target_search_qline_edit.second_search = (
            self.source_search_qline_edit
        )

        self.target_search_qline_edit.secondary_treeview = self.source_treeview
        self.target_search_qline_edit.secondary_proxy_model = (
            self.source_treeview.model()
        )
        self.target_model.rowsInserted.connect(
            self.target_search_qline_edit.proxy_model.invalidate
        )
        self.target_model.rowsRemoved.connect(
            self.target_search_qline_edit.proxy_model.invalidate
        )

        self.source_search_qline_edit.secondary_treeview = self.target_treeview
        self.source_search_qline_edit.secondary_proxy_model = (
            self.target_treeview.model()
        )
        self.source_model.rowsInserted.connect(
            self.source_search_qline_edit.proxy_model.invalidate
        )
        self.source_model.rowsRemoved.connect(
            self.source_search_qline_edit.proxy_model.invalidate
        )

    def create_tree_view(
        self, obj_name: str, hide_scrollbar: bool = True
    ) -> CustomQTreeView:
        """
        Create a QTreeView with specified properties.

        Args:
        - obj_name (str): Object name for the QTreeView.
        - hide_scrollbar (bool): If True, hide the scrollbar. Default is True.

        Returns:
        - CustomQTreeView: Configured QTreeView instance.
        """
        tree_view = CustomQTreeView(self)
        tree_view.setItemDelegate(HatchedItemDelegate(tree_view))
        tree_view.doubleClicked.connect(self.on_item_double_clicked)

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

        self.connect_tree_view_hover(self.source_treeview)
        self.connect_tree_view_hover(self.target_treeview)

        self.target_treeview.verticalScrollBar().valueChanged.connect(
            self.sync_scroll
        )
        self.source_treeview.verticalScrollBar().valueChanged.connect(
            self.sync_scroll
        )

    def connect_tree_view_hover(self, tree_view: CustomQTreeView) -> None:
        """
        Connect hover signals for a QTreeView.

        Args:
        - tree_view (CustomQTreeView): The QTreeView instance.
        """

        tree_view.setMouseTracking(True)
        tree_view.entered.connect(
            lambda index: self.sync_hover_state(index, hover=True)
        )

    def connect_tree_view_expansion(self, tree_view: CustomQTreeView) -> None:
        """
        Connect expansion signals for a QTreeView.

        Args:
        - tree_view (CustomQTreeView): The QTreeView instance.
        """
        tree_view.expanded.connect(
            lambda index: self.sync_expand(index, expand=True)
        )
        tree_view.collapsed.connect(
            lambda index: self.sync_expand(index, expand=False)
        )

    def sync_hover_state(self, index, hover: bool = True) -> None:
        """
        Synchronize hover/unhover state between tree views.

        Args:
        - index: QModelIndex of the item being hovered/unhovered.
        - hover (bool): If True, item is hovered. If False, it's unhovered.
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

        event_item = event_source_model.itemFromIndex(
            event_proxy_model.mapToSource(index)
        )
        event_item_path = event_item.data(event_source_model.path_role)

        item_in_other_source_model = (
            other_view.model().sourceModel().get_item_by_path(event_item_path)
        )

        index_in_other_proxy = other_view.model().mapFromSource(
            other_view.model().sourceModel().indexFromItem(item_in_other_source_model)
        )

        # Create a QHoverEvent and post it to the other tree view
        pos_in_other_view = other_view.visualRect(index_in_other_proxy).center()
        global_pos = other_view.mapToGlobal(pos_in_other_view)

        if hover:
            hover_event_type = QEvent.HoverEnter
        else:
            hover_event_type = QEvent.HoverLeave

        hover_event = QHoverEvent(hover_event_type, pos_in_other_view, global_pos)
        QApplication.postEvent(other_view.viewport(), hover_event)

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
                border-image: url("ui/icons/vline.svg")  center center no-repeat;
                }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url("ui/icons/more.svg")  center center no-repeat;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url("ui/icons/end.svg")  center center no-repeat;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: url(ui/icons/closed.svg)  center center no-repeat;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: url("ui/icons/opened.svg")  center center no-repeat;
            }
            QTreeView::branch:!adjoins-item{
                border-image: url("ui/icons/empty.svg")  center center no-repeat;
            }
            QTreeView::item {
                height: 1.1em;
                font-size: 0.4em;
                padding: 0.12em;
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
            QCheckBox {
                color: #818181;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 1px solid #818181;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border: 1px solid rgb(185, 134, 32);
            }
        """
        )

    def setup_checkboxes(self):
        self.show_only_edited_checkbox = QCheckBox("Show only edited nodes")
        self.show_only_edited_checkbox.stateChanged.connect(
            self.on_checkbox_toggled
        )

        self.checkbox_h_layout = QHBoxLayout()
        self.checkbox_h_layout.addWidget(self.show_only_edited_checkbox)
        self.checkbox_h_layout.setContentsMargins(10, 0, 0, 0)
        self.main_layout.addLayout(self.checkbox_h_layout)

    def handle_compare_button_click(self) -> None:
        """
        Handle the logic when the "Compare" button is clicked.
        """
        source_path = self.source_file_line_edit.text()
        target_path = self.target_file_line_edit.text()

        if not (os.path.exists(source_path) and os.path.exists(target_path)):
            QMessageBox.warning(
                self,
                "Invalid Paths",
                "Please select valid .hip files to compare.",
            )
            return

        self.source_model.clear()
        self.source_treeview.item_dictionary = {}
        self.source_treeview.model().invalidateFilter()

        self.target_model.clear()
        self.target_treeview.item_dictionary = {}
        self.target_treeview.model().invalidateFilter()

        if Path(source_path).suffix[1:] in HIP_FILE_FORMATS:
            self.houdini_comparator = HipFileComparator(source_path, target_path)
        elif Path(source_path).suffix[1:] in HDA_FILE_FORMATS:
            self.houdini_comparator = HdaFileComparator(source_path, target_path)

        self.houdini_comparator.compare()

        # Assuming 'comparison_result' contains the differences,
        # we can now update our tree views based on the results.
        self.source_model.populate_with_data(
            self.houdini_comparator.source_nodes, self.source_treeview.objectName()
        )
        self.target_model.populate_with_data(
            self.houdini_comparator.target_nodes, self.target_treeview.objectName()
        )

        self.source_treeview.model().invalidateFilter()
        self.target_treeview.model().invalidateFilter()

    def on_checkbox_toggled(self, state) -> None:
        """
        Handle the logic when "Show only edited nodes" checkbox is toggled.

        Args:
        - state: Current state of the checkbox.
        """
        if state == Qt.Checked:
            self.source_model.show_only_edited = True
            self.target_model.show_only_edited = True

            self.source_search_qline_edit.capture_tree_state()
            self.target_search_qline_edit.capture_tree_state()

            self.source_treeview.model().reset_proxy_view()
            self.target_treeview.model().reset_proxy_view()
        else:
            self.source_model.show_only_edited = False
            self.target_model.show_only_edited = False

            self.source_treeview.model().reset_proxy_view()
            self.target_treeview.model().reset_proxy_view()

            self.source_search_qline_edit.restore_tree_state()
            self.target_search_qline_edit.restore_tree_state()

    def sync_expand(self, index, expand: bool = True) -> None:
        """
        Synchronize expansion state between tree views.

        Args:
        - index: QModelIndex of the item being expanded or collapsed.
        - expand (bool): If True, item is expanded. If False, it's collapsed.
        """
        other_view, index_in_other_proxy = self.get_index_in_other_model(index)
        other_view.setExpanded(index_in_other_proxy, expand)

    def get_index_in_other_model(self, index):
        event_proxy_model = index.model()
        if isinstance(event_proxy_model, QSortFilterProxyModel):
            event_source_model = event_proxy_model.sourceModel()
        else:
            event_source_model = event_proxy_model
            event_proxy_model = event_proxy_model.proxy_model
            index = event_proxy_model.mapFromSource(index)

        if event_source_model == self.source_model:
            other_view = self.target_treeview
        else:
            other_view = self.source_treeview

        event_item = event_source_model.itemFromIndex(
            event_proxy_model.mapToSource(index)
        )
        event_item_path = event_item.data(event_source_model.path_role)

        item_in_other_source_model = (
            other_view.model().sourceModel().get_item_by_path(event_item_path)
        )

        index_in_other_proxy = other_view.model().mapFromSource(
            other_view.model()
            .sourceModel()
            .indexFromItem(item_in_other_source_model)
        )
        return other_view, index_in_other_proxy

    def sync_scroll(self, value: int) -> None:
        """
        Synchronize vertical scrolling between tree views.

        Args:
        - value (int): Vertical scroll position.
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

    def on_item_double_clicked(self, index):
        index_displ_role_text = index.data(Qt.DisplayRole)
        if index_displ_role_text.count("\n") >= 3 :
            _, index_in_other_proxy = self.get_index_in_other_model(index)
            string_diff_dialog = StringDiffDialog(
                index, 
                index_in_other_proxy, 
                parent=self
            )
            self.installEventFilter(string_diff_dialog)
            string_diff_dialog.show()
