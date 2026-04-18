import re

PII_GROUPS = {
    "FIO": "Ordinary",
    "EMAIL": "Ordinary",
    "PHONE": "Ordinary",
    "ADDRESS": "Ordinary",
    "BIRTHDAY": "Ordinary",
    "PASSPORT": "Government",
    "SNILS": "Government",
    "INN": "Government",
    "DRIVER_LICENSE": "Government",
    "CREDIT_CARD": "Payment",
    "BANK_ACCOUNT": "Payment",
    "BIK": "Payment",
    "CVV": "Payment",
    "BIOMETRIC": "Biometric",
    "SPECIAL": "Special",
}

REGEX_PATTERNS = {
    "EMAIL": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "PHONE": re.compile(
        r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b|\b9\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b"
    ),
    "BIRTHDAY": re.compile(
        r"\b(?:0[1-9]|[12]\d|3[01])\.(?:0[1-9]|1[0-2])\.(?:19|20)\d{2}\b"
    ),
    "PASSPORT": re.compile(r"\b\d{2}[\s\-]?\d{2}[\s\-]?\d{6}\b"),
    "SNILS": re.compile(r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}\b"),
    "INN": re.compile(r"\b\d{10}(?:\d{2})?\b"),
    "DRIVER_LICENSE": re.compile(
        r"\b\d{2}[\s\-]?[А-ЯЕКМНОРСТУХA-Z]{2}[\s\-]?\d{6}\b", re.IGNORECASE
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:4\d{15}|5[1-5]\d{14}|220[0-4]\d{12})\b"
    ),  # Visa, MC, Mir
    "BANK_ACCOUNT": re.compile(r"\b\d{20}\b"),
    "BIK": re.compile(r"\b04\d{7}\b"),
    "CVV": re.compile(
        r"(?i)\b(?:cvv|cvc|cvv2)[\s\:\-]{1,3}(\d{3})\b"
    ),  # Только рядом с ключевым словом
}

# Строгие ключевые слова и фразы (минимум ложных срабатываний)
KEYWORDS = {
    "BIOMETRIC": [
        "дактилоскопическая карта",
        "биометрический профиль",
        "скан сетчатки",
        "образец голоса",
        "отпечатки пальцев",
    ],
    "SPECIAL": [
        "справка о несудимости",
        "медицинская карта",
        "диагноз: ",
        "история болезни",
        "вероисповедание:",
        "политические убеждения:",
    ],
}
