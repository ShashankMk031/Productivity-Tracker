from config import TIMEZONE, DAY_RESET_HOUR, DAY_RESET_LABEL

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
FULL_WEEK = DAY_ORDER[:]

# Aliases kept stable for existing imports (date_service, helpers).
# The values themselves are owned by config.py.
IST = TIMEZONE
DAY_RESET_HOUR_IST = DAY_RESET_HOUR
