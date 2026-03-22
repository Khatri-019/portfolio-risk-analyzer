"""Formatting helpers shared across the portfolio risk analyser."""

import math


def format_currency(value: float, symbol: str = "$", indian_format: bool = True) -> str:
    """Format a float as a currency string.

    When indian_format is True (default), uses Indian lakh/crore grouping (e.g. ₹1,23,456.78).
    When indian_format is False, uses standard thousands grouping (e.g. $1,234,567.89).
    """
    negative = value < 0
    value = abs(value)

    integer_part = int(math.floor(value))
    fractional = round(value - integer_part, 2)
    decimal_str = f"{fractional:.2f}"[1:]  # ".78"

    digits = str(integer_part)

    if not indian_format:
        grouped = f"{integer_part:,}"
    elif len(digits) <= 3:
        grouped = digits
    else:
        # last 3 digits are the hundreds group; remaining digits group in pairs
        last_three = digits[-3:]
        remaining = digits[:-3]
        pairs: list[str] = []
        while len(remaining) > 2:
            pairs.append(remaining[-2:])
            remaining = remaining[:-2]
        pairs.append(remaining)
        pairs.reverse()
        grouped = ",".join(pairs) + "," + last_three

    formatted = f"{symbol}{grouped}{decimal_str}"
    return f"-{formatted}" if negative else formatted


def format_pct(value: float) -> str:
    """Format a float as a percentage string with explicit sign."""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"
