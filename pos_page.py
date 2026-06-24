from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QSpinBox, QDoubleSpinBox, QMessageBox, QFrame, QHeaderView,
    QDialog, QDialogButtonBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from database.db import get_all_products, save_transaction, get_categories
from datetime import datetime


def fmt_rp(v):
    return f"Rp {v:,.0f}".replace(',', '.')


class PaymentDialog(QDialog):
    def __init__(self, final_amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proses Pembayaran")
        self.setFixedSize(380, 280)
        self.final_amount = final_amount
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        header = QLabel("💳 Proses Pembayaran")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2D25;")
        lay.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Total Tagihan:"), 0, 0)
        total_lbl = QLabel(fmt_rp(self.final_amount))
        total_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #2D6A4F;")
        grid.addWidget(total_lbl, 0, 1)

        grid.addWidget(QLabel("Uang Diterima:"), 1, 0)
        self.inp_paid = QDoubleSpinBox()
        self.inp_paid.setRange(0, 99999999)
        self.inp_paid.setSingleStep(1000)
        self.inp_paid.setValue(self.final_amount)
        self.inp_paid.setPrefix("Rp ")
        self.inp_paid.setGroupSeparatorShown(True)
        self.inp_paid.valueChanged.connect(self._update_change)
        grid.addWidget(self.inp_paid, 1, 1)

        grid.addWidget(QLabel("Kembalian:"), 2, 0)
        self.change_lbl = QLabel(fmt_rp(0))
        self.change_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #E63946;")
        grid.addWidget(self.change_lbl, 2, 1)

        lay.addLayout(grid)
        lay.addStretch()

        btn_box = QDialogButtonBox()
        self.btn_ok = btn_box.addButton("✅ Bayar Sekarang", QDialogButtonBox.AcceptRole)
        self.btn_ok.setObjectName("btn_primary")
        btn_cancel = btn_box.addButton("Batal", QDialogButtonBox.RejectRole)
        btn_cancel.setObjectName("btn_secondary")
        btn_box.accepted.connect(self._confirm)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)
        self._update_change(self.final_amount)

    def _update_change(self, paid):
        change = max(0, paid - self.final_amount)
        self.change_lbl.setText(fmt_rp(change))
        self.change_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {'#52B788' if change >= 0 else '#E63946'};"
        )

    def _confirm(self):
        paid = self.inp_paid.value()
        if paid < self.final_amount:
            QMessageBox.warning(self, "Kurang Bayar",
                                f"Uang diterima kurang dari total tagihan.\n"
                                f"Kekurangan: {fmt_rp(self.final_amount - paid)}")
            return
        self.accept()

    def get_values(self):
        paid = self.inp_paid.value()
        return paid, max(0, paid - self.final_amount)


