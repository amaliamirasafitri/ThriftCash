from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QDialogButtonBox, QComboBox, QMessageBox, QHeaderView, QGridLayout
)
from PySide6.QtCore import Qt
from database.db import get_all_users, insert_user, update_user, delete_user


class UserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Edit Pengguna" if user else "Tambah Pengguna")
        self.setFixedSize(400, 340)
        self._build()
        if user:
            self._fill(user)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 16)
        lay.setSpacing(10)

        title = QLabel("✏️ Edit Pengguna" if self.user else "➕ Tambah Pengguna")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2D25;")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        def lbl(text):
            l = QLabel(text)
            l.setObjectName("form_label")
            return l

        self.inp_username = QLineEdit(); self.inp_username.setPlaceholderText("username")
        self.inp_fullname = QLineEdit(); self.inp_fullname.setPlaceholderText("Nama lengkap")
        self.cmb_role = QComboBox(); self.cmb_role.addItems(["kasir", "admin"])
        self.inp_password = QLineEdit()
        self.inp_password.setEchoMode(QLineEdit.Password)
        self.inp_password.setPlaceholderText("Password baru (kosongkan jika tidak diubah)" if self.user else "Password")

        grid.addWidget(lbl("Username *"), 0, 0); grid.addWidget(self.inp_username, 0, 1)
        grid.addWidget(lbl("Nama Lengkap *"), 1, 0); grid.addWidget(self.inp_fullname, 1, 1)
        grid.addWidget(lbl("Role"), 2, 0); grid.addWidget(self.cmb_role, 2, 1)
        grid.addWidget(lbl("Password *"), 3, 0); grid.addWidget(self.inp_password, 3, 1)

        lay.addLayout(grid)
        lay.addStretch()

        btn_box = QDialogButtonBox()
        btn_save = btn_box.addButton("💾 Simpan", QDialogButtonBox.AcceptRole)
        btn_save.setObjectName("btn_primary")
        btn_cancel = btn_box.addButton("Batal", QDialogButtonBox.RejectRole)
        btn_cancel.setObjectName("btn_secondary")
        btn_box.accepted.connect(self._validate)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _fill(self, u):
        self.inp_username.setText(u['username'])
        self.inp_fullname.setText(u['full_name'])
        idx = self.cmb_role.findText(u['role'])
        if idx >= 0:
            self.cmb_role.setCurrentIndex(idx)

    def _validate(self):
        errors = []
        if not self.inp_username.text().strip():
            errors.append("Username wajib diisi.")
        if not self.inp_fullname.text().strip():
            errors.append("Nama lengkap wajib diisi.")
        if not self.user and not self.inp_password.text():
            errors.append("Password wajib diisi untuk pengguna baru.")
        if errors:
            QMessageBox.warning(self, "Validasi Gagal", "\n".join(errors))
            return
        self.accept()

    def get_values(self):
        return (
            self.inp_username.text().strip(),
            self.inp_fullname.text().strip(),
            self.cmb_role.currentText(),
            self.inp_password.text() or None,
        )


class UserPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self._build_ui()
        self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        info = QLabel("⚙️  Manajemen pengguna hanya dapat diakses oleh Admin.")
        info.setStyleSheet(
            "background-color: #FFF3CD; color: #856404; padding: 10px 14px; "
            "border-radius: 6px; font-size: 13px;"
        )
        lay.addWidget(info)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Tambah Pengguna")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._add_user)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        lay.addLayout(toolbar)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["ID", "Username", "Nama Lengkap", "Role", "Aksi"])
        self.tbl.setColumnHidden(0, True)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.verticalHeader().setDefaultSectionSize(45)
        lay.addWidget(self.tbl)

    def _load(self):
        users = get_all_users()
        self.tbl.setRowCount(0)
        for i, u in enumerate(users):
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(str(u['id'])))
            self.tbl.setItem(i, 1, QTableWidgetItem(u['username']))
            self.tbl.setItem(i, 2, QTableWidgetItem(u['full_name']))

            role_item = QTableWidgetItem(u['role'].upper())
            role_item.setTextAlignment(Qt.AlignCenter)
            self.tbl.setItem(i, 3, role_item)

            action_w = QWidget()
            ah = QHBoxLayout(action_w)
            ah.setContentsMargins(4, 2, 4, 2)
            ah.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setObjectName("btn_warning")
            btn_edit.setFixedSize(32, 28)
            btn_edit.setStyleSheet("padding: 0px; border-radius: 3px;")
            btn_edit.clicked.connect(lambda _, uid=u['id']: self._edit_user(uid))

            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedSize(32, 28)
            btn_del.setStyleSheet("padding: 0px; border-radius: 3px;")
            # Prevent deleting self
            btn_del.setEnabled(u['id'] != self.current_user['id'])
            btn_del.clicked.connect(lambda _, uid=u['id'], uname=u['username']: self._delete_user(uid, uname))

            ah.addWidget(btn_edit)
            ah.addWidget(btn_del)
            self.tbl.setCellWidget(i, 4, action_w)

    def _add_user(self):
        dlg = UserDialog(self)
        if dlg.exec() == QDialog.Accepted:
            username, full_name, role, password = dlg.get_values()
            try:
                insert_user(username, password, full_name, role)
                self._load()
                QMessageBox.information(self, "Berhasil", "Pengguna berhasil ditambahkan.")
            except Exception as e:
                if "UNIQUE" in str(e):
                    QMessageBox.warning(self, "Username Duplikat", "Username sudah digunakan.")
                else:
                    QMessageBox.critical(self, "Error", str(e))

    def _edit_user(self, user_id):
        users = {u['id']: u for u in get_all_users()}
        u = users.get(user_id)
        if not u:
            return
        dlg = UserDialog(self, dict(u))
        if dlg.exec() == QDialog.Accepted:
            username, full_name, role, password = dlg.get_values()
            try:
                update_user(user_id, username, full_name, role, password)
                self._load()
                QMessageBox.information(self, "Berhasil", "Data pengguna diperbarui.")
            except Exception as e:
                if "UNIQUE" in str(e):
                    QMessageBox.warning(self, "Username Duplikat", "Username sudah digunakan.")
                else:
                    QMessageBox.critical(self, "Error", str(e))

    def _delete_user(self, user_id, username):
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Hapus pengguna \"{username}\"?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_user(user_id)
            self._load()
