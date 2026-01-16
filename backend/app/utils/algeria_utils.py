import re

def normalize_darja(text: str) -> str:
    """
    Normalizes common Darja variations to a standard form for better AI matching
    """
    # Simple normalization logic
    text = text.lower()
    # Replace common phonetics
    text = text.replace("ch", "sh")
    text = text.replace("ou", "u")
    return text.strip()

def validate_wilaya(wilaya_code: str) -> bool:
    """
    Validates Algerian wilaya codes (01-58)
    """
    try:
        code = int(wilaya_code)
        return 1 <= code <= 58
    except (ValueError, TypeError):
        return False

def format_dz_phone(phone: str) -> str:
    """
    Formats phone numbers to +213 format
    """
    # Remove non-digits
    digits = re.sub(r'\D', '', phone)

    if digits.startswith('213') and len(digits) == 12:
        return f"+{digits}"
    elif digits.startswith('0') and len(digits) == 10:
        return f"+213{digits[1:]}"
    elif len(digits) == 9:
        return f"+213{digits}"

    return phone
