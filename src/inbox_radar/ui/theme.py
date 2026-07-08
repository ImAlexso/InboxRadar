APP_STYLESHEET = """
QWidget {
    background-color: #0b0f14;
    color: #f2f5f8;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow {
    background-color: #0b0f14;
}

QLabel {
    background-color: transparent;
    border: none;
}

QLabel#brandTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
}

QLabel#privacyBadge {
    background-color: #131d31;
    color: #9eb5ff;
    border: 1px solid #293b66;
    border-radius: 8px;
    padding: 5px 9px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#sectionTitle {
    color: #ffffff;
    font-size: 25px;
    font-weight: 700;
}

QLabel#sectionSummary {
    color: #8f99a8;
    font-size: 13px;
}

QScrollArea#pendingScroll {
    border: none;
    background-color: transparent;
}

QScrollArea#pendingScroll > QWidget > QWidget {
    background-color: transparent;
}

QFrame#pendingCard {
    background-color: #151b23;
    border: 1px solid #252d39;
    border-radius: 12px;
}

QFrame#pendingCard:hover {
    border: 1px solid #3a4657;
}

QFrame#pendingCard QLabel {
    background-color: transparent;
    border: none;
}

QLabel#messageSubject {
    color: #f7f9fc;
    font-size: 15px;
    font-weight: 600;
}

QLabel#messageMeta {
    color: #a5aebb;
    font-size: 12px;
}

QLabel#unreadBadge {
    background-color: #222d4b;
    color: #b6c5ff;
    border: 1px solid #364673;
    border-radius: 7px;
    padding: 3px 7px;
    font-size: 9px;
    font-weight: 700;
}

QLabel#mailboxBadge {
    background-color: #29231d;
    color: #d8b487;
    border: 1px solid #4a3b2b;
    border-radius: 7px;
    padding: 3px 7px;
    font-size: 9px;
    font-weight: 700;
}

QPushButton {
    min-height: 32px;
    border-radius: 8px;
    padding: 0 13px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#openButton {
    background-color: #202732;
    color: #e6ebf1;
    border: 1px solid #343e4c;
}

QPushButton#openButton:hover {
    background-color: #29313d;
    border-color: #4a5667;
}

QPushButton#managedButton {
    background-color: #4e6df2;
    color: #ffffff;
    border: 1px solid #4e6df2;
}

QPushButton#managedButton:hover {
    background-color: #5d7afb;
    border-color: #5d7afb;
}

QPushButton#managedButton:pressed {
    background-color: #405edc;
}

QPushButton#ignoredButton {
    background-color: transparent;
    color: #aab3bf;
    border: 1px solid transparent;
}

QPushButton#ignoredButton:hover {
    background-color: #291f23;
    color: #e29aa3;
    border-color: #4a2c34;
}

QFrame#emptyState {
    background-color: #11171e;
    border: 1px dashed #2a3440;
    border-radius: 12px;
}

QLabel#emptyTitle {
    color: #f0f3f6;
    font-size: 17px;
    font-weight: 600;
}

QLabel#emptyText {
    color: #7f8997;
    font-size: 12px;
}

QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #303a47;
    border-radius: 3px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #465365;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #0b0f14;
    color: #7f8997;
    border-top: 1px solid #1d252f;
    font-size: 11px;
}
"""

APP_STYLESHEET += """
QWidget#alertWindow {
    background-color: transparent;
}

QFrame#alertPopup {
    background-color: #161d27;
    border: 1px solid #344154;
    border-radius: 13px;
}

QFrame#alertPopup QLabel {
    background-color: transparent;
    border: none;
}

QLabel#alertEyebrow {
    color: #8fa7ff;
    font-size: 9px;
    font-weight: 700;
}

QLabel#alertSubject {
    color: #ffffff;
    font-size: 15px;
    font-weight: 650;
}

QLabel#alertSender {
    color: #9ba6b5;
    font-size: 12px;
}

QPushButton#dismissAlertButton {
    min-height: 0;
    padding: 0;
    background-color: transparent;
    color: #8792a2;
    border: none;
    font-size: 18px;
    font-weight: 400;
}

QPushButton#dismissAlertButton:hover {
    background-color: #252e3a;
    color: #ffffff;
}

QPushButton#alertOpenButton {
    background-color: #222b37;
    color: #e8edf3;
    border: 1px solid #374352;
}

QPushButton#alertOpenButton:hover {
    background-color: #2c3643;
}

QPushButton#alertIgnoredButton {
    background-color: transparent;
    color: #aeb7c3;
    border: 1px solid transparent;
}

QPushButton#alertIgnoredButton:hover {
    background-color: #2b2025;
    color: #e6a0a8;
}

QPushButton#alertManagedButton {
    background-color: #4e6df2;
    color: #ffffff;
    border: 1px solid #4e6df2;
}

QPushButton#alertManagedButton:hover {
    background-color: #5d7afb;
}
"""
