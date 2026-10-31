import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "instance", "subscriptions.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "hackathon-dev-key-change-before-production")
