from typing import Any

def format_number(val: Any) -> str:
    """Formats numbers into human-readable representation ($ / K / M / B)."""
    if val is None:
        return "N/A"
    try:
        f = float(val)
        if abs(f) >= 1_000_000_000:
            return f"{f / 1_000_000_000:.2f}B"
        if abs(f) >= 1_000_000:
            return f"{f / 1_000_000:.2f}M"
        if abs(f) >= 1_000:
            return f"{f / 1_000:.1f}K"
        if f.is_integer():
            return f"{int(f):,}"
        return f"{f:.2f}"
    except (ValueError, TypeError):
        return str(val)

def format_percentage(val: Any) -> str:
    """Formats decimal or raw percentage value."""
    if val is None:
        return "0.0%"
    try:
        f = float(val)
        if 0.0 <= f <= 1.0:
            f *= 100
        return f"{f:.1f}%"
    except (ValueError, TypeError):
        return "0.0%"
