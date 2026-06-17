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
    
    # 1. More than 50 days
    if days > 50:
        weeks = days // 7
        months = days // 30
        text = f"{days} days left ({weeks} weeks, {months} month{'s' if months != 1 else ''})"
    
    # 2. Between 2 and 50 days
    elif days >= 2:
        text = f"{days} days left"
        
    # 3. Under 2 days (but >= 24 hours)
    else:
        hours, remainder = divmod(total_seconds, 3600)
        
        if hours >= 24:
            live = True
            d = hours // 24
            h = hours % 24
            text = f"1 day {h} hour{'s' if h != 1 else ''} left"
            
        # 4. Under 24 hours (but >= 1 hour)
        elif hours >= 1:
            live = True
            text = f"{hours} hour{'s' if hours != 1 else ''} left"
            
        # 5. Under 1 hour
        else:
            live = True
            minutes = remainder // 60
            text = f"{minutes} minute{'s' if minutes != 1 else ''} left"
            
    return {
        "text": text,
        "urgency": urgency,
        "live": live
    }
