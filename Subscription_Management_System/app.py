import os
from flask import Flask, redirect, url_for, session, flash
from config import DATABASE, SECRET_KEY
from database import init_db, close_db, get_db
from auth import auth_bp
from products import products_bp
from subscriptions import subscriptions_bp
from billing import billing_bp
from dashboard import dashboard_bp
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY=SECRET_KEY, DATABASE=DATABASE)
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
        db = get_db()
        admin = db.execute("SELECT id FROM users WHERE email='admin@brightloop.test'").fetchone()
        if not admin:
            db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'admin')",
                       ("System Admin","admin@brightloop.test",generate_password_hash("Admin123!")))
            db.commit()
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/health")
    def health():
        return {"status":"ok"}

    @app.errorhandler(404)
    def not_found(_):
        return "Page not found", 404
    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
