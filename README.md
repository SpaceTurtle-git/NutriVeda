# 🌿 NutriVeda

NutriVeda is an Ayurvedic diet web application designed to help users discover their primary dosha (Vata, Pitta, or Kapha) and generate highly personalized 7-day meal plans.

By combining the ancient wisdom of Ayurveda with modern AI, NutriVeda delivers an interactive, intelligent, and visually striking experience.

---

## ✨ Features

- 🧘‍♂️ Dosha Assessment Quiz  
  A streamlined 9-question quiz to accurately determine the user's dominant dosha.

- 🧠 AI-Powered Diet Plans  
  Uses Groq's LLM to generate customized 7-day meal plans tailored to individual dosha and nutritional needs.

- 🍲 Real Recipe Integration  
  Fetches real recipes asynchronously via TheMealDB API, including:
  - Ingredients  
  - Step-by-step instructions  
  - Embedded YouTube tutorials  

- 🤖 Dosha-Aware Chatbot  
  A context-aware chatbot offering personalized Ayurvedic advice.

- 🔐 User Authentication & Profiles  
  Secure signup, login, and profile management.

- 📄 PDF Export  
  Download meal plans for offline access.

- 📖 Ayurveda Guide  
  Learn the fundamentals of Ayurvedic nutrition and lifestyle.

- 🎨 Neo-Brutalist UI  
  Bold, modern design using Vanilla JS and CSS with smooth animations.

---

## 🛠️ Tech Stack

Backend: Python, Flask  
Database: SQLite  
Frontend: HTML5, CSS3 (Neo-Brutalist), Vanilla JavaScript  
AI / LLM: Groq API  
External APIs: TheMealDB API  

---

## 🚀 Getting Started

Follow these steps to run NutriVeda locally:

### ✅ Prerequisites

- Python 3.x  
- Groq API Key  

---

### 📦 Installation

# Navigate to project directory
cd NutriVeda

# Create virtual environment
python3 -m venv venv

---

### Activate Virtual Environment

Mac/Linux:
source venv/bin/activate

Windows:
venv\Scripts\activate

---

### 📥 Install Dependencies

pip install -r requirements.txt  
pip install --upgrade groq  

---

### 🔐 Environment Variables

Create a `.env` file in the root directory and add:

GROQ_API_KEY=your_api_key_here

---

### ▶️ Run the Application

python run.py

---

### 🌐 Access the App

Open your browser and go to:
http://127.0.0.1:5000

---

## 💡 How It Works

1. Sign Up / Log In  
   Create an account to save your profile.

2. Take the Quiz  
   Answer 9 questions to determine your Ayurvedic dosha.

3. Generate Your Plan  
   AI creates a 7-day personalized meal plan using Groq.

4. Explore Recipes  
   View detailed recipes with instructions and video tutorials.

5. Chat & Learn  
   Interact with the dosha-aware chatbot for tailored advice.

6. Export  
   Download your meal plan as a PDF.

