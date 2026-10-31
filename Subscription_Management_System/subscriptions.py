from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db
from auth import login_required, role_required
from datetime import date, timedelta
import calendar

subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")

def add_period(d, frequency):
    if frequency == "daily": return d + timedelta(days=1)
    if frequency == "weekly": return d + timedelta(days=7)
    if frequency == "yearly":
        year = d.year + 1
        return d.replace(year=year, day=min(d.day, 29 if calendar.isleap(year) and d.month == 2 else 28) if d.month == 2 else d.day)
    month = d.month % 12 + 1
    year = d.year + (d.month // 12)
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)

@subscriptions_bp.route("/", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def index():
    db = get_db()
    if request.method == "POST":
        try:
            customer_id, plan_id = int(request.form["customer_id"]), int(request.form["plan_id"])
            start = date.fromisoformat(request.form.get("start_date") or date.today().isoformat())
            plan = db.execute("SELECT * FROM plans WHERE id=? AND active=1", (plan_id,)).fetchone()
            if not plan: raise ValueError()
            nxt = start  # First billing period is billable immediately for the hackathon demo.
            number = "SUB-" + date.today().strftime("%Y%m%d") + "-" + str(int(date.today().strftime("%j"))) + str(customer_id) + str(plan_id)
            cur = db.execute("""INSERT INTO subscriptions(subscription_number,customer_id,plan_id,start_date,next_billing_date)
                VALUES(?,?,?,?,?)""", (number, customer_id, plan_id, start.isoformat(), nxt.isoformat()))
            product = db.execute("SELECT product_id FROM plans WHERE id=?", (plan_id,)).fetchone()
            db.execute("INSERT INTO subscription_lines(subscription_id,product_id,quantity,unit_price) VALUES(?,?,1,?)",
                       (cur.lastrowid, product["product_id"], plan["price"]))
            db.commit()
            flash("Subscription created.", "success")
        except Exception:
            db.rollback()
            flash("Could not create subscription. Check customer, plan and date.", "danger")
        return redirect(url_for("subscriptions.index"))
    customers = db.execute("""SELECT customers.id, COALESCE(users.name, customers.company_name, 'Customer') name
        FROM customers LEFT JOIN users ON users.id=customers.user_id""").fetchall()
    plans = db.execute("SELECT plans.*, products.name product_name FROM plans JOIN products ON products.id=plans.product_id WHERE plans.active=1").fetchall()
    rows = db.execute("""SELECT s.*, COALESCE(u.name,c.company_name,'Customer') customer_name,
        p.name plan_name FROM subscriptions s JOIN customers c ON c.id=s.customer_id
        LEFT JOIN users u ON u.id=c.user_id JOIN plans p ON p.id=s.plan_id ORDER BY s.id DESC""").fetchall()
    return render_template("subscriptions.html", customers=customers, plans=plans, subscriptions=rows)

@subscriptions_bp.post("/<int:sid>/status")
@login_required
@role_required("admin", "staff")
def status(sid):
    value = request.form.get("status")
    if value in ("active", "paused", "closed"):
        db = get_db()
        db.execute("UPDATE subscriptions SET status=? WHERE id=?", (value, sid))
        db.commit()
        flash("Subscription status updated.", "success")
    return redirect(url_for("subscriptions.index"))

@subscriptions_bp.route("/quotations", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def quotations():
    db = get_db()
    if request.method == "POST":
        try:
            cid, pid = int(request.form["customer_id"]), int(request.form["plan_id"])
            plan = db.execute("SELECT price FROM plans WHERE id=?", (pid,)).fetchone()
            number = "QUO-" + date.today().strftime("%Y%m%d%H%M%S")
            db.execute("INSERT INTO quotations(quote_number,customer_id,plan_id,amount,valid_until) VALUES(?,?,?,?,?)",
                       (number, cid, pid, plan["price"], request.form.get("valid_until") or None))
            db.commit()
            flash("Quotation saved.", "success")
        except Exception:
            db.rollback()
            flash("Unable to create quotation.", "danger")
        return redirect(url_for("subscriptions.quotations"))
    customers = db.execute("SELECT c.id, COALESCE(u.name,c.company_name,'Customer') name FROM customers c LEFT JOIN users u ON u.id=c.user_id").fetchall()
    plans = db.execute("SELECT * FROM plans WHERE active=1").fetchall()
    quotes = db.execute("SELECT q.*, COALESCE(u.name,c.company_name,'Customer') customer_name FROM quotations q JOIN customers c ON c.id=q.customer_id LEFT JOIN users u ON u.id=c.user_id ORDER BY q.id DESC").fetchall()
    return render_template("quotations.html", customers=customers, plans=plans, quotations=quotes)
