from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..application import (
    ApplicationService,
    OpenPendingResult,
)
from .app_icon import build_app_icon
from .pending_card import PendingCard


class MainWindow(QMainWindow):
    """Main InboxRadar pending-message window."""

    pending_count_changed = Signal(int)

    def __init__(
        self,
        application: ApplicationService,
    ) -> None:
        super().__init__()

        self._application = application
        self._close_to_tray_enabled = False

        self.setWindowTitle("InboxRadar")
        self.setMinimumSize(660, 420)
        self.resize(740, 540)

        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(
            self._clear_feedback
        )

        self._sync_status_label = QLabel("Iniciando")
        self._sync_status_label.setObjectName(
            "syncStatus"
        )
        self._sync_status_label.setProperty(
            "kind",
            "neutral",
        )
        self._sync_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._feedback_label = QLabel()
        self._feedback_label.setObjectName(
            "feedbackLabel"
        )
        self._feedback_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        self._feedback_label.setWordWrap(True)
        self._feedback_label.hide()

        self._count_label = QLabel("0")
        self._count_label.setObjectName("countBadge")
        self._count_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._cards_container = QWidget()
        self._cards_container.setObjectName(
            "cardsContainer"
        )

        self._cards_layout = QVBoxLayout(
            self._cards_container
        )
        self._cards_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self._cards_layout.setSpacing(8)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("pendingScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setWidget(
            self._cards_container
        )

        brand_icon = QLabel()
        brand_icon.setObjectName("brandIcon")
        brand_icon.setPixmap(
            build_app_icon().pixmap(24, 24)
        )
        brand_icon.setFixedSize(26, 26)
        brand_icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        brand_label = QLabel("InboxRadar")
        brand_label.setObjectName("brandTitle")

        brand_left_layout = QHBoxLayout()
        brand_left_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        brand_left_layout.setSpacing(9)
        brand_left_layout.addWidget(brand_icon)
        brand_left_layout.addWidget(brand_label)

        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        status_layout.setSpacing(4)
        status_layout.addWidget(
            self._sync_status_label,
            alignment=Qt.AlignmentFlag.AlignRight,
        )
        status_layout.addWidget(
            self._feedback_label,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        brand_layout.addLayout(brand_left_layout)
        brand_layout.addStretch()
        brand_layout.addLayout(status_layout)

        section_title = QLabel("Pendientes")
        section_title.setObjectName("sectionTitle")

        section_title_layout = QHBoxLayout()
        section_title_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        section_title_layout.setSpacing(9)
        section_title_layout.addWidget(section_title)
        section_title_layout.addWidget(
            self._count_label
        )
        section_title_layout.addStretch()

        section_summary = QLabel(
            "Correos que todavía requieren una decisión"
        )
        section_summary.setObjectName(
            "sectionSummary"
        )

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )
        content_layout.setSpacing(0)
        content_layout.addLayout(brand_layout)
        content_layout.addSpacing(22)
        content_layout.addLayout(
            section_title_layout
        )
        content_layout.addSpacing(2)
        content_layout.addWidget(section_summary)
        content_layout.addSpacing(13)
        content_layout.addWidget(scroll_area, 1)

        central_widget = QWidget()
        central_widget.setObjectName("mainSurface")
        central_widget.setLayout(content_layout)

        self.setCentralWidget(central_widget)

        # The old status bar is intentionally hidden. Sync state
        # and transient feedback now live in the compact header.
        self.statusBar().hide()

        self.refresh_pending()

    def set_close_to_tray_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._close_to_tray_enabled = enabled

    @Slot()
    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        if self._close_to_tray_enabled:
            event.ignore()
            self.hide()
            return

        super().closeEvent(event)

    def set_sync_state(
        self,
        text: str,
        *,
        kind: str = "neutral",
    ) -> None:
        self._sync_status_label.setText(text)
        self._sync_status_label.setProperty(
            "kind",
            kind,
        )

        style = self._sync_status_label.style()
        style.unpolish(self._sync_status_label)
        style.polish(self._sync_status_label)
        self._sync_status_label.update()

    def show_feedback(
        self,
        message: str,
        timeout_ms: int = 4000,
    ) -> None:
        clean_message = message.strip()

        if not clean_message:
            self._clear_feedback()
            return

        self._feedback_timer.stop()
        self._feedback_label.setText(clean_message)
        self._feedback_label.show()

        if timeout_ms > 0:
            self._feedback_timer.start(timeout_ms)

    def _clear_feedback(self) -> None:
        self._feedback_timer.stop()
        self._feedback_label.clear()
        self._feedback_label.hide()

    def _clear_cards(self) -> None:
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _update_count(
        self,
        count: int,
    ) -> None:
        self._count_label.setText(str(count))

    def _show_empty_state(self) -> None:
        empty_state = QFrame()
        empty_state.setObjectName("emptyState")

        icon_label = QLabel()
        icon_label.setObjectName("emptyIcon")
        icon_label.setPixmap(
            build_app_icon().pixmap(40, 40)
        )
        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title = QLabel("Todo al día")
        title.setObjectName("emptyTitle")

        text = QLabel(
            "InboxRadar seguirá vigilando "
            "en segundo plano."
        )
        text.setObjectName("emptyText")
        text.setWordWrap(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(
            24,
            30,
            24,
            30,
        )
        layout.setSpacing(7)
        layout.addWidget(
            icon_label,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        layout.addSpacing(3)
        layout.addWidget(
            title,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        layout.addWidget(
            text,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )

        empty_state.setLayout(layout)

        self._cards_layout.addWidget(empty_state)
        self._cards_layout.addStretch()

    def _show_load_error(self) -> None:
        error_state = QFrame()
        error_state.setObjectName("errorState")

        title = QLabel(
            "No se pudieron cargar los pendientes"
        )
        title.setObjectName("emptyTitle")

        text = QLabel(
            "InboxRadar no ha podido leer "
            "el estado local."
        )
        text.setObjectName("emptyText")
        text.setWordWrap(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(
            24,
            30,
            24,
            30,
        )
        layout.setSpacing(7)
        layout.addWidget(title)
        layout.addWidget(text)

        error_state.setLayout(layout)

        self._cards_layout.addWidget(error_state)
        self._cards_layout.addStretch()

    def refresh_pending(self) -> None:
        self._clear_cards()

        try:
            messages = self._application.list_pending()

        except Exception:
            self._update_count(0)
            self._show_load_error()
            self.show_feedback(
                "Error al cargar los pendientes.",
                6000,
            )
            return

        count = len(messages)
        self._update_count(count)
        self.pending_count_changed.emit(count)

        if not messages:
            self._show_empty_state()
            return

        for message in messages:
            card = PendingCard(message)

            card.open_requested.connect(
                self._open_message
            )
            card.managed_requested.connect(
                self._mark_managed
            )
            card.ignored_requested.connect(
                self._mark_ignored
            )

            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()

    @Slot(str)
    def _open_message(
        self,
        message_key: str,
    ) -> None:
        try:
            result = self._application.open_pending(
                message_key
            )

        except Exception:
            self.show_feedback(
                "No se pudo abrir el correo.",
                5000,
            )
            return

        if result is OpenPendingResult.OPENED:
            self.show_feedback(
                "Correo abierto en Outlook.",
                3000,
            )
            return

        if result is OpenPendingResult.NOT_PENDING:
            self.show_feedback(
                "Ese correo ya no está pendiente.",
                4000,
            )
            self.refresh_pending()
            return

        if result is OpenPendingResult.INVALID_LINK:
            message = (
                "El correo no tiene un enlace válido."
            )

        elif (
            result
            is OpenPendingResult.BROWSER_UNAVAILABLE
        ):
            message = (
                "El navegador configurado "
                "no está disponible."
            )

        else:
            message = "No se pudo abrir el correo."

        self.show_feedback(message, 5000)

    @Slot(str)
    def _mark_managed(
        self,
        message_key: str,
    ) -> None:
        try:
            changed = self._application.mark_managed(
                message_key
            )

        except Exception:
            self.show_feedback(
                "No se pudo actualizar el correo.",
                5000,
            )
            return

        if changed:
            self.show_feedback(
                "Correo marcado como gestionado.",
                3500,
            )
        else:
            self.show_feedback(
                "Ese correo ya no estaba pendiente.",
                4000,
            )

        self.refresh_pending()

    @Slot(str)
    def _mark_ignored(
        self,
        message_key: str,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Ignorar correo",
            (
                "Este correo desaparecerá "
                "de pendientes.\n\n"
                "¿Quieres ignorarlo?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            changed = self._application.mark_ignored(
                message_key
            )

        except Exception:
            self.show_feedback(
                "No se pudo actualizar el correo.",
                5000,
            )
            return

        if changed:
            self.show_feedback(
                "Correo ignorado.",
                3500,
            )
        else:
            self.show_feedback(
                "Ese correo ya no estaba pendiente.",
                4000,
            )

        self.refresh_pending()
