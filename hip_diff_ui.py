import sys
from PySide2.QtWidgets import QApplication, QMainWindow

class SimpleWindow(QMainWindow):
    def __init__(self):
        super(SimpleWindow, self).__init__()
        
        # Set window properties
        self.setWindowTitle('Simple Window')
        self.setGeometry(100, 100, 400, 300)

def main():
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()