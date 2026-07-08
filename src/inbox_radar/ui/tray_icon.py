from __future__ import annotations

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QMenu,
    QSystemTrayIcon,
)


class InboxRadarTrayIcon(QSystemTrayIcon):
    open_requested = Signal()
    sync_requested = Signal()
    quit_requested = Signal()

    def __init__(
        self,
        icon: QIcon,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(icon, parent)

        self._pending_count = 0
        self._status_text = "Iniciando"

        self._open_action = QAction(
            "Abrir InboxRadar",
            self,
        )

        self._pending_action = QAction(
            "Pendientes: 0",
            self,
        )
        self._pending_action.setEnabled(False)

        self._status_action = QAction(
            "Estado: Iniciando",
            self,
        )
        self._status_action.setEnabled(False)

        self._sync_action = QAction(
            "Sincronizar ahora",
            self,
        )

        self._quit_action = QAction(
            "Salir",
            self,
        )

        self._menu = QMenu()

        self._menu.addAction(
            self._open_action
        )
        self._menu.setDefaultAction(
            self._open_action
        )

        self._menu.addSeparator()

        self._menu.addAction(
            self._pending_action
        )
        self._menu.addAction(
            self._status_action
        )

        self._menu.addSeparator()

        self._menu.addAction(
            self._sync_action
        )

        self._menu.addSeparator()

        self._menu.addAction(
            self._quit_action
        )

        self.setContextMenu(self._menu)

        self._open_action.triggered.connect(
            lambda _checked=False:
            self.open_requested.emit()
        )

        self._sync_action.triggered.connect(
            lambda _checked=False:
            self.sync_requested.emit()
        )

        self._quit_action.triggered.connect(
            lambda _checked=False:
            self.quit_requested.emit()
        )

        self.activated.connect(
            self._on_activated
        )

        self._update_tooltip()

    @Slot(int)
    def set_pending_count(
        self,
        count: int,
    ) -> None:
        self._pending_count = max(
            0,
            count,
        )

        self._pending_action.setText(
            f"Pendientes: {self._pending_count}"
        )

        self._update_tooltip()

    def set_status(
        self,
        status_text: str,
        *,
        syncing: bool = False,
    ) -> None:
        self._status_text = status_text

        self._status_action.setText(
            f"Estado: {status_text}"
        )

        self._sync_action.setEnabled(
            not syncing
        )

        self._update_tooltip()

    def set_syncing(self) -> None:
        self.set_status(
            "Sincronizando...",
            syncing=True,
        )

    def _update_tooltip(self) -> None:
        if self._pending_count == 1:
            pending_text = "1 pendiente"
        else:
            pending_text = (
                f"{self._pending_count} pendientes"
            )

        self.setToolTip(
            "InboxRadar"
            f"\n{pending_text}"
            f"\n{self._status_text}"
        )

    @Slot(
        QSystemTrayIcon.ActivationReason
    )
    def _on_activated(
        self,
        reason: (
            QSystemTrayIcon.ActivationReason
        ),
    ) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.open_requested.emit()
