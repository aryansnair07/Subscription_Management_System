from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db_connection

products = Blueprint("products", __name__)


# Check admin/staff access
def check_access():
    return (
        "user_id" in session
        and session.get("user_role") in ["admin", "staff"]
    )


# VIEW ALL PRODUCTS
@products.route("/products")
def view_products():

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    all_products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=all_products
    )


# ADD PRODUCT
@products.route("/products/add", methods=["POST"])
def add_product():

    if not check_access():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    sku = request.form.get("sku", "").strip()
    sales_price = request.form.get("sales_price", "")
    cost_price = request.form.get("cost_price", "0")

    if not name or not sales_price:
        flash("Product name and selling price are required.")
        return redirect(url_for("products.view_products"))

    try:
        sales_price = float(sales_price)
        cost_price = float(cost_price)

        if sales_price < 0 or cost_price < 0:
            raise ValueError()

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO products
            (name, description, sku, sales_price, cost_price)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            description,
            sku or None,
            sales_price,
            cost_price
        ))

        conn.commit()
        conn.close()

        flash("Product added successfully!")

    except ValueError:
        flash("Please enter valid non-negative prices.")

    except Exception:
        flash("Unable to add product. Check whether the SKU already exists.")

    return redirect(url_for("products.view_products"))


# DELETE PRODUCT
@products.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    flash("Product deleted successfully!")

    return redirect(url_for("products.view_products"))


# EDIT PRODUCT
@products.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        sku = request.form.get("sku", "").strip()
        
        try:
            sales_price = float(request.form.get("sales_price"))
            cost_price = float(request.form.get("cost_price", 0))

            if not name or sales_price < 0 or cost_price < 0:
                raise ValueError()

            conn.execute("""
                UPDATE products
                SET name=?, description=?, sku=?,
                    sales_price=?, cost_price=?
                WHERE id=?
            """, (
                name, description, sku or None,
                sales_price, cost_price, product_id
            ))

            conn.commit()
            flash("Product updated successfully!")

        except ValueError:
            flash("Please enter valid product details.")

        except Exception:
            flash("Could not update product. Check the SKU.")

        finally:
            conn.close()

        return redirect(url_for("products.view_products"))

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    conn.close()

    if not product:
        flash("Product not found.")
        return redirect(url_for("products.view_products"))

    return render_template("edit_product.html", product=product)
# VIEW PRODUCT VARIANTS
@products.route("/products/<int:product_id>/variants")
def view_variants(product_id):

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        flash("Product not found.")
        return redirect(url_for("products.view_products"))

    variants = conn.execute(
        "SELECT * FROM product_variants WHERE product_id = ?",
        (product_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "variants.html",
        product=product,
        variants=variants
    )
# ADD PRODUCT VARIANT
@products.route("/products/<int:product_id>/variants/add", methods=["POST"])
def add_variant(product_id):

    if not check_access():
        return redirect(url_for("auth.login"))

    name = request.form.get("variant_name", "").strip()

    try:
        extra_price = float(request.form.get("extra_price", 0))

        if not name or extra_price < 0:
            raise ValueError()

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO product_variants
            (product_id, variant_name, extra_price)
            VALUES (?, ?, ?)
        """, (product_id, name, extra_price))

        conn.commit()
        conn.close()

        flash("Variant added successfully!")

    except ValueError:
        flash("Enter a valid variant name and price.")

    return redirect(url_for(
        "products.view_variants",
        product_id=product_id
    ))
# DELETE PRODUCT VARIANT
@products.route("/variants/delete/<int:variant_id>", methods=["POST"])
def delete_variant(variant_id):

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    variant = conn.execute(
        "SELECT product_id FROM product_variants WHERE id = ?",
        (variant_id,)
    ).fetchone()

    if not variant:
        conn.close()
        flash("Variant not found.")
        return redirect(url_for("products.view_products"))

    product_id = variant["product_id"]

    conn.execute(
        "DELETE FROM product_variants WHERE id = ?",
        (variant_id,)
    )

    conn.commit()
    conn.close()

    flash("Variant deleted successfully!")

    return redirect(url_for(
        "products.view_variants",
        product_id=product_id
    ))
# VIEW AND ADD SUBSCRIPTION PLANS
@products.route("/plans", methods=["GET", "POST"])
def view_plans():

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    if request.method == "POST":

        product_id = request.form.get("product_id")
        name = request.form.get("name", "").strip()
        frequency = request.form.get("billing_frequency")
        
        try:
            price = float(request.form.get("price"))
            min_quantity = int(request.form.get("min_quantity", 1))

            if price < 0 or min_quantity < 1 or not name:
                raise ValueError()

            conn.execute("""
                INSERT INTO plans
                (product_id, name, billing_frequency, price, min_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                product_id,
                name,
                frequency,
                price,
                min_quantity
            ))

            conn.commit()
            flash("Subscription plan created successfully!")

        except ValueError:
            flash("Please enter valid plan details.")

        except Exception:
            flash("Unable to create plan. Check the selected product.")

        finally:
            conn.close()

        return redirect(url_for("products.view_plans"))

    all_products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1"
    ).fetchall()

    all_plans = conn.execute("""
        SELECT plans.*, products.name AS product_name
        FROM plans
        JOIN products ON plans.product_id = products.id
        ORDER BY plans.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "plans.html",
        products=all_products,
        plans=all_plans
    )


# DELETE SUBSCRIPTION PLAN
@products.route("/plans/delete/<int:plan_id>", methods=["POST"])
def delete_plan(plan_id):

    if not check_access():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM plans WHERE id = ?",
        (plan_id,)
    )

    conn.commit()
    conn.close()

    flash("Subscription plan deleted successfully!")

    return redirect(url_for("products.view_plans"))