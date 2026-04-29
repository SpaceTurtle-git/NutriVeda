# app/routes.py

import os
import json
import threading
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserProfile, DietPlan
from app.dosha import calculate_dosha, get_dosha_description, DOSHA_QUESTIONS
from app.ai_service import generate_diet_plan, chat_response
from app.meal_service import enrich_meal_plan_with_recipes
logger = logging.getLogger(__name__)


main = Blueprint("main", __name__)


# ──────────────────────────────────────────────
# AUTH ROUTES
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
        age=0,
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
    if user.role == "doctor":
        return jsonify({"redirect": url_for("main.doctor_dashboard")}), 200
    elif user.profile and user.profile.age > 0:
        return jsonify({"redirect": url_for("main.dashboard", user_id=user.profile.id)}), 200
    else:
        return jsonify({"redirect": url_for("main.profile_new")}), 200


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# ──────────────────────────────────────────────
# PROFILE CREATION PAGE (intake form)
# ──────────────────────────────────────────────

@main.route("/profile/new")
@login_required
def profile_new():
    # If user already has a complete profile, redirect to dashboard
    if current_user.profile and current_user.profile.age > 0:
        return redirect(url_for("main.dashboard", user_id=current_user.profile.id))
    return render_template("index.html", questions=DOSHA_QUESTIONS)


# ──────────────────────────────────────────────
# CREATE PROFILE (POST /api/profile)
# ──────────────────────────────────────────────

@main.route("/api/profile", methods=["POST"])
@login_required
def create_profile():
    data = request.get_json()
    required = ["age", "weight", "dietary_preference", "answers"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Get cuisine preference (default to international if not provided)
    cuisine_pref = data.get("cuisine_preference", "international")

    # Update the existing profile attached to current_user
    profile = current_user.profile
    profile.age = int(data["age"])
    profile.weight = float(data["weight"])
    profile.dietary_preference = data["dietary_preference"]
    profile.cuisine_preference = cuisine_pref   # <-- NEW
    profile.questionnaire_answers = json.dumps(data["answers"])
    profile.primary_dosha = calculate_dosha(data["answers"])
    profile.updated_at = datetime.utcnow()

    db.session.flush()

    # Generate diet plan via AI (no recipes yet)
    try:
        plan_data = generate_diet_plan(profile.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Diet plan generation failed: {str(e)}"}), 500

    # Save plan with pending status
    diet_plan = DietPlan(
        user_id=profile.id,
        plan_data=json.dumps(plan_data),
        dosha_at_generation=profile.primary_dosha,
        recipe_status="pending"
    )
    db.session.add(diet_plan)
    db.session.commit()

    # Inside create_profile, after diet_plan is saved
    # Capture the app instance BEFORE starting the thread
    app = current_app._get_current_object()

    def enrich_in_background(plan_id, plan_data, dosha):
        with app.app_context():
            from app.meal_service import enrich_meal_plan_with_recipes
            from app.models import DietPlan, db
            try:
                enriched = enrich_meal_plan_with_recipes(plan_data, dosha)
                plan = DietPlan.query.get(plan_id)
                if plan:
                    plan.plan_data = json.dumps(enriched)
                    plan.recipe_status = "complete"
                    db.session.commit()
                    logger.info(f"✅ Plan {plan_id} enriched successfully.")
            except Exception as e:
                logger.error(f"❌ Enrichment failed for plan {plan_id}: {e}")
                plan = DietPlan.query.get(plan_id)
                if plan:
                    plan.recipe_status = "failed"
                    db.session.commit()

    thread = threading.Thread(target=enrich_in_background, args=(diet_plan.id, plan_data, profile.primary_dosha))
    thread.daemon = True
    thread.start()

    # Return response with plan that has pending status
    return jsonify({
        "user": profile.to_dict(),
        "plan": diet_plan.to_dict(),
        "dosha_info": get_dosha_description(profile.primary_dosha),
        "redirect": url_for("main.dashboard", user_id=profile.id),
    }), 201


# ──────────────────────────────────────────────
# POLLING ENDPOINT FOR RECIPE STATUS
# ──────────────────────────────────────────────

@main.route("/api/plan/<int:plan_id>/status", methods=["GET"])
@login_required
def plan_status(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)
    # Check that the plan belongs to the logged-in user's profile
    if plan.user.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "status": plan.recipe_status,
        "plan": plan.to_dict() if plan.recipe_status == "complete" else None
    })


# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

@main.route("/dashboard/<int:user_id>")
@login_required
def dashboard(user_id):
    # Doctors can view any patient's dashboard
    if current_user.role == "doctor":
        # Ensure the requested user is a patient (role = 'patient')
        patient_user = User.query.get(user_id)
        if not patient_user or patient_user.role != "patient":
            return "Patient not found", 404
        user_profile = UserProfile.query.filter_by(user_id=user_id).first_or_404()
        is_doctor_view = True
    else:
        # Regular users can only see their own dashboard
        if current_user.profile.id != user_id:
            return "Unauthorized", 403
        user_profile = UserProfile.query.get_or_404(user_id)
        is_doctor_view = False

    latest_plan = DietPlan.query.filter_by(user_id=user_profile.id).order_by(DietPlan.created_at.desc()).first()
    dosha_info = get_dosha_description(user_profile.primary_dosha)
    
    return render_template(
        "dashboard.html",
        user=user_profile.to_dict(),
        plan=latest_plan.to_dict() if latest_plan else None,
        dosha_info=dosha_info,
        is_doctor_view=is_doctor_view
    )


# ──────────────────────────────────────────────
# API: GET PROFILE
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# API: UPDATE PROFILE (regenerate plan)
# ──────────────────────────────────────────────

@main.route("/api/profile/<int:user_id>", methods=["PUT"])
@login_required
def update_profile(user_id):
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
    if "cuisine_preference" in data:          # <-- NEW
        profile.cuisine_preference = data["cuisine_preference"]
    if "answers" in data:
        profile.questionnaire_answers = json.dumps(data["answers"])
        profile.primary_dosha = calculate_dosha(data["answers"])

    profile.updated_at = datetime.utcnow()

    # Regenerate plan
    try:
        plan_data = generate_diet_plan(profile.to_dict())
        # Enrich with recipes synchronously for update (or you could also do async)
        plan_data = enrich_meal_plan_with_recipes(plan_data, profile.primary_dosha)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Diet plan generation failed: {str(e)}"}), 500

    # Save new diet plan (complete with recipes)
    new_plan = DietPlan(
        user_id=profile.id,
        plan_data=json.dumps(plan_data),
        dosha_at_generation=profile.primary_dosha,
        recipe_status="complete"
    )
    db.session.add(new_plan)
    db.session.commit()

    return jsonify({
        "user": profile.to_dict(),
        "plan": new_plan.to_dict(),
        "dosha_info": get_dosha_description(profile.primary_dosha),
    })


# ──────────────────────────────────────────────
# LANDING PAGE
# ──────────────────────────────────────────────

@main.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.profile and current_user.profile.age > 0:
            return redirect(url_for("main.dashboard", user_id=current_user.profile.id))
        else:
            return redirect(url_for("main.profile_new"))
    return render_template("landing.html")


# ──────────────────────────────────────────────
# CHATBOT
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


# ──────────────────────────────────────────────
# GUIDE PAGE
# ──────────────────────────────────────────────

@main.route("/guide")
def guide():
    return render_template("guide.html")

