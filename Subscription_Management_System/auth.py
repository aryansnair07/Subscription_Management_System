from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from functools import wraps

auth_bp = Blueprint("auth", __name__)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard.index"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            return redirect(url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter a name, valid email and password of at least 6 characters.", "warning")
        else:
            db = get_db()
            try:
                cur = db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'customer')",
                    (name, email, generate_password_hash(password)))
                db.execute("INSERT INTO customers(user_id) VALUES(?)", (cur.lastrowid,))
                db.commit()
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("auth.login"))
            except Exception:
                db.rollback()
                flash("That email may already be registered.", "danger")
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
