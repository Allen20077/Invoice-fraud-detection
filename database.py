import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        po_id TEXT,
        vendor TEXT,
        amount REAL,
        date TEXT,
        status TEXT DEFAULT 'PENDING'
    )
    """)

    conn.commit()
    conn.close()

def add_invoice(invoice_id, po_id, vendor, amount, date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, 'PENDING')",
        (invoice_id, po_id, vendor, amount, date)
    )
    conn.commit()
    conn.close()

def get_invoice(invoice_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_status(invoice_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE invoices SET status=? WHERE invoice_id=?",
        (status, invoice_id)
    )
    conn.commit()
    conn.close()
