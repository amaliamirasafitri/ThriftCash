# ThriftCash

**Sistem Kasir Desktop untuk Toko Pakaian Bekas (Thrift Shop) Berbasis PySide6**

> Final Project — Pemrograman Visual | Semester Genap 2025/2026

---

## Deskripsi

ThriftCash adalah aplikasi kasir desktop yang dirancang khusus untuk operasional toko pakaian bekas (*thrift shop*). Aplikasi ini menyediakan antarmuka yang intuitif bagi kasir untuk mengelola produk, memproses transaksi penjualan, serta melihat laporan pendapatan secara real-time.

---

## Anggota Kelompok

| Nama | NIM | Tanggung Jawab |
|------|-----|----------------|
| [Nama 1] | [NIM 1] | Login, Dashboard, Manajemen Pengguna |
| [Nama 2] | [NIM 2] | Halaman POS / Kasir, Database |
| [Nama 3] | [NIM 3] | Manajemen Produk, Laporan, Export |

---

## Fitur Utama

- **🔐 Login & Manajemen Sesi** — Autentikasi pengguna dengan role admin/kasir
- **🏠 Dashboard** — Statistik hari ini, grafik pendapatan 7 hari, distribusi kategori
- **🧾 Kasir / POS** — Tambah produk ke keranjang, diskon, hitung kembalian otomatis
- **👕 Manajemen Produk** — CRUD produk dengan search, filter, dan sorting
- **📊 Laporan Transaksi** — Riwayat transaksi, filter tanggal, detail per invoice
- **📥 Export Data** — CSV & PDF untuk produk dan laporan transaksi
- **👤 Manajemen Pengguna** — CRUD pengguna (khusus admin)

---

## Struktur Database (SQLite)

```
users             — Data pengguna sistem
products          — Katalog produk thrift shop  
transactions      — Header transaksi penjualan
transaction_items — Detail item per transaksi
```

---

## Cara Menjalankan

### 1. Clone repository
```bash
git clone https://github.com/[username]/pv26-finalproject-thriftcash.git
cd pv26-finalproject-thriftcash
```

### 2. Install dependensi
```bash
pip install -r requirements.txt
```

### 3. Jalankan aplikasi
```bash
python main.py
```

### 4. Login default
- **Username:** `admin`
- **Password:** `admin123`

---

## Struktur Folder

```
thriftcash/
├── main.py              # Entry point
├── requirements.txt
├── README.md
├── assets/
│   └── style.qss        # Stylesheet global
├── database/
│   └── db.py            # Inisialisasi & query SQLite
├── ui/
│   ├── login_window.py
│   ├── main_window.py
│   ├── dashboard_page.py
│   ├── pos_page.py
│   ├── product_page.py
│   ├── report_page.py
│   └── user_page.py
└── utils/
    └── export.py        # Export CSV & PDF
```

---

## Screenshot

*(Tambahkan screenshot di sini setelah aplikasi berjalan)*

---

## Teknologi

- **Python 3.10+**
- **PySide6** — GUI framework
- **SQLite** — Database lokal
- **ReportLab** — Export PDF
