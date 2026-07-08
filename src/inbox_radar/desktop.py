from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .application import (
    ApplicationService,
    ApplicationSyncResult,
)
from .sync_controller import (
    SyncController,
    SyncFailure,
)
from .ui.main_window import MainWindow
from .ui.theme import APP_STYLESHEET


def _handle_sync_success(
    window: MainWindow,
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


def _handle_sync_failure(
    window: MainWindow,
    failure: SyncFailure,
) -> None:
    window.statusBar().showMessage(
        failure.user_message
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

    application = ApplicationService()

    window = MainWindow(application)

    sync_controller = SyncController(
        application,
        interval_seconds=60,
        parent=window,
    )

    sync_controller.sync_started.connect(
        lambda: window.statusBar().showMessage(
            "Sincronizando..."
        )
    )

    sync_controller.sync_succeeded.connect(
        lambda result: _handle_sync_success(
            window,
            result,
        )
    )

    sync_controller.sync_failed.connect(
        lambda failure: _handle_sync_failure(
            window,
            failure,
        )
    )

    qt_application.aboutToQuit.connect(
        sync_controller.stop
    )

    window.show()

    sync_controller.start()

    return qt_application.exec()
