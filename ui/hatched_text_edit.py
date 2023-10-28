from hutil.Qt.QtWidgets import QTextEdit
from hutil.Qt.QtGui import (
    QPixmap, 
    QColor, 
    QBrush, 
    QPen, 
    QPainter, 
    QPixmap, 
    QPainter, 
    QPen, 
    QColor, 
    QBrush
)
from hutil.Qt.QtWidgets import QTextEdit
from hutil.Qt.QtCore import Qt, QRect

class HatchedTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super(HatchedTextEdit, self).__init__(*args, **kwargs)
        self.hatched_line = None

    def setHatchedPatternForLine(self, line_number):
        self.hatched_line = line_number
        self.viewport().update()

    def paintEvent(self, event):
        # Let the QTextEdit handle its regular painting
        super(HatchedTextEdit, self).paintEvent(event)

        # If there's a line to hatch, draw the pattern on it
        if self.hatched_line is not None:
            painter = QPainter(self.viewport())
            block = self.document().findBlockByLineNumber(self.hatched_line - 1)
            layout = block.layout()
            position = layout.position()
            rect = QRect(0, position.y(), self.viewport().width(), layout.boundingRect().height())

            self._paint_hatched_pattern(painter, rect)
            painter.end()

    def _paint_hatched_pattern(self, painter, rect):
        hatch_width = 1000
        pixmap = QPixmap(hatch_width, hatch_width)
        pixmap.fill(Qt.transparent)

        pen_color = QColor("#505050")
        pen_width = 3
        pen = QPen(pen_color, pen_width)
        pen.setCapStyle(Qt.FlatCap)

        pixmap_painter = QPainter(pixmap)
        pixmap_painter.setPen(pen)
        for i in range(-hatch_width, hatch_width, pen_width * 6):
            pixmap_painter.drawLine(i, hatch_width, hatch_width + i, 0)
        pixmap_painter.end()

        brush = QBrush(pixmap)
        painter.fillRect(rect, brush)
