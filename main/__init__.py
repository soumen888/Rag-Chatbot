# main package initialization
from .menu import run_app
import sys

def main():
    try:
        run_app()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)
