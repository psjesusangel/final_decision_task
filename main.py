"""
main.py

Entry point for the Effort-Based Decision Task experiment
"""

from utils import setup_logging
from gui import ExperimentApp


def main():
    setup_logging()
    app = ExperimentApp()
    app.mainloop()


if __name__ == "__main__":
    main()  # TODO: add CLI arguments for test mode or domain selection
