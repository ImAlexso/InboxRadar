APP_STYLESHEET = """
QWidget {
    background-color: #0a0e13;
    color: #edf2f7;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow,
QWidget#mainSurface {
    background-color: #0a0e13;
}

QLabel {
    background-color: transparent;
    border: none;
}

QLabel#brandTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
}

QLabel#brandIcon {
    background-color: transparent;
}

QLabel#syncStatus {
    min-height: 22px;
    padding: 2px 9px;
    border: 1px solid #303846;
    border-radius: 9px;
    background-color: #151b24;
    color: #aab4c2;
    font-size: 11px;
    font-weight: 600;
}

QLabel#syncStatus[kind="ok"] {
    background-color: #102019;
    color: #8ed0a6;
    border-color: #254431;
}

QLabel#syncStatus[kind="syncing"] {
    background-color: #141d32;
    color: #9db2ff;
    border-color: #2a3b68;
}

QLabel#syncStatus[kind="warning"] {
    background-color: #292216;
    color: #dfbd78;
    border-color: #4a3b24;
}

QLabel#syncStatus[kind="error"] {
    background-color: #2a1b20;
    color: #e7a0a8;
    border-color: #4b2d36;
}

QLabel#feedbackLabel {
    color: #788392;
    font-size: 10px;
}

QLabel#sectionTitle {
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
}

QLabel#countBadge {
    min-width: 20px;
    min-height: 20px;
    padding: 1px 6px;
    background-color: #192231;
    color: #afc1ff;
    border: 1px solid #2b3a57;
    border-radius: 9px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#sectionSummary {
    color: #7f8a99;
    font-size: 12px;
}

QWidget#cardsContainer {
    background-color: transparent;
}

QScrollArea#pendingScroll {
    border: none;
    background-color: transparent;
}

QScrollArea#pendingScroll > QWidget > QWidget {
    background-color: transparent;
}

QFrame#pendingCard {
    background-color: #131922;
    border: 1px solid #242d39;
    border-radius: 11px;
}

QFrame#pendingCard:hover {
    background-color: #151c26;
    border-color: #394657;
}

QFrame#pendingCard QLabel {
    background-color: transparent;
    border: none;
}

QLabel#messageSubject {
    color: #f5f7fa;
    font-size: 14px;
    font-weight: 600;
}

QLabel#messageMeta {
    color: #8f9aa8;
    font-size: 11px;
}

QLabel#unreadBadge {
    color: #8fa7ff;
    font-size: 10px;
    font-weight: 600;
}

QLabel#mailboxBadge {
    background-color: #211d18;
    color: #c7a979;
    border: 1px solid #3a3125;
    border-radius: 7px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 600;
}

QPushButton {
    min-height: 28px;
    border-radius: 7px;
    padding: 0 11px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#openButton {
    background-color: #1b232e;
    color: #dfe5ec;
    border: 1px solid #303b49;
}

QPushButton#openButton:hover {
    background-color: #242e3a;
    border-color: #465467;
}

QPushButton#managedButton {
    background-color: #405fdc;
    color: #ffffff;
    border: 1px solid #405fdc;
    padding: 0 12px;
}

QPushButton#managedButton:hover {
    background-color: #4d6bea;
    border-color: #4d6bea;
}

QPushButton#managedButton:pressed {
    background-color: #3653c9;
}

QPushButton#ignoredButton {
    background-color: transparent;
    color: #8f99a6;
    border: 1px solid transparent;
    padding: 0 9px;
}

QPushButton#ignoredButton:hover {
    background-color: #241b1f;
    color: #dc969f;
    border-color: #402932;
}

QFrame#emptyState,
QFrame#errorState {
    background-color: #10161d;
    border: 1px dashed #2a3440;
    border-radius: 11px;
}

QFrame#errorState {
    border-color: #4a2d36;
}

QLabel#emptyIcon {
    background-color: transparent;
}

QLabel#emptyTitle {
    color: #edf2f7;
    font-size: 16px;
    font-weight: 600;
}

QLabel#emptyText {
    color: #788392;
    font-size: 12px;
}

QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #2d3744;
    border-radius: 3px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #435064;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QMessageBox {
    background-color: #10161d;
}

QMessageBox QLabel {
    color: #edf2f7;
}

QWidget#alertWindow {
    background-color: transparent;
}

QFrame#alertPopup {
    background-color: #131a24;
    border: 1px solid #354258;
    border-radius: 12px;
}

QFrame#alertPopup QLabel {
    background-color: transparent;
    border: none;
}

QLabel#alertIcon {
    background-color: transparent;
}

QLabel#alertTitle {
    color: #a8b9f7;
    font-size: 11px;
    font-weight: 700;
}

QLabel#alertSubject {
    color: #f7f9fc;
    font-size: 15px;
    font-weight: 600;
}

QLabel#alertMeta {
    color: #8995a4;
    font-size: 11px;
}

QPushButton#dismissAlertButton {
    min-height: 0;
    padding: 0;
    background-color: transparent;
    color: #758192;
    border: none;
    border-radius: 6px;
    font-size: 17px;
    font-weight: 400;
}

QPushButton#dismissAlertButton:hover {
    background-color: #222b37;
    color: #eef2f7;
}

QPushButton#alertOpenButton {
    min-height: 28px;
    padding: 0 11px;
    background-color: #1b232e;
    color: #dfe5ec;
    border: 1px solid #303b49;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#alertOpenButton:hover {
    background-color: #242e3a;
    border-color: #465467;
}

QPushButton#alertIgnoredButton {
    min-height: 28px;
    padding: 0 9px;
    background-color: transparent;
    color: #8f99a6;
    border: 1px solid transparent;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#alertIgnoredButton:hover {
    background-color: #241b1f;
    color: #dc969f;
    border-color: #402932;
}

QPushButton#alertManagedButton {
    min-height: 28px;
    padding: 0 12px;
    background-color: #405fdc;
    color: #ffffff;
    border: 1px solid #405fdc;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#alertManagedButton:hover {
    background-color: #4d6bea;
    border-color: #4d6bea;
}

QPushButton#alertManagedButton:pressed {
    background-color: #3653c9;
}
"""
