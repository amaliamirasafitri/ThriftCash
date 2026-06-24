import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from database.db import init_db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def load_stylesheet(app):
    qss_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    # Initialize database
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("ThriftCash")
    app.setApplicationVersion("1.0")

    load_stylesheet(app)

    # State containers
    state = {"main_window": None}

    def on_login(user):
        login.hide()
        mw = MainWindow(user)
        state["main_window"] = mw

        def on_logout():
            mw.close()
            state["main_window"] = None
            login.inp_password.clear()
            login.show()

        mw.logout_requested.connect(on_logout)
        mw.show()

    login = LoginWindow()
    login.login_success.connect(on_login)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
