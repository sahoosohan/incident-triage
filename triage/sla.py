from datetime import datetime, timedelta

TARGET_HOURS = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}

def sla_status(priority, created, resolved=None, now=None):
    now = now or datetime.now()
    target = timedelta(hours=TARGET_HOURS.get(priority, 72))
    used = (resolved or now) - created
    if resolved:
        return "Met" if used <= target else "Breached"
    if used > target: return "Breached"
    return "At risk" if used > 0.75 * target else "On track"
