# config.py
import os
from dotenv import load_dotenv

load_dotenv()

def validate_env():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Missing required environment variable: OPENAI_API_KEY")
