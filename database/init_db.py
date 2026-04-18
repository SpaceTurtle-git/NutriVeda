"""
Run this script once to explicitly initialize the database:
    python database/init_db.py
The Flask app also auto-creates tables on startup via db.create_all().
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db

def init_database():
    app = create_app()
    with app.app_context():
        db.drop_all()   # Wipe existing tables (clean slate)
        db.create_all()
        print("✅  Database initialized successfully.")
        print(f"📁  Location: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == "__main__":
    init_database()
