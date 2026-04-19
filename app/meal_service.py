# app/meal_service.py

import requests
import logging
import re
from typing import Dict, List, Optional
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1/"

#MEAL LOOKUP
# Load the local meal database once when the service starts
MEAL_NAMES_DB = None
def load_meal_names_db():
    global MEAL_NAMES_DB
    if MEAL_NAMES_DB is None:
        db_path = Path(__file__).parent.parent / "meal_names.json"
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            MEAL_NAMES_DB = set(data.get("meal_names", []))
    return MEAL_NAMES_DB

def is_valid_meal_name(meal_name: str) -> bool:
    """Check if a meal name exists in our local database."""
    meal_names = load_meal_names_db()
    return meal_name in meal_names


def clean_meal_name(name: str) -> str:
    """Remove common filler words and keep the main noun phrase."""
    # Convert to lowercase and remove special characters
    name = name.lower()
    # Remove words like 'and', 'with', 'of', 'in', 'for', 'the'
    stop_words = ['and', 'with', 'of', 'in', 'for', 'the', 'a', 'an', 'from', 'to']
    words = name.split()
    filtered = [w for w in words if w not in stop_words]
    # Also remove common Ayurvedic descriptors that aren't in meal names
    remove_terms = ['warm', 'grounding', 'light', 'spiced', 'healing', 'digestive', 'ayurvedic']
    filtered = [w for w in filtered if w not in remove_terms]
    return ' '.join(filtered) if filtered else name

def search_meal_by_name(meal_name: str) -> Optional[Dict]:
    """
    Search TheMealDB with progressive fallback strategies.
    Returns the best matching meal dict or None.
    """
    if not meal_name:
        return None

    # Strategy 1: Use cleaned name
    cleaned = clean_meal_name(meal_name)
    candidates = [cleaned]

    # Strategy 2: Use first two words (often the core dish)
    words = cleaned.split()
    if len(words) >= 2:
        candidates.append(' '.join(words[:2]))
    # Strategy 3: Use first word only
    if len(words) >= 1:
        candidates.append(words[0])
    # Strategy 4: Original name (fallback)
    candidates.append(meal_name)

    # Remove duplicates and empty strings
    candidates = list(dict.fromkeys([c for c in candidates if c]))

    for search_term in candidates:
        try:
            url = f"{MEALDB_BASE_URL}search.php?s={search_term}"
            logger.info(f"Searching MealDB for: {search_term}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("meals") and len(data["meals"]) > 0:
                # Return the first match
                return data["meals"][0]
        except Exception as e:
            logger.warning(f"Search failed for '{search_term}': {e}")
            continue

    logger.warning(f"No recipe found for: {meal_name}")
    return None

def generate_fallback_recipe(meal_name: str, dosha: str = None) -> Dict:
    """
    Create a fallback recipe structure when TheMealDB has no match.
    """
    # Basic template
    return {
        "idMeal": "fallback",
        "strMeal": meal_name,
        "strCategory": "Ayurvedic",
        "strArea": "Indian",
        "strInstructions": f"This is a traditional Ayurvedic recipe for {meal_name}. To prepare, use fresh, organic ingredients appropriate for your dosha. Common preparation: heat ghee, add spices like cumin, coriander, turmeric, then add main ingredients, cook slowly. Serve warm with herbal tea.",
        "strMealThumb": "https://www.themealdb.com/images/category/ayurvedic-placeholder.png",  # optional placeholder
        "strYoutube": "",
        "strIngredient1": "Ghee",
        "strMeasure1": "1 tsp",
        "strIngredient2": "Cumin seeds",
        "strMeasure2": "1/2 tsp",
        "strIngredient3": "Turmeric",
        "strMeasure3": "1/4 tsp",
        "strIngredient4": meal_name.split()[0] if meal_name else "Vegetables",
        "strMeasure4": "as needed",
    }

def enrich_meal_plan_with_recipes(plan_data: Dict, dosha: str = None) -> Dict:
    """
    Enrich each meal with recipe data, falling back to generated Ayurvedic recipes.
    """
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

            # Try to get real recipe
            recipe_data = search_meal_by_name(meal_name)

            if recipe_data:
                meal["recipe"] = recipe_data
                meal["has_recipe"] = True
                meal["recipe_message"] = f"Recipe for '{meal_name}' fetched from TheMealDB."
            else:
                # Fallback: generate a simple Ayurvedic recipe
                fallback = generate_fallback_recipe(meal_name, dosha)
                meal["recipe"] = fallback
                meal["has_recipe"] = True   # still show button
                meal["recipe_message"] = f"Full recipe for '{meal_name}' is not available in TheMealDB. Here is a general Ayurvedic preparation guide."

    return plan_data