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
        self.hatched_lines = set()
        self.text_lines = ""

    def clearHatchedPatternForLine(self, line_number):
        if line_number in self.hatched_lines:
            self.hatched_lines.remove(line_number)
        self.viewport().update()

    def paintEvent(self, event):
        # Let the QTextEdit handle its regular painting
        super(HatchedTextEdit, self).paintEvent(event)

        for index, line in enumerate(self.text_lines):
            if "data_hashed_line" in line:
                self.hatched_lines.add(index)
        if self.hatched_lines:
            painter = QPainter(self.viewport())
            for line_number in self.hatched_lines:
                block = self.document().findBlockByLineNumber(line_number)
                layout = block.layout()
                if layout is not None:
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