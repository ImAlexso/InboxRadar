from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .application import ApplicationService
from .ui.main_window import MainWindow


def main() -> int:
    qt_application = QApplication(sys.argv)

    qt_application.setApplicationName(
        "InboxRadar"
    )
    qt_application.setOrganizationName(
        "InboxRadar"
    )

    application = ApplicationService()

    window = MainWindow(application)
    window.show()

    return qt_application.exec()
