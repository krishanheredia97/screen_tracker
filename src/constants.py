# --- Constants ---
LOG_FILE = "window_logs.csv"
UNIQUE_WINDOWS_FILE = "unique_windows.txt"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- User States ---
STATE_INACTIVE = "Inactive"
STATE_TRACKING = "Tracking"

# --- Tags ---
TAG_PACING = "Pacing"  # This is a special tag that must always be available

# Default tags - these can be modified by the user
DEFAULT_TAGS = [TAG_PACING, "Learning (work)", "Learning (fun)", "Work"]
