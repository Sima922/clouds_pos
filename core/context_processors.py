from django.conf import settings

def currency_settings(request):
    """
    Add currency settings to template context with safe defaults.
    """
    return {
        'CURRENCY_SYMBOL': getattr(settings, 'CURRENCY_SYMBOL', 'P'),
        'CURRENCY': getattr(settings, 'CURRENCY', 'BWP'),
        'THOUSAND_SEPARATOR': getattr(settings, 'THOUSAND_SEPARATOR', True),
        'DECIMAL_PLACES': getattr(settings, 'DECIMAL_PLACES', 2),
        
    }
    