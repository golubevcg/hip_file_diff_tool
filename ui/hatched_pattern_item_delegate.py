from hutil.Qt.QtGui import QPixmap, QColor, QBrush, QPen, QPainter
from hutil.Qt.QtWidgets import QStyledItemDelegate
from hutil.Qt.QtCore import Qt
from ui.constants import DATA_ROLE


class HatchedItemDelegate(QStyledItemDelegate):
    """
    Custom item delegate class that supports hatched patterns as backgrounds.
    """

    def paint(self, painter: QPainter, option, index) -> None:
        """
        Custom paint method to render items with a hatched pattern.

        :param painter: QPainter instance used to draw the item.
        :param option: Provides style options for the item.
        :param index: QModelIndex of the item in the model.
        """
        is_hatched = index.data(DATA_ROLE).is_hatched
        if is_hatched:
            self._paint_hatched_pattern(painter, option)

        # Let the default delegate handle the rest (e.g., text rendering)
        super().paint(painter, option, index)

    def _paint_hatched_pattern(self, painter: QPainter, option) -> None:
        """
        Draws the hatched pattern on the item.

        :param painter: QPainter instance used to draw the item.
        :param option: Provides style options for the item.
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
        painter.fillRect(option.rect, brush)

        # Clear the background brush to avoid default painting
        option.backgroundBrush = QBrush(Qt.transparent)
