from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import UserProfile, DietPlan
from app.dosha import calculate_dosha, get_dosha_description, DOSHA_QUESTIONS
from app.ai_service import generate_diet_plan, chat_response
from datetime import datetime
import json

main = Blueprint("main", __name__)


# ──────────────────────────────────────────────
# PAGE ROUTES
# ──────────────────────────────────────────────

@main.route("/")
def index():
    return render_template("index.html", questions=DOSHA_QUESTIONS)


@main.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    user = UserProfile.query.get_or_404(user_id)
    latest_plan = (
        DietPlan.query.filter_by(user_id=user_id)
        .order_by(DietPlan.created_at.desc())
        .first()
    )
    dosha_info = get_dosha_description(user.primary_dosha)
    return render_template(
        "dashboard.html",
        user=user.to_dict(),
        plan=latest_plan.to_dict() if latest_plan else None,
        dosha_info=dosha_info,
    )


# ──────────────────────────────────────────────
# API: USER PROFILE
# ──────────────────────────────────────────────

@main.route("/api/questions", methods=["GET"])
def get_questions():
    return jsonify({"questions": DOSHA_QUESTIONS})


@main.route("/api/profile", methods=["POST"])
def create_profile():
    """Create a new user profile, calculate dosha, generate diet plan, save all."""
    data = request.get_json()

    # Validate required fields
    required = ["name", "age", "weight", "dietary_preference", "answers"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Calculate dosha
    dosha = calculate_dosha(data["answers"])

    # Create user profile
    user = UserProfile(
        name=data["name"],
        age=int(data["age"]),
        weight=float(data["weight"]),
        dietary_preference=data["dietary_preference"],
        questionnaire_answers=json.dumps(data["answers"]),
        primary_dosha=dosha,
    )
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    # Generate diet plan via AI
    try:
        plan_data = generate_diet_plan(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Diet plan generation failed: {str(e)}"}), 500

    # Save diet plan
    diet_plan = DietPlan(
        user_id=user.id,
        plan_data=json.dumps(plan_data),
        dosha_at_generation=dosha,
    )
    db.session.add(diet_plan)
    db.session.commit()

    return jsonify({
        "user": user.to_dict(),
        "plan": diet_plan.to_dict(),
        "dosha_info": get_dosha_description(dosha),
        "redirect": f"/dashboard/{user.id}",
    }), 201


@main.route("/api/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    user = UserProfile.query.get_or_404(user_id)
    latest_plan = (
        DietPlan.query.filter_by(user_id=user_id)
        .order_by(DietPlan.created_at.desc())
        .first()
    )
    return jsonify({
        "user": user.to_dict(),
        "plan": latest_plan.to_dict() if latest_plan else None,
        "dosha_info": get_dosha_description(user.primary_dosha),
    })


@main.route("/api/profile/<int:user_id>", methods=["PUT"])
def update_profile(user_id):
    """Update profile, recalculate dosha, regenerate and overwrite diet plan."""
    user = UserProfile.query.get_or_404(user_id)
    data = request.get_json()

    if "name" in data:
        user.name = data["name"]
    if "age" in data:
        user.age = int(data["age"])
    if "weight" in data:
        user.weight = float(data["weight"])
    if "dietary_preference" in data:
        user.dietary_preference = data["dietary_preference"]
    if "answers" in data:
        user.questionnaire_answers = json.dumps(data["answers"])
        user.primary_dosha = calculate_dosha(data["answers"])

    user.updated_at = datetime.utcnow()

    # Regenerate plan
    try:
        plan_data = generate_diet_plan(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Diet plan generation failed: {str(e)}"}), 500

    new_plan = DietPlan(
        user_id=user.id,
        plan_data=json.dumps(plan_data),
        dosha_at_generation=user.primary_dosha,
    )
    db.session.add(new_plan)
    db.session.commit()

    return jsonify({
        "user": user.to_dict(),
        "plan": new_plan.to_dict(),
        "dosha_info": get_dosha_description(user.primary_dosha),
    })


# ──────────────────────────────────────────────
# API: CHATBOT
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
