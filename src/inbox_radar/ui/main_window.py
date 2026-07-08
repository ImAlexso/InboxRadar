from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot
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
        self.setMinimumSize(680, 400)
        self.resize(760, 480)

        self._summary_label = QLabel()
        self._summary_label.setObjectName(
            "sectionSummary"
        )

        self._cards_container = QWidget()

        self._cards_layout = QVBoxLayout(
            self._cards_container
        )
        self._cards_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self._cards_layout.setSpacing(10)

        scroll_area = QScrollArea()
        scroll_area.setObjectName(
            "pendingScroll"
        )
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setWidget(
            self._cards_container
        )

        brand_label = QLabel("InboxRadar")
        brand_label.setObjectName(
            "brandTitle"
        )

        privacy_badge = QLabel(
            "LOCAL · PRIVADO"
        )
        privacy_badge.setObjectName(
            "privacyBadge"
        )

        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        brand_layout.addWidget(brand_label)
        brand_layout.addStretch()
        brand_layout.addWidget(
            privacy_badge
        )

        section_title = QLabel("Pendientes")
        section_title.setObjectName(
            "sectionTitle"
        )

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(
            24,
            20,
            24,
            16,
        )
        content_layout.setSpacing(0)

        content_layout.addLayout(
            brand_layout
        )
        content_layout.addSpacing(24)
        content_layout.addWidget(
            section_title
        )
        content_layout.addSpacing(3)
        content_layout.addWidget(
            self._summary_label
        )
        content_layout.addSpacing(16)
        content_layout.addWidget(
            scroll_area,
            1,
        )

        central_widget = QWidget()
        central_widget.setLayout(
            content_layout
        )

        self.setCentralWidget(central_widget)

        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage("Listo")

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

    def _clear_cards(self) -> None:
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _update_summary(
        self,
        count: int,
    ) -> None:
        if count == 0:
            text = (
                "No hay correos esperando "
                "una decisión"
            )
        elif count == 1:
            text = (
                "1 correo esperando tu decisión"
            )
        else:
            text = (
                f"{count} correos esperando "
                "tu decisión"
            )

        self._summary_label.setText(text)

    def _show_empty_state(self) -> None:
        empty_state = QFrame()
        empty_state.setObjectName(
            "emptyState"
        )

        title = QLabel("Todo al día")
        title.setObjectName("emptyTitle")

        text = QLabel(
            "No hay correos pendientes "
            "de decisión."
        )
        text.setObjectName("emptyText")

        layout = QVBoxLayout()
        layout.setContentsMargins(
            24,
            38,
            24,
            38,
        )
        layout.setSpacing(7)
        layout.addWidget(
            title,
            alignment=(
                Qt.AlignmentFlag.AlignHCenter
            ),
        )
        layout.addWidget(
            text,
            alignment=(
                Qt.AlignmentFlag.AlignHCenter
            ),
        )

        empty_state.setLayout(layout)

        self._cards_layout.addWidget(
            empty_state
        )
        self._cards_layout.addStretch()

    def _show_load_error(self) -> None:
        error_state = QFrame()
        error_state.setObjectName(
            "emptyState"
        )

        title = QLabel(
            "No se pudieron cargar "
            "los pendientes"
        )
        title.setObjectName("emptyTitle")

        text = QLabel(
            "InboxRadar no ha podido leer "
            "el estado local."
        )
        text.setObjectName("emptyText")

        layout = QVBoxLayout()
        layout.setContentsMargins(
            24,
            38,
            24,
            38,
        )
        layout.setSpacing(7)
        layout.addWidget(title)
        layout.addWidget(text)

        error_state.setLayout(layout)

        self._cards_layout.addWidget(
            error_state
        )
        self._cards_layout.addStretch()

    def refresh_pending(self) -> None:
        self._clear_cards()

        try:
            messages = (
                self._application.list_pending()
            )
        except Exception:
            self._update_summary(0)
            self._show_load_error()

            self.statusBar().showMessage(
                "Error al cargar los pendientes.",
                5000,
            )
            return

        self._update_summary(len(messages))

        self.pending_count_changed.emit(
            len(messages)
        )

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
            self.statusBar().showMessage(
                "No se pudo abrir el correo.",
                5000,
            )
            return

        if result is OpenPendingResult.OPENED:
            self.statusBar().showMessage(
                "Correo abierto en Outlook.",
                3000,
            )
            return

        if result is OpenPendingResult.NOT_PENDING:
            self.statusBar().showMessage(
                "Ese correo ya no está pendiente.",
                4000,
            )
            self.refresh_pending()
            return

        if result is OpenPendingResult.INVALID_LINK:
            message = (
                "El correo no tiene "
                "un enlace válido."
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

        self.statusBar().showMessage(
            message,
            5000,
        )

    @Slot(str)
    def _mark_managed(
        self,
        message_key: str,
    ) -> None:
        try:
            changed = (
                self._application.mark_managed(
                    message_key
                )
            )
        except Exception:
            self.statusBar().showMessage(
                "No se pudo actualizar el correo.",
                5000,
            )
            return

        if changed:
            self.statusBar().showMessage(
                "Correo marcado como gestionado.",
                3500,
            )
        else:
            self.statusBar().showMessage(
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

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            changed = (
                self._application.mark_ignored(
                    message_key
                )
            )
        except Exception:
            self.statusBar().showMessage(
                "No se pudo actualizar el correo.",
                5000,
            )
            return

        if changed:
            self.statusBar().showMessage(
                "Correo ignorado.",
                3500,
            )
        else:
            self.statusBar().showMessage(
                "Ese correo ya no estaba pendiente.",
                4000,
            )

        self.refresh_pending()
