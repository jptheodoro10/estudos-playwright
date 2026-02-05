def clean_price(s: str) -> float:
    return float(s.replace("£", "").strip())
