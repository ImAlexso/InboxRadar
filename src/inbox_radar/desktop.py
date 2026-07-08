from __future__ import annotations

import sys

from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
)

from .application import (
    ApplicationService,
    ApplicationSyncResult,
)
from .sync_controller import (
    SyncController,
    SyncFailure,
)
from .ui.app_icon import build_app_icon
from .ui.main_window import MainWindow
from .ui.theme import APP_STYLESHEET
from .ui.tray_icon import InboxRadarTrayIcon


def _handle_sync_started(
    window: MainWindow,
    tray: InboxRadarTrayIcon | None,
) -> None:
    window.statusBar().showMessage(
        "Sincronizando..."
    )

    if tray is not None:
        tray.set_syncing()


def _handle_sync_success(
    window: MainWindow,
    tray: InboxRadarTrayIcon | None,
    result: ApplicationSyncResult,
) -> None:
    window.refresh_pending()

    new_count = len(
        result.new_pending_keys
    )

    if new_count == 1:
        message = (
            "1 nuevo pendiente detectado"
        )

    elif new_count > 1:
        message = (
            f"{new_count} nuevos "
            "pendientes detectados"
        )

    elif result.pending_count == 1:
        message = "Al día · 1 pendiente"

    else:
        message = (
            f"Al día · "
            f"{result.pending_count} pendientes"
        )

    window.statusBar().showMessage(message)

    if tray is not None:
        tray.set_pending_count(
            result.pending_count
        )
        tray.set_status("Al día")


def _tray_failure_status(
    failure: SyncFailure,
) -> str:
    statuses = {
        "AUTHENTICATION": (
            "Autenticación necesaria"
        ),
        "CONFIGURATION": (
            "Configuración incorrecta"
        ),
        "NETWORK": "Sin conexión",
        "GRAPH": "Error temporal de Outlook",
        "DATABASE": "Estado local ocupado",
        "APPLICATION": (
            "Error temporal"
        ),
        "UNEXPECTED": "Error",
    }

    return statuses.get(
        failure.code,
        "Error",
    )


def _handle_sync_failure(
    window: MainWindow,
    tray: InboxRadarTrayIcon | None,
    failure: SyncFailure,
) -> None:
    window.statusBar().showMessage(
        failure.user_message
    )

    if tray is not None:
        tray.set_status(
            _tray_failure_status(failure)
        )


def main() -> int:
    qt_application = QApplication(sys.argv)

    qt_application.setApplicationName(
        "InboxRadar"
    )
    qt_application.setOrganizationName(
        "InboxRadar"
    )

    qt_application.setStyle("Fusion")
    qt_application.setStyleSheet(
        APP_STYLESHEET
    )

    app_icon = build_app_icon()

    qt_application.setWindowIcon(app_icon)

    application = ApplicationService()

    window = MainWindow(application)
    window.setWindowIcon(app_icon)

    sync_controller = SyncController(
        application,
        interval_seconds=60,
        parent=window,
    )

    tray: InboxRadarTrayIcon | None = None

    if QSystemTrayIcon.isSystemTrayAvailable():
        qt_application.setQuitOnLastWindowClosed(
            False
        )

        window.set_close_to_tray_enabled(True)

        tray = InboxRadarTrayIcon(
            app_icon,
            parent=qt_application,
        )

        tray.open_requested.connect(
            window.show_from_tray
        )

        tray.sync_requested.connect(
            sync_controller.request_sync
        )

        tray.quit_requested.connect(
            qt_application.quit
        )

        window.pending_count_changed.connect(
            tray.set_pending_count
        )

        tray.set_pending_count(
            application.count_pending()
        )

        tray.show()

        qt_application.aboutToQuit.connect(
            tray.hide
        )

    sync_controller.sync_started.connect(
        lambda: _handle_sync_started(
            window,
            tray,
        )
    )

    sync_controller.sync_succeeded.connect(
        lambda result: _handle_sync_success(
            window,
            tray,
            result,
        )
    )

    sync_controller.sync_failed.connect(
        lambda failure: _handle_sync_failure(
            window,
            tray,
            failure,
        )
    )

    qt_application.aboutToQuit.connect(
        sync_controller.stop
    )

    window.show()

    sync_controller.start()

    return qt_application.exec()
