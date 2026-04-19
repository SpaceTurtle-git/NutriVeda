# app/ai_service.py

import json
import re
import os
from groq import Groq
from flask import current_app
from pathlib import Path

# ──────────────────────────────────────────────
# Load meal names from JSON file (cached)
# ──────────────────────────────────────────────
_MEAL_NAMES_LIST = None

def get_meal_names_list(max_names=200):
    """Load meal names from root directory and return a list of unique names."""
    global _MEAL_NAMES_LIST
    if _MEAL_NAMES_LIST is None:
        # Look for meal_names.json in the project root (one level above app/)
        root_dir = Path(__file__).parent.parent
        json_path = root_dir / "meal_names.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_names = data.get("meal_names", [])
                # Remove duplicates (already unique) and limit
                _MEAL_NAMES_LIST = sorted(set(all_names))[:max_names]
        else:
            # Fallback to a small default list
            _MEAL_NAMES_LIST = [
                "Chicken Curry", "Vegetable Soup", "Spaghetti Arrabiata",
                "Beef Stew", "Oatmeal with Berries", "Scrambled Eggs",
                "Greek Salad", "Lentil Soup", "Pancakes", "Omelette"
            ]
    return _MEAL_NAMES_LIST


# ──────────────────────────────────────────────
# 1. DIET PLAN GENERATION
# ──────────────────────────────────────────────

def generate_diet_plan(user_profile: dict) -> dict:
    """
    Constructs a detailed prompt and calls Groq to generate a
    7-day Ayurvedic meal plan in strict JSON format.

    Returns a dict with keys: days (list of 7 day objects).
    Raises ValueError on parse failure.
    """
    client = _get_client()

    dosha = user_profile["primary_dosha"]
    name = user_profile["name"]
    age = user_profile["age"]
    weight = user_profile["weight"]
    diet_pref = user_profile["dietary_preference"]

    # Get list of valid meal names from JSON
    meal_names_list = get_meal_names_list(max_names=200)
    meal_names_str = ", ".join(meal_names_list)

    system_prompt = f"""You are an expert Ayurvedic nutritionist.
Your task is to generate a 7-day meal plan using ONLY real dish names that exist in TheMealDB database.
Here is a list of valid meal names you MUST choose from (do not use any other names):
{meal_names_str}

DO NOT use generic names like "Warm Porridge", "Grounding Dinner", "Spiced Tea", "Digestive Lassi".
Each meal name must be exactly as shown in the list above.
Output ONLY valid JSON as specified. No markdown, no extra text.
The JSON structure must be exactly:
{{
  "dosha_summary": "2-3 sentence summary of the dosha and dietary philosophy",
  "days": [
    {{
      "day": 1,
      "day_name": "Monday",
      "breakfast": {{
        "name": "Meal name from list",
        "description": "Brief Ayurvedic description",
        "ingredients": ["item1", "item2"],
        "benefits": "Ayurvedic benefit"
      }},
      "lunch": {{ ... }},
      "dinner": {{ ... }},
      "daily_tip": "One Ayurvedic lifestyle tip for the day"
    }}
  ]
}}
All 7 days must be present. Do not repeat the same meals across days."""

    user_prompt = f"""Generate a 7-day Ayurvedic meal plan for:
- Name: {name}
- Age: {age} years
- Weight: {weight} kg
- Dietary Preference: {diet_pref} ({"includes meat, fish, eggs" if diet_pref == "non-veg" else "strictly vegetarian, no meat/fish/eggs"})
- Primary Dosha: {dosha}

Tailor every meal to balance the {dosha} dosha. Use ONLY meal names from the provided list.
For Non-Veg preference, include appropriate lean meats/fish in lunch/dinner on some days.
Include herbal teas, spices, and cooking techniques that pacify {dosha}.
Remember: respond with ONLY the JSON object."""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
    )

    raw = completion.choices[0].message.content.strip()

    # Strip any accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse diet plan JSON from AI: {e}\nRaw response: {raw[:500]}")

    return plan


# ──────────────────────────────────────────────
# 2. CHATBOT (unchanged)
# ──────────────────────────────────────────────

def _get_client() -> Groq:
    return Groq(api_key=current_app.config["GROQ_API_KEY"])

def chat_response(messages, user_context=None):
    """
    Get a response from the Groq API for the chatbot.
    """
    try:
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])

        system_message = "You are KimJongGoon, an expert Ayurvedic guide. You are helpful, wise, and concise in your responses."
        if user_context:
            system_message += f" The user you are speaking with has the following Ayurvedic profile: {user_context}. Tailor your advice accordingly."

        formatted_messages = [
            {"role": "system", "content": system_message},
            *messages
        ]

        chat_completion = client.chat.completions.create(
            messages=formatted_messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stop=None,
        )

        reply = chat_completion.choices[0].message.content
        return reply

    except Exception as e:
        print(f"Error in chat_response: {e}")
        raise Exception(f"Chat API error: {str(e)}")