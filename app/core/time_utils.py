from datetime import datetime


def get_current_utc_time() -> datetime:
    """Return the current UTC time without timezone info (naive datetime in UTC)."""
    # return datetime.now(timezone.utc).replace(tzinfo=None)
    return datetime.utcnow()
