from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QStatusBar,
    QSizePolicy, QFrame, QMenuBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction

from ui.dashboard_page import DashboardPage
from ui.pos_page import POSPage
from ui.product_page import ProductPage
from ui.report_page import ReportPage
from ui.user_page import UserPage


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("ThriftCash — Sistem Kasir Thrift Shop")
        self.setMinimumSize(1520, 820)
        self._build_menubar()
        self._build_ui()
        self._build_statusbar()
        self._navigate(0)

    # ── MENU BAR ──────────────────────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        act_pos = QAction("Transaksi Baru (POS)", self)
        act_pos.triggered.connect(lambda: self._navigate(1))
        act_export = QAction("Export Laporan...", self)
        act_export.triggered.connect(lambda: self._navigate(3))
        act_logout = QAction("Logout", self)
        act_logout.triggered.connect(self._logout)
        act_exit = QAction("Keluar", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_pos)
        file_menu.addAction(act_export)
        file_menu.addSeparator()
        file_menu.addAction(act_logout)
        file_menu.addAction(act_exit)

        help_menu = mb.addMenu("Help")
        act_about = QAction("Tentang ThriftCash", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ── MAIN UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(0, 0, 0, 0)
        sv.setSpacing(0)

        logo = QLabel("ThriftCash")
        logo.setObjectName("sidebar_logo")
        sub = QLabel("Thrift Shop POS")
        sub.setObjectName("sidebar_subtitle")
        sv.addWidget(logo)
        sv.addWidget(sub)

        # Nav buttons
        nav_items = [
            ("🏠", "Dashboard",      0),
            ("🧾", "Kasir / POS",    1),
            ("👕", "Produk",         2),
            ("📊", "Laporan",        3),
        ]
        if self.user['role'] == 'admin':
            nav_items.append(("👤", "Manajemen Pengguna", 4))

        sep = QLabel("MENU UTAMA")
        sep.setObjectName("nav_separator")
        sv.addWidget(sep)

        self.nav_buttons = []
        for icon, text, idx in nav_items:
            btn = QPushButton(f"  {icon}  {text}")
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(44)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            sv.addWidget(btn)
            self.nav_buttons.append((btn, idx))

        sv.addStretch()

        # User info box
        user_box = QFrame()
        user_box.setObjectName("sidebar_user_box")
        ubv = QVBoxLayout(user_box)
        ubv.setContentsMargins(0, 0, 0, 0)
        ubv.setSpacing(2)
        uname = QLabel(f"👤 {self.user['full_name']}")
        uname.setObjectName("sidebar_user_name")
        uname.setWordWrap(True)
        urole = QLabel(self.user['role'].capitalize())
        urole.setObjectName("sidebar_user_role")
        ubv.addWidget(uname)
        ubv.addWidget(urole)

        sv.addWidget(user_box)

        btn_logout = QPushButton("  🚪  Logout")
        btn_logout.setObjectName("nav_btn")
        btn_logout.setFixedHeight(40)
        btn_logout.clicked.connect(self._logout)
        sv.addWidget(btn_logout)

        # ── Content area ─────────────────────────────────────────────────────
        content_area = QWidget()
        cv = QVBoxLayout(content_area)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(56)
        tbh = QHBoxLayout(topbar)
        tbh.setContentsMargins(20, 0, 20, 0)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("page_title")
        tbh.addWidget(self.page_title)
        tbh.addStretch()
        cv.addWidget(topbar)

        # Pages
        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage(self.user)
        self.pos_page = POSPage(self.user)
        self.product_page = ProductPage(self.user)
        self.report_page = ReportPage(self.user)
        self.user_page = UserPage(self.user)

        self.pos_page.transaction_done.connect(self.dashboard_page._refresh)

        self.stack.addWidget(self.dashboard_page)  # 0
        self.stack.addWidget(self.pos_page)         # 1
        self.stack.addWidget(self.product_page)     # 2
        self.stack.addWidget(self.report_page)      # 3
        self.stack.addWidget(self.user_page)        # 4
        cv.addWidget(self.stack)

        root.addWidget(sidebar)
        root.addWidget(content_area, stretch=1)

    def _build_statusbar(self):
        sb = self.statusBar()
        # Show all members — update as needed for your group
        members = "ThriftCash © 2025/2026  |  Anggota: [Nama1 / NIM1] · [Nama2 / NIM2] · [Nama3 / NIM3]"
        sb.showMessage(members)

    # ── NAVIGATION ────────────────────────────────────────────────────────────

    def _navigate(self, index):
        titles = {0: "Dashboard", 1: "Kasir / POS", 2: "Manajemen Produk",
                  3: "Laporan Transaksi", 4: "Manajemen Pengguna"}
        self.stack.setCurrentIndex(index)
        self.page_title.setText(titles.get(index, ""))

        for btn, idx in self.nav_buttons:
            active = (idx == index)
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh data when navigating to certain pages
        if index == 3:
            self.report_page._load()
        elif index == 2:
            self.product_page._load()

    def _logout(self):
        reply = QMessageBox.question(self, "Logout",
                                     "Yakin ingin keluar dari sesi ini?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()

    def _show_about(self):
        QMessageBox.about(self, "Tentang ThriftCash",
                          "<b>ThriftCash v1.0</b><br>"
                          "Sistem Kasir Desktop untuk Toko Pakaian Bekas<br><br>"
                          "Dibuat dengan PySide6 · Python<br>"
                          "Final Project Pemrograman Visual 2025/2026")
