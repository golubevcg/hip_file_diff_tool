import sys

from ui.hip_file_diff_window import HipFileDiffWindow

from hutil.Qt.QtWidgets import QApplication
from hutil.Qt.QtCore import Qt, QSize
from hutil.Qt.QtWidgets import QStyleFactory


def main(): 
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    app = QApplication(sys.argv)
    window = HipFileDiffWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
