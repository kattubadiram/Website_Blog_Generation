# utils/ordinal.py

def ordinal(n: int) -> str:
    """Return the ordinal representation of an integer (e.g., 1 -> '1st', 2 -> '2nd')."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"
