import spacy
from src.detection.patterns import KEYWORDS, REGEX_PATTERNS
from src.detection.validation import is_valid_luhn
from src.config.config import settings

# Глобальный объект nlp для воркера
nlp = None

def init_nlp():
    global nlp
    if nlp is None:
        try:
            # Загружаем модель, отключаем ненужные компоненты для ускорения
            # Нам нужны только 'ner' и сопутствующие для нормализации (если требуется)
            nlp = spacy.load(settings.SPACY_MODEL, disable=["parser", "attribute_ruler"])
        except OSError:
            # Фолбэк, если модель не скачана (хотя лучше скачать заранее)
            import os
            os.system(f"python -m spacy download {settings.SPACY_MODEL}")
            nlp = spacy.load(settings.SPACY_MODEL)

def find_pii_in_chunk(text: str) -> dict:
    found_data = {}
    init_nlp()

    # 1. Быстрый Regex (остается без изменений)
    for cat, pattern in REGEX_PATTERNS.items():
        matches = list(set(pattern.findall(text)))
        if not matches:
            continue
        if cat == "CREDIT_CARD":
            matches = [m for m in matches if is_valid_luhn(m)]
        if matches:
            found_data[cat] = {"count": len(matches), "examples": [matches[0]]}

    # 2. Поиск строгих ключевых фраз (остается без изменений)
    lower_text = text.lower()
    for cat, kwords in KEYWORDS.items():
        for kw in kwords:
            if kw in lower_text:
                found_data.setdefault(cat, {"count": 0, "examples": []})
                found_data[cat]["count"] += 1
                if not found_data[cat]["examples"]:
                    found_data[cat]["examples"].append(kw)

    # 3. spaCy NER (ФИО и Адреса)
    if 0 < len(text) < 100000:
        doc = nlp(text)
        
        fio_list, loc_list = [], []
        
        for ent in doc.ents:
            # PER - Person (ФИО), LOC - Location (Адреса)
            if ent.label_ == "PER":
                # В spaCy ent.lemma_ возвращает нормальную форму
                # Проверяем, что это похоже на ФИО (минимум 2 слова)
                if len(ent.text.split()) > 1:
                    fio_list.append(ent.lemma_)
            elif ent.label_ == "LOC":
                loc_list.append(ent.lemma_)

        if fio_list:
            found_data["FIO"] = {"count": len(set(fio_list)), "examples": [fio_list[0]]}
        if loc_list:
            found_data["ADDRESS"] = {
                "count": len(set(loc_list)),
                "examples": [loc_list[0]],
            }

    return found_data
