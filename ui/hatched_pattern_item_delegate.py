from hutil.Qt.QtGui import QPixmap, QColor, QBrush, QPen, QPainter, QLinearGradient
from hutil.Qt.QtWidgets import QStyledItemDelegate, QStyle
from hutil.Qt.QtCore import Qt, QSize, QEvent
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

        option.displayAlignment = Qt.AlignTop

        if index.data(Qt.DisplayRole).count("\n") >= 3:
            # Create the gradient overlay effect for darkening
            gradient = QLinearGradient(
                option.rect.topLeft(), 
                option.rect.bottomLeft()
            )
            gradient.setColorAt(0.25, Qt.transparent)     
            gradient.setColorAt(1, QColor("#202020"))

            painter.fillRect(option.rect, gradient)

        borderColor = QColor(Qt.transparent)
        is_hovered = option.state & QStyle.State_MouseOver
        if is_hovered:
            borderColor = QColor(185, 134, 32)
            
        painter.setPen(borderColor)
        painter.drawLine(option.rect.topLeft(), option.rect.topRight())
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())

        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        text = index.data(Qt.DisplayRole)
        if "\n" in text:
            return QSize(option.rect.width(), 100)
        
        return super().sizeHint(option, index)
    
    def helpEvent(self, event, view, option, index):
        if event.type() == QEvent.ToolTip:
            if index.data(Qt.DisplayRole).count("\n") >= 3 :
                view.setToolTip(
                    "String diff available for this item,"
                    "double click on item to open.")
            else:
                view.setToolTip("")  # Clear the tooltip for other items
        return super(HatchedItemDelegate, self)\
                .helpEvent(event, view, option, index)


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
