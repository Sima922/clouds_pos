from django.conf import settings
from decimal import Decimal, InvalidOperation

def currency(value):
    """
    Format a numeric value as currency using settings with safe defaults.
    """
    try:
        # Convert to Decimal for precision; handle None values
        if value is None:
            amt = Decimal('0.00')
        else:
            amt = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        # On invalid input, show zero amount
        amt = Decimal('0.00')
    
    # Ensure settings exist with safe defaults
    places = getattr(settings, 'DECIMAL_PLACES', 2)
    symbol = getattr(settings, 'CURRENCY_SYMBOL', 'P')
    
    try:
        # Format with thousands separator and fixed decimals. E.g. 10000 -> "10,000.00"
        fmt = f"{{:,.{places}f}}"
        formatted_number = fmt.format(amt)
        return f"{symbol}{formatted_number}"
    except Exception:
        # Ultimate fallback formatting
        return f"{symbol}{float(amt):.2f}"