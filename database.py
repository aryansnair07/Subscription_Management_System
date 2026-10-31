import sqlite3
from pathlib import Path

DATABASE = Path(__file__).resolve().parent / "subscriptions.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff'
                    CHECK (role IN ('admin', 'staff', 'customer')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                contact_name TEXT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                address TEXT,
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active', 'Inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                sku TEXT UNIQUE,
                sales_price REAL NOT NULL DEFAULT 0 CHECK (sales_price >= 0),
                cost_price REAL NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                variant_name TEXT NOT NULL,
                extra_price REAL NOT NULL DEFAULT 0 CHECK (extra_price >= 0),
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE (product_id, variant_name)
            );

            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                frequency TEXT NOT NULL
                    CHECK (frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
                price REAL NOT NULL CHECK (price >= 0),
                min_quantity INTEGER NOT NULL DEFAULT 1 CHECK (min_quantity >= 1),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_number TEXT UNIQUE,
                customer_id INTEGER NOT NULL,
                quotation_date TEXT NOT NULL DEFAULT (date('now')),
                valid_until TEXT,
                status TEXT NOT NULL DEFAULT 'Draft'
                    CHECK (status IN ('Draft', 'Sent', 'Accepted', 'Rejected', 'Expired')),
                subtotal REAL NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
                discount_amount REAL NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
                tax_amount REAL NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
                total_amount REAL NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS quotation_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                plan_id INTEGER,
                product_id INTEGER,
                description TEXT,
                quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
                unit_price REAL NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
                amount REAL NOT NULL DEFAULT 0 CHECK (amount >= 0),
                FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE,
                FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_number TEXT UNIQUE,
                customer_id INTEGER NOT NULL,
                quotation_id INTEGER,
                plan_id INTEGER,
                start_date TEXT NOT NULL DEFAULT (date('now')),
                expiry_date TEXT,
                next_billing_date TEXT,
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK (status IN ('Pending', 'Active', 'Paused', 'Cancelled', 'Expired')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE SET NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS subscription_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER NOT NULL,
                product_id INTEGER,
                plan_id INTEGER,
                quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
                unit_price REAL NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS tax_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                percentage REAL NOT NULL CHECK (percentage >= 0),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS discounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                discount_type TEXT NOT NULL
                    CHECK (discount_type IN ('percentage', 'fixed')),
                value REAL NOT NULL CHECK (value >= 0),
                min_quantity INTEGER NOT NULL DEFAULT 1 CHECK (min_quantity >= 1),
                min_purchase REAL NOT NULL DEFAULT 0 CHECK (min_purchase >= 0),
                start_date TEXT NOT NULL DEFAULT (date('now')),
                end_date TEXT NOT NULL DEFAULT '9999-12-31',
                usage_limit INTEGER,
                usage_count INTEGER NOT NULL DEFAULT 0 CHECK (usage_count >= 0),
                applies_to TEXT NOT NULL DEFAULT 'subscription',
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE,
                subscription_id INTEGER NOT NULL,
                billing_period_start TEXT NOT NULL,
                billing_period_end TEXT NOT NULL,
                invoice_date TEXT NOT NULL DEFAULT (date('now')),
                due_date TEXT NOT NULL DEFAULT (date('now', '+14 days')),
                subtotal REAL NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
                discount_amount REAL NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
                tax_amount REAL NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
                total_amount REAL NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
                amount_paid REAL NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
                status TEXT NOT NULL DEFAULT 'Draft'
                    CHECK (status IN ('Draft', 'Issued', 'Paid', 'Overdue', 'Cancelled')),
                discount_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE RESTRICT,
                FOREIGN KEY (discount_id) REFERENCES discounts(id) ON DELETE SET NULL,
                UNIQUE (subscription_id, billing_period_start, billing_period_end)
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                description TEXT,
                quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
                unit_price REAL NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
                amount REAL NOT NULL DEFAULT 0 CHECK (amount >= 0),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                method TEXT NOT NULL,
                payment_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'Completed'
                    CHECK (status IN ('Pending', 'Completed', 'Failed', 'Refunded')),
                transaction_reference TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
            CREATE INDEX IF NOT EXISTS idx_quotations_customer ON quotations(customer_id);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
            CREATE INDEX IF NOT EXISTS idx_invoice_status ON invoices(status);
            CREATE INDEX IF NOT EXISTS idx_invoice_due_date ON invoices(due_date);
            CREATE INDEX IF NOT EXISTS idx_payment_invoice ON payments(invoice_id);
            """
        )
        conn.commit()
        print(f"Database initialized successfully: {DATABASE}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
