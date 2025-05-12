"""
config.py

Global configuration parameters for the effort-based decision task experiment 
"""

# Number of trials per block (not currently used in practice trials)
N_TRIALS = 42

# TODO: Implement these values as well
# Number of catch trials
N_CATCH_TRIALS = 3

# Monetary magnitudes (placeholder list)
MONEY_MAGNITUDES = [
    1.00, 1.23, 1.46, 1.69, 1.92,
    2.15, 2.38, 2.61, 2.84, 3.07,
    3.30, 3.53, 3.76, 3.99, 4.00
]

# Probabilities of loss
PROBABILITIES = [0.12, 0.50, 0.88]

# Inter-trial interval jitter range (in seconds) 
ITI_RANGE = (1.0, 2.0)

# Click requirements
EASY_CLICKS_REQUIRED = 30  # for practice

# Calibration duration for each key press block (in seconds)
CALIBRATION_DURATION = 10.5

# Practice trials configuration (monetary only)
PRACTICE_TRIALS = [
    {'magnitude_hard': 1.00, 'prob': 0.88},
    {'magnitude_hard': 2.50, 'prob': 0.50},
    {'magnitude_hard': 3.90, 'prob': 0.12},
]

# TODO: Expand to full trial list as per spec
# TODO: Add food domain parameters for the future
