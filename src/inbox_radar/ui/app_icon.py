from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)


_ICON_SIZES = (16, 20, 24, 32, 48, 64, 128, 256)


def _build_icon_pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    inset = max(1.0, size * 0.055)
    background_rect = QRectF(
        inset,
        inset,
        size - (inset * 2),
        size - (inset * 2),
    )

    background = QLinearGradient(
        QPointF(0, 0),
        QPointF(size, size),
    )
    background.setColorAt(0.0, QColor("#172238"))
    background.setColorAt(1.0, QColor("#0a101b"))

    painter.setPen(
        QPen(
            QColor("#31405b"),
            max(1.0, size * 0.022),
        )
    )
    painter.setBrush(background)
    painter.drawRoundedRect(
        background_rect,
        size * 0.22,
        size * 0.22,
    )

    center = QPointF(size * 0.5, size * 0.5)
    outer_radius = size * 0.275
    inner_radius = size * 0.145
    radar_width = max(1.0, size * 0.048)

    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(
        QPen(
            QColor("#607bd6"),
            radar_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
    )

    painter.drawEllipse(
        center,
        outer_radius,
        outer_radius,
    )

    painter.setPen(
        QPen(
            QColor("#3d508d"),
            max(1.0, radar_width * 0.78),
        )
    )
    painter.drawEllipse(
        center,
        inner_radius,
        inner_radius,
    )

    sweep_end = QPointF(
        size * 0.755,
        size * 0.31,
    )

    painter.setPen(
        QPen(
            QColor("#91a8ff"),
            radar_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
    )
    painter.drawLine(center, sweep_end)

    center_radius = max(1.2, size * 0.045)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#dce5ff"))
    painter.drawEllipse(
        center,
        center_radius,
        center_radius,
    )

    target = QPointF(
        size * 0.69,
        size * 0.36,
    )
    target_radius = max(1.0, size * 0.038)
    painter.setBrush(QColor("#6f8fff"))
    painter.drawEllipse(
        target,
        target_radius,
        target_radius,
    )

    painter.end()

    return pixmap


def build_app_icon() -> QIcon:
    icon = QIcon()

    for size in _ICON_SIZES:
        icon.addPixmap(_build_icon_pixmap(size))

    return icon
