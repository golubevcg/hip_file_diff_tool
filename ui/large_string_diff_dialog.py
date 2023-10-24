from hutil.Qt.QtWidgets import QDialog, QTextEdit, QVBoxLayout


class LargeStringDiffDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(text)
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)