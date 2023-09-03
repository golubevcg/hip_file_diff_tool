import sys

from ui.hip_file_diff_window import HipFileDiffWindow
from PySide2.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    window = HipFileDiffWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()