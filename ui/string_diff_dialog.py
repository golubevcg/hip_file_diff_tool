from hutil.Qt.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QHBoxLayout
from hutil.Qt.QtGui import QPixmap, QColor, QBrush, QPen, QPainter, QPalette
from hutil.Qt.QtWidgets import QDialog, QWidget, QTextEdit, QVBoxLayout, QStyledItemDelegate, QStyle, QLabel
from hutil.Qt.QtCore import Qt, QSize, QEvent
from ui.constants import DATA_ROLE

import difflib

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
    def __init__(self, text, parent=None):
        super().__init__(parent)

        old_text = '''
        def init_ui(self) -> None:
            """Initialize UI components."""
            self.set_window_properties()
            self.setup_layouts()
            self.setup_tree_views()
            self.setup_checkboxes()
            self.setup_signals_and_slots()
            self.apply_stylesheet()

            # TODO: TEMP CODE REMOVE BEFORE MERGE
            self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test/fixtures/billowy_smoke_source.hipnc")
            self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test/fixtures/billowy_smoke_source_edited.hipnc")
            self.handle_compare_button_click()
        '''

        new_text = '''
        def init_ui(self) -> None:
            """Initialize UI components."""
            self.set_window_properties()
            self.setup_checkboxes()
            self.setup_signals_and_slots()
            self.apply_stylesheet()
            print("tralala")

            # TODO: TEMP CODE REMOVE BEFORE MERGE
            self.source_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test/fixtures/billowy_smoke_source.hipnc")
            self.target_file_line_edit.setText("C:/Users/golub/Documents/hip_file_diff_tool/test/fixtures/billowy_smoke_source_edited.hipnc")
            self.handle_compare_button_click()
        '''

        # Split texts into lines for difflib processing
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        # Get diffs
        diff = difflib.Differ()
        diffs = list(diff.compare(old_lines, new_lines))

        # Process the diffs and get formatted strings for both QTextEdits
        old_html, new_html = self.process_diffs(diffs)

        # Create text edits and set their content
        self.old_text_edit = QTextEdit(self)
        self.old_text_edit.setHtml(old_html)
        self.new_text_edit = QTextEdit(self)
        self.new_text_edit.setHtml(new_html)

        # Layouts and widgets setup
        layout = QVBoxLayout(self)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.old_text_edit)
        h_layout.addWidget(self.new_text_edit)
        layout.addLayout(h_layout)
        self.setLayout(layout)

        self.overlay = Overlay(parent)
        self.overlay.show()
        
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

        for diff in diffs:
            opcode = diff[0]
            text = diff[2:]

            if opcode == ' ':
                old_html.append(f'<span style="background-color: #EEEEEE;">{text}</span>')
                new_html.append(f'<span style="background-color: #EEEEEE;">{text}</span>')
            elif opcode == '-':
                old_html.append(f'<span style="background-color: #FFDDDD; display: block;">{text}</span>')
                new_html.append('<span style="background-color: #FFEEEE; display: block;">&nbsp;</span>')
            elif opcode == '+':
                old_html.append('<span style="background-color: #EEFFEE; display: block;">&nbsp;</span>')
                new_html.append(f'<span style="background-color: #DDFFDD; display: block;">{text}</span>')

        return '<br>'.join(old_html), '<br>'.join(new_html)


