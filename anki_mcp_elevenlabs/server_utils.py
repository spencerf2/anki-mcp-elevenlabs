def safe_get_error(result):
    """Safely get error from AnkiConnect result, handling string responses"""
    if isinstance(result, str):
        return result
    return result.get("error")
