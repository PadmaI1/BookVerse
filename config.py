# config.py

import os

from dotenv import load_dotenv
load_dotenv()

class Config:

# WTF config
    SECRET_KEY = os.getenv("SECRET_KEY")

# ✅ DATABASE CONFIG
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = bool(os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS"))