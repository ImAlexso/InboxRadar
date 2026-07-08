from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)


def build_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)

    pixmap.fill(
        Qt.GlobalColor.transparent
    )

    painter = QPainter(pixmap)

    painter.setRenderHint(
        QPainter.RenderHint.Antialiasing
    )

    painter.setPen(
        Qt.PenStyle.NoPen
    )
    painter.setBrush(
        QColor("#111827")
    )

    painter.drawRoundedRect(
        4,
        4,
        56,
        56,
        14,
        14,
    )

    radar_pen = QPen(
        QColor("#7697ff"),
        3,
    )

    painter.setPen(radar_pen)
    painter.setBrush(
        Qt.BrushStyle.NoBrush
    )

    painter.drawEllipse(
        15,
        15,
        34,
        34,
    )

    painter.drawEllipse(
        23,
        23,
        18,
        18,
    )

    painter.drawLine(
        32,
        32,
        47,
        22,
    )

    painter.setPen(
        Qt.PenStyle.NoPen
    )
    painter.setBrush(
        QColor("#b5c3ff")
    )

    painter.drawEllipse(
        28,
        28,
        8,
        8,
    )

    painter.end()

    return QIcon(pixmap)
