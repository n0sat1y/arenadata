from natasha import Doc, MorphVocab, NewsEmbedding, NewsNERTagger, Segmenter

from src.detection.patterns import KEYWORDS, REGEX_PATTERNS
from src.detection.validation import is_valid_luhn

# Глобальные объекты для воркеров (инициализируются один раз)
segmenter = None
morph_vocab = None
ner_tagger = None


def init_nlp():
    global segmenter, morph_vocab, ner_tagger
    if segmenter is None:
        segmenter = Segmenter()
        morph_vocab = MorphVocab()
        emb = NewsEmbedding()
        ner_tagger = NewsNERTagger(emb)  # Оставили только NER! Синтаксис удален.


def find_pii_in_chunk(text: str) -> dict:
    found_data = {}
    init_nlp()

    # 1. Быстрый Regex
    for cat, pattern in REGEX_PATTERNS.items():
        matches = list(set(pattern.findall(text)))
        if not matches:
            continue

        if cat == "CREDIT_CARD":
            matches = [m for m in matches if is_valid_luhn(m)]

        if matches:
            found_data[cat] = {"count": len(matches), "examples": [matches[0]]}

    # 2. Поиск строгих ключевых фраз
    lower_text = text.lower()
    for cat, kwords in KEYWORDS.items():
        for kw in kwords:
            if kw in lower_text:
                found_data.setdefault(cat, {"count": 0, "examples": []})
                found_data[cat]["count"] += 1
                if not found_data[cat]["examples"]:
                    found_data[cat]["examples"].append(kw)

    # 3. Natasha (NER: ФИО и Адреса)
    # Защита от гигантских строк для NLP
    if len(text) < 100000:
        doc = Doc(text)
        doc.segment(segmenter)
        doc.tag_ner(ner_tagger)

        fio_list, loc_list = [], []
        for span in doc.spans:
            if span.type == "PER":
                span.normalize(morph_vocab)
                if len(span.normal.split()) > 1:
                    fio_list.append(span.normal)
            elif span.type == "LOC":
                span.normalize(morph_vocab)
                loc_list.append(span.normal)

        if fio_list:
            found_data["FIO"] = {"count": len(set(fio_list)), "examples": [fio_list[0]]}
        if loc_list:
            found_data["ADDRESS"] = {
                "count": len(set(loc_list)),
                "examples": [loc_list[0]],
            }

    return found_data
