# app/routes.py (partial update – only show changes)

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserProfile, DietPlan
from app.dosha import calculate_dosha, get_dosha_description, DOSHA_QUESTIONS
from app.ai_service import generate_diet_plan, chat_response
from datetime import datetime
import json

main = Blueprint("main", __name__)


# ──────────────────────────────────────────────
# AUTH ROUTES (new)
# ──────────────────────────────────────────────

@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json() or request.form
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not email or not password or not name:
        return jsonify({"error": "All fields required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Create an empty profile with only name (other fields will be filled later)
    profile = UserProfile(
        user_id=user.id,
        name=name,
        age=0,                     # temporary placeholder
        weight=0.0,
        dietary_preference="veg",
        questionnaire_answers="{}",
        primary_dosha="Vata"
    )
    db.session.add(profile)
    db.session.commit()

    login_user(user)
    return jsonify({"redirect": url_for("main.profile_new")}), 201


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json() or request.form
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(user)
    # If user has a complete profile (age > 0), go to dashboard, else to profile creation
    if user.profile and user.profile.age > 0:
        return jsonify({"redirect": url_for("main.dashboard", user_id=user.profile.id)}), 200
    else:
        return jsonify({"redirect": url_for("main.profile_new")}), 200


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# ──────────────────────────────────────────────
# NEW: PROFILE CREATION PAGE (intake form)
# ──────────────────────────────────────────────

@main.route("/profile/new")
@login_required
def profile_new():
    # If user already has a complete profile, redirect to dashboard
    if current_user.profile and current_user.profile.age > 0:
        return redirect(url_for("main.dashboard", user_id=current_user.profile.id))
    return render_template("index.html", questions=DOSHA_QUESTIONS)


# ──────────────────────────────────────────────
# MODIFIED: CREATE PROFILE (POST /api/profile)
# Now uses current_user instead of creating new UserProfile from scratch
# ──────────────────────────────────────────────

@main.route("/api/profile", methods=["POST"])
@login_required
def create_profile():
    data = request.get_json()
    required = ["age", "weight", "dietary_preference", "answers"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Update the existing profile attached to current_user
    profile = current_user.profile
    profile.age = int(data["age"])
    profile.weight = float(data["weight"])
    profile.dietary_preference = data["dietary_preference"]
    profile.questionnaire_answers = json.dumps(data["answers"])
    profile.primary_dosha = calculate_dosha(data["answers"])
    profile.updated_at = datetime.utcnow()

    db.session.flush()

    try:
        plan_data = generate_diet_plan(profile.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Diet plan generation failed: {str(e)}"}), 500

    diet_plan = DietPlan(
        user_id=profile.id,
        plan_data=json.dumps(plan_data),
        dosha_at_generation=profile.primary_dosha,
    )
    db.session.add(diet_plan)
    db.session.commit()

    return jsonify({
        "user": profile.to_dict(),
        "plan": diet_plan.to_dict(),
        "dosha_info": get_dosha_description(profile.primary_dosha),
        "redirect": url_for("main.dashboard", user_id=profile.id),
    }), 201


# ──────────────────────────────────────────────
# PROTECT DASHBOARD AND OTHER USER-SPECIFIC ROUTES
# ──────────────────────────────────────────────

@main.route("/dashboard/<int:user_id>")
@login_required
def dashboard(user_id):
    # Ensure the logged-in user can only see their own dashboard
    if current_user.profile.id != user_id:
        return "Unauthorized", 403
    user = UserProfile.query.get_or_404(user_id)
    latest_plan = DietPlan.query.filter_by(user_id=user_id).order_by(DietPlan.created_at.desc()).first()
    dosha_info = get_dosha_description(user.primary_dosha)
    return render_template(
        "dashboard.html",
        user=user.to_dict(),
        plan=latest_plan.to_dict() if latest_plan else None,
        dosha_info=dosha_info,
    )


@main.route("/api/profile/<int:user_id>", methods=["GET"])
@login_required
def get_profile(user_id):
    if current_user.profile.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    user = UserProfile.query.get_or_404(user_id)
    latest_plan = DietPlan.query.filter_by(user_id=user_id).order_by(DietPlan.created_at.desc()).first()
    return jsonify({
        "user": user.to_dict(),
        "plan": latest_plan.to_dict() if latest_plan else None,
        "dosha_info": get_dosha_description(user.primary_dosha),
    })


@main.route("/api/profile/<int:user_id>", methods=["PUT"])
@login_required
def update_profile(user_id):
    """Update profile, recalculate dosha, regenerate and overwrite diet plan."""
    # Ensure the profile belongs to the logged-in user
    profile = UserProfile.query.get_or_404(user_id)
    if profile.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    # Update fields if provided
    if "name" in data:
        profile.name = data["name"]
    if "age" in data:
        profile.age = int(data["age"])
    if "weight" in data:
        profile.weight = float(data["weight"])
    if "dietary_preference" in data:
        profile.dietary_preference = data["dietary_preference"]
    if "answers" in data:
        profile.questionnaire_answers = json.dumps(data["answers"])
        profile.primary_dosha = calculate_dosha(data["answers"])

    profile.updated_at = datetime.utcnow()

    # Regenerate plan
    try:
        plan_data = generate_diet_plan(profile.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Diet plan generation failed: {str(e)}"}), 500

    # Save new diet plan
    new_plan = DietPlan(
        user_id=profile.id,
        plan_data=json.dumps(plan_data),
        dosha_at_generation=profile.primary_dosha,
    )
    db.session.add(new_plan)
    db.session.commit()

    # ✅ MUST return a response
    return jsonify({
        "user": profile.to_dict(),
        "plan": new_plan.to_dict(),
        "dosha_info": get_dosha_description(profile.primary_dosha),
    })

# ──────────────────────────────────────────────
# LANDING PAGE (no intake form, just hero + buttons)
# ──────────────────────────────────────────────

@main.route("/")
def index():
    # If already logged in, redirect to their profile new or dashboard
    if current_user.is_authenticated:
        if current_user.profile and current_user.profile.age > 0:
            return redirect(url_for("main.dashboard", user_id=current_user.profile.id))
        else:
            return redirect(url_for("main.profile_new"))
    return render_template("landing.html")

# ──────────────────────────────────────────────
# CHAT BOT
# ──────────────────────────────────────────────

@main.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    user_context = data.get("user_context", None)

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    try:
        reply = chat_response(messages, user_context)
    except Exception as e:
        return jsonify({"error": f"Chat failed: {str(e)}"}), 500

    return jsonify({"reply": reply})