# ──────────────────────────────────────────────
# SWAP FUNCTION
# ──────────────────────────────────────────────
@main.route("/api/swap-meal", methods=["POST"])
@login_required
def swap_meal():
    data = request.get_json()
    user_id = data.get("user_id")
    day_index = data.get("day_index")      # 0-6
    meal_type = data.get("meal_type")      # breakfast/lunch/dinner
    custom_request = data.get("custom_request", "")

    # Get user profile and latest plan
    profile = UserProfile.query.get_or_404(user_id)
    if profile.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    latest_plan = DietPlan.query.filter_by(user_id=profile.id).order_by(DietPlan.created_at.desc()).first()
    if not latest_plan:
        return jsonify({"error": "No diet plan found"}), 404

    plan_dict = json.loads(latest_plan.plan_data)
    days = plan_dict.get("days", [])
    if day_index >= len(days) or meal_type not in days[day_index]:
        return jsonify({"error": "Invalid day or meal type"}), 400

    # Generate alternative meal
    from app.ai_service import generate_alternative_meal
    try:
        new_meal = generate_alternative_meal(profile.to_dict(), meal_type, custom_request)
    except Exception as e:
        return jsonify({"error": f"AI generation failed: {str(e)}"}), 500

    # Enrich with recipe data (synchronous, single meal)
    from app.meal_service import search_meal_by_name, generate_fallback_recipe
    recipe = search_meal_by_name(new_meal.get("name", ""))
    if recipe:
        new_meal["recipe"] = recipe
        new_meal["has_recipe"] = True
    else:
        fallback = generate_fallback_recipe(new_meal.get("name", ""), profile.primary_dosha)
        new_meal["recipe"] = fallback
        new_meal["has_recipe"] = True

    # Replace the meal in plan
    days[day_index][meal_type] = new_meal
    plan_dict["days"] = days

    # Save as a new DietPlan entry (keeping history)
    new_plan = DietPlan(
        user_id=profile.id,
        plan_data=json.dumps(plan_dict),
        dosha_at_generation=profile.primary_dosha,
        recipe_status="complete"
    )
    db.session.add(new_plan)
    db.session.commit()

    return jsonify({
        "success": True,
        "meal": new_meal,
        "plan_id": new_plan.id
    })

# ──────────────────────────────────────────────
# Doctor
# ──────────────────────────────────────────────

from flask import flash, redirect, url_for, render_template_string

# Secret key for doctor signup (store in .env)
DOCTOR_SECRET_KEY = os.environ.get("DOCTOR_SECRET_KEY", "supersecret123")

@main.route("/doctor/signup", methods=["GET", "POST"])
def doctor_signup():
    if request.method == "GET":
        return render_template("doctor_signup.html")
    
    data = request.get_json() or request.form
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    secret = data.get("secret")
    
    if secret != DOCTOR_SECRET_KEY:
        return jsonify({"error": "Invalid secret key"}), 403
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400
    
    user = User(email=email, role="doctor")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Create a minimal profile (doctors don't need full profile but for consistency)
    profile = UserProfile(
        user_id=user.id,
        name=name,
        age=0,
        weight=0.0,
        dietary_preference="veg",
        questionnaire_answers="{}",
        primary_dosha="Vata"
    )
    db.session.add(profile)
    db.session.commit()
    
    login_user(user)
    return jsonify({"redirect": url_for("main.doctor_dashboard")}), 201

@main.route("/doctor/dashboard")
@login_required
def doctor_dashboard():
    if current_user.role != "doctor":
        flash("Access denied.", "error")
        return redirect(url_for("main.index"))
    
    # Get all patients (users with role='patient' and have completed profile)
    patients = User.query.filter_by(role="patient").all()
    # Only include those with age > 0 (completed intake)
    patients_with_profiles = [u for u in patients if u.profile and u.profile.age > 0]
    
    return render_template("doctor_dashboard.html", patients=patients_with_profiles)

@main.route("/api/doctor/patient/<int:user_id>")
@login_required
def doctor_view_patient(user_id):
    if current_user.role != "doctor":
        return jsonify({"error": "Unauthorized"}), 403
    
    patient = User.query.get_or_404(user_id)
    if patient.role != "patient":
        return jsonify({"error": "Not a patient"}), 400
    
    profile = patient.profile
    latest_plan = DietPlan.query.filter_by(user_id=profile.id).order_by(DietPlan.created_at.desc()).first()
    
    return jsonify({
        "user": {
            "id": patient.id,
            "email": patient.email,
            "created_at": patient.created_at.isoformat()
        },
        "profile": profile.to_dict(),
        "plan": latest_plan.to_dict() if latest_plan else None,
        "dosha_info": get_dosha_description(profile.primary_dosha)
    })