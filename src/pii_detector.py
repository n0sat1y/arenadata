"""
Детектор персональных данных с использованием регулярных выражений и валидации.
Поддерживает все категории ПДн согласно 152-ФЗ.
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """Класс для хранения найденного ПДн"""
    category: str
    value: str
    position: int
    masked_value: str


class PIIDetector:
    """Детектор персональных данных"""
    
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, re.Pattern]:
        """Инициализация regex паттернов для всех категорий ПДн"""
        return {
            # ФИО (кириллица)
            'fio': re.compile(
                r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b',
                re.UNICODE
            ),
            
            # Телефоны (различные форматы)
            'phone': re.compile(
                r'(?:\+7|8|7)?[\s\-]?\(?[489]\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b'
            ),
            
            # Email
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            
            # Паспорт РФ (серия и номер)
            'passport': re.compile(
                r'\b(?:паспорт|серия)?[\s:]*(\d{2}[\s\-]?\d{2})[\s\-№]+(\d{6})\b',
                re.IGNORECASE
            ),
            
            # СНИЛС
            'snils': re.compile(
                r'\b\d{3}[\-\s]?\d{3}[\-\s]?\d{3}[\-\s]?\d{2}\b'
            ),
            
            # ИНН (12 цифр для физлиц, 10 для юрлиц)
            'inn': re.compile(
                r'\b(?:ИНН[\s:№]*)?(\d{10}|\d{12})\b',
                re.IGNORECASE
            ),
            
            # Водительское удостоверение
            'driver_license': re.compile(
                r'\b\d{2}[\s]?\d{2}[\s]?\d{6}\b'
            ),
            
            # Банковская карта (16 цифр)
            'bank_card': re.compile(
                r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'
            ),
            
            # Банковский счет (20 цифр)
            'bank_account': re.compile(
                r'\b\d{20}\b'
            ),
            
            # БИК
            'bik': re.compile(
                r'\b(?:БИК[\s:№]*)?(04\d{7})\b',
                re.IGNORECASE
            ),
            
            # Дата рождения
            'birth_date': re.compile(
                r'\b(?:0?[1-9]|[12][0-9]|3[01])[\.\-/](?:0?[1-9]|1[012])[\.\-/](?:19|20)\d{2}\b'
            ),
            
            # Адрес (упрощенный паттерн)
            'address': re.compile(
                r'(?:г\.|город|ул\.|улица|пр\.|проспект|д\.|дом)[\s\.]+[А-ЯЁа-яё0-9\s\-,\.]+',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Биометрические данные (ключевые слова)
            'biometric': re.compile(
                r'\b(?:отпечат(?:ок|ки)\s+пальц|радужн(?:ая|ой)\s+оболочк|'
                r'голосов(?:ой|ые)\s+образ|биометр|сканирование\s+лиц|'
                r'распознавание\s+лиц)\w*\b',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Данные о здоровье
            'health': re.compile(
                r'\b(?:диагноз|заболевание|болезнь|лечение|медицинск|'
                r'анализ|обследование|терапия|операция|инвалидность|'
                r'группа\s+здоровья)\w*\b',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Специальные категории
            'special': re.compile(
                r'\b(?:религ|вероисповедание|национальность|раса|'
                r'политическ(?:ие|ая)\s+(?:взгляд|убеждени)|'
                r'профсоюз|интимн)\w*\b',
                re.IGNORECASE | re.UNICODE
            ),
        }
    
    def detect(self, text: str) -> Dict[str, List[PIIMatch]]:
        """
        Обнаружение всех категорий ПДн в тексте
        
        Args:
            text: Текст для анализа
            
        Returns:
            Словарь с найденными ПДн по категориям
        """
        results = {}
        
        for category, pattern in self.patterns.items():
            matches = []
            for match in pattern.finditer(text):
                value = match.group(0)
                
                # Валидация найденных данных
                if self._validate(category, value):
                    masked = self._mask_value(category, value)
                    matches.append(PIIMatch(
                        category=category,
                        value=value,
                        position=match.start(),
                        masked_value=masked
                    ))
            
            if matches:
                results[category] = matches
        
        return results
    
    def _validate(self, category: str, value: str) -> bool:
        """
        Валидация найденных данных
        
        Args:
            category: Категория ПДн
            value: Значение для проверки
            
        Returns:
            True если данные валидны
        """
        if category == 'bank_card':
            return self._validate_luhn(value)
        elif category == 'snils':
            return self._validate_snils(value)
        elif category == 'inn':
            return self._validate_inn(value)
        elif category == 'fio':
            # Проверка что это не просто два слова подряд
            words = value.split()
            return len(words) >= 2 and all(len(w) >= 2 for w in words)
        
        return True
    
    def _validate_luhn(self, card_number: str) -> bool:
        """Проверка номера карты алгоритмом Луна"""
        digits = [int(d) for d in card_number if d.isdigit()]
        if len(digits) != 16:
            return False
        
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        
        return checksum % 10 == 0
    
    def _validate_snils(self, snils: str) -> bool:
        """Проверка контрольной суммы СНИЛС"""
        digits = [int(d) for d in snils if d.isdigit()]
        if len(digits) != 11:
            return False
        
        checksum = sum((9 - i) * digit for i, digit in enumerate(digits[:9]))
        control = digits[9] * 10 + digits[10]
        
        if checksum < 100:
            return control == checksum
        elif checksum == 100 or checksum == 101:
            return control == 0
        else:
            return control == checksum % 101
    
    def _validate_inn(self, inn: str) -> bool:
        """Проверка контрольной суммы ИНН"""
        digits = [int(d) for d in inn if d.isdigit()]
        
        if len(digits) == 10:
            # ИНН юрлица
            weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum = sum(w * d for w, d in zip(weights, digits[:9])) % 11 % 10
            return checksum == digits[9]
        elif len(digits) == 12:
            # ИНН физлица
            weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            
            checksum1 = sum(w * d for w, d in zip(weights1, digits[:10])) % 11 % 10
            checksum2 = sum(w * d for w, d in zip(weights2, digits[:11])) % 11 % 10
            
            return checksum1 == digits[10] and checksum2 == digits[11]
        
        return False
    
    def _mask_value(self, category: str, value: str) -> str:
        """
        Маскирование найденного значения для безопасного отображения
        
        Args:
            category: Категория ПДн
            value: Значение для маскирования
            
        Returns:
            Замаскированное значение
        """
        if category == 'fio':
            parts = value.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1][0]}."
            return value[0] + "*" * (len(value) - 1)
        
        elif category in ['phone', 'bank_card', 'snils', 'inn', 'passport']:
            if len(value) > 6:
                return value[:3] + "*" * (len(value) - 6) + value[-3:]
            return "*" * len(value)
        
        elif category == 'email':
            parts = value.split('@')
            if len(parts) == 2:
                return parts[0][:2] + "***@" + parts[1]
            return value
        
        else:
            # Для остальных категорий - частичное скрытие
            if len(value) > 10:
                return value[:10] + "..."
            return value
    
    def count_by_category(self, results: Dict[str, List[PIIMatch]]) -> Dict[str, int]:
        """
        Подсчет количества найденных ПДн по категориям
        
        Args:
            results: Результаты детектирования
            
        Returns:
            Словарь с количеством находок по категориям
        """
        return {category: len(matches) for category, matches in results.items()}
