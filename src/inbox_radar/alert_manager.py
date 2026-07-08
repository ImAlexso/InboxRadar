from __future__ import annotations

from collections import deque

from PySide6.QtCore import (
    QObject,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QDesktopServices,
)
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)

from .application import ApplicationService
from .ui.alert_popup import AlertPopup


class AlertManager(QObject):
    pending_changed = Signal()
    status_message = Signal(str)

    def __init__(
        self,
        application: ApplicationService,
        anchor_window: QWidget,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._application = application
        self._anchor_window = anchor_window

        self._queue: deque[str] = deque()
        self._queued_keys: set[str] = set()

        self._current_key: str | None = None
        self._current_popup: (
            AlertPopup | None
        ) = None

    def enqueue(
        self,
        message_keys: tuple[str, ...],
    ) -> None:
        for message_key in message_keys:
            if (
                message_key == self._current_key
                or message_key in self._queued_keys
            ):
                continue

            self._queue.append(message_key)
            self._queued_keys.add(message_key)

        self._show_next()

    def _show_next(self) -> None:
        if self._current_popup is not None:
            return

        while self._queue:
            message_key = self._queue.popleft()
            self._queued_keys.discard(
                message_key
            )

            try:
                message = (
                    self._application.get_pending(
                        message_key
                    )
                )
            except Exception:
                self.status_message.emit(
                    "No se pudo preparar "
                    "una alerta."
                )
                continue

            if message is None:
                continue

            popup = AlertPopup(message)

            popup.dismissed.connect(
                self._finish_current
            )
            popup.open_requested.connect(
                self._open_message
            )
            popup.managed_requested.connect(
                self._mark_managed
            )
            popup.ignored_requested.connect(
                self._mark_ignored
            )

            self._current_key = message_key
            self._current_popup = popup

            screen = self._anchor_window.screen()

            if screen is None:
                screen = (
                    QApplication.primaryScreen()
                )

            if screen is None:
                self._finish_current()
                return

            popup.show_on_screen(screen)
            return

    @Slot()
    def _finish_current(self) -> None:
        popup = self._current_popup

        self._current_popup = None
        self._current_key = None

        if popup is not None:
            popup.close_from_manager()
            popup.deleteLater()

        QTimer.singleShot(
            150,
            self._show_next,
        )

    @Slot(str)
    def _open_message(
        self,
        message_key: str,
    ) -> None:
        try:
            message = self._application.get_pending(
                message_key
            )
        except Exception:
            self.status_message.emit(
                "No se pudo cargar el correo."
            )
            return

        if message is None:
            self.pending_changed.emit()
            self._finish_current()
            return

        web_link = str(
            message.get("web_link")
            or ""
        ).strip()

        url = QUrl(web_link)

        if (
            not url.isValid()
            or url.scheme().lower()
            not in {"http", "https"}
        ):
            self.status_message.emit(
                "El correo no tiene "
                "un enlace válido."
            )
            return

        if not QDesktopServices.openUrl(url):
            self.status_message.emit(
                "No se pudo abrir el correo."
            )
            return

        self.status_message.emit(
            "Correo abierto en Outlook."
        )

        self._finish_current()

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
            self.status_message.emit(
                "No se pudo actualizar "
                "el correo."
            )
            return

        self.pending_changed.emit()

        if changed:
            self.status_message.emit(
                "Correo marcado como gestionado."
            )

        self._finish_current()

    @Slot(str)
    def _mark_ignored(
        self,
        message_key: str,
    ) -> None:
        try:
            changed = (
                self._application.mark_ignored(
                    message_key
                )
            )
        except Exception:
            self.status_message.emit(
                "No se pudo actualizar "
                "el correo."
            )
            return

        self.pending_changed.emit()

        if changed:
            self.status_message.emit(
                "Correo ignorado."
            )

        self._finish_current()
