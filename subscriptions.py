

from datetime import datetime
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from database import get_db

subscriptions_bp = Blueprint("subscriptions", __name__)


@subscriptions_bp.route("/customers", methods=["GET", "POST"])
def manage_customers():
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()

        if not name or not email:
            flash("Customer name and email are required.")
        else:
            try:
                conn.execute(
                    """INSERT INTO customers
                       (company_name, contact_name, email)
                       VALUES (?, ?, ?)""",
                    (company or name, name, email)
                )
                conn.commit()
                flash("Customer added successfully.")
                conn.close()
                return redirect(url_for("subscriptions.manage_customers"))
            except Exception as error:
                conn.rollback()
                flash(f"Could not add customer: {error}")

    customers = conn.execute(
        """SELECT id, contact_name AS name, email,
                  company_name AS company
           FROM customers ORDER BY id DESC"""
    ).fetchall()
    conn.close()
    return render_template("customers.html", customers=customers)


@subscriptions_bp.route("/quotations", methods=["GET", "POST"])
def manage_quotations():
    conn = get_db()

    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        plan_id = request.form.get("plan_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)
        notes = request.form.get("notes", "").strip()

        customer = conn.execute(
            "SELECT id FROM customers WHERE id = ?", (customer_id,)
        ).fetchone() if customer_id else None

        plan = conn.execute(
            "SELECT id, name, price FROM plans WHERE id = ? AND is_active = 1",
            (plan_id,)
        ).fetchone() if plan_id else None

        if not customer or not plan or not quantity or quantity < 1:
            flash("Choose a valid customer, plan, and quantity.")
        else:
            try:
                subtotal = float(plan["price"]) * quantity
                number = "Q-" + datetime.now().strftime("%Y%m%d%H%M%S%f")

                cursor = conn.execute(
                    """INSERT INTO quotations
                       (quotation_number, customer_id, subtotal,
                        total_amount, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    (number, customer_id, subtotal, subtotal, notes)
                )
                quotation_id = cursor.lastrowid

                conn.execute(
                    """INSERT INTO quotation_items
                       (quotation_id, plan_id, description,
                        quantity, unit_price, amount)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (quotation_id, plan_id, plan["name"],
                     quantity, plan["price"], subtotal)
                )
                conn.commit()
                flash(f"Quotation {number} created successfully.")
                conn.close()
                return redirect(url_for("subscriptions.manage_quotations"))
            except Exception as error:
                conn.rollback()
                flash(f"Could not create quotation: {error}")

    customers = conn.execute(
        "SELECT id, contact_name, company_name FROM customers ORDER BY id"
    ).fetchall()
    plans = conn.execute(
        """SELECT id, name, price, frequency FROM plans
           WHERE is_active = 1 ORDER BY name"""
    ).fetchall()
    quotations = conn.execute(
        """SELECT q.id, q.quotation_number, q.status, q.total_amount,
                  q.quotation_date, c.company_name
           FROM quotations q
           JOIN customers c ON c.id = q.customer_id
           ORDER BY q.id DESC"""
    ).fetchall()

    conn.close()
    return render_template(
        "quotations.html",
        customers=customers,
        plans=plans,
        quotations=quotations
    )


@subscriptions_bp.route("/subscriptions", methods=["GET", "POST"])
def manage_subscriptions():
    conn = get_db()

    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        plan_id = request.form.get("plan_id", type=int)
        start_date = request.form.get("start_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip() or None
        quantity = request.form.get("quantity", 1, type=int)

        customer = conn.execute(
            "SELECT id FROM customers WHERE id = ?", (customer_id,)
        ).fetchone() if customer_id else None

        plan = conn.execute(
            "SELECT id, price FROM plans WHERE id = ? AND is_active = 1",
            (plan_id,)
        ).fetchone() if plan_id else None

        if not customer or not plan or not start_date or not quantity or quantity < 1:
            flash("Choose a customer, plan, start date, and valid quantity.")
        elif expiry_date and expiry_date < start_date:
            flash("Expiry date cannot be before the start date.")
        else:
            try:
                number = "S-" + datetime.now().strftime("%Y%m%d%H%M%S%f")

                cursor = conn.execute(
                    """INSERT INTO subscriptions
                       (subscription_number, customer_id, plan_id,
                        start_date, expiry_date, next_billing_date, status)
                       VALUES (?, ?, ?, ?, ?, ?, 'Active')""",
                    (number, customer_id, plan_id,
                     start_date, expiry_date, start_date)
                )
                subscription_id = cursor.lastrowid

                conn.execute(
                    """INSERT INTO subscription_lines
                       (subscription_id, plan_id, quantity, unit_price)
                       VALUES (?, ?, ?, ?)""",
                    (subscription_id, plan_id, quantity, plan["price"])
                )
                conn.commit()
                flash(f"Subscription {number} created successfully.")
                conn.close()
                return redirect(url_for("subscriptions.manage_subscriptions"))
            except Exception as error:
                conn.rollback()
                flash(f"Could not create subscription: {error}")

    customers = conn.execute(
        "SELECT id, contact_name, company_name FROM customers ORDER BY id"
    ).fetchall()
    plans = conn.execute(
        """SELECT id, name, price, frequency FROM plans
           WHERE is_active = 1 ORDER BY name"""
    ).fetchall()
    records = conn.execute(
        """SELECT s.id, s.subscription_number, s.status,
                  s.start_date, s.expiry_date, c.company_name, p.name AS plan_name
           FROM subscriptions s
           JOIN customers c ON c.id = s.customer_id
           LEFT JOIN plans p ON p.id = s.plan_id
           ORDER BY s.id DESC"""
    ).fetchall()

    conn.close()
    return render_template(
        "subscriptions.html",
        customers=customers,
        plans=plans,
        subscriptions=records
    )

