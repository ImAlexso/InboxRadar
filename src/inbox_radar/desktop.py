from __future__ import annotations

import sqlite3
import sys

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QSystemTrayIcon,
)

from .alert_manager import AlertManager
from .application import (
    ApplicationService,
    ApplicationSyncResult,
)
from .errors import (
    ConfigurationError,
    InboxRadarError,
)
from .single_instance import (
    SingleInstanceCoordinator,
    SingleInstanceError,
)
from .sync_controller import (
    SyncController,
    SyncFailure,
)
from .ui.app_icon import build_app_icon
from .ui.main_window import MainWindow
from .ui.theme import APP_STYLESHEET
from .ui.tray_icon import InboxRadarTrayIcon


def _startup_error_message(
    error: Exception,
) -> str:
    if isinstance(error, ConfigurationError):
        return (
            "La configuración local de InboxRadar "
            "no es válida.\n\n"
            "Revisa el archivo .env y vuelve "
            "a intentarlo."
        )

    if isinstance(error, sqlite3.Error):
        return (
            "No se pudo abrir el estado local "
            "de InboxRadar.\n\n"
            "Cierra cualquier otra instancia y "
            "vuelve a intentarlo."
        )

    if isinstance(error, OSError):
        return (
            "No se pudo acceder al almacenamiento "
            "seguro o a los archivos locales "
            "de InboxRadar."
        )

    if isinstance(error, InboxRadarError):
        return (
            "InboxRadar no pudo completar "
            "la inicialización."
        )

    return (
        "Se produjo un error inesperado "
        "al iniciar InboxRadar."
    )


def _handle_sync_started(
    window: MainWindow,
    tray: InboxRadarTrayIcon | None,
) -> None:
    window.set_sync_state(
        "Sincronizando",
        kind="syncing",
    )

    if tray is not None:
        tray.set_syncing()


def _handle_sync_success(
    window: MainWindow,
    tray: InboxRadarTrayIcon | None,
    result: ApplicationSyncResult,
) -> None:
    window.refresh_pending()
    window.set_sync_state(
        "Al día",
        kind="ok",
    )

    new_count = len(result.new_pending_keys)

    if new_count == 1:
        window.show_feedback(
            "1 nuevo pendiente detectado",
            5000,
        )

    elif new_count > 1:
        window.show_feedback(
            f"{new_count} nuevos pendientes detectados",
            5000,
        )

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
    status_text = _tray_failure_status(failure)

    window.set_sync_state(
        status_text,
        kind="error",
    )
    window.show_feedback(
        failure.user_message,
        8000,
    )

    if tray is not None:
        tray.set_status(status_text)


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

    instance_coordinator = (
        SingleInstanceCoordinator(
            parent=qt_application,
        )
    )

    try:
        is_primary_instance = (
            instance_coordinator
            .acquire_or_notify()
        )

    except SingleInstanceError:
        QMessageBox.critical(
            None,
            "InboxRadar",
            (
                "No se pudo iniciar InboxRadar "
                "de forma segura.\n\n"
                "Cierra cualquier instancia abierta "
                "y vuelve a intentarlo."
            ),
        )

        return 1

    if not is_primary_instance:
        return 0

    try:
        application = ApplicationService()

    except Exception as error:
        instance_coordinator.close()

        QMessageBox.critical(
            None,
            "InboxRadar",
            _startup_error_message(error),
        )

        return 1

    window = MainWindow(application)
    window.setWindowIcon(app_icon)

    instance_coordinator.activation_requested.connect(
        window.show_from_tray
    )

    sync_controller = SyncController(
        application,
        interval_seconds=60,
        parent=window,
    )

    alert_manager = AlertManager(
        application,
        window,
        parent=window,
    )

    alert_manager.pending_changed.connect(
        window.refresh_pending
    )

    alert_manager.status_message.connect(
        lambda message:
        window.show_feedback(
            message,
            4000,
        )
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

    def handle_sync_success(
        result: ApplicationSyncResult,
    ) -> None:
        _handle_sync_success(
            window,
            tray,
            result,
        )

        alert_manager.enqueue(
            result.new_pending_keys
        )

    sync_controller.sync_succeeded.connect(
        handle_sync_success
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

    qt_application.aboutToQuit.connect(
        instance_coordinator.close
    )

    window.show()

    sync_controller.start()

    return qt_application.exec()
