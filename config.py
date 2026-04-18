import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    # Store DB in project root instance/ folder
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'ayurveda.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
