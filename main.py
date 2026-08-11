import os
import sys
from dotenv import load_dotenv

# Load variables from .env file relative to this script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from main.menu import run_app

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)
