from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QDialog, QDialogButtonBox, QSpinBox,
    QDoubleSpinBox, QTextEdit, QHeaderView, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from database.db import (
    get_all_products, insert_product, update_product,
    delete_product, get_categories
)

CATEGORIES = ["Kaos", "Kemeja", "Jaket", "Celana", "Dress", "Aksesoris", "Lainnya"]


def fmt_rp(v):
    return f"Rp {v:,.0f}".replace(',', '.')


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Edit Produk" if product else "Tambah Produk")
        self.setFixedSize(440, 480)
        self._build()
        if product:
            self._fill(product)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 16)
        lay.setSpacing(10)

        title = QLabel("✏️ Edit Produk" if self.product else "➕ Tambah Produk Baru")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2D25;")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        def lbl(text):
            l = QLabel(text)
            l.setObjectName("form_label")
            return l

        self.inp_code = QLineEdit(); self.inp_code.setPlaceholderText("KAO-001")
        self.inp_name = QLineEdit(); self.inp_name.setPlaceholderText("Nama produk")
        self.cmb_cat = QComboBox()
        for c in CATEGORIES:
            self.cmb_cat.addItem(c)
        self.inp_price = QDoubleSpinBox()
        self.inp_price.setRange(0, 9999999); self.inp_price.setPrefix("Rp "); self.inp_price.setSingleStep(1000)
        self.inp_stock = QSpinBox()
        self.inp_stock.setRange(0, 9999)
        self.inp_desc = QTextEdit(); self.inp_desc.setFixedHeight(70)
        self.inp_desc.setPlaceholderText("Deskripsi singkat (opsional)")

        grid.addWidget(lbl("Kode Produk *"), 0, 0); grid.addWidget(self.inp_code, 0, 1)
        grid.addWidget(lbl("Nama Produk *"), 1, 0); grid.addWidget(self.inp_name, 1, 1)
        grid.addWidget(lbl("Kategori *"), 2, 0); grid.addWidget(self.cmb_cat, 2, 1)
        grid.addWidget(lbl("Harga (Rp) *"), 3, 0); grid.addWidget(self.inp_price, 3, 1)
        grid.addWidget(lbl("Stok *"), 4, 0); grid.addWidget(self.inp_stock, 4, 1)
        grid.addWidget(lbl("Deskripsi"), 5, 0); grid.addWidget(self.inp_desc, 5, 1)

        lay.addLayout(grid)
        lay.addStretch()

        btn_box = QDialogButtonBox()
        self.btn_save = btn_box.addButton("💾 Simpan", QDialogButtonBox.AcceptRole)
        self.btn_save.setObjectName("btn_primary")
        btn_cancel = btn_box.addButton("Batal", QDialogButtonBox.RejectRole)
        btn_cancel.setObjectName("btn_secondary")
        btn_box.accepted.connect(self._validate)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _fill(self, p):
        self.inp_code.setText(p['code'])
        self.inp_name.setText(p['name'])
        idx = self.cmb_cat.findText(p['category'])
        if idx >= 0:
            self.cmb_cat.setCurrentIndex(idx)
        self.inp_price.setValue(p['price'])
        self.inp_stock.setValue(p['stock'])
        self.inp_desc.setPlainText(p['description'] or '')

    def _validate(self):
        errors = []
        if not self.inp_code.text().strip():
            errors.append("Kode produk wajib diisi.")
        if not self.inp_name.text().strip():
            errors.append("Nama produk wajib diisi.")
        if self.inp_price.value() <= 0:
            errors.append("Harga harus lebih dari 0.")
        if errors:
            QMessageBox.warning(self, "Validasi Gagal", "\n".join(errors))
            return
        self.accept()

    def get_values(self):
        return (
            self.inp_code.text().strip(),
            self.inp_name.text().strip(),
            self.cmb_cat.currentText(),
            self.inp_price.value(),
            self.inp_stock.value(),
            self.inp_desc.toPlainText().strip(),
        )


class ProductPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.all_products = []
        self._build_ui()
        self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # Toolbar
        toolbar = QHBoxLayout()

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 Cari kode / nama produk...")
        self.inp_search.textChanged.connect(self._filter)
        self.inp_search.setFixedWidth(260)

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("Semua Kategori")
        for c in CATEGORIES:
            self.cmb_cat.addItem(c)
        self.cmb_cat.currentTextChanged.connect(self._filter)

        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["Nama ↑", "Nama ↓", "Harga ↑", "Harga ↓", "Stok ↑", "Stok ↓"])
        self.cmb_sort.currentTextChanged.connect(self._filter)

        btn_add = QPushButton("➕ Tambah Produk")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._add_product)

        btn_export = QPushButton("📥 Export CSV")
        btn_export.setObjectName("btn_outline")
        btn_export.clicked.connect(self._export_csv)

        toolbar.addWidget(self.inp_search)
        toolbar.addWidget(self.cmb_cat)
        toolbar.addWidget(self.cmb_sort)
        toolbar.addStretch()
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_add)
        lay.addLayout(toolbar)

        # Table
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels(["ID", "Kode", "Nama Produk", "Kategori", "Harga", "Stok", "Aksi"])
        self.tbl.setColumnHidden(0, True)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().sectionClicked.connect(self._sort_by_header)
        lay.addWidget(self.tbl)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #6C757D; font-size: 12px;")
        lay.addWidget(self.status_lbl)

    def _load(self):
        sort_map = {
            "Nama ↑": ("name", "ASC"),
            "Nama ↓": ("name", "DESC"),
            "Harga ↑": ("price", "ASC"),
            "Harga ↓": ("price", "DESC"),
            "Stok ↑": ("stock", "ASC"),
            "Stok ↓": ("stock", "DESC"),
        }
        sort_text = self.cmb_sort.currentText()
        col, order = sort_map.get(sort_text, ("name", "ASC"))

        search = self.inp_search.text().strip()
        cat = self.cmb_cat.currentText()
        if cat == "Semua Kategori":
            cat = ""
        self.all_products = list(get_all_products(search=search, category=cat,
                                                   sort_col=col, sort_order=order))
        self._render(self.all_products)

    def _filter(self):
        self._load()

    def _sort_by_header(self, col_idx):
        pass  # handled by combobox; header click can be extended

    def _render(self, products):
        self.tbl.setRowCount(0)
        for i, p in enumerate(products):
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(str(p['id'])))
            self.tbl.setItem(i, 1, QTableWidgetItem(p['code']))
            self.tbl.setItem(i, 2, QTableWidgetItem(p['name']))
            self.tbl.setItem(i, 3, QTableWidgetItem(p['category']))
            self.tbl.setItem(i, 4, QTableWidgetItem(fmt_rp(p['price'])))

            stk = QTableWidgetItem(str(p['stock']))
            stk.setTextAlignment(Qt.AlignCenter)
            if p['stock'] == 0:
                stk.setForeground(QColor("#E63946"))
                stk.setBackground(QColor("#F8D7DA"))
            elif p['stock'] <= 3:
                stk.setForeground(QColor("#856404"))
                stk.setBackground(QColor("#FFF3CD"))
            self.tbl.setItem(i, 5, stk)

            # Action buttons
            action_w = QWidget()
            ah = QHBoxLayout(action_w)
            ah.setContentsMargins(4, 2, 4, 2)
            ah.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setObjectName("btn_warning")
            btn_edit.setFixedSize(25, 25)
            btn_edit.setToolTip("Edit")
            btn_edit.setStyleSheet("padding: 0px; border-radius: 3px;")
            btn_edit.clicked.connect(lambda _, pid=p['id']: self._edit_product(pid))

            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedSize(25, 25)
            btn_del.setToolTip("Hapus")
            btn_del.setStyleSheet("padding: 0px; border-radius: 3px;")
            btn_del.clicked.connect(lambda _, pid=p['id'], pname=p['name']: self._delete_product(pid, pname))

            ah.addWidget(btn_edit)
            ah.addWidget(btn_del)
            self.tbl.setCellWidget(i, 6, action_w)

        self.tbl.resizeRowsToContents()
        self.status_lbl.setText(f"Menampilkan {len(products)} produk")

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.Accepted:
            try:
                insert_product(*dlg.get_values())
                self._load()
                QMessageBox.information(self, "Berhasil", "Produk berhasil ditambahkan.")
            except Exception as e:
                if "UNIQUE" in str(e):
                    QMessageBox.warning(self, "Kode Duplikat", "Kode produk sudah digunakan.")
                else:
                    QMessageBox.critical(self, "Error", str(e))

    def _edit_product(self, product_id):
        from database.db import get_product_by_id
        p = get_product_by_id(product_id)
        if not p:
            return
        dlg = ProductDialog(self, dict(p))
        if dlg.exec() == QDialog.Accepted:
            try:
                update_product(product_id, *dlg.get_values())
                self._load()
                QMessageBox.information(self, "Berhasil", "Produk berhasil diperbarui.")
            except Exception as e:
                if "UNIQUE" in str(e):
                    QMessageBox.warning(self, "Kode Duplikat", "Kode produk sudah digunakan.")
                else:
                    QMessageBox.critical(self, "Error", str(e))

    def _delete_product(self, product_id, name):
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Yakin ingin menghapus produk:\n\"{name}\"?\n\nData tidak bisa dikembalikan.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_product(product_id)
            self._load()

    def _export_csv(self):
        from utils.export import export_products_csv
        import os
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "produk_thriftcash.csv", "CSV (*.csv)")
        if path:
            export_products_csv(self.all_products, path)
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{path}")
