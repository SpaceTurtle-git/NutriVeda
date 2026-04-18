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
    return Groq(api_key=current_app.config["GROQ_API_KEY"])


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
      "lunch": {
        "name": "Meal name",
        "description": "Brief description",
        "ingredients": ["item1", "item2"],
        "benefits": "Ayurvedic benefit"
      },
      "dinner": {
        "name": "Meal name",
        "description": "Brief description",
        "ingredients": ["item1", "item2"],
        "benefits": "Ayurvedic benefit"
      },
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

    # Strip any accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse diet plan JSON from AI: {e}\nRaw response: {raw[:500]}")

    return plan


# ──────────────────────────────────────────────
# 2. CHATBOT
# ──────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are KimJungGoon, a warm, knowledgeable Ayurvedic health assistant.
You help users understand their dosha, Ayurvedic diet principles, herbs, lifestyle practices, and wellness.
Keep responses concise (3-5 sentences unless more detail is asked for), friendly, and practical.
Always ground advice in Ayurvedic principles. If asked about serious medical conditions, 
remind the user to consult a qualified healthcare professional.
Never recommend specific medications or dosages."""


# app/ai_service.py
import os
from groq import Groq
from flask import current_app, g

# ... (keep your existing generate_diet_plan function as is) ...

def chat_response(messages, user_context=None):
    """
    Get a response from the Groq API for the chatbot.
    """
    try:
        # Initialize the Groq client with the API key from the app's config
        # 'current_app' is used to access the Flask app context
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])

        # Prepare the system message with user context if provided
        system_message = "You are KimJongGoon, an expert Ayurvedic guide. You are helpful, wise, and concise in your responses."
        if user_context:
            # You can customize how the user's dosha is incorporated here
            system_message += f" The user you are speaking with has the following Ayurvedic profile: {user_context}. Tailor your advice accordingly."

        # Format messages for the Groq API
        formatted_messages = [
            {"role": "system", "content": system_message},
            *messages  # This includes the conversation history
        ]

        # Make the API call to Groq
        # Make sure the model name is the updated one you're using
        chat_completion = client.chat.completions.create(
            messages=formatted_messages,
            model="llama-3.3-70b-versatile",  # Or your chosen model
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stop=None,
        )

        # Extract and return the reply text
        reply = chat_completion.choices[0].message.content
        return reply

    except Exception as e:
        # Log the error for debugging
        print(f"Error in chat_response: {e}")
        # Re-raise the exception so the route can handle it
        raise Exception(f"Chat API error: {str(e)}")
