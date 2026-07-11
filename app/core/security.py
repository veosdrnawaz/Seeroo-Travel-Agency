import re

def clean_phone_number(phone: str) -> str:
    """
    Cleans and normalizes Pakistani phone numbers to standard format (e.g. 03001234567).
    """
    # Remove all non-numeric characters
    cleaned = re.sub(r"\D", "", phone)
    
    # If it starts with country code, e.g. 923001234567, replace 92 with 0
    if len(cleaned) == 12 and cleaned.startswith("92"):
        cleaned = "0" + cleaned[2:]
        
    return cleaned

def validate_phone_format(phone: str) -> bool:
    """
    Validates if a cleaned phone number matches Pakistani mobile network digits length.
    """
    cleaned = clean_phone_number(phone)
    # Match standard length e.g. 03001234567 (11 digits, starts with 03)
    return len(cleaned) == 11 and cleaned.startswith("03")
