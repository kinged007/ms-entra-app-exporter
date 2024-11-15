from datetime import datetime, timezone

def nice_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H.%M.%S")