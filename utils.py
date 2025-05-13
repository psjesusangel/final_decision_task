"""
utils.py

Utility functions: data saving and logging setup
"""

import csv
import logging
from datetime import datetime

# Module-level logger
logger = logging.getLogger(__name__)


def setup_logging():
    """
    Configure root logger to display INFO-level messages
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

def save_data(subject, domain, valence, data):
    """
    Save experiment data to a CSV file
    """
    fname = f"{subject}_{domain}_{valence}.csv"
    header = [
        'date','time','subject','handedness','trial_num','domain','valence',
        'magnitude_hard','probability','EV','choice','choice_rt',
        'n_clicks_required','n_clicks_executed','task_complete'
    ]
    with open(fname, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in data:
            writer.writerow(row)
    logger.info(f"Data saved to {fname}")

# TODO: Add more utilities (e.g., error logging, file management)
