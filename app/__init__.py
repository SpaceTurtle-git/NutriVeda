import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    # --- FIX: Ensure the instance folder exists ---
    # Flask creates an 'instance' folder automatically when you pass instance_relative_config=True,
    # but since you didn't, we create it manually.
    instance_path = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_path, exist_ok=True)

    db.init_app(app)
    CORS(app)

    from app.routes import main
    app.register_blueprint(main)

    # Auto-create tables on first run
    with app.app_context():
        db.create_all()

    return app