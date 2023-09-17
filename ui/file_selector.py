import os

from hutil.Qt.QtGui import QPixmap, QIcon
from hutil.Qt.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from ui.constants import ICONS_PATH


class FileSelector(QWidget):
    """
    A custom QWidget for selecting and displaying a file path. This widget combines a QLineEdit and a QPushButton
    for file browsing.
    """

    def __init__(self, parent: QWidget = None):
        """
        Initialize the FileSelector widget.

        Args:
            parent (QWidget, optional): The parent widget for the FileSelector. Defaults to None.
        """
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)

        self.setup_line_edit()
        self.setup_browse_button()
        self._set_styles()

        self.setContentsMargins(0, 0, 0, 0)

    def setup_line_edit(self):
        """Configure the QLineEdit component."""
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setFixedHeight(30)
        self.layout.addWidget(self.lineEdit)

    def setup_browse_button(self):
        """Configure the QPushButton component for file browsing."""
        self.browseButton = QPushButton(self)
        pixmap = QPixmap(os.path.join(ICONS_PATH, "folder.png"))
        self.browseButton.setIcon(QIcon(pixmap))
        self.browseButton.setFixedSize(30, 30)
        self.browseButton.clicked.connect(self.browse)
        self.layout.addWidget(self.browseButton)

    def browse(self):
        """Open a file dialog and set the selected file path to the QLineEdit."""
        fname, _ = QFileDialog.getOpenFileName(self, "Open file")
        if fname:
            self.lineEdit.setText(fname)

    def setText(self, text: str):
        """
        Set the content of the QLineEdit.

        Args:
            text (str): The text to display in the QLineEdit.
        """
        self.lineEdit.setText(text)

    def setPlaceholderText(self, text: str):
        """
        Set placeholder text for the QLineEdit.

        Args:
            text (str): Placeholder text to be displayed when QLineEdit is empty.
        """
        self.lineEdit.setPlaceholderText(text)

    def text(self) -> str:
        """Return the current text from the QLineEdit.

        Returns:
            str: Text currently displayed in the QLineEdit.
        """
        return self.lineEdit.text()

    def _set_styles(self):
        """Private method to apply CSS styles for the widget components."""
        # Styles for the browse button
        self.browseButton.setStyleSheet(
            """
            QPushButton{
                font: 8pt "Arial";
                background-color: transparent;
                border-radius: 10px;
            }
            QPushButton:hover {
                color: #919191;
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
            }
        """
        )

        # Styles for the line edit
        self.lineEdit.setStyleSheet(
            """
            QLineEdit{
                font: 10pt "Arial";
                color: #818181;
                background-color: #464646;
                border-radius: 10px;
                padding-left: 5px;
                padding-right: 5px;
            }
            QLineEdit:hover, QLineEdit:selected {
                color: #919191;
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
            }            
        """
        )
