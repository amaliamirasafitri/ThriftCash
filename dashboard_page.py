from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis,
    QValueAxis, QPieSeries, QLineSeries
)
from database.db import get_dashboard_stats
from datetime import datetime, timedelta


def format_rupiah(v):
    return f"Rp {v:,.0f}".replace(',', '.')


class StatCard(QFrame):
    def __init__(self, icon, label, value, color="#2D6A4F"):
        super().__init__()
        self.setObjectName("stat_card")
        self.setMinimumWidth(160)
        lay = QVBoxLayout(self)
        lay.setSpacing(4)

        row = QHBoxLayout()
        ico = QLabel(icon)
        ico.setStyleSheet(f"font-size: 28px;")
        row.addWidget(ico)
        row.addStretch()

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setObjectName("stat_value")
        self.val_lbl.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")

        lbl = QLabel(label)
        lbl.setObjectName("stat_label")
        lbl.setWordWrap(True)

        lay.addLayout(row)
        lay.addWidget(self.val_lbl)
        lay.addWidget(lbl)

    def update_value(self, v):
        self.val_lbl.setText(str(v))


class BarChartWidget(QChartView):
    def __init__(self, title):
        super().__init__()
        self.chart_obj = QChart()
        self.chart_obj.setTitle(title)
        self.chart_obj.setAnimationOptions(QChart.SeriesAnimations)
        self.chart_obj.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.chart_obj.setTitleFont(QFont("Arial", 12, QFont.Bold))
        self.chart_obj.setTitleBrush(QBrush(QColor("#1B2D25")))
        self.setChart(self.chart_obj)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(260)

    def load_data(self, weekly):
        self.chart_obj.removeAllSeries()
        bar_set = QBarSet("Pendapatan")
        bar_set.setColor(QColor("#52B788"))
        labels = []

        # fill 7 days
        today = datetime.now().date()
        day_map = {r['day']: r['revenue'] for r in weekly}
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            ds = d.strftime('%Y-%m-%d')
            bar_set.append(day_map.get(ds, 0))
            labels.append(d.strftime('%d/%m'))

        series = QBarSeries()
        series.append(bar_set)
        self.chart_obj.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        self.chart_obj.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("Rp %.0f")
        self.chart_obj.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        self.chart_obj.legend().setVisible(False)


class PieChartWidget(QChartView):
    def __init__(self, title):
        super().__init__()
        self.chart_obj = QChart()
        self.chart_obj.setTitle(title)
        self.chart_obj.setAnimationOptions(QChart.SeriesAnimations)
        self.chart_obj.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.chart_obj.setTitleFont(QFont("Arial", 12, QFont.Bold))
        self.chart_obj.setTitleBrush(QBrush(QColor("#1B2D25")))
        self.setChart(self.chart_obj)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(260)

    def load_data(self, by_category):
        self.chart_obj.removeAllSeries()
        if not by_category:
            return
        series = QPieSeries()
        colors = ["#52B788", "#2D6A4F", "#74A68A", "#F4A261", "#E63946", "#4A90D9"]
        for i, row in enumerate(by_category):
            slc = series.append(row['category'], row['sold'])
            slc.setColor(QColor(colors[i % len(colors)]))
            slc.setLabel(f"{row['category']} ({row['sold']})")
        series.setLabelsVisible(True)
        self.chart_obj.addSeries(series)
        self.chart_obj.legend().setVisible(True)
        self.chart_obj.legend().setAlignment(Qt.AlignBottom)


class DashboardPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()
        self._refresh()
        # Auto-refresh every 30s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(30000)

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        # Welcome
        greet = QLabel(f"Selamat datang, {self.user['full_name']}! 👋")
        greet.setStyleSheet("font-size: 20px; font-weight: bold; color: #1B2D25;")
        time_lbl = QLabel(datetime.now().strftime("📅 %A, %d %B %Y"))
        time_lbl.setStyleSheet("color: #6C757D; font-size: 13px;")
        lay.addWidget(greet)
        lay.addWidget(time_lbl)

        # Stat cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)

        self.card_trans = StatCard("🧾", "Transaksi Hari Ini", "0")
        self.card_revenue = StatCard("💰", "Pendapatan Hari Ini", "Rp 0", "#2D6A4F")
        self.card_products = StatCard("👕", "Total Produk", "0", "#4A90D9")
        self.card_lowstock = StatCard("⚠️", "Stok Hampir Habis", "0", "#E63946")

        cards_layout.addWidget(self.card_trans, 0, 0)
        cards_layout.addWidget(self.card_revenue, 0, 1)
        cards_layout.addWidget(self.card_products, 0, 2)
        cards_layout.addWidget(self.card_lowstock, 0, 3)
        lay.addLayout(cards_layout)

        # Charts row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        self.bar_chart = BarChartWidget("Pendapatan 7 Hari Terakhir")
        self.pie_chart = PieChartWidget("Penjualan per Kategori")

        charts_row.addWidget(self.bar_chart, 3)
        charts_row.addWidget(self.pie_chart, 2)
        lay.addLayout(charts_row)

        scroll.setWidget(container)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(scroll)

    def _refresh(self):
        stats = get_dashboard_stats()
        self.card_trans.update_value(stats['today_count'])
        self.card_revenue.update_value(format_rupiah(stats['today_revenue']))
        self.card_products.update_value(stats['total_products'])
        self.card_lowstock.update_value(stats['low_stock'])
        self.bar_chart.load_data(stats['weekly'])
        self.pie_chart.load_data(stats['by_category'])
