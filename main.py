import os
import sys

# Ensure local workspace modules are prioritized
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

# Load variables from .env file relative to this script
load_dotenv(os.path.join(project_root, '.env'))

from main.menu import run_app

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)
