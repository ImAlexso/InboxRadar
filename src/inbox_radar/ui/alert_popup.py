from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtCore import (
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCloseEvent,
    QScreen,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .app_icon import build_app_icon


def _format_alert_time(value: object) -> str:
    raw_value = str(value or "").strip()

    if not raw_value:
        return "Ahora"

    try:
        normalized = raw_value.replace(
            "Z",
            "+00:00",
        )
        received = datetime.fromisoformat(normalized)

        if received.tzinfo is None:
            received = received.replace(
                tzinfo=timezone.utc
            )

        local_received = received.astimezone()
        local_now = datetime.now().astimezone()

        difference = local_now - local_received

        if timedelta(0) <= difference < timedelta(minutes=2):
            return "Ahora"

        if local_received.date() == local_now.date():
            return f"Hoy, {local_received:%H:%M}"

        yesterday = (
            local_now - timedelta(days=1)
        ).date()

        if local_received.date() == yesterday:
            return f"Ayer, {local_received:%H:%M}"

        if local_received.year == local_now.year:
            return local_received.strftime(
                "%d/%m, %H:%M"
            )

        return local_received.strftime(
            "%d/%m/%Y, %H:%M"
        )

    except ValueError:
        return "Ahora"


class AlertPopup(QWidget):
    dismissed = Signal()
    open_requested = Signal(str)
    managed_requested = Signal(str)
    ignored_requested = Signal(str)

    def __init__(
        self,
        message: dict[str, object],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
            (
                Qt.WindowType.Tool
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            ),
        )

        self._message_key = str(
            message["message_key"]
        )
        self._allow_close = False
        self._dismiss_requested = False

        self.setObjectName("alertWindow")
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )
        self.setFixedWidth(410)

        container = QFrame()
        container.setObjectName("alertPopup")

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 120))
        container.setGraphicsEffect(shadow)

        icon_label = QLabel()
        icon_label.setObjectName("alertIcon")
        icon_label.setPixmap(
            build_app_icon().pixmap(20, 20)
        )
        icon_label.setFixedSize(22, 22)
        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label = QLabel("Nuevo pendiente")
        title_label.setObjectName("alertTitle")

        dismiss_button = QPushButton("×")
        dismiss_button.setObjectName(
            "dismissAlertButton"
        )
        dismiss_button.setFixedSize(26, 26)
        dismiss_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        dismiss_button.setToolTip(
            "Cerrar esta alerta"
        )

        heading_layout = QHBoxLayout()
        heading_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        heading_layout.setSpacing(8)
        heading_layout.addWidget(icon_label)
        heading_layout.addWidget(title_label)
        heading_layout.addStretch()
        heading_layout.addWidget(dismiss_button)

        subject = str(
            message.get("subject")
            or "(Sin asunto)"
        )

        subject_label = QLabel(subject)
        subject_label.setObjectName("alertSubject")
        subject_label.setWordWrap(True)
        subject_label.setToolTip(subject)

        sender_name = str(
            message.get("sender_name")
            or ""
        ).strip()
        sender_address = str(
            message.get("sender_address")
            or ""
        ).strip()

        sender = (
            sender_name
            or sender_address
            or "Remitente desconocido"
        )

        received = _format_alert_time(
            message.get("received_at")
        )

        meta_label = QLabel(
            f"{sender} · {received}"
        )
        meta_label.setObjectName("alertMeta")

        if (
            sender_address
            and sender_address.lower()
            != sender.lower()
        ):
            meta_label.setToolTip(sender_address)

        open_button = QPushButton("Abrir")
        open_button.setObjectName("alertOpenButton")
        open_button.setToolTip("Abrir en Outlook")

        ignored_button = QPushButton("Ignorar")
        ignored_button.setObjectName(
            "alertIgnoredButton"
        )

        managed_button = QPushButton(
            "✓  Gestionado"
        )
        managed_button.setObjectName(
            "alertManagedButton"
        )

        for button in (
            open_button,
            ignored_button,
            managed_button,
        ):
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        actions_layout.setSpacing(5)
        actions_layout.addWidget(open_button)
        actions_layout.addStretch()
        actions_layout.addWidget(ignored_button)
        actions_layout.addWidget(managed_button)

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(
            16,
            13,
            16,
            14,
        )
        container_layout.setSpacing(0)
        container_layout.addLayout(heading_layout)
        container_layout.addSpacing(11)
        container_layout.addWidget(subject_label)
        container_layout.addSpacing(4)
        container_layout.addWidget(meta_label)
        container_layout.addSpacing(13)
        container_layout.addLayout(actions_layout)

        container.setLayout(container_layout)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(
            12,
            12,
            12,
            14,
        )
        root_layout.addWidget(container)

        self.setLayout(root_layout)

        dismiss_button.clicked.connect(
            self.request_dismiss
        )
        open_button.clicked.connect(
            lambda: self.open_requested.emit(
                self._message_key
            )
        )
        ignored_button.clicked.connect(
            lambda: self.ignored_requested.emit(
                self._message_key
            )
        )
        managed_button.clicked.connect(
            lambda: self.managed_requested.emit(
                self._message_key
            )
        )

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.setInterval(15_000)
        self._dismiss_timer.timeout.connect(
            self.request_dismiss
        )

    def show_on_screen(
        self,
        screen: QScreen,
    ) -> None:
        self.adjustSize()

        geometry = screen.availableGeometry()
        margin = 10

        x = (
            geometry.right()
            - self.width()
            - margin
            + 1
        )
        y = (
            geometry.bottom()
            - self.height()
            - margin
            + 1
        )

        self.move(x, y)
        self.show()
        self.raise_()

        self._dismiss_timer.start()

    def request_dismiss(self) -> None:
        if self._dismiss_requested:
            return

        self._dismiss_requested = True
        self._dismiss_timer.stop()

        self.dismissed.emit()

    def close_from_manager(self) -> None:
        self._dismiss_timer.stop()
        self._allow_close = True
        self.close()

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        if self._allow_close:
            event.accept()
            return

        event.ignore()
        self.request_dismiss()
