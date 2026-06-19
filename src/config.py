import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "claude-haiku-4-5-20251001")
