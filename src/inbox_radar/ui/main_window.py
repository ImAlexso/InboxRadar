from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..application import ApplicationService


class MainWindow(QMainWindow):
    """Minimal pending-message window."""

    def __init__(
        self,
        application: ApplicationService,
    ) -> None:
        super().__init__()

        self._application = application

        self.setWindowTitle("InboxRadar")
        self.resize(900, 500)

        self._count_label = QLabel()

        self._refresh_button = QPushButton(
            "Actualizar"
        )
        self._refresh_button.clicked.connect(
            self.refresh_pending
        )

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(
            [
                "Asunto",
                "Remitente",
                "Fecha",
            ]
        )

        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        title_label = QLabel("Pendientes")

        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)

        header_layout = QHBoxLayout()
        header_layout.addWidget(title_label)
        header_layout.addWidget(self._count_label)
        header_layout.addStretch()
        header_layout.addWidget(self._refresh_button)

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addWidget(self._table)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        self.refresh_pending()

    def refresh_pending(self) -> None:
        messages = self._application.list_pending()

        self._table.setRowCount(len(messages))

        for row_index, message in enumerate(messages):
            message_key = str(
                message["message_key"]
            )

            subject_item = QTableWidgetItem(
                str(message["subject"])
            )
            subject_item.setData(
                Qt.ItemDataRole.UserRole,
                message_key,
            )

            sender = (
                str(message["sender_name"])
                or str(message["sender_address"])
            )

            sender_item = QTableWidgetItem(sender)

            received_item = QTableWidgetItem(
                str(message["received_at"])
            )

            self._table.setItem(
                row_index,
                0,
                subject_item,
            )
            self._table.setItem(
                row_index,
                1,
                sender_item,
            )
            self._table.setItem(
                row_index,
                2,
                received_item,
            )

        self._count_label.setText(
            f"({len(messages)})"
        )
