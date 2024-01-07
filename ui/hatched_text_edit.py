from hutil.Qt.QtWidgets import QTextEdit
from hutil.Qt.QtGui import (
    QPixmap, 
    QPen, 
    QPainter, 
    QColor, 
    QBrush
)
from hutil.Qt.QtWidgets import QTextEdit
from hutil.Qt.QtCore import Qt, QRect

class HatchedTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        """
        A custom QTextEdit that supports displaying hatched patterns on specific lines.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super(HatchedTextEdit, self).__init__(*args, **kwargs)
        self.hatched_lines = set()
        self.text_lines = ""

    def clearHatchedPatternForLine(self, line_number) -> None:
        """
        Clears the hatched pattern for a specified line number.

        Args:
            line_number (int): The line number for which the hatched pattern should be cleared.
        """
        if line_number in self.hatched_lines:
            self.hatched_lines.remove(line_number)
        self.viewport().update()

    def paintEvent(self, event) -> None:
        """
        Handles the paint event to draw hatched patterns on specified lines.

        Args:
            event: The paint event.
        """
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

    def _paint_hatched_pattern(self, painter: QPainter, rect: QRect) -> None:
        """
        Paints a hatched pattern within a given rectangle.

        Args:
            painter (QPainter): The painter used for drawing.
            rect (QRect): The rectangle area where the pattern should be painted.
        """
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