import os
import sys
import difflib

from hutil.Qt.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QHBoxLayout
from hutil.Qt.QtGui import QColor, QPalette, QColor
from hutil.Qt.QtWidgets import (
    QDialog, 
    QWidget, 
    QTextEdit, 
    QVBoxLayout, 
    QSplitter, 
    QPushButton,  
    QLineEdit
)
from hutil.Qt.QtCore import Qt, QTimer, QEvent
from ui.constants import PATH_ROLE
from ui.hatched_text_edit import HatchedTextEdit
 
from api.comparators.houdini_base_comparator import COLORS


class Overlay(QWidget):
    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, QColor(15, 15, 15, 128))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
    def resizeEvent(self, event):
        """ Resize the overlay to cover the entire parent. """
        self.resize(self.parent().size())
        super().resizeEvent(event)


class StringDiffDialog(QDialog):
    def __init__(self, index, other_index, parent=None):
        super().__init__(parent)

        self.setWindowTitle("String diff tool")

        self.parent_application = parent

        source_text = index.data(Qt.DisplayRole)
        target_text = other_index.data(Qt.DisplayRole)

        self.setGeometry(300, 300, 1200, 600)

        self.setStyleSheet(
            """
            QDialog{
                background-color: #333333;
            }

            QTextEdit{
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
                border:none;
            }
            """
        )
        
        self.top_buttons_widget = QWidget()
        self.top_buttons_widget.setStyleSheet(
            """
                background-color: #404040;
                border: 1px solid #4d4d4d;
                border-radius: 15px;
            """
        )
        self.top_buttons_widget.setFixedHeight(40)
        self.top_buttons_widget.setContentsMargins(5, 1, 0, 0)

        self.top_buttons_hbox_layout = QHBoxLayout(self.top_buttons_widget)
        self.top_buttons_hbox_layout.setContentsMargins(0, 0, 0, 0)

        self.copy_link_button = QPushButton("copy link", self)
        self.copy_link_button.setObjectName("copyLink")
        self.copy_link_button.setFixedHeight(30)
        self.copy_link_button.setFixedWidth(120)
        self.copy_link_button.setStyleSheet(
            """
            QPushButton#copyLink {
                font: 10pt "Arial";
                color: #919191;
                border:none;
                border-right: 1px solid #4d4d4d;
                border-radius:0px;
            }
            QPushButton#copyLink:hover {
                border: 1px solid rgb(185, 134, 32);
                border-radius:10px;
            }
            """
        )
        self.copy_link_button.clicked.connect(self._handle_copy_link)

        self.copy_path_button = QPushButton("copy path", self)
        self.copy_path_button.setObjectName("copyLink")
        self.copy_path_button.setFixedHeight(30)
        self.copy_path_button.setFixedWidth(120)
        self.copy_path_button.setStyleSheet(
            """
            QPushButton#copyLink {
                font: 10pt "Arial";
                color: #919191;
                border:none;
                border-radius:0px;
            }
            QPushButton#copyLink:hover {
                border: 1px solid rgb(185, 134, 32);
                border-radius:10px;
            }
            """
        )
        self.copy_path_button.clicked.connect(self._handle_copy_path)

        self._copy_link_timer = QTimer(self)
        self._copy_link_timer.timeout.connect(self.reset_link_button_text)
        self._copy_link_timer.setSingleShot(True)

        self._copy_path_timer = QTimer(self)
        self._copy_path_timer.timeout.connect(self.reset_path_button_text)
        self._copy_path_timer.setSingleShot(True)

        path_to_node = index.data(PATH_ROLE)
        self.node_path_line_edit = QLineEdit(path_to_node)
        self.node_path_line_edit.setContentsMargins(0, 0, 3, 0)

        self.node_path_line_edit.setFixedHeight(35)
        self.node_path_line_edit.setReadOnly(True)
        self.node_path_line_edit.setStyleSheet(
            """
            font: 10pt "DS Houdini";
            color: #919191;
            background-color: #333333;
            border:none;
            border-radius: 15px;
            padding-left:15px;
            padding-bottom:3px;
            """
        )

        self.top_buttons_hbox_layout.addWidget(self.copy_link_button)
        self.top_buttons_hbox_layout.addWidget(self.copy_path_button)
        self.top_buttons_hbox_layout.addWidget(self.node_path_line_edit)

        # Split texts into lines for difflib processing
        old_lines = source_text.splitlines()
        new_lines = target_text.splitlines()

        # Get diffs
        diff = difflib.Differ()
        diffs = list(diff.compare(old_lines, new_lines))


        self.new_text_hashed_line_numbers = []
        self.old_text_hashed_line_numbers = []
        # Process the diffs and get formatted strings for both QTextEdits
        old_html, new_html = self.process_diffs(diffs)

        # Create text edits and set their content
        self.line_nums_qtedit = QTextEdit(self)
        self.line_nums_qtedit.setReadOnly(True)
        self.line_nums_qtedit.setLineWrapMode(QTextEdit.NoWrap)
        self.line_nums_qtedit.setFixedWidth(60)
        self.line_nums_qtedit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.line_nums_qtedit.setStyleSheet(
            """
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
                border-right: 1px solid #4d4d4d;
            """
        )

        line_nums = []
        for lin_num in range(0, len(old_html)):
            line_nums.append(f'<div style="text-align: right;">{str(lin_num)}</div>')
        self.line_nums_qtedit.setHtml(''.join(line_nums))

        # Create text edits and set their content
        self.old_text_edit = HatchedTextEdit(self)
        self.old_text_edit.setReadOnly(True)
        self.old_text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.old_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.old_text_edit.setStyleSheet(
            """
            QTextEdit {
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
                border-right: 1px solid #4d4d4d;
            }
            QScrollBar:vertical {
                border: none;
                background: #333333;
                width: 15px;
                border: 1px solid #3c3c3c;
            }
            QScrollBar::handle:vertical {
                background: #464646;
                min-width: 15px;
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
            QScrollBar:horizontal {
                border: none;
                background: #333333;
                height: 15px;
                border: 1px solid #3c3c3c;
            }
            QScrollBar::handle:horizontal {
                background: #464646;
                min-height: 15px;
            }
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
                border: none;
                background: none;
                width: 0;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            """
        )
        self.old_text_edit.setHtml(''.join(old_html))
        self.old_text_edit.text_lines = old_html

        widget = QWidget()
        hlayout = QHBoxLayout(widget)
        hlayout.setSpacing(0)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(self.line_nums_qtedit)
        hlayout.addWidget(self.old_text_edit)

        self.new_text_edit = HatchedTextEdit(self)
        self.new_text_edit.setReadOnly(True)
        self.new_text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.new_text_edit.setHtml(''.join(new_html))
        self.new_text_edit.text_lines = new_html
        self.new_text_edit.setStyleSheet(
            """
            QTextEdit {
                font: 10pt "DS Houdini";
                color: #dfdfdf;
                background-color: #333333;
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

            QScrollBar:horizontal {
                border: none;
                background: #333333;
                height: 15px;
                border: 1px solid #3c3c3c;
            }
            QScrollBar::handle:horizontal {
                background: #464646;
                min-height: 15px;
            }
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
                border: none;
                background: none;
                width: 0;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            """
        )

        # Create a splitter and add text edits to it
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.addWidget(widget)
        # self.splitter.addWidget(self.old_text_edit)
        self.splitter.addWidget(self.new_text_edit)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #4d4d4d;
            }
        """)

        # Layouts and widgets setup
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.top_buttons_widget)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        self.overlay = Overlay(parent)
        self.overlay.show()

        self.old_text_edit.verticalScrollBar().valueChanged.connect(
            self.sync_scroll
        )
        
        self.new_text_edit.verticalScrollBar().valueChanged.connect(
            self.sync_scroll
        )
        
        self.old_text_edit.horizontalScrollBar().valueChanged.connect(
            self.sync_scroll
        )
        
        self.new_text_edit.horizontalScrollBar().valueChanged.connect(
            self.sync_scroll
        )

        # Point 1: Lock the child window to the center of the parent window
        self.centerOnParent()

    def centerOnParent(self):
        if self.parent():
            parent_geometry = self.parent().geometry()
            self.setGeometry(
                parent_geometry.x() + (parent_geometry.width() - self.width()) / 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) / 2,
                self.width(),
                self.height()
            )

    def closeEvent(self, event):
        """ When the dialog is closed, also close the overlay. """
        self.overlay.close()
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        """ Listen to the parent's move events and adjust the position of the child window accordingly. """
        if obj == self.parent() and event.type() == QEvent.Move:
            self.centerOnParent()
        return super().eventFilter(obj, event)

    def process_diffs(self, diffs):
        old_html = []
        new_html = []

        green_with_50_alpha = "#%s" + COLORS["green"][1:]
        red_with_50_alpha = "#%s" + COLORS["red"][1:]

        for diff in diffs:
            opcode = diff[0]
            text = diff[2:]

            text_display = text if text.strip() != "" else "&nbsp;"
            if opcode == ' ':
                old_html.append(f'<div>{text_display}</div>')
                new_html.append(f'<div>{text_display}</div>')
            elif opcode == '-':
                old_html.append(f'<div style="background-color: {red_with_50_alpha % 40};">{text_display}</div>')
                new_html.append(f'<div data_hashed_line=True>&nbsp;</div>')
            elif opcode == '+':
                old_html.append(f'<div data_hashed_line=True>&nbsp;</div>')
                new_html.append(f'<div style="background-color: {green_with_50_alpha % 40};">{text_display}</div>')

        return old_html, new_html
    
    def sync_scroll(self, value: int) -> None:
        """
        Synchronize vertical scrolling between tree views.

        Args:
        - value (int): Vertical scroll position.
        """
        # Fetch the source of the signal
        source_scrollbar = self.sender()

        # Determine the target scrollbar for synchronization
        if source_scrollbar == self.old_text_edit.verticalScrollBar():
            target_scrollbar = self.new_text_edit.verticalScrollBar()
        elif source_scrollbar == self.new_text_edit.verticalScrollBar():
            target_scrollbar = self.old_text_edit.verticalScrollBar()

        elif source_scrollbar == self.old_text_edit.horizontalScrollBar():
            target_scrollbar = self.new_text_edit.horizontalScrollBar()
        elif source_scrollbar == self.new_text_edit.horizontalScrollBar():
            target_scrollbar = self.old_text_edit.horizontalScrollBar()

        # Update the target's scrollbar position to match the source's
        target_scrollbar.setValue(value)

    def _handle_copy_link(self) -> None:
        self.copy_link_button.setText("link copied")

        hython_executable_path = os.environ.get('HOUDINI_HYTHON')
        if not hython_executable_path:
            hython_executable_path = sys.executable

        diff_tool_path = os.environ.get('HOUDINI_AGOL_DIFF_TOOL')
        if not diff_tool_path:
            diff_tool_path = self.parent_application.main_path
        
        source_file_path = self.parent_application.source_file_line_edit.text()
        target_file_path = self.parent_application.target_file_line_edit.text()

        link = (
            f'& "{hython_executable_path}" '
            f'{diff_tool_path} '
            f'--source={source_file_path} '
            f'--target={target_file_path} '
            f'--item-path={self.node_path_line_edit.text()}'
        )
        self.parent_application.clipboard.setText(link)

        self._copy_link_timer.start(2500)

    def _handle_copy_path(self) -> None:
        self.copy_path_button.setText("path copied")
        self.parent_application.clipboard.setText(self.node_path_line_edit.text())

        self._copy_path_timer.start(2500)

    def reset_link_button_text(self) -> None:
        self.copy_link_button.setText("copy link")

    def reset_path_button_text(self) -> None:
        self.copy_path_button.setText("copy path")
