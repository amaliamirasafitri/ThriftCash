import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "thriftcash.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ── USERS ────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'kasir',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── PRODUCTS ─────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── TRANSACTIONS ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no      TEXT    NOT NULL UNIQUE,
            cashier_id      INTEGER NOT NULL REFERENCES users(id),
            total_amount    REAL    NOT NULL DEFAULT 0,
            discount_amount REAL    NOT NULL DEFAULT 0,
            final_amount    REAL    NOT NULL DEFAULT 0,
            paid_amount     REAL    NOT NULL DEFAULT 0,
            change_amount   REAL    NOT NULL DEFAULT 0,
            notes           TEXT,
            status          TEXT    NOT NULL DEFAULT 'completed',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── TRANSACTION ITEMS ────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id  INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
            product_id      INTEGER NOT NULL REFERENCES products(id),
            product_name    TEXT    NOT NULL,
            category        TEXT    NOT NULL,
            price           REAL    NOT NULL,
            quantity        INTEGER NOT NULL,
            subtotal        REAL    NOT NULL
        )
    """)

    # ── SEED DEFAULT ADMIN ───────────────────────────────────────────────────
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, ('admin', hash_password('admin123'), 'Administrator', 'admin'))

    # ── SEED SAMPLE PRODUCTS ─────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) as cnt FROM products")
    if cur.fetchone()['cnt'] == 0:
        sample_products = [
            ('KAO-001', 'Kaos Polos Vintage', 'Kaos',    25000,  15, 'Kondisi bagus'),
            ('KAO-002', 'Kaos Band Rock',     'Kaos',    35000,  8,  'Rare item'),
            ('KMS-001', 'Kemeja Flanel Kotak','Kemeja',  45000,  10, 'Size M-XL'),
            ('KMS-002', 'Kemeja Denim',       'Kemeja',  55000,  6,  'Original Levi\'s'),
            ('JAK-001', 'Jaket Bomber Hitam', 'Jaket',   85000,  5,  'Anti air'),
            ('JAK-002', 'Jaket Jeans',        'Jaket',   75000,  4,  'Vintage wash'),
            ('CLN-001', 'Celana Jeans Slim',  'Celana',  65000,  12, 'Stretch material'),
            ('CLN-002', 'Celana Chino',       'Celana',  50000,  9,  'Berbagai warna'),
            ('DRS-001', 'Dress Floral',       'Dress',   60000,  7,  'Casual wear'),
            ('ACC-001', 'Topi Vintage Cap',   'Aksesoris',20000, 20, 'Adjustable'),
        ]
        cur.executemany("""
            INSERT INTO products (code, name, category, price, stock, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_products)

    conn.commit()
    conn.close()


# ── PRODUCT CRUD ──────────────────────────────────────────────────────────────

def get_all_products(search='', category='', sort_col='name', sort_order='ASC'):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR code LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if category:
        query += " AND category = ?"
        params.append(category)
    allowed_cols = {'name', 'code', 'category', 'price', 'stock', 'created_at'}
    if sort_col not in allowed_cols:
        sort_col = 'name'
    query += f" ORDER BY {sort_col} {sort_order}"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_product_by_id(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row


def insert_product(code, name, category, price, stock, description=''):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (code, name, category, price, stock, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (code, name, category, price, stock, description))
    conn.commit()
    conn.close()


def update_product(product_id, code, name, category, price, stock, description=''):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE products SET code=?, name=?, category=?, price=?, stock=?,
        description=?, updated_at=datetime('now','localtime') WHERE id=?
    """, (code, name, category, price, stock, description, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    cats = [r['category'] for r in cur.fetchall()]
    conn.close()
    return cats


# ── USER CRUD ─────────────────────────────────────────────────────────────────

def authenticate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                (username, hash_password(password)))
    row = cur.fetchone()
    conn.close()
    return row


def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_user(username, password, full_name, role='kasir'):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, password, full_name, role)
        VALUES (?, ?, ?, ?)
    """, (username, hash_password(password), full_name, role))
    conn.commit()
    conn.close()


