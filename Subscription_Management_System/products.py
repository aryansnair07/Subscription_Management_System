from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from auth import login_required, role_required

products_bp = Blueprint("products", __name__, url_prefix="/catalog")

@products_bp.route("/products", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def products():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("sales_price", "0")
        if name:
            try:
                db.execute("INSERT INTO products(name,description,sales_price,cost_price) VALUES(?,?,?,?)",
                    (name, request.form.get("description",""), float(price), float(request.form.get("cost_price") or 0)))
                db.commit()
                flash("Product added.", "success")
            except ValueError:
                flash("Enter valid prices.", "danger")
        return redirect(url_for("products.products"))
    rows = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template("products.html", products=rows)

@products_bp.route("/plans", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def plans():
    db = get_db()
    if request.method == "POST":
        try:
            db.execute("INSERT INTO plans(product_id,name,frequency,price,min_quantity) VALUES(?,?,?,?,?)",
                (int(request.form["product_id"]), request.form["name"].strip(),
                 request.form["frequency"], float(request.form["price"]), int(request.form.get("min_quantity") or 1)))
            db.commit()
            flash("Plan created.", "success")
        except (ValueError, KeyError):
            flash("Check the plan details.", "danger")
        return redirect(url_for("products.plans"))
    products = db.execute("SELECT * FROM products WHERE active=1").fetchall()
    plans = db.execute("""SELECT plans.*, products.name product_name FROM plans
                          JOIN products ON products.id=plans.product_id ORDER BY plans.id DESC""").fetchall()
    return render_template("plans.html", products=products, plans=plans)
