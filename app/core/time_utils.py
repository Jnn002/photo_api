from datetime import datetime, timezone


def get_current_utc_time() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)