class POSPage(QWidget):
    transaction_done = Signal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.cart = []
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ── LEFT: Product selection + Cart ───────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        # Search + Filter bar
        search_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 Cari produk...")
        self.inp_search.textChanged.connect(self._load_products)

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("Semua Kategori")
        for cat in get_categories():
            self.cmb_cat.addItem(cat)
        self.cmb_cat.currentTextChanged.connect(self._load_products)
        self.cmb_cat.setFixedWidth(160)

        search_row.addWidget(self.inp_search)
        search_row.addWidget(self.cmb_cat)
        left.addLayout(search_row)

        # Product table
        prod_lbl = QLabel("📦 Pilih Produk")
        prod_lbl.setObjectName("section_title")
        left.addWidget(prod_lbl)

        self.tbl_products = QTableWidget()
        self.tbl_products.setColumnCount(5)
        self.tbl_products.setHorizontalHeaderLabels(["Kode", "Nama Produk", "Kategori", "Harga", "Stok"])
        self.tbl_products.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_products.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_products.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_products.doubleClicked.connect(self._add_from_double_click)
        self.tbl_products.setMinimumHeight(220)
        left.addWidget(self.tbl_products)

        # Add to cart controls
        add_row = QHBoxLayout()
        qty_lbl = QLabel("Qty:")
        self.inp_qty = QSpinBox()
        self.inp_qty.setRange(1, 999)
        self.inp_qty.setFixedWidth(80)

        btn_add = QPushButton("➕ Tambah ke Keranjang")
        btn_add.setObjectName("btn_success")
        btn_add.clicked.connect(self._add_to_cart)

        add_row.addWidget(qty_lbl)
        add_row.addWidget(self.inp_qty)
        add_row.addWidget(btn_add)
        add_row.addStretch()
        left.addLayout(add_row)

        # Cart
        cart_lbl = QLabel("🛒 Keranjang Belanja")
        cart_lbl.setObjectName("section_title")
        left.addWidget(cart_lbl)

        self.tbl_cart = QTableWidget()
        self.tbl_cart.setColumnCount(6)
        self.tbl_cart.setHorizontalHeaderLabels(["Kode", "Nama", "Kategori", "Harga", "Qty", "Subtotal"])
        self.tbl_cart.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_cart.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_cart.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_cart.setMinimumHeight(160)
        left.addWidget(self.tbl_cart)

        btn_remove = QPushButton("🗑️ Hapus Item Dipilih")
        btn_remove.setObjectName("btn_danger")
        btn_remove.clicked.connect(self._remove_cart_item)
        left.addWidget(btn_remove, alignment=Qt.AlignLeft)

        root.addLayout(left, stretch=3)

        # ── RIGHT: Summary + Payment ──────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        summary = QFrame()
        summary.setObjectName("pos_cart")
        sv = QVBoxLayout(summary)
        sv.setContentsMargins(16, 16, 16, 16)
        sv.setSpacing(12)

        inv_lbl = QLabel("📋 Ringkasan Transaksi")
        inv_lbl.setObjectName("section_title")
        sv.addWidget(inv_lbl)

        self.inv_no_lbl = QLabel("Invoice: —")
        self.inv_no_lbl.setStyleSheet("color: #6C757D; font-size: 12px;")
        sv.addWidget(self.inv_no_lbl)

        # Cashier
        sv.addWidget(self._row("Kasir:", self.user['full_name']))

        # Discount
        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("Diskon (Rp):"))
        self.inp_discount = QDoubleSpinBox()
        self.inp_discount.setRange(0, 9999999)
        self.inp_discount.setSingleStep(1000)
        self.inp_discount.valueChanged.connect(self._recalc)
        disc_row.addWidget(self.inp_discount)
        sv.addLayout(disc_row)

        sv.addWidget(QFrame(frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))

        self.lbl_subtotal = self._summary_row(sv, "Subtotal:", "Rp 0")
        self.lbl_discount = self._summary_row(sv, "Diskon:", "Rp 0")

        total_box = QFrame()
        total_box.setObjectName("pos_total_box")
        tbv = QVBoxLayout(total_box)
        tbv.setContentsMargins(12, 12, 12, 12)

        t1 = QLabel("TOTAL BAYAR")
        t1.setObjectName("pos_total_label")
        self.lbl_total = QLabel("Rp 0")
        self.lbl_total.setObjectName("pos_total_value")

        tbv.addWidget(t1)
        tbv.addWidget(self.lbl_total)
        sv.addWidget(total_box)

        sv.addStretch()

        btn_pay = QPushButton("💳 Proses Pembayaran")
        btn_pay.setObjectName("btn_primary")
        btn_pay.setFixedHeight(46)
        btn_pay.setFont(QFont("Arial", 13, QFont.Bold))
        btn_pay.clicked.connect(self._process_payment)

        btn_reset = QPushButton("🔄 Reset Transaksi")
        btn_reset.setObjectName("btn_secondary")
        btn_reset.clicked.connect(self._reset)

        sv.addWidget(btn_pay)
        sv.addWidget(btn_reset)

        right.addWidget(summary)
        root.addLayout(right, stretch=1)

    def _row(self, label, value):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel(label))
        v = QLabel(value)
        v.setStyleSheet("font-weight: bold;")
        h.addWidget(v, alignment=Qt.AlignRight)
        return w

    def _summary_row(self, parent_layout, label, value):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel(label))
        lbl = QLabel(value)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D6A4F;")
        h.addWidget(lbl, alignment=Qt.AlignRight)
        parent_layout.addWidget(w)
        return lbl

    def _load_products(self):
        search = self.inp_search.text().strip()
        cat_text = self.cmb_cat.currentText()
        cat = "" if cat_text == "Semua Kategori" else cat_text
        rows = get_all_products(search=search, category=cat)

        self.tbl_products.setRowCount(0)
        self.products_data = list(rows)
        for i, p in enumerate(self.products_data):
            self.tbl_products.insertRow(i)
            self.tbl_products.setItem(i, 0, QTableWidgetItem(p['code']))
            self.tbl_products.setItem(i, 1, QTableWidgetItem(p['name']))
            self.tbl_products.setItem(i, 2, QTableWidgetItem(p['category']))
            self.tbl_products.setItem(i, 3, QTableWidgetItem(fmt_rp(p['price'])))
            stk_item = QTableWidgetItem(str(p['stock']))
            stk_item.setTextAlignment(Qt.AlignCenter)
            if p['stock'] <= 3:
                stk_item.setForeground(QColor("#E63946"))
            self.tbl_products.setItem(i, 4, stk_item)

    def _add_from_double_click(self):
        self._add_to_cart()

    def _add_to_cart(self):
        row = self.tbl_products.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Produk", "Pilih produk dari tabel terlebih dahulu.")
            return
        product = self.products_data[row]
        qty = self.inp_qty.value()

        if product['stock'] <= 0:
            QMessageBox.warning(self, "Stok Habis", f"Stok {product['name']} sudah habis.")
            return

        # Check total qty in cart
        total_in_cart = sum(it['quantity'] for it in self.cart if it['product_id'] == product['id'])
        if total_in_cart + qty > product['stock']:
            QMessageBox.warning(self, "Stok Tidak Cukup",
                                f"Stok tersedia hanya {product['stock']} pcs, sudah ada {total_in_cart} di keranjang.")
            return

        # Find existing
        for it in self.cart:
            if it['product_id'] == product['id']:
                it['quantity'] += qty
                it['subtotal'] = it['price'] * it['quantity']
                self._refresh_cart()
                self._recalc()
                return

        self.cart.append({
            'product_id': product['id'],
            'product_code': product['code'],
            'product_name': product['name'],
            'category': product['category'],
            'price': product['price'],
            'quantity': qty,
            'subtotal': product['price'] * qty,
        })
        self._refresh_cart()
        self._recalc()

    def _refresh_cart(self):
        self.tbl_cart.setRowCount(0)
        for i, it in enumerate(self.cart):
            self.tbl_cart.insertRow(i)
            self.tbl_cart.setItem(i, 0, QTableWidgetItem(it['product_code']))
            self.tbl_cart.setItem(i, 1, QTableWidgetItem(it['product_name']))
            self.tbl_cart.setItem(i, 2, QTableWidgetItem(it['category']))
            self.tbl_cart.setItem(i, 3, QTableWidgetItem(fmt_rp(it['price'])))
            q_item = QTableWidgetItem(str(it['quantity']))
            q_item.setTextAlignment(Qt.AlignCenter)
            self.tbl_cart.setItem(i, 4, q_item)
            self.tbl_cart.setItem(i, 5, QTableWidgetItem(fmt_rp(it['subtotal'])))

    def _remove_cart_item(self):
        row = self.tbl_cart.currentRow()
        if row < 0:
            return
        self.cart.pop(row)
        self._refresh_cart()
        self._recalc()

    def _recalc(self):
        subtotal = sum(it['subtotal'] for it in self.cart)
        disc = self.inp_discount.value()
        total = max(0, subtotal - disc)
        self.lbl_subtotal.setText(fmt_rp(subtotal))
        self.lbl_discount.setText(fmt_rp(disc))
        self.lbl_total.setText(fmt_rp(total))

    def _process_payment(self):
        if not self.cart:
            QMessageBox.warning(self, "Keranjang Kosong",
                                "Tambahkan produk ke keranjang terlebih dahulu.")
            return

        subtotal = sum(it['subtotal'] for it in self.cart)
        disc = self.inp_discount.value()
        final = max(0, subtotal - disc)

        dlg = PaymentDialog(final, self)
        if dlg.exec() == QDialog.Accepted:
            paid, change = dlg.get_values()
            invoice = save_transaction(
                cashier_id=self.user['id'],
                items=self.cart,
                total=subtotal,
                discount=disc,
                final=final,
                paid=paid,
                change=change,
            )
            msg = (
                f"✅ Transaksi Berhasil!\n\n"
                f"Invoice : {invoice}\n"
                f"Total   : {fmt_rp(final)}\n"
                f"Bayar   : {fmt_rp(paid)}\n"
                f"Kembalian: {fmt_rp(change)}"
            )
            QMessageBox.information(self, "Transaksi Selesai", msg)
            self._reset()
            self.transaction_done.emit()

    def _reset(self):
        self.cart.clear()
        self._refresh_cart()
        self.inp_discount.setValue(0)
        self._recalc()
        self.inp_search.clear()
        self._load_products()
