import sqlite3
from flask import current_app, g

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
 email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','staff','customer')),
 created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS customers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
 company_name TEXT, phone TEXT, address TEXT,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
 description TEXT, product_type TEXT DEFAULT 'service',
 sales_price REAL NOT NULL DEFAULT 0, cost_price REAL DEFAULT 0,
 active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS variants (
 id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
 name TEXT NOT NULL, extra_price REAL DEFAULT 0,
 FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS plans (
 id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
 name TEXT NOT NULL, frequency TEXT NOT NULL
 CHECK(frequency IN ('daily','weekly','monthly','yearly')),
 price REAL NOT NULL, min_quantity INTEGER DEFAULT 1, active INTEGER DEFAULT 1,
 FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS quotations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, quote_number TEXT UNIQUE,
 customer_id INTEGER NOT NULL, plan_id INTEGER NOT NULL,
 amount REAL NOT NULL, status TEXT DEFAULT 'draft',
 valid_until TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(customer_id) REFERENCES customers(id),
 FOREIGN KEY(plan_id) REFERENCES plans(id)
);
CREATE TABLE IF NOT EXISTS subscriptions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, subscription_number TEXT UNIQUE,
 customer_id INTEGER NOT NULL, plan_id INTEGER NOT NULL,
 start_date TEXT NOT NULL, next_billing_date TEXT NOT NULL,
 end_date TEXT, status TEXT DEFAULT 'active',
 FOREIGN KEY(customer_id) REFERENCES customers(id),
 FOREIGN KEY(plan_id) REFERENCES plans(id)
);
CREATE TABLE IF NOT EXISTS subscription_lines (
 id INTEGER PRIMARY KEY AUTOINCREMENT, subscription_id INTEGER NOT NULL,
 product_id INTEGER NOT NULL, quantity INTEGER DEFAULT 1, unit_price REAL NOT NULL,
 FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
 FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS tax_rules (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
 percentage REAL NOT NULL DEFAULT 0, active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS discounts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
 discount_type TEXT NOT NULL CHECK(discount_type IN ('fixed','percentage')),
 value REAL NOT NULL, start_date TEXT, end_date TEXT,
 usage_limit INTEGER, used_count INTEGER DEFAULT 0, active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS invoices (
 id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT UNIQUE,
 subscription_id INTEGER NOT NULL, period_start TEXT NOT NULL,
 period_end TEXT NOT NULL, subtotal REAL NOT NULL, discount REAL DEFAULT 0,
 tax REAL DEFAULT 0, total REAL NOT NULL, due_date TEXT NOT NULL,
 status TEXT DEFAULT 'unpaid', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(subscription_id, period_start),
 FOREIGN KEY(subscription_id) REFERENCES subscriptions(id)
);
CREATE TABLE IF NOT EXISTS payments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL,
 amount REAL NOT NULL, method TEXT NOT NULL, reference TEXT,
 payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(invoice_id) REFERENCES invoices(id)
);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()

def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
