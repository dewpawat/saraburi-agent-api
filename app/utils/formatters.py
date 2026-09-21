from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Optional, Mapping

def safe_str(val: Any, default: Optional[str] = None) -> Optional[str]:
    """
    Safely converts a value to string.
    Returns `default` if the value is None, empty, or string "None"/"null".
    """
    if val is None:
        return default
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null"):
        return default
    return s

def safe_date_iso(val: Any) -> Optional[str]:
    """
    Safely formats a date, datetime, time, or date string into ISO 8601 string.
    Handles '0000-00-00', None, and invalid strings gracefully without throwing exceptions.
    """
    if val is None:
        return None
    if isinstance(val, (datetime, date, time)):
        try:
            return val.isoformat()
        except Exception:
            return None
    if isinstance(val, str):
        cleaned = val.strip()
        if cleaned in ("", "0000-00-00", "0000-00-00 00:00:00", "None", "null"):
            return None
        return cleaned
    try:
        return str(val).strip()
    except Exception:
        return None

def safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely converts a value (string, int, Decimal) to float.
    Returns `default` on None or conversion error.
    """
    if val is None:
        return default
    if isinstance(val, (int, float, Decimal)):
        return float(val)
    try:
        s = str(val).strip()
        if s == "" or s.lower() in ("none", "null"):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default

def safe_int(val: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Safely converts a value to integer.
    Returns `default` on None or conversion error.
    """
    if val is None:
        return default
    if isinstance(val, int):
        return val
    try:
        s = str(val).strip()
        if s == "" or s.lower() in ("none", "null"):
            return default
        return int(float(s))
    except (ValueError, TypeError):
        return default

def safe_get(row: Any, key: str, default: Any = None) -> Any:
    """
    Safely retrieves a value from a RowMapping, dictionary, or object.
    Prevents KeyError if key is missing.
    """
    if row is None:
        return default
    if isinstance(row, Mapping) or hasattr(row, "get"):
        return row.get(key, default)
    if hasattr(row, "__getitem__"):
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default
    return getattr(row, key, default)
