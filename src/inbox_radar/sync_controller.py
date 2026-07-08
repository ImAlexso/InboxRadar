from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal

import requests
from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    Signal,
    Slot,
)

from .application import (
    ApplicationService,
    ApplicationSyncResult,
)
from .errors import (
    AuthenticationError,
    ConfigurationError,
    GraphApiError,
    InboxRadarError,
)


SyncFailureCode = Literal[
    "AUTHENTICATION",
    "CONFIGURATION",
    "NETWORK",
    "GRAPH",
    "DATABASE",
    "APPLICATION",
    "UNEXPECTED",
]


@dataclass(frozen=True, slots=True)
class SyncFailure:
    code: SyncFailureCode
    user_message: str
    retryable: bool


def _safe_sync_failure(
    error: Exception,
) -> SyncFailure:
    if isinstance(error, ConfigurationError):
        return SyncFailure(
            code="CONFIGURATION",
            user_message=(
                "La configuración local "
                "de InboxRadar no es válida."
            ),
            retryable=False,
        )

    if isinstance(error, AuthenticationError):
        return SyncFailure(
            code="AUTHENTICATION",
            user_message=(
                "No se pudo completar "
                "la autenticación."
            ),
            retryable=False,
        )

    if isinstance(
        error,
        requests.RequestException,
    ):
        return SyncFailure(
            code="NETWORK",
            user_message=(
                "Sin conexión con Outlook. "
                "Se reintentará automáticamente."
            ),
            retryable=True,
        )

    if isinstance(error, GraphApiError):
        return SyncFailure(
            code="GRAPH",
            user_message=(
                "Outlook no respondió correctamente. "
                "Se reintentará automáticamente."
            ),
            retryable=True,
        )

    if isinstance(error, sqlite3.Error):
        return SyncFailure(
            code="DATABASE",
            user_message=(
                "El estado local está "
                "temporalmente ocupado. "
                "Se reintentará automáticamente."
            ),
            retryable=True,
        )

    if isinstance(error, InboxRadarError):
        return SyncFailure(
            code="APPLICATION",
            user_message=(
                "La sincronización no se completó. "
                "Se reintentará automáticamente."
            ),
            retryable=True,
        )

    return SyncFailure(
        code="UNEXPECTED",
        user_message=(
            "Se produjo un error inesperado. "
            "La sincronización automática se ha detenido."
        ),
        retryable=False,
    )


class _SyncWorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(object)


class _SyncWorker(QRunnable):
    def __init__(
        self,
        application: ApplicationService,
    ) -> None:
        super().__init__()

        self._application = application
        self.signals = _SyncWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._application.sync_now()

        except Exception as error:
            self.signals.failed.emit(
                _safe_sync_failure(error)
            )
            return

        self.signals.succeeded.emit(result)


class SyncController(QObject):
    sync_started = Signal()
    sync_succeeded = Signal(object)
    sync_failed = Signal(object)

    def __init__(
        self,
        application: ApplicationService,
        *,
        interval_seconds: int = 60,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        if interval_seconds < 1:
            raise ValueError(
                "interval_seconds must be positive"
            )

        self._application = application
        self._interval_ms = (
            interval_seconds * 1000
        )
        self._max_retry_interval_ms = (
            5 * 60 * 1000
        )

        self._started = False
        self._sync_in_progress = False
        self._consecutive_failures = 0

        self._active_worker: (
            _SyncWorker | None
        ) = None

        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(
            self.request_sync
        )

    @property
    def is_syncing(self) -> bool:
        return self._sync_in_progress

    def start(self) -> None:
        if self._started:
            return

        self._started = True

        # Primera sync en cuanto arranque
        # el event loop de Qt.
        self._timer.start(0)

    def stop(self) -> None:
        self._started = False
        self._timer.stop()
        self._thread_pool.clear()

    @Slot()
    def request_sync(self) -> bool:
        if self._sync_in_progress:
            return False

        self._timer.stop()

        self._sync_in_progress = True

        worker = _SyncWorker(
            self._application
        )

        worker.signals.succeeded.connect(
            self._on_sync_succeeded
        )
        worker.signals.failed.connect(
            self._on_sync_failed
        )

        self._active_worker = worker

        self.sync_started.emit()

        self._thread_pool.start(worker)

        return True

    @Slot(object)
    def _on_sync_succeeded(
        self,
        result: ApplicationSyncResult,
    ) -> None:
        self._sync_in_progress = False
        self._active_worker = None
        self._consecutive_failures = 0

        self.sync_succeeded.emit(result)

        self._schedule_next(
            self._interval_ms
        )

    @Slot(object)
    def _on_sync_failed(
        self,
        failure: SyncFailure,
    ) -> None:
        self._sync_in_progress = False
        self._active_worker = None
        self._consecutive_failures += 1

        self.sync_failed.emit(failure)

        if not failure.retryable:
            return

        multiplier = 2 ** (
            self._consecutive_failures - 1
        )

        retry_delay_ms = min(
            self._interval_ms * multiplier,
            self._max_retry_interval_ms,
        )

        self._schedule_next(
            retry_delay_ms
        )

    def _schedule_next(
        self,
        delay_ms: int,
    ) -> None:
        if not self._started:
            return

        self._timer.start(delay_ms)