def update_user(user_id, username, full_name, role, password=None):
    conn = get_connection()
    cur = conn.cursor()
    if password:
        cur.execute("""
            UPDATE users SET username=?, full_name=?, role=?, password=? WHERE id=?
        """, (username, full_name, role, hash_password(password), user_id))
    else:
        cur.execute("""
            UPDATE users SET username=?, full_name=?, role=? WHERE id=?
        """, (username, full_name, role, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# ── TRANSACTION CRUD ──────────────────────────────────────────────────────────

def generate_invoice_no():
    now = datetime.now()
    conn = get_connection()
    cur = conn.cursor()
    prefix = f"TC{now.strftime('%Y%m%d')}"
    cur.execute("SELECT COUNT(*) as cnt FROM transactions WHERE invoice_no LIKE ?",
                (f'{prefix}%',))
    seq = cur.fetchone()['cnt'] + 1
    conn.close()
    return f"{prefix}{seq:04d}"


def save_transaction(cashier_id, items, total, discount, final, paid, change, notes=''):
    conn = get_connection()
    cur = conn.cursor()
    invoice_no = generate_invoice_no()
    cur.execute("""
        INSERT INTO transactions
        (invoice_no, cashier_id, total_amount, discount_amount,
         final_amount, paid_amount, change_amount, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (invoice_no, cashier_id, total, discount, final, paid, change, notes))
    trans_id = cur.lastrowid
    for it in items:
        cur.execute("""
            INSERT INTO transaction_items
            (transaction_id, product_id, product_name, category, price, quantity, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (trans_id, it['product_id'], it['product_name'],
              it['category'], it['price'], it['quantity'], it['subtotal']))
        cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                    (it['quantity'], it['product_id']))
    conn.commit()
    conn.close()
    return invoice_no


def get_transactions(search='', date_from='', date_to=''):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT t.*, u.full_name as cashier_name
        FROM transactions t
        JOIN users u ON t.cashier_id = u.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (t.invoice_no LIKE ? OR u.full_name LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if date_from:
        query += " AND DATE(t.created_at) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND DATE(t.created_at) <= ?"
        params.append(date_to)
    query += " ORDER BY t.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_transaction_items(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transaction_items WHERE transaction_id=?", (transaction_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ── DASHBOARD / ANALYTICS ─────────────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM transactions WHERE DATE(created_at)=DATE('now','localtime')")
    today_count = cur.fetchone()['cnt']

    cur.execute("SELECT COALESCE(SUM(final_amount),0) as total FROM transactions WHERE DATE(created_at)=DATE('now','localtime')")
    today_revenue = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as cnt FROM products WHERE stock <= 3")
    low_stock = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) as cnt FROM products")
    total_products = cur.fetchone()['cnt']

    cur.execute("""
        SELECT DATE(created_at) as day, SUM(final_amount) as revenue, COUNT(*) as count
        FROM transactions
        WHERE created_at >= DATE('now','localtime','-6 days')
        GROUP BY DATE(created_at)
        ORDER BY day
    """)
    weekly = cur.fetchall()

    cur.execute("""
        SELECT p.category, COUNT(ti.id) as sold
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        WHERE DATE(ti.rowid) >= DATE('now','localtime','-30 days')
        GROUP BY p.category
        ORDER BY sold DESC
    """)
    by_category_raw = cur.fetchall()

    cur.execute("""
        SELECT p.category, SUM(ti.quantity) as sold
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        GROUP BY p.category
        ORDER BY sold DESC
    """)
    by_category = cur.fetchall()

    conn.close()
    return {
        'today_count': today_count,
        'today_revenue': today_revenue,
        'low_stock': low_stock,
        'total_products': total_products,
        'weekly': [dict(r) for r in weekly],
        'by_category': [dict(r) for r in by_category],
    }
