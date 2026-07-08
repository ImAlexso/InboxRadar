from __future__ import annotations

import hashlib

from PySide6.QtCore import (
    QObject,
    QLockFile,
    Signal,
    Slot,
)
from PySide6.QtNetwork import (
    QLocalServer,
    QLocalSocket,
)

from .paths import app_data_dir


class SingleInstanceError(RuntimeError):
    """InboxRadar could not establish instance ownership."""


class SingleInstanceCoordinator(QObject):
    """Keep one InboxRadar instance and reactivate it."""

    activation_requested = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        data_dir = app_data_dir()

        self._lock = QLockFile(
            str(data_dir / "inbox_radar.lock")
        )

        # This lock lives for the whole application
        # lifetime, not for a short operation.
        self._lock.setStaleLockTime(0)

        identity = (
            str(data_dir.resolve())
            .casefold()
            .encode("utf-8")
        )

        instance_hash = hashlib.sha256(
            identity
        ).hexdigest()[:16]

        self._server_name = (
            f"inbox-radar-{instance_hash}"
        )

        self._server = QLocalServer(self)

        self._server.setSocketOptions(
            QLocalServer.SocketOption.UserAccessOption
        )

        self._server.newConnection.connect(
            self._on_new_connection
        )

        self._owns_instance = False

    def acquire_or_notify(self) -> bool:
        """
        Return True for the primary instance.

        Return False when another instance exists and
        has been asked to show itself.
        """
        if self._try_acquire_primary():
            return True

        if self._notify_existing():
            return False

        # The first process may have disappeared between
        # the lock check and the activation attempt.
        if self._lock.tryLock(250):
            try:
                self._start_server()

            except Exception:
                self._lock.unlock()
                raise

            self._owns_instance = True

            return True

        return False

    def _try_acquire_primary(self) -> bool:
        if not self._lock.tryLock(0):
            return False

        try:
            self._start_server()

        except Exception:
            self._lock.unlock()
            raise

        self._owns_instance = True

        return True

    def _start_server(self) -> None:
        if self._server.listen(
            self._server_name
        ):
            return

        # Safe here because this process already owns
        # the exclusive application lock.
        QLocalServer.removeServer(
            self._server_name
        )

        if self._server.listen(
            self._server_name
        ):
            return

        raise SingleInstanceError(
            "Could not start local activation server."
        )

    def _notify_existing(self) -> bool:
        socket = QLocalSocket()

        socket.connectToServer(
            self._server_name
        )

        if not socket.waitForConnected(750):
            return False

        socket.write(b"ACTIVATE")
        socket.waitForBytesWritten(250)
        socket.disconnectFromServer()

        return True

    @Slot()
    def _on_new_connection(self) -> None:
        activation_received = False

        while self._server.hasPendingConnections():
            socket = (
                self._server.nextPendingConnection()
            )

            if socket is None:
                break

            activation_received = True

            socket.disconnectFromServer()
            socket.deleteLater()

        if activation_received:
            self.activation_requested.emit()

    @Slot()
    def close(self) -> None:
        if self._server.isListening():
            self._server.close()

        if (
            self._owns_instance
            and self._lock.isLocked()
        ):
            self._lock.unlock()

        self._owns_instance = False
