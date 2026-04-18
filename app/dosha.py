"""
Dosha calculation logic.
Each question maps answers to dosha scores.
The dosha with the highest total score wins.
"""

# Question definitions sent to the frontend
DOSHA_QUESTIONS = [
    {
        "id": "q1",
        "text": "How would you describe your body frame and weight?",
        "options": [
            {"value": "a", "label": "Thin, light, hard to gain weight", "dosha": "vata"},
            {"value": "b", "label": "Medium, muscular, gain/lose weight easily", "dosha": "pitta"},
            {"value": "c", "label": "Large, sturdy, tend to gain weight easily", "dosha": "kapha"},
        ],
    },
    {
        "id": "q2",
        "text": "How would you describe your energy and activity levels?",
        "options": [
            {"value": "a", "label": "Bursts of energy, tire quickly, always moving", "dosha": "vata"},
            {"value": "b", "label": "Intense, focused, driven — rarely stop until done", "dosha": "pitta"},
            {"value": "c", "label": "Steady, slow to start but excellent endurance", "dosha": "kapha"},
        ],
    },
    {
        "id": "q3",
        "text": "How do you typically react to stress?",
        "options": [
            {"value": "a", "label": "Anxiety, worry, overwhelm — mind races", "dosha": "vata"},
            {"value": "b", "label": "Irritability, frustration, become critical", "dosha": "pitta"},
            {"value": "c", "label": "Withdraw, become quiet, prefer to sleep it off", "dosha": "kapha"},
        ],
    },
]


def calculate_dosha(answers: dict) -> str:
    """
    Takes a dict of {question_id: answer_value} and returns
    the primary dosha as a capitalized string: 'Vata', 'Pitta', or 'Kapha'.
    """
    scores = {"vata": 0, "pitta": 0, "kapha": 0}

    for question in DOSHA_QUESTIONS:
        qid = question["id"]
        selected_value = answers.get(qid)
        if not selected_value:
            continue
        for option in question["options"]:
            if option["value"] == selected_value:
                scores[option["dosha"]] += 1
                break

    # Return the dosha with the highest score; default to Vata on tie
    primary = max(scores, key=lambda d: (scores[d], ["vata", "pitta", "kapha"].index(d) * -1))
    return primary.capitalize()


def get_dosha_description(dosha: str) -> dict:
    """Returns a short description and key dietary traits for the dosha."""
    descriptions = {
        "Vata": {
            "element": "Air & Space",
            "traits": "Creative, energetic, quick-thinking",
            "dietary_focus": "Warm, moist, grounding foods",
            "avoid": "Cold, raw, dry foods",
            "color": "#E8935A",
        },
        "Pitta": {
            "element": "Fire & Water",
            "traits": "Focused, ambitious, intelligent",
            "dietary_focus": "Cooling, refreshing, moderately spiced foods",
            "avoid": "Hot, spicy, oily, fermented foods",
            "color": "#E85A5A",
        },
        "Kapha": {
            "element": "Earth & Water",
            "traits": "Calm, loyal, nurturing",
            "dietary_focus": "Light, dry, warming, spiced foods",
            "avoid": "Heavy, oily, sweet, cold foods",
            "color": "#5A9BE8",
        },
    }
    return descriptions.get(dosha, descriptions["Vata"])
