from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from database.db import authenticate_user


class LoginWindow(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThriftCash — Login")
        self.setMinimumSize(1520, 820)
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left panel (branding) ─────────────────────────────────────────
        left = QWidget()
        left.setObjectName("login_left")
        left.setStyleSheet("""
            #login_left {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1B2D25, stop:1 #2D6A4F);
            }
        """)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lv = QVBoxLayout(left)
        lv.setAlignment(Qt.AlignCenter)
        lv.setSpacing(0)

        
        icon_lbl = QLabel("👕")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 200px; margin-bottom: -10px")

        brand = QLabel("ThriftCash")
        brand.setAlignment(Qt.AlignCenter)
        brand.setFont(QFont("Arial", 42, QFont.Bold))
        brand.setStyleSheet("color: #52B788; font-size: 60px;")

        tagline = QLabel("Sistem Kasir Toko Pakaian Bekas")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("color: #B7D5C4; font-size: 40px;")

        desc = QLabel("Transaksi cepat, akurat, dan \nterdokumentasi untuk bisnis thrift shop kamu.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #74A68A; font-size: 20px; line-height: 1.6;")

        lv.addStretch()
        lv.addWidget(icon_lbl)
        lv.addSpacing(0)
        lv.addWidget(brand)
        lv.addSpacing(70)
        lv.addWidget(tagline)
        lv.addSpacing(0)
        lv.addWidget(desc)
        lv.addStretch()

        # ── Right panel (form) ────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background-color: #F0F4F1;")
        right.setMinimumWidth(400)
        rv = QVBoxLayout(right)
        rv.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(360)
        cv = QVBoxLayout(card)
        cv.setSpacing(16)
        cv.setContentsMargins(10, 15, 10, 15)

        title = QLabel("Masuk ke ThriftCash")
        title.setObjectName("login_title")

        subtitle = QLabel("Masukkan username dan password Anda")
        subtitle.setObjectName("login_subtitle")

        # Username
        lbl_user = QLabel("Username")
        lbl_user.setObjectName("form_label")
        self.inp_username = QLineEdit()
        self.inp_username.setPlaceholderText("Masukkan username")

        # Password
        lbl_pass = QLabel("Password")
        lbl_pass.setObjectName("form_label")
        self.inp_password = QLineEdit()
        self.inp_password.setEchoMode(QLineEdit.Password)
        self.inp_password.setPlaceholderText("Masukkan password")
        self.inp_password.returnPressed.connect(self._do_login)

        # Button
        self.btn_login = QPushButton("Masuk")
        self.btn_login.setObjectName("btn_primary")
        self.btn_login.setFixedHeight(42)
        self.btn_login.setFont(QFont("Arial", 13, QFont.Bold))
        self.btn_login.clicked.connect(self._do_login)


        cv.addWidget(title)
        cv.addWidget(subtitle)
        cv.addSpacing(8)
        cv.addWidget(lbl_user)
        cv.addWidget(self.inp_username)
        cv.addWidget(lbl_pass)
        cv.addWidget(self.inp_password)
        cv.addSpacing(8)
        cv.addWidget(self.btn_login)

        rv.addWidget(card)

        root.addWidget(left, stretch=1)
        root.addWidget(right)

    def _do_login(self):
        username = self.inp_username.text().strip()
        password = self.inp_password.text()
        if not username or not password:
            QMessageBox.warning(self, "Login Gagal", "Username dan password wajib diisi.")
            return
        user = authenticate_user(username, password)
        if user:
            self.login_success.emit(dict(user))
        else:
            QMessageBox.critical(self, "Login Gagal", "Username atau password salah.")
            self.inp_password.clear()
            self.inp_password.setFocus()
