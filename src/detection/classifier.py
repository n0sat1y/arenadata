from src.config.config import settings
from src.detection.patterns import PII_GROUPS


def classify_protection_level(summary_counts: dict) -> str:
    """
    Классификатор УЗ по логике 152-ФЗ и ТЗ Хакатона:
    - УЗ-1: Специальные > 0 ИЛИ Биометрия > 0
    - УЗ-2: Платежные >= большие объемы ИЛИ Государтсвенные >= большие объемы
    - УЗ-3: Государтсвенные > 0 ИЛИ Обычные >= большие объемы
    - УЗ-4: Обычные > 0
    """
    g_counts = {
        "Ordinary": 0,
        "Government": 0,
        "Payment": 0,
        "Special": 0,
        "Biometric": 0,
    }

    for pii_type, count in summary_counts.items():
        group = PII_GROUPS.get(pii_type)
        if group:
            g_counts[group] += count

    thr = settings.LARGE_THRESHOLDS

    if g_counts["Special"] > 0 or g_counts["Biometric"] > 0:
        return "УЗ-1"
    if (
        g_counts["Payment"] >= thr["Payment"]
        or g_counts["Government"] >= thr["Government"]
    ):
        return "УЗ-2"
    if g_counts["Government"] > 0 or g_counts["Ordinary"] >= thr["Ordinary"]:
        return "УЗ-3"
    if g_counts["Ordinary"] > 0:
        return "УЗ-4"

    return "Нет ПДн"
