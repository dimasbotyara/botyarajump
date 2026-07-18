"""
botyarajump - Main Entry Point
Launch the game from here.
"""

import sys
import os

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Generate default story levels before game starts
from story_mode import generate_default_levels
generate_default_levels()

# Import and run
from game import Game


def main():
    """Main entry point."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()