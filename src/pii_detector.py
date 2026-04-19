"""
Детектор персональных данных с использованием регулярных выражений и валидации.
Поддерживает все категории ПДн согласно 152-ФЗ.
Ужесточенная версия: требует комбинации данных для идентификации субъекта.
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """Класс для хранения найденного ПДн"""
    category: str
    value: str
    position: int
    masked_value: str


class PIIDetector:
    """Детектор персональных данных с ужесточенными правилами"""
    
    # Минимальное расстояние между связанными ПДн (в символах)
    PROXIMITY_THRESHOLD = 500
    
    # Минимальное количество уникальных записей ПДн в файле
    MIN_UNIQUE_RECORDS = 2
    
    def __init__(self):
        self.patterns = self._init_patterns()
        # Словарь распространенных русских имен и фамилий для валидации
        self.common_names = self._load_common_names()
    
    def _load_common_names(self) -> Set[str]:
        """Загрузка списка распространенных русских имен и фамилий"""
        # Распространенные русские имена
        names = {
            'александр', 'алексей', 'андрей', 'антон', 'артем', 'борис', 'вадим', 'валентин',
            'валерий', 'василий', 'виктор', 'виталий', 'владимир', 'владислав', 'вячеслав',
            'геннадий', 'георгий', 'григорий', 'даниил', 'денис', 'дмитрий', 'евгений', 'егор',
            'иван', 'игорь', 'илья', 'кирилл', 'константин', 'леонид', 'максим', 'михаил',
            'никита', 'николай', 'олег', 'павел', 'петр', 'роман', 'сергей', 'станислав',
            'степан', 'тимофей', 'федор', 'юрий', 'ярослав',
            'александра', 'алина', 'алла', 'анастасия', 'анна', 'валентина', 'валерия', 'вера',
            'виктория', 'галина', 'дарья', 'диана', 'екатерина', 'елена', 'елизавета', 'жанна',
            'зоя', 'инна', 'ирина', 'кристина', 'ксения', 'лариса', 'лидия', 'любовь', 'людмила',
            'маргарита', 'марина', 'мария', 'надежда', 'наталья', 'нина', 'оксана', 'ольга',
            'полина', 'раиса', 'светлана', 'софья', 'тамара', 'татьяна', 'ульяна', 'юлия'
        }
        
        # Распространенные русские фамилии
        surnames = {
            'иванов', 'петров', 'сидоров', 'смирнов', 'кузнецов', 'попов', 'васильев', 'соколов',
            'михайлов', 'новиков', 'федоров', 'морозов', 'волков', 'алексеев', 'лебедев',
            'семенов', 'егоров', 'павлов', 'козлов', 'степанов', 'николаев', 'орлов', 'андреев',
            'макаров', 'никитин', 'захаров', 'зайцев', 'соловьев', 'борисов', 'яковлев',
            'григорьев', 'романов', 'воробьев', 'сергеев', 'кузьмин', 'фролов', 'александров',
            'дмитриев', 'королев', 'гусев', 'киселев', 'ильин', 'максимов', 'поляков', 'сорокин',
            'виноградов', 'ковалев', 'белов', 'медведев', 'антонов', 'тарасов', 'жуков',
            'баранов', 'филиппов', 'комаров', 'давыдов', 'беляев', 'герасимов', 'богданов',
            'осипов', 'сидоров', 'матвеев', 'титов', 'марков', 'миронов', 'крылов', 'куликов',
            'карпов', 'власов', 'мельников', 'денисов', 'гаврилов', 'тихонов', 'казаков',
            'афанасьев', 'данилов', 'савельев', 'тимофеев', 'фомин', 'чернов', 'абрамов',
            'мартынов', 'ефимов', 'федотов', 'щербаков', 'назаров', 'калинин', 'исаев',
            'чернышев', 'быков', 'маслов', 'родионов', 'коновалов', 'лазарев', 'воронин',
            'климов', 'филатов', 'пономарев', 'голубев', 'кудрявцев', 'прохоров', 'наумов',
            'потапов', 'журавлев', 'овчинников', 'трофимов', 'леонов', 'соболев', 'ермаков',
            'колесников', 'гончаров', 'емельянов', 'никифоров', 'грачев', 'котов', 'гришин',
            'ефремов', 'архипов', 'громов', 'кириллов', 'панов', 'ситников', 'симонов',
            'мишин', 'фадеев', 'комиссаров', 'мамонтов', 'носков', 'гуляев', 'шаров',
            'устинов', 'вишняков', 'евсеев', 'лаврентьев', 'брагин', 'константинов',
            'корнилов', 'авдеев', 'зимин', 'петухов', 'кудряшов', 'азаров', 'бирюков'
        }
        
        # Добавляем женские варианты фамилий
        all_names = names.copy()
        for surname in surnames:
            all_names.add(surname)
            all_names.add(surname + 'а')  # женский вариант
        
        return all_names
    
    def _init_patterns(self) -> Dict[str, re.Pattern]:
        """Инициализация regex паттернов для всех категорий ПДн"""
        return {
            # ФИО (кириллица) - требуем минимум 3 слова (Фамилия Имя Отчество)
            'fio': re.compile(
                r'\b[А-ЯЁ][а-яё]{2,}\s+[А-ЯЁ][а-яё]{2,}\s+[А-ЯЁ][а-яё]{2,}\b',
                re.UNICODE
            ),
            
            # Телефоны (различные форматы) - российские номера
            'phone': re.compile(
                r'(?:\+7|8|7)[\s\-]?\(?[489]\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b'
            ),
            
            # Email - требуем личные email (не корпоративные шаблоны)
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            
            # Паспорт РФ (серия и номер) - с контекстом
            'passport': re.compile(
                r'(?:паспорт|серия|passport)[\s:№]*(\d{2}[\s\-]?\d{2})[\s\-№]+(\d{6})\b',
                re.IGNORECASE
            ),
            
            # СНИЛС - с контекстом
            'snils': re.compile(
                r'(?:СНИЛС|снилс)[\s:№]*(\d{3}[\-\s]?\d{3}[\-\s]?\d{3}[\-\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            # ИНН (12 цифр для физлиц, 10 для юрлиц) - с контекстом
            'inn': re.compile(
                r'(?:ИНН|инн)[\s:№]*(\d{10}|\d{12})\b',
                re.IGNORECASE
            ),
            
            # Водительское удостоверение - с контекстом
            'driver_license': re.compile(
                r'(?:водительск|удостоверение|ВУ)[\s\w]*[\s:№]*(\d{2}[\s]?\d{2}[\s]?\d{6})\b',
                re.IGNORECASE
            ),
            
            # Банковская карта (16 цифр) - с контекстом
            'bank_card': re.compile(
                r'(?:карт|card)[\s\w]*[\s:№]*(\d{4}[\s\-]?){3}\d{4}\b',
                re.IGNORECASE
            ),
            
            # Банковский счет (20 цифр) - с контекстом
            'bank_account': re.compile(
                r'(?:счет|счёт|account|р/с|расчетный)[\s\w]*[\s:№]*(\d{20})\b',
                re.IGNORECASE
            ),
            
            # БИК - с контекстом
            'bik': re.compile(
                r'(?:БИК|бик)[\s:№]*(04\d{7})\b',
                re.IGNORECASE
            ),
            
            # Дата рождения - с контекстом
            'birth_date': re.compile(
                r'(?:дата\s+рождения|д\.р\.|родился|родилась|birth)[\s:]*(\d{1,2}[\.\-/]\d{1,2}[\.\-/](?:19|20)\d{2})\b',
                re.IGNORECASE
            ),
            
            # Адрес (полный с номером дома) - требуем более полный адрес
            'address': re.compile(
                r'(?:адрес|address|проживает|зарегистрирован)[\s:]*(?:г\.|город|ул\.|улица|пр\.|проспект)[\s\.]+[А-ЯЁа-яё0-9\s\-,\.]+(?:д\.|дом)[\s\.]*\d+',
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
        Обнаружение всех категорий ПДн в тексте с ужесточенными правилами
        
        Args:
            text: Текст для анализа
            
        Returns:
            Словарь с найденными ПДн по категориям (только если есть комбинации)
        """
        # Шаг 1: Найти все совпадения по паттернам
        raw_results = {}
        
        for category, pattern in self.patterns.items():
            matches = []
            for match in pattern.finditer(text):
                value = match.group(0)
                
                # Валидация найденных данных
                if self._validate(category, value, text, match.start()):
                    masked = self._mask_value(category, value)
                    matches.append(PIIMatch(
                        category=category,
                        value=value,
                        position=match.start(),
                        masked_value=masked
                    ))
            
            if matches:
                raw_results[category] = matches
        
        # Шаг 2: Проверка на наличие комбинаций данных
        if not self._has_valid_combinations(raw_results, text):
            return {}
        
        # Шаг 3: Фильтрация дубликатов и проверка минимального количества
        filtered_results = self._filter_duplicates(raw_results)
        
        # Шаг 4: Проверка минимального количества уникальных записей
        if not self._has_minimum_records(filtered_results):
            return {}
        
        return filtered_results
    
    def _has_valid_combinations(self, results: Dict[str, List[PIIMatch]], text: str) -> bool:
        """
        Проверка наличия валидных комбинаций ПДн для идентификации субъекта
        
        Согласно 152-ФЗ, ПДн - это информация, позволяющая идентифицировать субъекта.
        Требуем:
        1. ФИО + хотя бы один идентификатор (телефон/email/паспорт/адрес/дата рождения)
        2. Или несколько сильных идентификаторов (паспорт + СНИЛС, банковская карта + телефон)
        3. Или специальные категории (биометрия, здоровье) + любой идентификатор
        """
        if not results:
            return False
        
        categories = set(results.keys())
        
        # Специальные категории всегда считаются ПДн если есть хоть какой-то идентификатор
        special_cats = {'biometric', 'health', 'special'}
        if categories & special_cats:
            # Проверяем наличие хотя бы одного идентификатора
            identifiers = {'fio', 'phone', 'email', 'passport', 'snils', 'inn', 
                          'driver_license', 'address', 'birth_date'}
            if categories & identifiers:
                return True
        
        # Комбинация 1: ФИО + идентификатор
        if 'fio' in categories:
            identifiers = {'phone', 'email', 'passport', 'snils', 'inn', 
                          'driver_license', 'address', 'birth_date', 'bank_card', 'bank_account'}
            if categories & identifiers:
                # Проверяем близость ФИО и идентификатора
                if self._check_proximity(results, 'fio', identifiers):
                    return True
        
        # Комбинация 2: Паспорт + другой государственный идентификатор
        if 'passport' in categories:
            gov_ids = {'snils', 'inn', 'driver_license'}
            if categories & gov_ids:
                return True
        
        # Комбинация 3: Банковская карта + контактные данные
        if 'bank_card' in categories or 'bank_account' in categories:
            contacts = {'phone', 'email', 'fio'}
            if categories & contacts:
                return True
        
        # Комбинация 4: СНИЛС + ИНН
        if 'snils' in categories and 'inn' in categories:
            return True
        
        # Комбинация 5: Телефон + Email + Адрес (достаточно для идентификации)
        contact_combo = {'phone', 'email', 'address'}
        if len(categories & contact_combo) >= 2:
            return True
        
        return False
    
    def _check_proximity(self, results: Dict[str, List[PIIMatch]], 
                        main_category: str, other_categories: Set[str]) -> bool:
        """
        Проверка близости данных разных категорий
        
        Args:
            results: Найденные ПДн
            main_category: Основная категория (например, 'fio')
            other_categories: Другие категории для проверки близости
            
        Returns:
            True если найдены близкие данные
        """
        if main_category not in results:
            return False
        
        main_matches = results[main_category]
        
        for main_match in main_matches:
            main_pos = main_match.position
            
            # Проверяем все другие категории
            for other_cat in other_categories:
                if other_cat not in results:
                    continue
                
                for other_match in results[other_cat]:
                    other_pos = other_match.position
                    distance = abs(main_pos - other_pos)
                    
                    # Если данные находятся близко друг к другу
                    if distance <= self.PROXIMITY_THRESHOLD:
                        return True
        
        return False
    
    def _filter_duplicates(self, results: Dict[str, List[PIIMatch]]) -> Dict[str, List[PIIMatch]]:
        """
        Фильтрация дубликатов - оставляем только уникальные значения
        
        Args:
            results: Найденные ПДн
            
        Returns:
            Отфильтрованные результаты
        """
        filtered = {}
        
        for category, matches in results.items():
            # Используем set для отслеживания уникальных значений
            seen_values = set()
            unique_matches = []
            
            for match in matches:
                # Нормализуем значение для сравнения
                normalized = self._normalize_value(match.value)
                
                if normalized not in seen_values:
                    seen_values.add(normalized)
                    unique_matches.append(match)
            
            if unique_matches:
                filtered[category] = unique_matches
        
        return filtered
    
    def _normalize_value(self, value: str) -> str:
        """
        Нормализация значения для сравнения (удаление пробелов, дефисов и т.д.)
        
        Args:
            value: Значение для нормализации
            
        Returns:
            Нормализованное значение
        """
        # Удаляем все пробелы, дефисы, скобки
        normalized = re.sub(r'[\s\-\(\)]+', '', value.lower())
        return normalized
    
    def _has_minimum_records(self, results: Dict[str, List[PIIMatch]]) -> bool:
        """
        Проверка минимального количества уникальных записей ПДн
        
        Args:
            results: Найденные ПДн
            
        Returns:
            True если достаточно записей
        """
        if not results:
            return False
        
        # Для специальных категорий достаточно одной записи
        special_cats = {'biometric', 'health', 'special'}
        if any(cat in results for cat in special_cats):
            return True
        
        # Для остальных категорий требуем минимум MIN_UNIQUE_RECORDS уникальных записей
        # Считаем общее количество уникальных записей по ключевым категориям
        key_categories = {'fio', 'phone', 'email', 'passport', 'snils', 'inn'}
        total_records = sum(
            len(matches) for cat, matches in results.items() 
            if cat in key_categories
        )
        
        return total_records >= self.MIN_UNIQUE_RECORDS
    
    def _validate(self, category: str, value: str, text: str, position: int) -> bool:
        """
        Валидация найденных данных с учетом контекста
        
        Args:
            category: Категория ПДн
            value: Значение для проверки
            text: Полный текст для контекстной проверки
            position: Позиция найденного значения в тексте
            
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
            # Проверка что это реальное ФИО (3 слова, проверка по словарю имен)
            words = value.split()
            if len(words) != 3:
                return False
            
            # Проверяем минимальную длину слов
            if not all(len(w) >= 3 for w in words):
                return False
            
            # Проверяем, что хотя бы одно слово есть в словаре имен/фамилий
            words_lower = [w.lower() for w in words]
            if not any(w in self.common_names for w in words_lower):
                return False
            
            # Проверяем контекст - исключаем заголовки типа "Январь Февраль Март"
            context = self._get_context(text, position, 50)
            # Если рядом есть слова-маркеры ФИО, это хороший знак
            fio_markers = ['фио', 'ф.и.о', 'имя', 'фамилия', 'отчество', 'сотрудник', 'клиент', 'пациент']
            has_marker = any(marker in context.lower() for marker in fio_markers)
            
            return has_marker or True  # Если есть маркер - точно ФИО, иначе полагаемся на словарь
        
        elif category == 'email':
            # Исключаем типовые корпоративные email без личных данных
            generic_patterns = ['info@', 'admin@', 'support@', 'contact@', 'sales@', 
                              'office@', 'help@', 'service@', 'noreply@', 'no-reply@']
            if any(value.lower().startswith(pattern) for pattern in generic_patterns):
                return False
            return True
        
        elif category == 'phone':
            # Базовая валидация - номер должен быть корректным
            digits = re.sub(r'\D', '', value)
            return len(digits) == 11 and digits[0] in ['7', '8']
        
        elif category == 'address':
            # Проверяем, что адрес содержит номер дома
            return bool(re.search(r'д\.\s*\d+|дом\s+\d+', value, re.IGNORECASE))
        
        return True
    
    def _get_context(self, text: str, position: int, window: int = 100) -> str:
        """
        Получение контекста вокруг найденного значения
        
        Args:
            text: Полный текст
            position: Позиция найденного значения
            window: Размер окна контекста (символов до и после)
            
        Returns:
            Контекст вокруг значения
        """
        start = max(0, position - window)
        end = min(len(text), position + window)
        return text[start:end]
    
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
