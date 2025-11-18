# config.py
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- OANDA Configuration ---
OANDA_API_TOKEN = os.getenv("OANDA_API_TOKEN")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice") # Default to 'practice' if not set

# --- Validation ---
if not OANDA_API_TOKEN or not OANDA_ACCOUNT_ID:
    raise ValueError(
        "OANDA_API_TOKEN and OANDA_ACCOUNT_ID must be set in your .env file. "
        "Please copy .env.example to .env and fill in your credentials."
    )

print("Configuration loaded successfully.")
print(f"OANDA Environment: {OANDA_ENVIRONMENT}")

