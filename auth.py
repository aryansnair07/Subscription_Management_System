from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection

auth = Blueprint("auth", __name__)


# USER REGISTRATION
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed_password, "customer"))

            conn.commit()

            flash("Registration successful! Please login.")
            return redirect(url_for("auth.login"))

        except Exception:
            flash("Email already registered or invalid details.")

        finally:
            conn.close()

    return render_template("register.html")


# USER LOGIN
@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password_hash"], password
        ):

            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]

            flash("Login successful!")

            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


# USER LOGOUT
@auth.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("auth.login"))