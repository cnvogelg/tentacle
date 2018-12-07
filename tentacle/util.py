"""Some helper functions."""


def ts_to_hms(t):
    """Convert timestamp in seconds to (hours, minutes, seconds)."""
    seconds = int(t)
    minutes = seconds // 60
    seconds -= minutes * 60
    hours = minutes // 60
    minutes -= hours * 60
    hours = hours % 24
    return hours, minutes, seconds
