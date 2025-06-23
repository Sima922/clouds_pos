from django import template
from decimal import Decimal, InvalidOperation
from django.conf import settings

register = template.Library()

@register.filter(name='currency')
def currency_filter(value):
    """
    Format a numeric value as currency using settings.
    Falls back to safe defaults if settings are missing.
    """
    try:
        # Convert to Decimal for precision
        if value is None:
            amt = Decimal('0.00')
        else:
            amt = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        # On invalid input, show zero amount
        amt = Decimal('0.00')
    
    # Get settings with safe defaults
    places = getattr(settings, 'DECIMAL_PLACES', 2)
    symbol = getattr(settings, 'CURRENCY_SYMBOL', 'P')
    
    # Format with thousands separator and fixed decimals
    try:
        fmt = f"{{:,.{places}f}}"
        formatted_number = fmt.format(amt)
        return f"{symbol}{formatted_number}"
    except Exception:
        # Ultimate fallback
        return f"{symbol}{amt:.2f}"