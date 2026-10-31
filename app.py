
from flask import Flask, render_template
from database import init_db
from subscriptions import subscriptions_bp

app = Flask(__name__)
app.secret_key = "subscription-management-dev-key"


app.register_blueprint(subscriptions_bp)


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
