# app/meal_service.py

import requests
import logging
import re
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1/"

def clean_meal_name(name: str) -> str:
    """Remove common filler words and return cleaned name."""
    if not name:
        return ""
    stop_words = ['and', 'with', 'of', 'in', 'for', 'the', 'a', 'an', 'from', 'to']
    # Also remove Ayurvedic descriptors
    remove_terms = ['warm', 'grounding', 'light', 'spiced', 'healing', 'digestive', 'ayurvedic']
    words = name.lower().split()
    filtered = [w for w in words if w not in stop_words and w not in remove_terms]
    return ' '.join(filtered) if filtered else name

def search_meal_by_name(meal_name: str) -> Optional[Dict]:
    """Search TheMealDB and return the best match (exact match preferred)."""
    if not meal_name:
        return None

    # First try exact match (case‑insensitive)
    search_term = meal_name.replace(' ', '_')
    url = f"{MEALDB_BASE_URL}search.php?s={search_term}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        meals = data.get("meals")
        if meals:
            # Look for exact name match (case‑insensitive)
            for meal in meals:
                if meal["strMeal"].lower() == meal_name.lower():
                    return meal
            # Otherwise return the first result
            return meals[0]
    except Exception as e:
        logger.warning(f"Exact search failed for '{meal_name}': {e}")

    # Fallback: try cleaned name
    cleaned = clean_meal_name(meal_name)
    if cleaned and cleaned != meal_name:
        return search_meal_by_name(cleaned)

    return None

def generate_fallback_recipe(meal_name: str, dosha: str = None) -> Dict:
    """Create a fallback recipe structure when TheMealDB has no match."""
    return {
        "idMeal": "fallback",
        "strMeal": meal_name,
        "strCategory": "Ayurvedic",
        "strArea": "Traditional",
        "strInstructions": f"To prepare {meal_name}, heat ghee, add cumin, coriander, turmeric. Add fresh vegetables or protein as preferred. Cook gently, season with salt and herbs. Serve warm with rice or bread.",
        "strMealThumb": "",
        "strYoutube": "",
        "strIngredient1": "Ghee",
        "strMeasure1": "1 tbsp",
        "strIngredient2": "Cumin seeds",
        "strMeasure2": "1 tsp",
        "strIngredient3": "Turmeric",
        "strMeasure3": "1/2 tsp",
        "strIngredient4": meal_name.split()[0] if meal_name else "Vegetables",
        "strMeasure4": "as needed",
    }

def enrich_meal_plan_with_recipes(plan_data: Dict, dosha: str = None) -> Dict:
    """Enrich each meal with recipe data, falling back to generated Ayurvedic recipes."""
    if not plan_data or "days" not in plan_data:
        return plan_data

    for day in plan_data["days"]:
        for meal_type in ["breakfast", "lunch", "dinner"]:
            meal = day.get(meal_type)
            if not meal or not isinstance(meal, dict):
                continue

            meal_name = meal.get("name")
            if not meal_name:
                continue

            recipe = search_meal_by_name(meal_name)
            if recipe:
                meal["recipe"] = recipe
                meal["has_recipe"] = True
            else:
                fallback = generate_fallback_recipe(meal_name, dosha)
                meal["recipe"] = fallback
                meal["has_recipe"] = True
                meal["recipe_message"] = f"Full recipe for '{meal_name}' not found in TheMealDB. Here is a general Ayurvedic guide."

    return plan_data