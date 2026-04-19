# fetch_meals.py
import requests
import json
import time
import string
from typing import Dict, Set

def fetch_all_meal_names() -> Set[str]:
    """Fetch all meal names from TheMealDB by iterating through the alphabet."""
    base_url = "https://www.themealdb.com/api/json/v1/1/search.php?f="
    all_meal_names = set()
    letter_count = 0

    print("🌐 Fetching meal names from TheMealDB API...")
    for letter in string.ascii_lowercase:
        try:
            response = requests.get(base_url + letter, timeout=10)
            response.raise_for_status()
            data = response.json()
            meals = data.get("meals")
            if meals:
                for meal in meals:
                    meal_name = meal.get("strMeal")
                    if meal_name:
                        all_meal_names.add(meal_name)
                print(f"✅ Letter '{letter}': found {len(meals)} meals.")
            else:
                print(f"⚠️ Letter '{letter}': no meals found.")
            letter_count += 1
            # Be respectful to the API
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Error fetching for letter '{letter}': {e}")

    print(f"\n🎉 Finished! Fetched a total of {len(all_meal_names)} unique meal names.")
    return all_meal_names

def save_meal_names_to_json(meal_names: Set[str], filename: str = "meal_names.json"):
    """Save the set of meal names to a JSON file."""
    data = {"meal_names": sorted(list(meal_names)), "total_count": len(meal_names)}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Meal names saved to '{filename}'.")

if __name__ == "__main__":
    print("🚀 Starting TheMealDB data fetcher...")
    all_meals = fetch_all_meal_names()
    if all_meals:
        save_meal_names_to_json(all_meals)
        print("✨ Done! You can now use 'meal_names.json' in your app.")
    else:
        print("❌ No meals were fetched. Please check your internet connection.")