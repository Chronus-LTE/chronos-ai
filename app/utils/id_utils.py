"""
ID generation utilities
"""

import uuid
from datetime import datetime, timezone


def generate_short_id(separator: str = "-") -> str:
    """
    Generate a short, readable ID based on timestamp and random string.
    Format: timestamp_hex-random_hex
    Example: 6769d88a-f7k2m
    Args:
        separator: Separator between timestamp and random parts

    Returns:
        Short ID string
    """
    # Convert current timestamp to hex (10 chars)
    timestamp_hex = format(int(datetime.now(timezone.utc).timestamp() * 1000), "x")[:8]

    # Generate random UUID and take first 6 chars
    random_part = str(uuid.uuid4()).replace("-", "")[:6]

    return f"{timestamp_hex}{separator}{random_part}"


def generate_uuid_short() -> str:
    """
    Generate a shorter version of UUID (remove dashes, take first 12 chars).

    Example: 6f8c3d6e1f4a

    Returns:
        Short UUID string
    """
    return str(uuid.uuid4()).replace("-", "")[:12]
