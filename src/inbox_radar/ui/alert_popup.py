from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QCloseEvent,
    QScreen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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

        self.setFixedWidth(430)

        container = QFrame()
        container.setObjectName("alertPopup")

        eyebrow = QLabel(
            "NUEVO CORREO PENDIENTE"
        )
        eyebrow.setObjectName(
            "alertEyebrow"
        )

        dismiss_button = QPushButton("×")
        dismiss_button.setObjectName(
            "dismissAlertButton"
        )
        dismiss_button.setFixedSize(28, 28)
        dismiss_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        heading_layout = QHBoxLayout()
        heading_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        heading_layout.addWidget(eyebrow)
        heading_layout.addStretch()
        heading_layout.addWidget(
            dismiss_button
        )

        subject = str(
            message.get("subject")
            or "(Sin asunto)"
        )

        subject_label = QLabel(subject)
        subject_label.setObjectName(
            "alertSubject"
        )
        subject_label.setWordWrap(True)

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

        sender_label = QLabel(sender)
        sender_label.setObjectName(
            "alertSender"
        )

        if (
            sender_address
            and sender_address.lower()
            != sender.lower()
        ):
            sender_label.setToolTip(
                sender_address
            )

        open_button = QPushButton(
            "Abrir en Outlook"
        )
        open_button.setObjectName(
            "alertOpenButton"
        )

        ignored_button = QPushButton(
            "Ignorar"
        )
        ignored_button.setObjectName(
            "alertIgnoredButton"
        )

        managed_button = QPushButton(
            "Gestionado"
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
        actions_layout.setSpacing(7)
        actions_layout.addWidget(open_button)
        actions_layout.addStretch()
        actions_layout.addWidget(
            ignored_button
        )
        actions_layout.addWidget(
            managed_button
        )

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(
            18,
            14,
            18,
            16,
        )
        container_layout.setSpacing(9)
        container_layout.addLayout(
            heading_layout
        )
        container_layout.addWidget(
            subject_label
        )
        container_layout.addWidget(
            sender_label
        )
        container_layout.addSpacing(4)
        container_layout.addLayout(
            actions_layout
        )

        container.setLayout(
            container_layout
        )

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
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
        self._dismiss_timer.setInterval(
            15_000
        )
        self._dismiss_timer.timeout.connect(
            self.request_dismiss
        )

    def show_on_screen(
        self,
        screen: QScreen,
    ) -> None:
        self.adjustSize()

        geometry = screen.availableGeometry()

        margin = 18

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
