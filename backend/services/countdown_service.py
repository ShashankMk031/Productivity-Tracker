from datetime import datetime
from zoneinfo import ZoneInfo
from utils.timezone import IST

def get_countdown_info(deadline_str: str) -> dict:
    try:
        deadline = datetime.fromisoformat(deadline_str)
        if len(deadline_str) == 10:  # YYYY-MM-DD
            deadline = deadline.replace(hour=23, minute=59, second=59)
            
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=IST)
    except ValueError:
        return {"text": "Invalid deadline", "urgency": "RED", "live": False}

    now = datetime.now(IST)
    diff = deadline - now
    
    total_seconds = int(diff.total_seconds())
    days = diff.days
    
    if total_seconds < 0:
        return {"text": "Overdue", "urgency": "RED", "live": False}
        
    urgency = "GREEN"
    if days <= 3:
        urgency = "RED"
    elif days <= 14:
        urgency = "YELLOW"
        
    live = False
    if days >= 2:
        text = f"{days} days left"
    else:
        live = True
        hours, remainder = divmod(total_seconds, 3600)
        d = hours // 24
        h = hours % 24
        
        if d > 0:
            text = f"{d} day{'s' if d > 1 else ''} {h} hour{'s' if h != 1 else ''} left"
        else:
            if hours > 0:
                text = f"{h} hour{'s' if h != 1 else ''} left"
            else:
                minutes = remainder // 60
                text = f"{minutes} min{'s' if minutes != 1 else ''} left"
            
    return {
        "text": text,
        "urgency": urgency,
        "live": live
    }
