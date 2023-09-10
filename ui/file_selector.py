import os

from hutil.Qt.QtGui import QPixmap, QIcon
from hutil.Qt.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog

from ui.custom_standart_item_model import ICONS_PATH


class FileSelector(QWidget):
    """
    A custom QWidget for selecting and displaying a file path.

    Attributes:
        layout (QHBoxLayout): Layout containing the lineEdit and browseButton.
        lineEdit (QLineEdit): Displays the selected file path.
        browseButton (QPushButton): Triggers the file selection dialog.
    """

    def __init__(self, parent: QWidget = None):
        """
        Initialize the FileSelector widget.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super(FileSelector, self).__init__(parent)

        # Setting up the layout and components
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.setup_line_edit()
        self.setup_browse_button()

        # Applying styles
        self._set_styles()
        self.setContentsMargins(0, 0, 0, 0)  # left, top, right, bottom

    def setup_line_edit(self):
        """Initialize and configure the QLineEdit component."""
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setFixedHeight(30)
        self.layout.addWidget(self.lineEdit)

    def setup_browse_button(self):
        """Initialize and configure the browse QPushButton component."""
        self.browseButton = QPushButton(self)
        self.browseButton.setObjectName("BrowseButton")
        self.browseButton.setFixedSize(30, 30)
        
        # Setting button icon
        pixmap = QPixmap(os.path.join(ICONS_PATH, "folder.png"))
        self.browseButton.setIcon(QIcon(pixmap))
        
        # Connecting the button click signal
        self.browseButton.clicked.connect(self.browse)
        
        self.layout.addWidget(self.browseButton)

    def browse(self):
        """Open a file dialog and update the QLineEdit with the selected file path."""
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file')
        if fname:
            self.lineEdit.setText(fname)

    def setText(self, text: str):
        """
        Set the content of the QLineEdit.

        Args:
            text (str): Text to display in the QLineEdit.
        """
        self.lineEdit.setText(text)

    def setPlaceholderText(self, text: str):
        """
        Set placeholder text for the QLineEdit.

        Args:
            text (str): Placeholder text to display.
        """
        self.lineEdit.setPlaceholderText(text)

    def text(self) -> str:
        """Get the current text from the QLineEdit.
        
        Returns:
            str: Text from the QLineEdit.
        """
        return self.lineEdit.text()

    def _set_styles(self):
        """Set the CSS styles for the widget's components."""
        # Styles for the browse button
        self.browseButton.setStyleSheet('''
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
        ''')

        # Styles for the line edit
        self.lineEdit.setStyleSheet('''
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
        ''')
