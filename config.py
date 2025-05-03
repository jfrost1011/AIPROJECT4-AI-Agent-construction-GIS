import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Verify keys loaded successfully
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY. Check your .env file.")
if not TAVILY_API_KEY:
    raise ValueError("Missing TAVILY_API_KEY. Check your .env file.") 