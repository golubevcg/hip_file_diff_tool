import sys
import os
import argparse

from ui.hip_file_diff_window import HipFileDiffWindow

from hutil.Qt.QtWidgets import QApplication
from hutil.Qt.QtCore import Qt


def main():
    parser = argparse.ArgumentParser(description="Command-line parser for given parameters.")

    # Argument for 'executable_path'
    parser.add_argument("-e", "--executable", dest="executable_path",
                        help="Path to the executable.")

    # Argument for 'source_file_path'
    parser.add_argument("-s", "--source", dest="source_file_path",
                        help="Path to the source file.")

    # Argument for 'target_file_path'
    parser.add_argument("-t", "--target", dest="target_file_path",
                        help="Path to the target file.")

    # Argument for 'item_path'
    parser.add_argument("-i", "--item-path", dest="item_path",
                        help="Path to the item to open in string diff.")

    args = parser.parse_args()

    main_path = os.path.abspath(__file__)
    args.main_path = main_path
    
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    app = QApplication(sys.argv)
    window = HipFileDiffWindow(args)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
