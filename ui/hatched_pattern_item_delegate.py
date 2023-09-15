import os
import copy
import zipfile
from hutil.Qt.QtGui import (
    QPixmap, QIcon, QStandardItemModel, QStandardItem,
    QColor, QBrush, QPen, QPainter, QTransform
)
from hutil.Qt.QtWidgets import QStyledItemDelegate
from hutil.Qt.QtCore import Qt
from typing import Dict, Optional
from ui.constants import *


class HatchedItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Draw the hatched pattern on the entire item rect

        is_hatched = index.data(DATA_ROLE).is_hatched
        if is_hatched:
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
            
            # Let the default delegate handle the rest (e.g., text rendering)
            option.backgroundBrush = QBrush(Qt.transparent)  # Clear the background brush to avoid default painting
        
        super().paint(painter, option, index)