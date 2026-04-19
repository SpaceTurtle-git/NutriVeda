# app/ai_service.py

import json
import re
from groq import Groq
from flask import current_app
from pathlib import Path

_MEAL_NAMES_LIST = None

def filter_indian_meals(meal_names):
    """Return only meal names that appear to be Indian cuisine."""
    indian_keywords = [
        'biryani', 'masala', 'paneer', 'tikka', 'curry', 'korma', 'sambar',
        'dosa', 'idli', 'vada', 'chana', 'dal', 'roti', 'naan', 'pakora',
        'samosa', 'aloo', 'gobi', 'palak', 'saag', 'khichdi', 'pulao',
        'lassi', 'chutney', 'raita', 'tandoori', 'bhaji', 'baingan',
        'mutter', 'paneer', 'chole', 'rajma', 'upma', 'pohe', 'pongal'
    ]
    filtered = [name for name in meal_names if any(keyword in name.lower() for keyword in indian_keywords)]
    if not filtered:
        return ["Chicken Curry", "Palak Paneer", "Masala Dosa", "Dal Makhani", "Vegetable Biryani"]
    return filtered

def get_meal_names_list(max_names=200, cuisine="international"):
    """Load meal names and filter by cuisine if needed."""
    global _MEAL_NAMES_LIST
    if _MEAL_NAMES_LIST is None:
        root_dir = Path(__file__).parent.parent
        json_path = root_dir / "meal_names.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_names = data.get("meal_names", [])
                _MEAL_NAMES_LIST = sorted(set(all_names))
        else:
            _MEAL_NAMES_LIST = [
                "Chicken Curry", "Vegetable Soup", "Spaghetti Arrabiata",
                "Beef Stew", "Oatmeal with Berries", "Scrambled Eggs",
                "Greek Salad", "Lentil Soup", "Pancakes", "Omelette"
            ]
    if cuisine == "indian":
        filtered = filter_indian_meals(_MEAL_NAMES_LIST)
        return filtered[:max_names]
    return _MEAL_NAMES_LIST[:max_names]

def _get_client() -> Groq:
    return Groq(api_key=current_app.config["GROQ_API_KEY"])

def generate_diet_plan(user_profile: dict) -> dict:
    client = _get_client()

    dosha = user_profile["primary_dosha"]
    name = user_profile["name"]
    age = user_profile["age"]
    weight = user_profile["weight"]
    diet_pref = user_profile["dietary_preference"]
    cuisine_pref = user_profile.get("cuisine_preference", "international")

    # Get filtered meal names based on cuisine preference
    meal_names_list = get_meal_names_list(max_names=200, cuisine=cuisine_pref)
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
  "dosha_summary": "2-3 sentence summary...",
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
      "daily_tip": "..."
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
- Cuisine Preference: {"Indian" if cuisine_pref == "indian" else "International"}

CRITICAL RULE: 
- If Cuisine Preference is "Indian", you MUST suggest ONLY Indian dishes from the provided list. DO NOT suggest any non-Indian dishes like beef stir-fry or pasta.
- If Cuisine Preference is "International", you may suggest dishes from any cuisine (Italian, Thai, Mexican, etc.) while maintaining Ayurvedic balance.

Tailor every meal to balance the {dosha} dosha. Use ONLY the meal names from the list above.
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
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse diet plan JSON: {e}\nRaw: {raw[:500]}")

    return plan

def chat_response(messages, user_context=None):
    try:
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])
        system_message = "You are KimJongGoon, an expert Ayurvedic guide. Be helpful, wise, and concise."
        if user_context:
            system_message += f" The user's profile: {user_context}. Tailor advice accordingly."
        formatted_messages = [{"role": "system", "content": system_message}, *messages]
        chat_completion = client.chat.completions.create(
            messages=formatted_messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Chat error: {e}")
        raise Exception(f"Chat API error: {str(e)}")