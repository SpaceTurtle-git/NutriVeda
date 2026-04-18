# app/models.py

from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

# ──────────────────────────────────────────────
# User (Authentication)
# ──────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-one relationship with UserProfile
    profile = db.relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ──────────────────────────────────────────────
# UserProfile (Dosha & Diet data)
# ──────────────────────────────────────────────
class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    dietary_preference = db.Column(db.String(20), nullable=False)  # 'veg' or 'non-veg'
    questionnaire_answers = db.Column(db.Text, nullable=False)
    primary_dosha = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")
    diet_plans = db.relationship("DietPlan", back_populates="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "weight": self.weight,
            "dietary_preference": self.dietary_preference,
            "questionnaire_answers": json.loads(self.questionnaire_answers),
            "primary_dosha": self.primary_dosha,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ──────────────────────────────────────────────
# DietPlan
# ──────────────────────────────────────────────
class DietPlan(db.Model):
    __tablename__ = "diet_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_profiles.id"), nullable=False)
    plan_data = db.Column(db.Text, nullable=False)   # JSON string of 7-day plan (may have recipes or not)
    dosha_at_generation = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipe_status = db.Column(db.String(20), default="pending")  # 'pending', 'complete', 'failed'

    user = db.relationship("UserProfile", back_populates="diet_plans")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_data": json.loads(self.plan_data),
            "dosha_at_generation": self.dosha_at_generation,
            "created_at": self.created_at.isoformat(),
            "recipe_status": self.recipe_status,
        }