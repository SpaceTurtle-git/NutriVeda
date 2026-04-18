"""
AI Service — handles all Groq API interactions:
  1. generate_diet_plan()  → 7-day Ayurvedic meal plan (JSON)
  2. chat_response()       → Conversational Ayurvedic health chatbot
"""

import json
import re
from groq import Groq
from flask import current_app

def _get_client() -> Groq:
    """Return Groq client using the API key from Flask config."""
    return Groq(api_key=current_app.config["GROQ_API_KEY"])

# ----------------------------------------------------------------------
# 1. DIET PLAN GENERATION (unchanged, works)
# ----------------------------------------------------------------------
def generate_diet_plan(user_profile: dict) -> dict:
    client = _get_client()
    dosha = user_profile["primary_dosha"]
    name = user_profile["name"]
    age = user_profile["age"]
    weight = user_profile["weight"]
    diet_pref = user_profile["dietary_preference"]

    system_prompt = """You are an expert Ayurvedic nutritionist and dietitian with 20+ years of experience.
Your task is to generate personalized 7-day Ayurvedic meal plans.
You MUST respond with ONLY valid JSON — no markdown, no code fences, no explanation, no preamble.
The JSON structure must be exactly:
{
  "dosha_summary": "2-3 sentence summary of the dosha and dietary philosophy",
  "days": [
    {
      "day": 1,
      "day_name": "Monday",
      "breakfast": {
        "name": "Meal name",
        "description": "Brief description",
        "ingredients": ["item1", "item2"],
        "benefits": "Ayurvedic benefit"
      },
      "lunch": { ... },
      "dinner": { ... },
      "daily_tip": "One Ayurvedic lifestyle tip for the day"
    }
  ]
}
All 7 days must be present. Do not repeat the same meals across days."""

    user_prompt = f"""Generate a 7-day Ayurvedic meal plan for:
- Name: {name}
- Age: {age} years
- Weight: {weight} kg
- Dietary Preference: {diet_pref} ({"includes meat, fish, eggs" if diet_pref == "non-veg" else "strictly vegetarian, no meat/fish/eggs"})
- Primary Dosha: {dosha}

Tailor every meal to balance the {dosha} dosha. Use traditional Ayurvedic ingredients and cooking methods.
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
        raise ValueError(f"Failed to parse diet plan JSON from AI: {e}\nRaw response: {raw[:500]}")
    return plan

# ----------------------------------------------------------------------
# 2. CHATBOT (fixed)
# ----------------------------------------------------------------------
def chat_response(messages, user_context=None):
    """
    Get a response from the Groq API for the chatbot.
    Returns a string reply.
    """
    try:
        client = _get_client()

        # Build system message – use a proper Ayurvedic guide name
        system_message = (
            "You are KimJongGoon, the divine Ayurvedic physician. "
            "You are warm, wise, and concise. Provide practical Ayurvedic advice "
            "about diet, lifestyle, herbs, and daily routines. "
            "Keep responses to 3-5 sentences unless more detail is asked. "
            "If asked about serious medical conditions, advise consulting a doctor."
        )

        if user_context:
            # user_context is typically a dict with dosha, name, etc.
            if isinstance(user_context, dict):
                dosha = user_context.get("primary_dosha", "unknown")
                name = user_context.get("name", "dear user")
                system_message += f" You are currently speaking with {name}, who has a {dosha} dosha constitution. Tailor your advice accordingly."
            else:
                system_message += f" User context: {user_context}"

        # Format messages – the incoming `messages` should be a list of {role, content}
        formatted_messages = [{"role": "system", "content": system_message}] + messages

        # Make API call
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
        # Print the actual error to the Flask log (visible in terminal)
        print(f"ERROR in chat_response: {type(e).__name__}: {str(e)}")
        # Re-raise with a clear message
        raise Exception(f"Chat API error: {str(e)}")