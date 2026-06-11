from zoneinfo import ZoneInfo
import json

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
FULL_WEEK = DAY_ORDER[:]
FULL_WEEK_JSON = json.dumps(FULL_WEEK)
IST = ZoneInfo("Asia/Kolkata")
DAY_RESET_HOUR_IST = 4
DAY_RESET_LABEL = "Day resets at 04:00 AM (IST)"
