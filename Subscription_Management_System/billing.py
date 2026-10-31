from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from auth import login_required, role_required
from datetime import date, timedelta
from subscriptions import add_period

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")

@billing_bp.route("/invoices")
@login_required
@role_required("admin", "staff")
def invoices():
    db = get_db()
    rows = db.execute("""SELECT i.*, s.subscription_number, COALESCE(u.name,c.company_name,'Customer') customer_name
      FROM invoices i JOIN subscriptions s ON s.id=i.subscription_id
      JOIN customers c ON c.id=s.customer_id LEFT JOIN users u ON u.id=c.user_id ORDER BY i.id DESC""").fetchall()
    return render_template("invoices.html", invoices=rows)

@billing_bp.post("/run")
@login_required
@role_required("admin", "staff")
def run_billing():
    db = get_db()
    today = date.today()
    subs = db.execute("""SELECT s.*, p.price, p.frequency FROM subscriptions s
        JOIN plans p ON p.id=s.plan_id WHERE s.status='active' AND s.next_billing_date<=?""",
        (today.isoformat(),)).fetchall()
    made = 0
    for s in subs:
        period_start = s["next_billing_date"]
        start = date.fromisoformat(period_start)
        end = add_period(start, s["frequency"])
        exists = db.execute("SELECT id FROM invoices WHERE subscription_id=? AND period_start=?",
                            (s["id"], period_start)).fetchone()
        if exists: continue
        subtotal = float(s["price"])
        discount = 0.0
        d = db.execute("""SELECT * FROM discounts WHERE active=1 AND (start_date IS NULL OR start_date<=?)
            AND (end_date IS NULL OR end_date>=?) AND (usage_limit IS NULL OR used_count<usage_limit)
            ORDER BY id DESC LIMIT 1""", (today.isoformat(), today.isoformat())).fetchone()
        if d:
            discount = min(subtotal, float(d["value"]) if d["discount_type"]=="fixed" else subtotal*float(d["value"])/100)
            db.execute("UPDATE discounts SET used_count=used_count+1 WHERE id=?", (d["id"],))
        taxrow = db.execute("SELECT percentage FROM tax_rules WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
        tax_rate = float(taxrow["percentage"]) if taxrow else 0.0
        tax = round((subtotal-discount)*tax_rate/100, 2)
        total = round(subtotal-discount+tax, 2)
        number = "INV-" + today.strftime("%Y%m%d") + "-" + str(s["id"]) + "-" + start.strftime("%m%d")
        db.execute("""INSERT INTO invoices(invoice_number,subscription_id,period_start,period_end,subtotal,discount,tax,total,due_date)
          VALUES(?,?,?,?,?,?,?,?,?)""", (number,s["id"],period_start,end.isoformat(),subtotal,discount,tax,total,(today+timedelta(days=7)).isoformat()))
        db.execute("UPDATE subscriptions SET next_billing_date=? WHERE id=?", (end.isoformat(),s["id"]))
        made += 1
    db.commit()
    flash(f"Billing complete: {made} invoice(s) generated. Existing periods were skipped.", "success")
    return redirect(url_for("billing.invoices"))

@billing_bp.route("/payments", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def payments():
    db = get_db()
    if request.method == "POST":
        try:
            iid, amount = int(request.form["invoice_id"]), float(request.form["amount"])
            invoice = db.execute("SELECT * FROM invoices WHERE id=?", (iid,)).fetchone()
            paid = db.execute("SELECT COALESCE(SUM(amount),0) n FROM payments WHERE invoice_id=?", (iid,)).fetchone()["n"]
            if not invoice or amount <= 0 or amount > invoice["total"]-paid+0.001:
                raise ValueError()
            db.execute("INSERT INTO payments(invoice_id,amount,method,reference) VALUES(?,?,?,?)",
                       (iid,amount,request.form["method"],request.form.get("reference","")))
            new_paid = paid + amount
            status = "paid" if new_paid >= invoice["total"]-0.001 else "partial"
            db.execute("UPDATE invoices SET status=? WHERE id=?", (status,iid))
            db.commit()
            flash("Payment recorded.", "success")
        except Exception:
            db.rollback()
            flash("Payment invalid or greater than remaining balance.", "danger")
        return redirect(url_for("billing.payments"))
    inv = db.execute("SELECT * FROM invoices WHERE status!='paid' ORDER BY id DESC").fetchall()
    pays = db.execute("SELECT p.*, i.invoice_number FROM payments p JOIN invoices i ON i.id=p.invoice_id ORDER BY p.id DESC").fetchall()
    return render_template("payments.html", invoices=inv, payments=pays)

@billing_bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required("admin")
def settings():
    db = get_db()
    if request.method == "POST":
        try:
            if request.form.get("kind") == "tax":
                db.execute("INSERT INTO tax_rules(name,percentage) VALUES(?,?)",
                           (request.form["name"],float(request.form["value"])))
            else:
                db.execute("INSERT INTO discounts(name,discount_type,value,start_date,end_date,usage_limit) VALUES(?,?,?,?,?,?)",
                    (request.form["name"],request.form["discount_type"],float(request.form["value"]),
                     request.form.get("start_date") or None,request.form.get("end_date") or None,
                     int(request.form["usage_limit"]) if request.form.get("usage_limit") else None))
            db.commit()
            flash("Setting saved.", "success")
        except Exception:
            db.rollback()
            flash("Invalid setting.", "danger")
        return redirect(url_for("billing.settings"))
    taxes = db.execute("SELECT * FROM tax_rules ORDER BY id DESC").fetchall()
    discounts = db.execute("SELECT * FROM discounts ORDER BY id DESC").fetchall()
    return render_template("settings.html", taxes=taxes, discounts=discounts)
