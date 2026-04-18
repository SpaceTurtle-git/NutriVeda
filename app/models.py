from app import db
from datetime import datetime
import json

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    dietary_preference = db.Column(db.String(20), nullable=False)  # 'veg' or 'non-veg'
    # Questionnaire answers stored as JSON string
    questionnaire_answers = db.Column(db.Text, nullable=False)
    primary_dosha = db.Column(db.String(20), nullable=False)  # Vata, Pitta, Kapha
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
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


class DietPlan(db.Model):
    __tablename__ = "diet_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_profiles.id"), nullable=False)
    plan_data = db.Column(db.Text, nullable=False)   # JSON string of 7-day plan
    dosha_at_generation = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("UserProfile", back_populates="diet_plans")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_data": json.loads(self.plan_data),
            "dosha_at_generation": self.dosha_at_generation,
            "created_at": self.created_at.isoformat(),
        }
