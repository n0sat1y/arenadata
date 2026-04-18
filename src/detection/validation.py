def is_valid_luhn(card_number: str) -> bool:
    """Алгоритм Луна для проверки банковских карт"""
    card_number = card_number.replace(" ", "").replace("-", "")
    if not card_number.isdigit():
        return False
    total = 0
    for i, digit in enumerate(reversed(card_number)):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def mask_data(text: str, category: str) -> str:
    """Маскирование ПДн для отчета"""
    if category in ["CREDIT_CARD", "BANK_ACCOUNT"]:
        return f"{text[:4]}********{text[-4:]}"
    if category == "FIO":
        parts = text.split()
        return f"{parts[0]} " + " ".join([f"{p[0]}." for p in parts[1:]])
    return "***MASKED***"
