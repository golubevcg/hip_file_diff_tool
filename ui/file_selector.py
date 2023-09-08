import os
from hutil.Qt.QtGui import QPixmap, QIcon
from hutil.Qt.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from ui.custom_standart_item_model import ICONS_PATH


class FileSelector(QWidget):
    """
    A custom QWidget to allow users to select and display a file path.
    
    Attributes:
        layout (QHBoxLayout): The main layout for the widget.
        lineEdit (QLineEdit): Input field to display the selected file path.
        browseButton (QPushButton): Button to open the file dialog for file selection.
    """
    
    def __init__(self, parent=None):
        """
        Initialize a new instance of the FileSelector widget.
        
        :param parent: Parent widget for this FileSelector widget.
        """
        super(FileSelector, self).__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setFixedHeight(40)
        self.layout.addWidget(self.lineEdit)
        
        self.browseButton = QPushButton(self)
        self.browseButton.setObjectName("browseButton")
        self.browseButton.setStyleSheet("background-color:transparent;")
        pixmap = QPixmap(os.path.join(ICONS_PATH, "folder.png"))
        qicon = QIcon(pixmap)
        self.browseButton.setIcon(qicon)

        self.browseButton.setObjectName("BrowseButton")
        self.browseButton.clicked.connect(self.browse)
        self.layout.addWidget(self.browseButton)
        self.browseButton.setFixedHeight(40)
        self.browseButton.setFixedWidth(40)

        # Setting CSS styles for the widget components
        self._set_styles()

    def browse(self):
        """
        Open a file dialog and set the selected file path to the lineEdit.
        """
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file')
        if fname:
            self.lineEdit.setText(fname)

    def setText(self, text: str):
        """
        Set the text of the lineEdit.
        
        :param text: Text to set in the lineEdit.
        """
        self.lineEdit.setText(text)

    def setPlaceholderText(self, text: str):
        """
        Set the placeholder text of the lineEdit.
        
        :param text: Placeholder text to set in the lineEdit.
        """
        self.lineEdit.setPlaceholderText(text)

    def text(self) -> str:
        """
        Retrieve the current text from the lineEdit.
        
        :return: The text from the lineEdit.
        """
        return self.lineEdit.text()

    def _set_styles(self):
        """
        Set the CSS styles for the widget components.
        """
        self.browseButton.setStyleSheet(
            '''
            QPushButton{
                font: 10pt "Arial";
                background-color: transparent;
                border-radius: 10px;
            }
            QPushButton:hover {
                color: #919191;
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
            }
            '''
        )

        self.lineEdit.setStyleSheet(
            '''
            QLineEdit{
                font: 10pt "Arial";
                color: #818181;
                background-color: #464646;
                border-radius: 10px;
            }
            QLineEdit:hover {
                color: #919191;
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
            }
            QLineEdit:selected {
                color: #919191;
                background-color: #555555;
                border: 1px solid rgb(185, 134, 32);
            }            
            '''
        )
