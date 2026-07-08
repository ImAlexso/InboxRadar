from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def _format_received_at(value: object) -> str:
    raw_value = str(value or "").strip()

    if not raw_value:
        return "Fecha desconocida"

    try:
        normalized = raw_value.replace(
            "Z",
            "+00:00",
        )

        received = datetime.fromisoformat(
            normalized
        )

        if received.tzinfo is None:
            received = received.replace(
                tzinfo=timezone.utc
            )

        local_received = received.astimezone()
        local_now = datetime.now().astimezone()

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
        return raw_value


class PendingCard(QFrame):
    open_requested = Signal(str)
    managed_requested = Signal(str)
    ignored_requested = Signal(str)

    def __init__(
        self,
        message: dict[str, object],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._message_key = str(
            message["message_key"]
        )

        self.setObjectName("pendingCard")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        subject = str(
            message.get("subject")
            or "(Sin asunto)"
        )

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

        received = _format_received_at(
            message.get("received_at")
        )

        subject_label = QLabel(subject)
        subject_label.setObjectName(
            "messageSubject"
        )
        subject_label.setToolTip(subject)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        top_layout.addWidget(subject_label, 1)

        if not bool(message.get("is_read")):
            unread_badge = QLabel("NO LEÍDO")
            unread_badge.setObjectName(
                "unreadBadge"
            )
            top_layout.addWidget(unread_badge)

        meta_label = QLabel(
            f"{sender} · {received}"
        )
        meta_label.setObjectName("messageMeta")

        if (
            sender_address
            and sender_address.lower()
            != sender.lower()
        ):
            meta_label.setToolTip(sender_address)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        actions_layout.setSpacing(7)

        if (
            message.get("mailbox_status")
            == "REMOVED_FROM_INBOX"
        ):
            mailbox_badge = QLabel(
                "FUERA DEL INBOX"
            )
            mailbox_badge.setObjectName(
                "mailboxBadge"
            )
            actions_layout.addWidget(
                mailbox_badge
            )

        actions_layout.addStretch()

        open_button = QPushButton(
            "Abrir en Outlook"
        )
        open_button.setObjectName("openButton")

        ignored_button = QPushButton("Ignorar")
        ignored_button.setObjectName(
            "ignoredButton"
        )

        managed_button = QPushButton(
            "Gestionado"
        )
        managed_button.setObjectName(
            "managedButton"
        )

        for button in (
            open_button,
            ignored_button,
            managed_button,
        ):
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
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

        actions_layout.addWidget(open_button)
        actions_layout.addWidget(ignored_button)
        actions_layout.addWidget(
            managed_button
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )
        layout.setSpacing(8)
        layout.addLayout(top_layout)
        layout.addWidget(meta_label)
        layout.addSpacing(3)
        layout.addLayout(actions_layout)

        self.setLayout(layout)
