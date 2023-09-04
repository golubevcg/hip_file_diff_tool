import sys
import os
import random
from PySide2.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QPushButton, 
                               QTreeView, QSplitter, QMessageBox)
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItemModel, QStandardItem

from api.hip_file_comparator import HipFileComparator, SUPPORTED_FILE_FORMATS


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
                padding: 4px;
            }
            QPushButton {
                font: 12pt "Arial";
                color: #FFFFFF;
                background-color: #555555;
                border: 1px solid black;
                border-radius: 5px;
                padding: 4px;

            }
            QTreeView {
                font: 12pt "Arial";
                color: #FFFFFF;
                background-color: #333333;
                border: 1px solid black;
                border-radius: 5px;
                padding: 4px;
            }
        """

        self.setStyleSheet(main_stylesheet)

        # Horizontal layout at the top
        self.source_file_line_edit = QLineEdit(self)
        self.source_file_line_edit.setMinimumWidth(100)
        self.source_file_line_edit.setPlaceholderText("source_file_line_edit")

        self.target_file_line_edit = QLineEdit(self)        
        self.target_file_line_edit.setMinimumWidth(100)
        self.target_file_line_edit.setPlaceholderText("target_file_line_edit")
        
        self.load_button = QPushButton("Load scenes", self)
        self.load_button.clicked.connect(self.handle_load_button_click)
        self.load_button.setMinimumWidth(100)

        self.top_hlayout = QHBoxLayout()
        self.top_hlayout.addWidget(self.source_file_line_edit)
        self.top_hlayout.addWidget(self.target_file_line_edit)
        self.top_hlayout.addWidget(self.load_button)
        self.main_layout.addLayout(self.top_hlayout)

        # splitter = QSplitter(Qt.Horizontal, self)
        # self.main_layout.addWidget(splitter)

        self.treeviews_layout = QHBoxLayout()
        self.main_layout.addLayout(self.treeviews_layout)

        # Splitter for three QTreeViews

        self.source_treeview = QTreeView(self)
        self.target_treeview = QTreeView(self)

        self.treeviews_layout.addWidget(self.source_treeview)
        self.treeviews_layout.addWidget(self.target_treeview)

        # Populate the treeviews with random data
        self.populate_random_data(self.source_treeview)
        self.populate_random_data(self.target_treeview)
        

    def populate_random_data(self, treeview):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Name'])
        
        num_folders = random.randint(3, 6)
        
        for _ in range(num_folders):
            folder_name = f"Folder_{random.randint(10, 99)}"
            folder_item = QStandardItem(folder_name)
            
            num_files = random.randint(2, 5)
            for _ in range(num_files):
                file_name = f"File_{random.randint(100, 999)}.txt"
                file_item = QStandardItem(file_name)
                folder_item.appendRow(file_item)
            
            model.appendRow(folder_item)
        
        treeview.setModel(model)

    def handle_load_button_click(self):

        source_scene_path = self.source_file_line_edit.text()
        self.check_file_path(source_scene_path)
        
        target_scene_path = self.target_file_line_edit.text()
        self.check_file_path(target_scene_path)

        hip_comparator = HipFileComparator(source_scene_path, target_scene_path)


        # create comparator
        # load it, save data
        # 

    def check_file_path(self, path):
        if not os.path.exists(path):
            incorrect_path_text = "Incorrect source path specified, such file don't exists."
            QMessageBox.critical(self, "Error", incorrect_path_text)
            raise RuntimeError(incorrect_path_text)
        
        _, extension = os.path.splitext(path)
        print("_, extension", _, extension)
        if extension[1:] not in SUPPORTED_FILE_FORMATS:
            only_hip_supported_text = "Incorrect source file specified, only .hip files supported."
            QMessageBox.critical(self, "Error", only_hip_supported_text)
            raise RuntimeError(only_hip_supported_text)


