from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QVBoxLayout as VL, QHeaderView, QMessageBox, QDateEdit,
    QFrame, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from database.db import get_transactions, get_transaction_items


def fmt_rp(v):
    return f"Rp {v:,.0f}".replace(',', '.')


class TransactionDetailDialog(QDialog):
    def __init__(self, transaction, parent=None):
        super().__init__(parent)
        self.transaction = transaction
        self.setWindowTitle(f"Detail Transaksi — {transaction['invoice_no']}")
        self.setMinimumSize(560, 480)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(12)

        header = QLabel(f"🧾 {self.transaction['invoice_no']}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D6A4F;")
        lay.addWidget(header)

        info = (
            f"Kasir: {self.transaction['cashier_name']}    "
            f"Tanggal: {self.transaction['created_at'][:16]}"
        )
        lay.addWidget(QLabel(info))

        tbl = QTableWidget()
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels(["Nama Produk", "Kategori", "Harga", "Qty", "Subtotal"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.NoSelection)

        items = get_transaction_items(self.transaction['id'])
        for i, it in enumerate(items):
            tbl.insertRow(i)
            tbl.setItem(i, 0, QTableWidgetItem(it['product_name']))
            tbl.setItem(i, 1, QTableWidgetItem(it['category']))
            tbl.setItem(i, 2, QTableWidgetItem(fmt_rp(it['price'])))
            q = QTableWidgetItem(str(it['quantity']))
            q.setTextAlignment(Qt.AlignCenter)
            tbl.setItem(i, 3, q)
            tbl.setItem(i, 4, QTableWidgetItem(fmt_rp(it['subtotal'])))
        lay.addWidget(tbl)

        # Summary
        sep = QFrame(frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        lay.addWidget(sep)

        def row(label, value, bold=False):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            l = QLabel(label)
            v = QLabel(value)
            if bold:
                v.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D6A4F;")
            h.addWidget(l)
            h.addWidget(v, alignment=Qt.AlignRight)
            return w

        lay.addWidget(row("Subtotal:", fmt_rp(self.transaction['total_amount'])))
        lay.addWidget(row("Diskon:", fmt_rp(self.transaction['discount_amount'])))
        lay.addWidget(row("Total Akhir:", fmt_rp(self.transaction['final_amount']), bold=True))
        lay.addWidget(row("Bayar:", fmt_rp(self.transaction['paid_amount'])))
        lay.addWidget(row("Kembalian:", fmt_rp(self.transaction['change_amount'])))

        btn_close = QPushButton("Tutup")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        lay.addWidget(btn_close, alignment=Qt.AlignRight)


class ReportPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.transactions = []
        self._build_ui()
        self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # Filter bar
        filter_row = QHBoxLayout()

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 Cari invoice / kasir...")
        self.inp_search.textChanged.connect(self._load)
        self.inp_search.setFixedWidth(220)

        lbl_from = QLabel("Dari:")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self._load)

        lbl_to = QLabel("Sampai:")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self._load)

        btn_reset = QPushButton("🔄 Reset Filter")
        btn_reset.setObjectName("btn_secondary")
        btn_reset.clicked.connect(self._reset_filter)

        btn_csv = QPushButton("📄 Export CSV")
        btn_csv.setObjectName("btn_outline")
        btn_csv.clicked.connect(self._export_csv)

        btn_pdf = QPushButton("🖨️ Export PDF")
        btn_pdf.setObjectName("btn_primary")
        btn_pdf.clicked.connect(self._export_pdf)

        filter_row.addWidget(self.inp_search)
        filter_row.addWidget(lbl_from)
        filter_row.addWidget(self.date_from)
        filter_row.addWidget(lbl_to)
        filter_row.addWidget(self.date_to)
        filter_row.addWidget(btn_reset)
        filter_row.addStretch()
        filter_row.addWidget(btn_csv)
        filter_row.addWidget(btn_pdf)
        lay.addLayout(filter_row)

        # Summary strip
        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet(
            "background-color: #D8EFE3; color: #1B5E3A; border-radius: 6px; "
            "padding: 8px 14px; font-weight: bold; font-size: 13px;"
        )
        lay.addWidget(self.summary_lbl)

        # Table
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(8)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Invoice", "Kasir", "Total", "Diskon",
            "Total Akhir", "Kembalian", "Tanggal"
        ])
        self.tbl.setColumnHidden(0, True)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.doubleClicked.connect(self._show_detail)
        lay.addWidget(self.tbl)

        hint = QLabel("💡 Double-klik baris untuk melihat detail transaksi")
        hint.setStyleSheet("color: #ADB5BD; font-size: 11px;")
        lay.addWidget(hint)

    def _load(self):
        search = self.inp_search.text().strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        self.transactions = list(get_transactions(search=search, date_from=date_from, date_to=date_to))
        self._render()

    def _reset_filter(self):
        self.inp_search.clear()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self._load()

    def _render(self):
        self.tbl.setRowCount(0)
        total_rev = 0
        for i, t in enumerate(self.transactions):
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(str(t['id'])))
            self.tbl.setItem(i, 1, QTableWidgetItem(t['invoice_no']))
            self.tbl.setItem(i, 2, QTableWidgetItem(t['cashier_name']))
            self.tbl.setItem(i, 3, QTableWidgetItem(fmt_rp(t['total_amount'])))
            self.tbl.setItem(i, 4, QTableWidgetItem(fmt_rp(t['discount_amount'])))
            final_item = QTableWidgetItem(fmt_rp(t['final_amount']))
            final_item.setForeground(QColor("#2D6A4F"))
            self.tbl.setItem(i, 5, final_item)
            self.tbl.setItem(i, 6, QTableWidgetItem(fmt_rp(t['change_amount'])))
            self.tbl.setItem(i, 7, QTableWidgetItem(t['created_at'][:16]))
            total_rev += t['final_amount']

        count = len(self.transactions)
        self.summary_lbl.setText(
            f"📊  {count} transaksi ditemukan   |   "
            f"Total Pendapatan: {fmt_rp(total_rev)}"
        )

    def _show_detail(self):
        row = self.tbl.currentRow()
        if row < 0:
            return
        t = self.transactions[row]
        dlg = TransactionDetailDialog(dict(t), self)
        dlg.exec()

    def _export_csv(self):
        from utils.export import export_transactions_csv
        from PySide6.QtWidgets import QFileDialog
        if not self.transactions:
            QMessageBox.warning(self, "Kosong", "Tidak ada data untuk diekspor.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "laporan_transaksi.csv", "CSV (*.csv)")
        if path:
            export_transactions_csv(self.transactions, path)
            QMessageBox.information(self, "Berhasil", f"CSV disimpan di:\n{path}")

    def _export_pdf(self):
        from utils.export import export_transactions_pdf_reportlab
        from PySide6.QtWidgets import QFileDialog
        if not self.transactions:
            QMessageBox.warning(self, "Kosong", "Tidak ada data untuk diekspor.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Simpan PDF", "laporan_transaksi.pdf", "PDF (*.pdf)")
        if path:
            result = export_transactions_pdf_reportlab(self.transactions, path)
            if result:
                QMessageBox.information(self, "Berhasil", f"PDF disimpan di:\n{path}")
            else:
                QMessageBox.warning(self, "ReportLab Tidak Tersedia",
                                    "Install 'reportlab' untuk export PDF:\n\npip install reportlab")
