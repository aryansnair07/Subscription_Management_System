from flask import Blueprint, render_template
from database import get_db
from auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def index():
    db = get_db()
    stats = {
      "customers": db.execute("SELECT COUNT(*) n FROM customers").fetchone()["n"],
      "products": db.execute("SELECT COUNT(*) n FROM products WHERE active=1").fetchone()["n"],
      "active": db.execute("SELECT COUNT(*) n FROM subscriptions WHERE status='active'").fetchone()["n"],
      "invoices": db.execute("SELECT COUNT(*) n FROM invoices").fetchone()["n"],
      "revenue": db.execute("SELECT COALESCE(SUM(amount),0) n FROM payments").fetchone()["n"],
      "outstanding": db.execute("""SELECT COALESCE(SUM(i.total-COALESCE(p.paid,0)),0) n FROM invoices i
        LEFT JOIN (SELECT invoice_id,SUM(amount) paid FROM payments GROUP BY invoice_id) p ON p.invoice_id=i.id
        WHERE i.status!='paid'""").fetchone()["n"],
      "overdue": db.execute("SELECT COUNT(*) n FROM invoices WHERE status!='paid' AND due_date<date('now')").fetchone()["n"]
    }
    recent = db.execute("SELECT invoice_number,total,status,due_date FROM invoices ORDER BY id DESC LIMIT 6").fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent)
